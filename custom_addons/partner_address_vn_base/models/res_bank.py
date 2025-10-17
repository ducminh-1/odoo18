from odoo import api, fields, models


class Bank(models.Model):
    _inherit = 'res.bank'

    ward_id = fields.Many2one('res.ward', 'Ward', domain="[('district_id', '=?', district_id)]")
    district_id = fields.Many2one('res.district', 'District', domain="[('city_id', '=?', city_id)]")
    city_id = fields.Many2one('res.city', 'City ID', domain="[('country_id', '=?', country)]")

    @api.onchange('country')
    def _onchange_country_id(self):
        res = super()._onchange_country_id()
        if self.country and self.country.code != 'VN':
            self.city_id = False
            self.district_id = False
            self.ward_id = False
        elif not self.country:
            self.city_id = False
            self.district_id = False
            self.ward_id = False
        return res

    @api.onchange('city_id')
    def _onchange_city_id(self):
        # res = super()._onchange_city_id()
        if not self.city_id:
            self.district_id = False
            self.ward_id = False
        if self.city_id and self.district_id.city_id != self.city_id:
            self.district_id = False
            self.ward_id = False
        # return res

    @api.onchange('district_id')
    def _onchange_district(self):
        if not self.district_id:
            self.ward_id = False
        if self.district_id and self.ward_id.district_id != self.district_id:
            self.ward_id = False
