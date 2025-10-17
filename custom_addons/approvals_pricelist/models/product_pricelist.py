import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    approver_ids = fields.One2many(
        "model.approver",
        "res_id",
        string="Approvers",
        check_company=True,
        compute="_compute_approver_ids",
        store=True,
        readonly=False,
    )
    request_status = fields.Selection(
        [
            ("new", "To Submit"),
            ("pending", "Submitted"),
            ("approved", "Approved"),
            ("refused", "Refused"),
            ("cancel", "Cancel"),
        ],
        default="new",
        compute="_compute_request_status",
        store=True,
        tracking=True,
    )
    user_status = fields.Selection(
        [
            ("new", "New"),
            ("pending", "To Approve"),
            ("waiting", "Waiting"),
            ("approved", "Approved"),
            ("refused", "Refused"),
            ("cancel", "Cancel"),
        ],
        compute="_compute_user_status",
    )
    approver_sequence = fields.Boolean(default=True)
    pricelist_approval = fields.Boolean(default=True)
    apply_partner_ids = fields.Many2many("res.partner", string="Apply to Partners")

    edit_from_approved = fields.Boolean(default=False, readonly=True)
    from_price_list_id = fields.Many2one(
        "product.pricelist", string="From Pricelist", copy=False
    )
    can_view_lognote = fields.Boolean(compute="_compute_can_view_lognote")

    @api.depends_context("uid")
    @api.depends("approver_ids.status")
    def _compute_user_status(self):
        for pricelist in self:
            pricelist.user_status = pricelist.approver_ids.filtered(
                lambda approver: approver.user_id == self.env.user
            ).status

    @api.depends("approver_ids.status", "approver_ids.required")
    def _compute_request_status(self):
        for pricelist in self:
            if not pricelist.pricelist_approval:
                pricelist.request_status = "approved"
                continue
            status_lst = pricelist.mapped("approver_ids.status")
            required_approved = all(
                a.status == "approved"
                for a in pricelist.approver_ids.filtered("required")
            )
            if status_lst:
                if status_lst.count("cancel"):
                    status = "cancel"
                elif status_lst.count("refused"):
                    status = "refused"
                elif status_lst.count("new"):
                    status = "new"
                elif status_lst.count("approved") and required_approved:
                    status = "approved"
                else:
                    status = "pending"
            else:
                status = "new"
            pricelist.request_status = status

        to_cancel = to_notify = self.filtered_domain(
            [("request_status", "in", ["approved", "refused", "cancel"])]
        )
        approved = self.filtered_domain([("request_status", "=", "approved")])
        self.env["model.approver"]._cancel_activities(to_cancel)
        self.env["model.approver"]._notify_users(to_notify)
        for pricelist in approved:
            for partner in pricelist.apply_partner_ids:
                partner.write({"property_product_pricelist": pricelist.id})
            pricelist.from_price_list_id.sudo().with_context(
                edit_from_approved=True
            ).write({"active": False})

    @api.depends_context("uid")
    def _compute_can_view_lognote(self):
        for record in self:
            all_users = (
                record.message_follower_ids.mapped("partner_id.user_ids")
                | record.create_uid
            )
            record.can_view_lognote = self.env.user in all_users

    @api.model
    def _update_approver_vals(
        self, approver_id_vals, approver, new_required, new_sequence
    ):
        if approver.required != new_required or approver.sequence != new_sequence:
            approver_id_vals.append(
                [1, approver.id, {"required": new_required, "sequence": new_sequence}]
            )

    @api.model
    def _create_or_update_approver(
        self, user_id, users_to_approver, approver_id_vals, required, sequence
    ):
        if user_id not in users_to_approver.keys():
            # approver_id_vals.append(Command.create({
            #     'user_id': user_id,
            #     'status': 'new',
            #     'required': required,
            #     'sequence': sequence,
            # }))
            approver_id_vals.append(
                [
                    0,
                    0,
                    {
                        "user_id": user_id,
                        "status": "new",
                        "required": required,
                        "sequence": sequence,
                        "res_model": self._name,
                        "res_id": self.id,
                    },
                ]
            )
        else:
            current_approver = users_to_approver.pop(user_id)
            self._update_approver_vals(
                approver_id_vals, current_approver, required, sequence
            )

    @api.depends("company_id")
    def _compute_approver_ids(self):
        for pricelist in self:
            users_to_approver = {}
            for approver in pricelist.approver_ids:
                users_to_approver[approver.user_id.id] = approver

            users_to_company_approver = {}
            for approver in pricelist.company_id.pricelist_approver_ids:
                users_to_company_approver[approver.user_id.id] = approver

            approver_id_vals = []
            for user_id in users_to_company_approver:
                self._create_or_update_approver(
                    user_id,
                    users_to_approver,
                    approver_id_vals,
                    users_to_company_approver[user_id].required,
                    users_to_company_approver[user_id].sequence,
                )

            for current_approver in users_to_approver.values():
                self._update_approver_vals(
                    approver_id_vals, current_approver, False, 1000
                )

            pricelist.update({"approver_ids": approver_id_vals})

    def _ensure_can_approve(self):
        if any(
            pricelist.approver_sequence and pricelist.user_status == "waiting"
            for pricelist in self
        ):
            raise ValidationError(_("You cannot approve before the previous approver."))

    def _update_next_approvers(
        self, new_status, approver, only_next_approver, cancel_activities=False
    ):
        approvers_updated = self.env["model.approver"]
        for pricelist in self.filtered("approver_sequence"):
            current_approver = pricelist.approver_ids & approver
            approvers_to_update = pricelist.approver_ids.filtered(
                # lambda a: a.status not in ["approved", "refused"]
                lambda a, current_approver=current_approver: a.status
                not in [
                    "approved",
                    "refused",
                ]
                and (
                    a.sequence > current_approver.sequence
                    or (
                        a.sequence == current_approver.sequence
                        and a.id > current_approver.id
                    )
                )
            )

            if only_next_approver and approvers_to_update:
                approvers_to_update = approvers_to_update[0]
            approvers_updated |= approvers_to_update

        approvers_updated.sudo().status = new_status
        if new_status == "pending":
            approvers_updated._create_activity()
        if cancel_activities:
            self.env["model.approver"]._cancel_activities(self)

    def action_submit(self):
        if len(self.approver_ids) <= 0:
            raise UserError(_("You have to add at least one approver."))

        approvers = self.approver_ids
        if self.approver_sequence:
            approvers = approvers.filtered(
                lambda a: a.status in ["new", "pending", "waiting"]
            )

            approvers[1:].status = "waiting"
            approvers = (
                approvers[0]
                if approvers and approvers[0].status != "pending"
                else self.env["model.approver"]
            )
        else:
            approvers = approvers.filtered(lambda a: a.status == "new")

        approvers._create_activity()
        approvers.sudo().write({"status": "pending"})

    def action_approve(self, approver=None):
        self._ensure_can_approve()

        if not isinstance(approver, models.BaseModel):
            approver = self.mapped("approver_ids").filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({"status": "approved"})
        self.sudo()._update_next_approvers("pending", approver, only_next_approver=True)
        self.env["model.approver"].sudo()._get_resource_user_approval_activities(
            self.env.user, self
        ).action_feedback()

    def action_refuse(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped("approver_ids").filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({"status": "refused"})
        self.sudo()._update_next_approvers(
            "refused", approver, only_next_approver=False, cancel_activities=True
        )
        self.env["model.approver"].sudo()._get_resource_user_approval_activities(
            self.env.user, self
        ).action_feedback()

    def copy(self, default=None):
        self.ensure_one()
        if not self.env.context.get("edit_from_approved"):
            raise UserError(_("You cannot copy a pricelist."))
        res = super().copy(default=default)
        return res

    def action_unarchive(self):
        for record in self:
            if record.request_status != "approved":
                raise UserError(_("You cannot unarchive a pricelist."))
        return super(
            ProductPricelist, self.with_context(edit_from_approved=True)
        ).action_unarchive()

    def action_archive(self):
        for record in self:
            if record.request_status != "approved":
                raise UserError(_("You cannot archive a pricelist."))
        return super(
            ProductPricelist, self.with_context(edit_from_approved=True)
        ).action_archive()

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._compute_approver_ids()
        return res

    def write(self, vals):
        for record in self:
            if record.request_status == "approved" and not self.env.context.get(
                "edit_from_approved"
            ):
                raise UserError(_("You cannot modify an approved pricelist."))
        res = super().write(vals)
        return res

    def button_edit(self):
        self.ensure_one()
        res = self.with_context(edit_from_approved=True).copy(default={"active": True})
        res.sudo().write(
            {
                "edit_from_approved": True,
                "from_price_list_id": self.id,
            }
        )
        return {
            "name": _("Edit Pricelist"),
            "type": "ir.actions.act_window",
            "res_model": "product.pricelist",
            "view_mode": "form",
            "res_id": res.id,
            "target": "current",
        }
