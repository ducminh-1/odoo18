import re
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ward_id = fields.Many2one('res.ward', 'Ward', domain="[('district_id', '=?', district_id)]")
    ward_name = fields.Char('Ward Name', related='ward_id.name')
    district_id = fields.Many2one('res.district', 'District', domain="[('city_id', '=?', city_id)]")
    district_name = fields.Char('District Name', related='district_id.name')
    city_id = fields.Many2one('res.city', 'City ID', domain="[('country_id', '=?', country_id)]")
    city_name = fields.Char('City Name', related='city_id.name')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',
        default=lambda self: self.env.ref('base.vn'))
    partner_address = fields.Char('Address', compute='_compute_partner_address')
    shipping_address = fields.Char(compute='_compute_complete_shipping_address')

    @api.onchange('country_id')
    def _onchange_country_id(self):
        res = super()._onchange_country_id()
        if self.country_id and self.country_id.code != 'VN':
            self.city_id = False
            self.district_id = False
            self.ward_id = False
        elif not self.country_id:
            self.city_id = False
            self.district_id = False
            self.ward_id = False
        return res

    @api.onchange('city_id')
    def _onchange_city_id(self):
        res = super()._onchange_city_id()
        if not self.city_id:
            self.district_id = False
            self.ward_id = False
        if self.city_id and self.district_id.city_id != self.city_id:
            self.district_id = False
            self.ward_id = False
        return res

    @api.onchange('district_id')
    def _onchange_district(self):
        if not self.district_id:
            self.ward_id = False
        if self.district_id and self.ward_id.district_id != self.district_id:
            self.ward_id = False


    # @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name')
    # def _compute_display_name(self):
    #     diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None, show_partner_address=None, show_phone=None,show_mobile=None)
    #     names = dict(self.with_context(**diff).name_get())
    #     for partner in self:
    #         partner.display_name = names.get(partner.id)
    #
    # def _get_name(self):
    #     res = super(ResPartner, self)._get_name()
    #     if self._context.get('show_partner_address') and self.partner_address:
    #         res = "%s\n %s" % (res, self.partner_address)
    #     if self._context.get('show_phone') and self.phone:
    #         res = "%s\n %s" % (res, self.phone)
    #     if self._context.get('show_mobile') and self.mobile:
    #         res = "%s - %s" % (res, self.mobile)
    #     return res

    def _compute_partner_address(self):
        for p in self:
            street = p.street or ''
            ward = p.ward_id.name or ''
            district = p.district_id.name or ''
            city = p.city_id.name or ''
            country = p.country_id.name or ''
            p.partner_address = ', '.join([el for el in [street, ward, district, city, country] if el != ''])

    @staticmethod
    def replace_address_name(pattern, name):
        for long_text, short_text in pattern.items():
            name = re.sub(long_text, short_text, name, flags=re.IGNORECASE)
        return name

    @staticmethod
    def replace_province_text(name):
        return re.sub(r'\btp\s+', '', name, flags=re.IGNORECASE)

    @api.depends('street', 'ward_id', 'district_id', 'city_id')
    def _compute_complete_shipping_address(self):
        for record in self:
            record.shipping_address = ''
            if record.street:
                record.shipping_address += record.street + ', '
            if record.ward_id:
                pattern = {r'\bphường\s+': 'P.', r'\bxã\s+': 'X.', r'\bthị\s+trấn\s+': 'TT.', r'\bhuyện\s+': 'H.'}
                record.shipping_address += self.replace_address_name(pattern, record.ward_id.name) + ', '
            if record.district_id:
                pattern = {r'\bquận\s+': 'Q.', r'\bhuyện\s+': 'H.', r'\bthị\s+xã\s+': 'TX.', r'\bthành\s+phố\s+': 'TP.'}
                record.shipping_address += self.replace_address_name(pattern, record.district_id.name) + ', '
            if record.city_id:
                record.shipping_address += self.replace_province_text(record.city_id.name) + ', '
            record.shipping_address = record.shipping_address.strip().strip(',')

    @api.model
    def create(self, values):
        _logger.info('Creating a new partner %s', values)
        if 'district_id' in values and 'city_id' in values:
            old_district = self.env['res.district'].browse(values['district_id'])
            if old_district.city_id.id != values['city_id']:
                _logger.warning('District %s does not belong to state %s', old_district, values['city_id'])
                correct_district = self.env['res.district'].search([('name', '=', old_district.name), ('city_id', '=', values['city_id'])])
                if not correct_district:
                    raise ValidationError('District %s not found in state %s' % (old_district.name, values['city_id']))
                if old_district != correct_district:
                    _logger.info('Replacing district %s with %s', old_district, correct_district)
                    values['district_id'] = correct_district.id

        if 'ward_id' in values and 'district_id' in values:
            old_ward = self.env['res.ward'].browse(values['ward_id'])
            if old_ward.district_id.id != values['district_id']:
                _logger.warning('Ward %s does not belong to district %s', old_ward, values['district_id'])
                correct_ward = self.env['res.ward'].search([('name', '=', old_ward.name), ('district_id', '=', values['district_id'])])
                if not correct_ward:
                    raise ValidationError('Ward %s not found in district %s' % (old_ward.name, values['district_id']))
                if old_ward != correct_ward:
                    _logger.info('Replacing ward %s with %s', old_ward, correct_ward)
                    values['ward_id'] = correct_ward.id
        return super(ResPartner, self).create(values)

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return super(ResPartner, self)._address_fields() + ['district_id', 'ward_id', 'district_name', 'ward_name', 'city_id', 'city_name']

    def _prepare_display_address(self, without_company=False):
        address_format, args = super()._prepare_display_address(without_company)
        args['district_name'] = self.district_id.name or ''
        args['ward_name'] = self.ward_id.name or ''
        args['city_name'] = self.city_id.name or ''
        return address_format, args
