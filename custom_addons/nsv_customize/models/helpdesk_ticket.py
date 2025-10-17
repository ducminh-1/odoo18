# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HelpdeskTicketDetails(models.Model):
    _name = "helpdesk.ticket.detail"
    _order = "sequence, id, ticket_id"
    _description = "Helpdesk Ticket Detail"

    sequence = fields.Integer("Sequence")
    ticket_id = fields.Many2one(
        "helpdesk.ticket", "Ticket Reference", ondelete="cascade", index=True
    )
    name = fields.Text("Description", required=True)
    product_id = fields.Many2one(
        "product.product", "Product", required=True, domain=[("sale_ok", "=", True)]
    )
    uom_id = fields.Many2one(
        "uom.uom", related="product_id.uom_id", string="Unit of Measure "
    )
    quantity = fields.Float("Quantity", required=True, digits="Product UoS", default=1)
    fee = fields.Float(
        "Helpdesk Fee",
        required=True,
        digits="Product Price",
        default=0.0,
        tracking=True,
    )
    note = fields.Text("Note")


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_detail_ids = fields.One2many(
        "helpdesk.ticket.detail", "ticket_id", string="Ticket Details", copy=True
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", copy=False)
    expiry_date = fields.Datetime("Expired Date", copy=False)
    customer_address = fields.Char(
        related="partner_id.street", string="Customer Address"
    )
    customer_phone = fields.Char(related="partner_id.phone", string="Customer Phone")
    done_date = fields.Datetime(string="Date Done")
    loyalty_level_id = fields.Many2one(
        "loyalty.level",
        string="Loyalty Level",
        related="partner_id.loyalty_level_id",
        store=True,
        tracking=True,
    )
    customer_birthday = fields.Date(
        related="partner_id.birthday", string="Customer Birthday", store=True
    )
    customer_loyalty_point_amount = fields.Float(
        related="partner_id.loyalty_point_amount", string="Loyalty Point Amount"
    )
    customer_tag = fields.Many2many(related="partner_id.category_id", string="Tag")
    color = fields.Integer(
        compute="compute_color_by_loyalty_level",
        string="Color",
        store=True,
        readonly=False,
    )
    date_order = fields.Datetime(string="Order Date")
    so_id = fields.Many2one("sale.order", string="Sale Order Ref")

    transfer_count = fields.Integer(string="Transfer", compute="_compute_transfer_ids")
    transfer_ids = fields.Many2many("stock.picking", compute="_compute_transfer_ids")
    create_transfer = fields.Boolean(related="team_id.create_transfer")

    # on change date order
    @api.onchange("so_id")
    def _onchange_date_order(self):
        if self.so_id and self.so_id.date_order:
            self.date_order = self.so_id.date_order

    @api.depends("color", "loyalty_level_id.color")
    def compute_color_by_loyalty_level(self):
        for rec in self:
            if not rec.color and rec.loyalty_level_id:
                rec.color = rec.loyalty_level_id.color

    def create_transfer_from_ticket(self):
        self.ensure_one()
        if len(self.ticket_detail_ids) == 0:
            raise UserError(_("Ticket does not have ticket details"))
        else:
            operation_type_id = self.team_id.picking_type_id
            if not operation_type_id:
                raise UserError(_("Operation type not configured"))
            else:
                if (
                    not operation_type_id.default_location_src_id
                    or not operation_type_id.default_location_dest_id
                ):
                    raise UserError(_("Default location not configured"))
                else:
                    transfer_vals = {
                        "picking_type_id": operation_type_id.id,
                        "location_id": operation_type_id.default_location_src_id.id,
                        "location_dest_id": operation_type_id.default_location_dest_id.id,
                        "ticket_id": self.id,
                        "move_ids_without_package": [
                            (
                                0,
                                0,
                                {
                                    "product_id": line.product_id.id,
                                    "location_id": operation_type_id.default_location_src_id.id,
                                    "location_dest_id": operation_type_id.default_location_dest_id.id,
                                    "product_uom_qty": line.quantity,
                                    "name": line.name,
                                    "product_uom": line.uom_id.id,
                                },
                            )
                            for line in self.ticket_detail_ids
                        ],
                        "owner_id": self.partner_id.id,
                        "company_id": self.company_id.id,
                        "partner_id": self.partner_id.id,
                    }
                    transfer = self.env["stock.picking"].create(transfer_vals)

    def _compute_transfer_ids(self):
        for ticket in self:
            ticket.transfer_ids = self.env["stock.picking"].search(
                [("ticket_id.id", "=", ticket.id)]
            )
            ticket.transfer_count = len(ticket.transfer_ids)

    def action_view_transfer(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": _("Transfer"),
            "res_model": "stock.picking",
            "view_mode": "list,form",
            "domain": [("id", "in", self.transfer_ids.ids)],
            "context": dict(
                self._context, create=False, default_company_id=self.company_id.id
            ),
        }
        if self.transfer_count == 1:
            action.update({"view_mode": "form", "res_id": self.transfer_ids.id})
        return action

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if "team_id" in res:
            team_id = self.env["helpdesk.team"].browse(res["team_id"])
            if team_id:
                if "user_id" not in res and team_id.assign_method == "manual":
                    res.update({"user_id": team_id.user_id.id})
                if "brandname_id" not in res:
                    res.update({"brandname_id": team_id.brand_id.id})
        return res

    @api.onchange("team_id")
    def _onchange_team_id(self):
        if self.team_id and self.team_id.assign_method == "manual":
            self.user_id = self.team_id.user_id
            self.brandname_id = self.team_id.brand_id


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    partner_id = fields.Many2one("res.partner", "Branch")
    filter_failure_report = fields.Boolean("Filter Failure Report")
    create_transfer = fields.Boolean(default=False, string="Is ticket transfer")
    picking_type_id = fields.Many2one("stock.picking.type", string="Operation Type")
    user_id = fields.Many2one("res.users", string="Assigned To")
    brand_id = fields.Many2one("brand.name", string="Brand")


class HelpdeskTicketType(models.Model):
    _inherit = "helpdesk.ticket.type"

    filter_failure_report = fields.Boolean("Filter Failure Report")
