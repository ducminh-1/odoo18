from odoo import fields, models


class HRSalaryType(models.Model):
    _name = "hr.salary.type"
    _description = "Salary Type"

    sequence = fields.Integer(default=10)
    name = fields.Char()
