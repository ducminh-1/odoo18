import logging

from odoo import http

logger = logging.getLogger(__name__)


class Website(http.Controller):

    @http.route(['/shop/custom_country_infos/<model("res.country"):country>'], type='json', auth="public", methods=['POST'], website=True)
    def custom_country_infos(self, country, **kw):
        return dict(
            # fields=country.get_address_fields(),
            cities=[(c.id, c.name, c.code) for c in country.get_partner_addres_vn_base_city()],
            # states=[(st.id, st.name, st.code) for st in country.get_website_sale_states(mode=mode)],
            phone_code=country.phone_code,
            # zip_required=country.zip_required,
            # state_required=country.state_required,
        )

    @http.route(['/shop/city_infos/<model("res.city"):city>'], type='json', auth="public", methods=['POST'], website=True)
    def city_infos(self, city, **kw):
        return dict(
            districts=[(d.id, d.name, d.code) for d in city.get_partner_addres_vn_base_districts()],
        )

    @http.route(['/shop/district_infos/<model("res.district"):district>'], type='json', auth="public", methods=['POST'], website=True)
    def district_infos(self, district, **kw):
        return dict(
            wards=[(w.id, w.name, w.code) for w in district.get_partner_addres_vn_base_wards()],
        )
