from odoo import fields, models


class PartnerHobby(models.Model):
    _name = "partner.hobby"

    name = fields.Char(string="Name")
