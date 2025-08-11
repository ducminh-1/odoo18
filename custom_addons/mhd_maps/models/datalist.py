from odoo import api, fields, models


class MHDDataList(models.Model):
    _inherit = 'mhd.datalist'

    customer_longitude = fields.Float(
        string='Customer Longitude', digits=(16, 5), tracking=True)
    customer_latitude = fields.Float(
        string='Customer Latitude', digits=(16, 5), tracking=True)

    # @api.onchange('partner_id')
    # def onchange_partner_id_geo(self):
    #     if self.partner_id:
    #         self.customer_latitude = self.partner_id.partner_latitude
    #         self.customer_longitude = self.partner_id.partner_longitude

    @api.model
    def _geo_localize(self, vitri_duong='', vitri_quan='', vitri_tinh='', country='Việt Nam'):
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(
            vitri_duong=vitri_duong, vitri_quan=vitri_quan, vitri_tinh=vitri_tinh, country=country
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(
                vitri_quan=vitri_quan, vitri_tinh=vitri_tinh, country=country
            )
            result = geo_obj.geo_find(search, force_country=country)
        print(result)
        print(geo_obj.geo_query_address)
        return result

    def geo_localize(self):
        for lead in self.with_context(lang='en_US'):
            result = self._geo_localize(
                vitri_duong=lead.vitri_duong.name,
                vitri_quan=lead.vitri_quan.name,
                vitri_tinh=lead.vitri_tinh.name,
                country='Việt Nam',
            )

            if result:
                lead.write(
                    {
                        'customer_latitude': result[0],
                        'customer_longitude': result[1],
                    }
                )

        return True
