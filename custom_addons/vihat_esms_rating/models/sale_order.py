from werkzeug import urls

from odoo import api, models


class SaleOrder(models.Model):
    # _name = 'sale.order'
    # _inherit = ['sale.order', 'rating.mixin', 'rating.parent.mixin']
    _inherit = "sale.order"

    @api.model
    def get_url_rating(self):
        brandname = self.env.context.get("brandname")
        website_id = self.env.context.get("rating_website_id")
        if not brandname and self.brandname_id:
            brandname = self.brandname_id.name
            if not website_id:
                website_id = self.brandname_id.sms_brandname_id.website_id.id or False
        website = self.env["website"].browse([website_id])
        # get access token rating
        access_token = self._rating_get_access_token(self.partner_id)
        # generate url
        domain_website = (
            website.domain if website and website.domain else self.get_base_url()
        )
        rating_url = "%s/customer-rating/%s/%s?brandname=%s&model=sale.order" % (
            domain_website,
            access_token,
            self.partner_id and self.partner_id.id or 0,
            brandname or "",
        )
        existing_tracker = self.env["link.tracker"].search(
            [("url", "=", rating_url)], limit=1
        )
        if existing_tracker:
            link_tracker = existing_tracker
        else:
            # create link tracker
            link_tracker = self.env["link.tracker"].create(
                {"url": rating_url, "title": "Ticket Rating"}
            )
            # re-update short link with website domain
            link_tracker.update(
                {
                    "short_url": urls.url_join(
                        domain_website, "/r/%(code)s" % {"code": link_tracker.code}
                    )
                }
            )
        return link_tracker
