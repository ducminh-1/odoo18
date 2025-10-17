from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    city_ids = fields.One2many('res.city', 'country_id', string='Cities')
    
    def get_partner_addres_vn_base_countries(self):
        return self.sudo().search([])

    def get_partner_addres_vn_base_city(self):
        return self.sudo().city_ids
