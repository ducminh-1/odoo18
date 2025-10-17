from odoo import fields, models


class MatterConcern(models.Model):
    _name = "matter.concern"

    name = fields.Char(string="Name")
