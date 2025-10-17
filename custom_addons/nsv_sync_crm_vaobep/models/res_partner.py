from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    guarantee_count = fields.Integer(
        string="#Guarantee Registers", compute="_compute_guarantee_count"
    )
    guarantee_registers_ids = fields.One2many(
        "guarantee.registers", "partner_id", string="Guarantee Registers"
    )

    def _compute_guarantee_count(self):
        for rec in self:
            rec.guarantee_count = len(rec.sudo().guarantee_registers_ids)

    def action_view_patient_opportunity(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "nsv_sync_crm_vaobep.action_guarantee_registers"
        )
        action["domain"] = [("id", "in", self.guarantee_registers_ids.ids)]
        action["context"] = {
            "default_partner_id": self.id,
            "default_contact_name": self.name,
            "default_phone": self.phone,
            "default_email": self.email,
            "default_street": self.street,
        }
        return action
