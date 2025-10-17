from odoo import fields, models


class Contract(models.Model):
    _inherit = "hr.contract"

    extra_allowance = fields.Monetary(
        string="Extra Allowance", default=0.0, tracking=True
    )
    social_ins_wage = fields.Monetary(string="Wage BHXH", default=0.0, tracking=True)
    telephone_allowance = fields.Float(
        string="Telephone Allowance", required=True, default=0.0, tracking=True
    )
    gasoline_allowance = fields.Float(
        string="Gasoline Allowance", required=True, default=0.0, tracking=True
    )
    respons_allowance = fields.Float(
        string="Responsibility Allowance", required=True, default=0.0, tracking=True
    )
    toxic_allowance = fields.Float(
        string="Toxic Allowance", required=True, default=0.0, tracking=True
    )
