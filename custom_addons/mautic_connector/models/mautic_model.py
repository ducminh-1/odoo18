import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import connector, mautic_api

_logger = logging.getLogger(__name__)


class MauticAPI(models.TransientModel):
    _name = "mautic.api"
    _description = "Mautic API"

    def _get_client(self):
        def get_auth_info(key):
            ICP = self.env["ir.config_parameter"].sudo()
            return ICP.get_param(key)

        client = connector.MauticBasicAuthClient(
            base_url=get_auth_info("mautic_api_base_url"),
            username=get_auth_info("mautic_api_user"),
            password=get_auth_info("mautic_api_password"),
        )
        return client

    def get_api_obj(self, endpoint):
        """
        endpoint = contact/segment
        """
        if endpoint == "contact":
            return mautic_api.Contacts(client=self._get_client())
        elif endpoint == "segment":
            return mautic_api.Segments(client=self._get_client())


class MauticContactSegment(models.Model):
    _name = "mautic.segment"
    _description = "Mautic Contact Segments"

    active = fields.Boolean(default=True, readonly=True)
    name = fields.Char(required=True, readonly=True)
    segment_alias = fields.Char(required=True, readonly=True)

    _sql_constraints = [
        (
            "segment_alias_uniq",
            "unique (segment_alias)",
            "The segment alias must be unique!",
        ),
    ]

    def name_get(self):
        result = []
        for segment in self:
            # name = segment.name + " (%s)" % segment.segment_alias
            name = segment.name + f" ({segment.segment_alias})"
            result.append((segment.id, name))
        return result

    def _get_segment_list(self):
        API = self.env["mautic.api"]
        resp_stt, segment_result = API.get_api_obj("segment").get_list()
        _logger.info(f"Response Status: {resp_stt}, Segment Result: {segment_result}")
        return segment_result

    def update_mautic_contact_segment(self):
        try:
            segment_data = self._get_segment_list()
            _logger.info(f"Crawling segments from Mautic: {segment_data}")
            if segment_data.get("total") > 0:
                lists = segment_data.get("lists")
                active_segment = []
                for key, _val in lists.items():
                    name = lists.get(key).get("name")
                    alias = lists.get(key).get("alias")
                    active_segment.append(alias)
                    exist_alias = self.with_context(active_test=False).search(
                        [("segment_alias", "=", alias)], limit=1
                    )
                    if not exist_alias and alias:
                        self.create([{"name": name, "segment_alias": alias}])
                    else:
                        exist_alias.write({"name": name, "active": True})
                for record in self.search([]):
                    if record.segment_alias not in active_segment:
                        record.write({"active": False})
        except Exception as e:
            _logger.error(
                _("Failed to crawl segments from Mautic: {error}").format(error=e)
            )


