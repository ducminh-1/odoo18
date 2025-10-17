# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _

CRM_LEAD_FIELDS_TO_MERGE = [
    # UTM mixin
    'campaign_id',
    'medium_id',
    'source_id',
    # Mail mixin
    'email_cc',
    # description
    'name',
    'user_id',
    'company_id',
    'team_id',
    # pipeline
    'stage_id',
    # revenues
    'expected_revenue',
    # dates
    'create_date',
    'date_action_last',
    # partner / contact
    'partner_id',
    'title',
    'partner_name',
    'contact_name',
    'email_from',
    'mobile',
    'phone',
    'website',
    # address
    'street',
    'street2',
    'zip',
    'city',
    'state_id',
    'country_id',
    # vn address customize
    'ward_id',
    'district_id',
    'city_id',
]


# Subset of partner fields: sync all or none to avoid mixed addresses
# PARTNER_ADDRESS_FIELDS_TO_SYNC = [
#     'street',
#     'street2',
#     'city',
#     'zip',
#     'state_id',
#     'country_id',
#     # vn address customize
#     'ward_id',
#     'district_id',
#     'city_id',
# ]


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    ward_id = fields.Many2one('res.ward', 'Ward', domain="[('district_id', '=?', district_id)]")
    district_id = fields.Many2one('res.district', 'District', domain="[('city_id', '=?', city_id)]")
    city_id = fields.Many2one('res.city', 'City ID', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(default=lambda self: self.env.ref('base.vn'))
    country_code = fields.Char(related='country_id.code', string="Country Code")

    partner_address = fields.Char('Address', compute='_compute_partner_address')

    def _compute_partner_address(self):
        for p in self:
            street = p.street or ''
            ward = p.ward_id.name or ''
            district = p.district_id.name or ''
            city = p.city_id.name or ''
            p.partner_address = ', '.join([el for el in [street, ward, district, city] if el != ''])

    # def _prepare_address_values_from_partner(self, partner):
    #     # Sync all address fields from partner, or none, to avoid mixing them.
    #     if any(partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC):
    #         values = {f: partner[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
    #     else:
    #         values = {f: self[f] for f in PARTNER_ADDRESS_FIELDS_TO_SYNC}
    #     return values

    # def _merge_get_fields(self):
    #     return list(CRM_LEAD_FIELDS_TO_MERGE) + list(self._merge_get_fields_specific().keys())

    def _merge_get_fields(self):
        return super(Lead, self)._merge_get_fields() + ['ward_id', 'district_id', 'city_id']

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        res = super()._prepare_customer_values(partner_name, is_company, parent_id)
        res.update({
            'ward_id': self.ward_id.id,
            'district_id': self.district_id.id,
            'city_id': self.city_id.id,
        })
        return res
