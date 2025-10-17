import logging
import re

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv.expression import get_unaccent_wrapper

_logger = logging.getLogger(__name__)


class LoyaltyLevel(models.Model):
    _name = "loyalty.level"
    _description = "Loyalty Level"
    _order = "point_policy desc"

    name = fields.Char(string="Name", required=True)
    point_policy = fields.Integer(string="Point")
    color = fields.Integer(string="Color")
    # birthday_coupon_program_id = fields.Many2one('coupon.program', 'Birthday Coupon Program')
    birthday_coupon_program_id = fields.Many2one(
        "loyalty.program", "Birthday Coupon Program"
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    channel_id = fields.Many2one("sale.channel", "Kênh", tracking=True)
    loyalty_level_id = fields.Many2one(
        "loyalty.level",
        string="Loyalty Level",
        compute="_compute_loyalty_level_id",
        store=True,
        tracking=True,
    )
    bought_amount = fields.Float(
        string="Tổng tiền tích luỹ", help="Số liệu hệ thống cũ", tracking=True
    )
    loyalty_point_amount = fields.Float(string="Tổng điểm tích luỹ", tracking=True)
    birthday = fields.Date("Date of Birth")
    last_downgrade_date = fields.Date("Last Downgrade Date")
    updated_wrong_loyalty_point = fields.Boolean(default=False)
    downgraded_date = fields.Date("Downgraded Date")
    upgraded_date = fields.Date("Upgraded Date")
    hobby_id = fields.Many2many("partner.hobby", string="Hobby")
    matter_of_concern_id = fields.Many2many(
        "matter.concern", string="Matter of Concern"
    )

    @api.depends("loyalty_point_amount")
    def _compute_loyalty_level_id(self):
        loyalty_level = self.env["loyalty.level"]
        for res in self:
            level_id = loyalty_level.search(
                [("point_policy", "<=", res.loyalty_point_amount)],
                order="point_policy desc",
                limit=1,
            )
            res.loyalty_level_id = level_id.id if level_id else False

    # # Check duplicate phone number
    # @api.constrains('phone', 'parent_id', 'is_company', 'company_type')
    # def _check_no_duplicate_number_phone(self):
    #     for record in self:
    #         partner_id = record._origin.id
    #         domain = [('phone', '=', record.phone), ('parent_id', '=', False)]
    #         if partner_id and (record.company_type == 'person' or record.parent_id):
    #             domain += [('id', '!=', partner_id)]
    #             if record.parent_id:
    #                 domain += [('id', '!=', record.parent_id.id)]
    #             exist_partners = bool(record.phone) and self.env['res.partner'].search(domain)
    #             if exist_partners:
    #                 raise ValidationError(_('Duplicated Error: The phone "%s" is already existed. Please check again!' % record.phone))

    @api.constrains("vat", "company_type", "parent_id")
    def _check_no_duplicate_vat(self):
        for record in self:
            partner_id = record._origin.id
            if (
                partner_id
                and record.same_vat_partner_id
                and record.company_type == "company"
            ):
                raise ValidationError(
                    _(
                        'Duplicated Error: VAT "%s" is already existed. Please check again!'
                        % record.vat
                    )
                )

    @api.depends(
        "complete_name",
        "email",
        "vat",
        "state_id",
        "country_id",
        "commercial_company_name",
    )
    @api.depends_context(
        "show_address",
        "partner_show_db_id",
        "address_inline",
        "show_email",
        "show_vat",
        "lang",
    )
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for partner in self:
            partner.display_name = partner.complete_name
            # if partner.company_type == 'person' and not partner.parent_id:
            #     if partner.phone:
            #         partner.display_name = partner.phone + ' - ' + partner.display_name
            #     else:
            #         partner.display_name = partner.display_name
        return res

    @api.depends(
        "is_company",
        "name",
        "parent_id.name",
        "type",
        "company_name",
        "commercial_company_name",
    )
    def _compute_complete_name(self):
        res = super()._compute_complete_name()
        for partner in self:
            if partner.phone:
                partner.complete_name = partner.phone + " - " + partner.complete_name
        return res

    # @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name')
    # def _compute_display_name(self):
    #     diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None, compute_display_name=True)
    #     names = dict(self.with_context(**diff).name_get())
    #     for partner in self:
    #         display_name = names.get(partner.id)
    #         if partner.company_type == 'person' and not partner.parent_id:
    #             display_name = partner.phone + ' - ' + display_name if partner.phone else display_name
    #         partner.display_name = display_name
    #
    # def name_get(self):
    #     res = []
    #     for partner in self:
    #         name = partner._get_name()
    #         if not self.env.context.get('compute_display_name') and partner.phone and partner.phone not in name:
    #             name = partner.phone + ' - ' + name
    #         res.append((partner.id, name))
    #     return res

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        self = self.with_user(name_get_uid or self.env.uid)
        # as the implementation is in SQL, we force the recompute of fields if necessary
        self.recompute(["display_name"])
        self.flush()
        if args is None:
            args = []
        order_by_rank = self.env.context.get("res_partner_search_mode")
        if (name or order_by_rank) and operator in (
            "=",
            "ilike",
            "=ilike",
            "like",
            "=like",
        ):
            self.check_access_rights("read")
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, "read")
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            from_str = from_clause if from_clause else "res_partner"
            where_str = where_clause and (" WHERE %s AND " % where_clause) or " WHERE "

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ("ilike", "like"):
                search_name = "%%%s%%" % name
            if operator in ("=ilike", "=like"):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            fields = self._get_name_search_order_by_fields()

            query = """SELECT res_partner.id
                         FROM {from_str}
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent}
                           OR {reference} {operator} {percent}
                           OR {phone} {operator} {percent}
                           OR {mobile} {operator} {percent}
                           OR {vat} {operator} {percent})
                           -- don't panic, trust postgres bitmap
                     ORDER BY {fields} {display_name} {operator} {percent} desc,
                              {display_name}
                    """.format(
                from_str=from_str,
                fields=fields,
                where=where_str,
                operator=operator,
                email=unaccent("res_partner.email"),
                display_name=unaccent("res_partner.display_name"),
                reference=unaccent("res_partner.ref"),
                phone=unaccent("res_partner.phone"),
                mobile=unaccent("res_partner.mobile"),
                percent=unaccent("%s"),
                vat=unaccent("res_partner.vat"),
            )

            where_clause_params += [
                search_name
            ] * 5  # for email / display_name, reference
            where_clause_params += [
                re.sub("[^a-zA-Z0-9\-\.]+", "", search_name) or None
            ]  # for vat
            where_clause_params += [search_name]  # for order by
            if limit:
                query += " limit %s"
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            return [row[0] for row in self.env.cr.fetchall()]

        return super()._name_search(
            name, args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )

    def cron_partner_birthday_lead(self):
        day_need_action = fields.Date.today()
        month_need_action = (
            "%-" + day_need_action.strftime("%m") + "-" + day_need_action.strftime("%d")
        )
        partners = self.search([("birthday", "like", month_need_action)])
        if partners:
            vals = []
            for partner in partners:
                vals.append(
                    {
                        "type": "lead",
                        "name": _("Birthday Customer - %s" % partner.name),
                        "contact_name": partner.name,
                        "partner_name": partner.parent_id
                        and partner.parent_id.name
                        or "",
                        "partner_id": partner.id,
                        "phone": partner.phone and partner.phone or "",
                        "mobile": partner.mobile and partner.mobile or "",
                        "email_from": partner.email and partner.email or "",
                        "function": partner.function and partner.function or "",
                        "street": partner.street and partner.street or "",
                        "country_id": partner.country_id
                        and partner.country_id.id
                        or False,
                        "state_id": partner.state_id and partner.state_id.id or False,
                        "user_id": self.env.company.birthday_lead_user_id.id
                        if self.env.company.birthday_lead_user_id
                        else partner.user_id.id or False,
                        "team_id": self.env.company.birthday_lead_team_id.id
                        if self.env.company.birthday_lead_team_id
                        else partner.team_id.id or False,
                    }
                )
            leads = self.env["crm.lead"].sudo().create(vals)

    def cron_update_loyalty_level(self):
        loyalty_level_ids = self.env["loyalty.level"].search(
            [], order="point_policy desc"
        )
        loyalty_level_ids_mappping = {r.point_policy: r for r in loyalty_level_ids}
        if not self.env.company.months_to_downgrade:
            return
        for partner in self._get_partners_to_update_loyalty_level():
            if partner._check_downgrade_loyalty_level():
                partner._downgrade_loyalty_level(loyalty_level_ids_mappping)

    def _get_partners_to_update_loyalty_level(self):
        return self.search(
            [("loyalty_level_id", "!=", False), ("loyalty_point_amount", "!=", 0)]
        )

    def _check_downgrade_loyalty_level(self):
        """
        Check if the partner should be downgraded to a lower loyalty level
        """
        # Tìm đơn mua hàng gần nhất của khách hàng
        self.ensure_one()
        need_action = False
        most_recent_order = self.env["sale.order"].search(
            [("partner_id", "=", self.id), ("state", "in", ["sale", "done"])],
            order="date_order desc",
            limit=1,
        )
        months_to_downgrade = self.env.company.months_to_downgrade
        if most_recent_order:
            today = fields.Date.today()
            # Get the relativedelta between two dates
            delta = relativedelta(today, most_recent_order.date_order)
            # get months difference
            res_months = delta.months + (delta.years * 12)
            if res_months > months_to_downgrade:
                if not self.last_downgrade_date:
                    need_action = True
                else:
                    delta = relativedelta(today, self.last_downgrade_date)
                    res_months = delta.months + (delta.years * 12)
                    if res_months > months_to_downgrade:
                        need_action = True
        return need_action

    def _downgrade_loyalty_level(self, loyalty_level_ids_mappping):
        self.ensure_one()
        lowest_loyalty_level = True
        for point_policy, level in loyalty_level_ids_mappping.items():
            if (
                self.loyalty_point_amount >= point_policy
                and self.loyalty_level_id != level
            ):
                self.loyalty_point_amount = point_policy - 1
                self.loyalty_level_id = level
                self.last_downgrade_date = fields.Date.today()
                lowest_loyalty_level = False
                break
        if lowest_loyalty_level:
            self.last_downgrade_date = fields.Date.today()
            self.loyalty_level_id = False
            self.loyalty_point_amount = 0

    def update_loyalty_point(self):
        for partner in self:
            invoiced = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("move_type", "in", ("out_invoice", "out_refund")),
                        ("sale_id", "!=", False),
                        ("state", "=", "posted"),
                        ("payment_state", "=", "paid"),
                        ("partner_id", "=", partner.id),
                    ]
                )
            )
            total_invoiced = sum([inv.amount_total_signed for inv in invoiced])
            partner.sudo().write(
                {
                    "loyalty_point_amount": total_invoiced / 1000
                    if total_invoiced > 0
                    else 0
                }
            )

    def cron_update_wrong_loyalty_point(self):
        need_updates = self.sudo().search(
            [
                ("is_company", "=", False),
                ("parent_id", "=", False),
                ("updated_wrong_loyalty_point", "=", False),
            ],
            limit=20,
        )
        for partner in need_updates:
            partner.update_loyalty_point()
            partner.update({"updated_wrong_loyalty_point": True})

    def write(self, values):
        if "loyalty_level_id" in values:
            for partner in self:
                old_loyalty_level_id = partner.loyalty_level_id
                current_loyalty_level_id = self.env["loyalty.level"].browse(
                    values["loyalty_level_id"]
                )
                if (
                    old_loyalty_level_id
                    and current_loyalty_level_id != old_loyalty_level_id
                ):
                    if (
                        current_loyalty_level_id.point_policy
                        < old_loyalty_level_id.point_policy
                    ):
                        values["downgraded_date"] = fields.Date.today()
                    else:
                        values["upgraded_date"] = fields.Date.today()
                elif not old_loyalty_level_id:
                    values["upgraded_date"] = fields.Date.today()
        return super().write(values)

    @api.model
    def create(self, vals):
        if vals and ("phone" in vals or "mobile" in vals):
            parent_id = False
            if "phone" in vals:
                parent_id = self.search(
                    [
                        ("phone", "=", vals["phone"]),
                    ],
                    limit=1,
                )
            elif "mobile" in vals:
                parent_id = self.search(
                    [
                        ("mobile", "=", vals["mobile"]),
                    ],
                    limit=1,
                )
            if parent_id:
                vals["parent_id"] = parent_id.id
                vals["type"] = "delivery"
        return super().create(vals)

    @api.constrains("phone", "mobile")
    def _check_phone_number(self):
        for record in self:
            if record.phone and not self._is_valid_vietnamese_phone_number(
                record.phone
            ):
                raise ValidationError(
                    _(
                        "Invalid phone number in 'Phone'. Please enter a valid Vietnamese phone number."
                    )
                )
            if record.mobile and not self._is_valid_vietnamese_phone_number(
                record.mobile
            ):
                raise ValidationError(
                    _(
                        "Invalid phone number in 'Mobile'. Please enter a valid Vietnamese phone number."
                    )
                )

    def _is_valid_vietnamese_phone_number(self, phone_number):
        mobile_pattern = r"^(\+84|84|0|\+62)(1|3|[4-9])([0-9]{8})$"

        landline_pattern = r"^(\+84|84|0)(2)([0-9]{9})$"

        pattern = re.compile(f"({mobile_pattern})|({landline_pattern})")
        return bool(pattern.match(phone_number))

    @api.onchange("phone", "country_id", "company_id")
    def _onchange_phone_validation(self):
        res = super()._onchange_phone_validation()
        if self.phone:
            self.phone = (
                self._phone_format(fname="phone", force_format="E164") or self.phone
            )
        return res

    @api.onchange("mobile", "country_id", "company_id")
    def _onchange_mobile_validation(self):
        res = super()._onchange_mobile_validation()
        if self.mobile:
            self.mobile = (
                self._phone_format(fname="mobile", force_format="E164") or self.mobile
            )
        return res

    def check_vat_vn(self, vat):
        return True
