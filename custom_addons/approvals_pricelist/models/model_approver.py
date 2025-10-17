import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ModelApprover(models.Model):
    _name = "model.approver"
    _description = "Model Approver"
    _order = "sequence, id"

    _check_company_auto = True

    sequence = fields.Integer(default=10)
    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        domain="[('id', 'not in', existing_user_ids)]",
    )
    existing_user_ids = fields.Many2many(
        "res.users", compute="_compute_existing_user_ids", precompute=True
    )
    status = fields.Selection(
        [
            ("new", "New"),
            ("pending", "To Approve"),
            ("waiting", "Waiting"),
            ("approved", "Approved"),
            ("refused", "Refused"),
            ("cancel", "Cancel"),
        ],
        default="new",
        readonly=True,
    )
    res_model = fields.Char("Resource Model")
    res_id = fields.Many2oneReference("Resource ID", model_field="res_model")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        compute="_compute_company_id",
        store=True,
        readonly=True,
    )
    required = fields.Boolean(default=True, readonly=True)

    @api.depends("res_id", "res_model")
    def _compute_company_id(self):
        for approver in self:
            resouce = self.env[approver.res_model].browse(approver.res_id)
            if hasattr(resouce, "company_id"):
                approver.company_id = resouce.company_id
            else:
                approver.company_id = False

    @api.model
    def get_or_create_mail_activity_type(self, res_model):
        mail_activity_type = self.env.ref(
            f"approvals_pricelist.mail_activity_data_{self.env[res_model]._table}",
            raise_if_not_found=False,
        )
        if not mail_activity_type:
            mail_activity_type = self.env["mail.activity.type"].create(
                {
                    "name": f"Approve {res_model}",
                    "icon": "mail_open",
                    "active": False,
                }
            )
            self.env["ir.model.data"].create(
                {
                    # "name": "mail_activity_data_%s" % self.env[res_model]._table,
                    "name": f"mail_activity_data_{self.env[res_model]._table}",
                    "module": "approvals_pricelist",
                    "res_id": mail_activity_type.id,
                    "noupdate": True,
                    "model": "mail.activity.type",
                }
            )

        return mail_activity_type

    @api.model
    def _cancel_activities(self, resource):
        approval_activity = self.get_or_create_mail_activity_type(resource._name)
        activities = resource.activity_ids.filtered(
            lambda a: a.activity_type_id == approval_activity
        )
        activities.unlink()

    def _create_activity(self):
        for approver in self:
            activity_type = approver.get_or_create_mail_activity_type(
                approver.res_model
            )
            activity_type_xml_id = activity_type.get_external_id()[activity_type.id]
            self.env[approver.res_model].browse(approver.res_id).activity_schedule(
                activity_type_xml_id, user_id=approver.user_id.id
            )

    def _notify_users(self, resources):
        for resource in resources:
            model_name = resource._table
            template = self.env.ref(
                f"approvals_pricelist.notify_user_approve_{model_name}_{resource.request_status}",
                raise_if_not_found=False,
            )
            if not template or not isinstance(resource.id, int) or not resource.id:
                continue
            if hasattr(resource, "get_users_to_notify"):
                users = resource.get_users_to_notify()
            else:
                continue
            values = {
                "object": resource,
                "model_description": resource._description,
            }
            body = self.env["ir.qweb"]._render(
                f"approvals_pricelist.notify_user_approve_{model_name}_{resource.request_status}",
                values,
            )
            for user in users:
                resource.message_notify(
                    subject=_(f"Approval Status Of {resource.display_name}"),
                    body=body,
                    partner_ids=user.partner_id.ids,
                )

    @api.model
    def _get_resource_user_approval_activities(self, user, resource):
        domain = [
            ("res_model", "=", resource._name),
            ("res_id", "in", resource.ids),
            (
                "activity_type_id",
                "=",
                self.get_or_create_mail_activity_type(resource._name).id,
            ),
            ("user_id", "=", user.id),
        ]
        activities = self.env["mail.activity"].search(domain)
        return activities

    @api.depends("res_id")
    def _compute_existing_user_ids(self):
        for approver in self:
            # import pdb; pdb.set_trace()
            approver.existing_user_ids = (
                self.env[approver.res_model]
                .browse(approver.res_id)
                .approver_ids.mapped("user_id")
                ._origin
                | self.env[approver.res_model]
                .browse(approver.res_id)
                .create_uid._origin
            )
