from odoo import fields, models


class HREthnicity(models.Model):
    _name = "hr.ethnicity"
    _description = "Ethnicity"

    sequence = fields.Integer(default=10)
    name = fields.Char(string="Ethnicity", required=True)
    country_id = fields.Many2one("res.country", string="Country")
