from odoo import api, fields, models


class City(models.Model):
    _inherit = 'res.city'
    _order = 'sequence'

    sequence = fields.Integer(default=10)
    code = fields.Char('Code')

    district_ids = fields.One2many('res.district', 'city_id', string='Districts')

    def get_partner_addres_vn_base_districts(self):
        return self.sudo().district_ids
