from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    vaobep_user_id = fields.Integer(string="Vaobep User ID", readonly=True)
    vaobep_contact_id = fields.Integer(string="Vaobep Contact ID", readonly=True)
    buy_date = fields.Date(string="Buye Date")
    product_id = fields.Many2one(
        "product.product", string="Interested Product", tracking=True
    )
    description = fields.Text("Description")