class MauticMigrateConfig(models.Model):
    _name = "mautic.migrate.config"
    _description = "Mautic Migrate Config"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    state = fields.Selection(
        [
            ("draft", "Not Confirmed"),
            ("done", "Confirmed"),
        ],
        string="Status",
        index=True,
        readonly=True,
        copy=False,
        default="draft",
        tracking=True,
    )
    execute_method = fields.Selection(
        [("manual", "Manual"), ("auto", "Automation")],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    segment_filter_type = fields.Selection(
        [("none", "None"), ("one", "Only One Segment"), ("common", "Segments Common")],
        string="Segment Filter Type",
        default="none",
        required=True,
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    segment_ids = fields.Many2many(
        "mautic.segment",
        "mautic_config_segment",
        "mautic_config_id",
        "segment_id",
        copy=False,
    )
    tag_filter = fields.Boolean(
        default=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    tag_name = fields.Char(
        "Mautic Tag",
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
        help='"Mautic tag name" which is used to filter contacts by!',
    )
    team_id = fields.Many2one(
        "crm.team",
        string="Sales Team Default",
        help="The new leads are set this sales team automatically! ",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        help="New leads are assigned to this User",
        domain=lambda self: [
            ("groups_id", "in", self.env.ref("sales_team.group_sale_salesman").id)
        ],
    )
    convert_type = fields.Selection(
        [
            ("check_exist", "Check Existing Leads"),
            ("convert_all", "Convert All Contacts"),
        ],
        readonly=True,
        states={"draft": [("readonly", False)]},
        default="check_exist",
        required=True,
        string="Convert Type",
    )
    date = fields.Datetime(string="Last Fetch Date", readonly=True)
    lead_type = fields.Selection(
        [("lead", "Lead"), ("opportunity", "Opportunity")],
        required=True,
        tracking=True,
        default="lead",
        help="Type is used to create Leads or Opportunities",
    )
    stage_id = fields.Many2one("crm.stage")
    date_deadline = fields.Integer(
        "Expected Date", help="Used to set Expected Closing for the lead. "
    )
    lead_count = fields.Integer(compute="_compute_lead_count", string="Lead Count")

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "name" not in default:
            default["name"] = _("%s (copy)") % self.name
        return super().copy(default=default)

    @api.depends()
    def _compute_lead_count(self):
        results = (
            self.env["crm.lead"]
            .with_context(active_test=False)
            .read_group(
                [("mautic_config_id", "in", self.ids)],
                ["mautic_config_id"],
                ["mautic_config_id"],
            )
        )
        dic = {}
        for x in results:
            dic[x["mautic_config_id"][0]] = x["mautic_config_id_count"]
        for record in self:
            record["lead_count"] = dic.get(record.id, 0)

    @api.constrains("segment_filter_type", "segment_ids")
    def check_valid_segment(self):
        for config in self:
            if config.segment_filter_type == "none" and not config.tag_filter:
                raise UserError("You must set Contact Segment or Tag to filter! ")
            if config.segment_filter_type != "none" and not config.segment_ids:
                raise UserError("You must set one Contact Segment at least! ")
            if config.segment_filter_type == "one" and len(config.segment_ids) > 1:
                raise UserError(
                    'Select only one Contact Segment with filter type: "Only One Segment" ! '  # noqa: E501
                )

    def _get_search_str_by_segment(self):
        """
        Get a search cmd by segments
        :param common: bool
        :param segments_alias: list segments, if common = False, a only segment in list
        :return: str
        """
        if self.segment_filter_type == "none":
            return None
        elif self.segment_filter_type == "common":
            segments_alias = [seg.segment_alias for seg in self.segment_ids]
            search_cmd = "common:" + "+".join(segments_alias)
        else:
            # search_cmd = "segment:%s" % self.segment_ids[0].segment_alias
            search_cmd = f"segment:{self.segment_ids[0].segment_alias}"
        return search_cmd

    def _get_search_str_by_tag(self):
        """
        Get a search cmd by tag
        :param tags: str tag defined in Mautic Contact
        :return: str
        """
        if self.tag_filter:
            # return 'tag:"%s"' % self.tag_name
            return f'tag:"{self.tag_name}"'
        else:
            return None

    def _get_search_str_by_email(self, email):
        """
        Get a search cmd by email
        :param email: str email
        :return: str
        """
        if email:
            return "email:%s"
        return None

    def get_search_command(self):
        search = []
        segment_cmd = self._get_search_str_by_segment()
        if segment_cmd:
            search.append(segment_cmd)
        tag_cmd = self._get_search_str_by_tag()
        if tag_cmd:
            search.append(tag_cmd)
        return " ".join(search) or ""

    def get_contact_data_from_mautic(self):
        """
        : return
        1. state True or False
        2. result: [] or error content
        """

        search_cmd = self.get_search_command()
        API = self.env["mautic.api"]
        resp_state, data = API.get_api_obj("contact").get_list(
            search=search_cmd, limit=500
        )

        if resp_state:
            result = []
            if int(data.get("total")) > 0:
                contacts = data.get("contacts")
                for _key, val in contacts.items():
                    result.append(val.get("fields", {}).get("all"))
        else:
            result = data

        return resp_state, result

    def button_set_draft(self):
        self.write({"state": "draft"})
        return True

    def button_confirm(self):
        self.write({"state": "done"})

    def _prepare_leads_list(self):
        """
        Prepare the new lead data
        """
        self.ensure_one()
        resp_state, data = self.get_contact_data_from_mautic()
        if not resp_state:
            error_content = data
            return resp_state, error_content

        # Set default UTM Source for the new leads
        source_id = self.env.ref("mautic_connector.utm_source_mautic").id

        # Get stage_id
        if self.stage_id:
            stage_id = self.stage_id.id
        else:
            stage_id = self.env["crm.lead"].search([], limit=1).id or False

        lead_values = []
        if self.convert_type == "check_exist":
            mautic_ids_list = [rec.get("id") for rec in data]
            existing_mautic_id = (
                self.env["crm.lead"]
                .search([("mautic_id", "in", mautic_ids_list)])
                .mapped("mautic_id")
            )
            for item in data:
                if int(item.get("id")) not in existing_mautic_id:
                    name_value = [item.get("lastname"), item.get("firstname")]
                    name = " ".join([el for el in name_value if el]).strip()
                    lead_values.append(
                        {
                            "name": name or item.get("email"),
                            "contact_name": name,
                            "title": "",
                            "email_from": item.get("email"),
                            "partner_name": item.get("company"),
                            "function": item.get("position"),
                            "phone": item.get("phone"),
                            "mobile": item.get("mobile"),
                            "street": item.get("address1"),
                            "street2": item.get("address2"),
                            "website": item.get("website"),
                            "source_id": source_id,
                            "user_id": self.user_id.id,
                            "team_id": self.team_id.id,
                            "date_deadline": self.date_deadline
                            and fields.Datetime.now()
                            + timedelta(days=self.date_deadline)
                            or False,
                            "stage_id": stage_id,
                            "type": self.lead_type,
                            "mautic_id": item.get("id"),
                            "mautic_config_id": self.id,
                        }
                    )
        elif self.convert_type == "convert_all":
            for item in data:
                name_value = [item.get("lastname"), item.get("firstname")]
                name = " ".join([el for el in name_value if el]).strip()
                lead_values.append(
                    {
                        "name": name or item.get("email"),
                        "contact_name": name,
                        "title": "",
                        "email_from": item.get("email"),
                        "partner_name": item.get("company"),
                        "function": item.get("position"),
                        "phone": item.get("phone"),
                        "mobile": item.get("mobile"),
                        "street": item.get("address1"),
                        "street2": item.get("address2"),
                        "website": item.get("website"),
                        "source_id": source_id,
                        "user_id": self.user_id.id,
                        "team_id": self.team_id.id,
                        "date_deadline": fields.Datetime.now()
                        + timedelta(days=self.date_deadline),
                        "stage_id": stage_id,  # FIXME
                        "type": self.lead_type,
                        "mautic_id": item.get("id"),
                        "mautic_config_id": self.id,
                    }
                )
        return resp_state, lead_values

    def action_open_wizard_confirm(self):
        self.ensure_one()
        view_id = self.env.ref("mautic_connector.mautic_confirm_migration_view_form")
        resp_state, data = self._prepare_leads_list()
        if not resp_state:
            response_state = False
            lead_count = 0
            error_content = data
        else:
            response_state = True
            lead_count = len(data)
            error_content = False
        return {
            "name": "Confirm Lead Migration",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mautic.confirm.migration",
            "views": [(False, "form")],
            "view_id": view_id.id,  # FIXME
            "target": "new",
            "context": {
                "active_id": self.id,
                "default_config_id": self.id,
                "default_lead_count": lead_count,
                "default_response_ok": response_state,
                "default_error_content": error_content,
            },
        }

    def action_process_migrate_leads(self):
        response_state, new_lead_list = self._prepare_leads_list()
        if response_state and new_lead_list:
            new_leads = self.env["crm.lead"].create(new_lead_list)
            for lead in new_leads:
                lead.message_post(
                    body="This lead/opportunity was created by Mautic Connector App! "
                    "<br/>Mautic ID: %s <br/> Mautic Config: <a href='#' data-oe-model='%s' data-oe-id='%s'>%s</a>"  # noqa: E501
                    % (lead.mautic_id, self._name, lead.mautic_config_id.id, self.name)
                )
            self.date = fields.Datetime.now()
            # self.message_post(
            #     body="<b>%s Lead/Opportunity(s)</b> were created successfully by %s method! "
            #     % (len(new_lead_list), self.execute_method)
            # )
            self.message_post(
                body=_(
                    "<b>{count} Lead/Opportunity(s)</b> were created successfully by {method} method! "
                ).format(count=len(new_lead_list), method=self.execute_method)
            )
        return True

    def action_update_contact_segment(self):
        return self.env["mautic.segment"].update_mautic_contact_segment()

    def _cron_auto_migrate_lead(self):
        configs = self.search([]).filtered(
            lambda rec: rec.state == "done" and rec.execute_method == "auto"
        )
        for config in configs:
            config.action_process_migrate_leads()
        return True
