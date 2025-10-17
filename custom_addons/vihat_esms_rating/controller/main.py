import logging

from odoo import _, http
from odoo.http import request
from odoo.tools.misc import get_lang

from odoo.addons.website.controllers.main import Website

_logger = logging.getLogger(__name__)


class VihateSMSRating(Website):
    @http.route(
        "/customer-rating/<string:token>/<int:partner_id>",
        methods=["GET", "POST"],
        type="http",
        auth="public",
        website=True,
    )
    def open_web_form_rating(self, token, partner_id, **kw):
        rating = (
            request.env["rating.rating"]
            .sudo()
            .search([("access_token", "=", token), ("partner_id", "=", partner_id)])
        )
        if not rating:
            return request.not_found()
        rate_names = {
            5: _("Very Satisfied"),
            4: _("Satisfied "),
            3: _("Neutral"),
            2: _("Dissatisfied"),
            1: _("Very Dissatisfied"),
        }
        lang = rating.partner_id.lang or get_lang(request.env).code
        return (
            request.env["ir.ui.view"]
            .with_context(lang=lang)
            ._render_template(
                "vihat_esms_rating.rating_web_form_submit",
                {
                    "rating": rating,
                    "token": token,
                    "rate_names": rate_names,
                    "partner_id": rating.partner_id,
                    "brand_name": kw.get("brandname", ""),
                    "model_name": kw.get("model", ""),
                },
            )
        )

    @http.route(
        ["/customer-rating/<string:token>/submit_rating"],
        type="http",
        auth="public",
        methods=["post"],
        website=True,
    )
    def action_submit_web_form_rating(self, token, **kwargs):
        rate = int(kwargs.get("rate") or 0)
        assert rate in (0, 1, 2, 3, 4, 5), "Incorrect rating"
        rating = (
            request.env["rating.rating"].sudo().search([("access_token", "=", token)])
        )
        if not rating:
            return request.not_found()
        # vihat esms customize start -->
        data_update = {
            "rating": rate,
            "consumed": True,
        }
        if kwargs.get("rating_seller", ""):
            data_update.update({"rating_seller": kwargs.get("rating_seller", "")})
        if kwargs.get("rating_delivery", ""):
            data_update.update({"rating_delivery": kwargs.get("rating_delivery", "")})
        rating.write(data_update)
        # end -->
        record_sudo = request.env[rating.res_model].sudo().browse(rating.res_id)
        # customize update employee to rating
        if (
            "employee_id" in request.env[rating.res_model].sudo()._fields
            and record_sudo.employee_id
        ):
            rating.update({"employee_id": record_sudo.employee_id.id})
        record_sudo.rating_apply(rate, token=token, feedback=kwargs.get("feedback"))
        lang = rating.partner_id.lang or get_lang(request.env).code
        return (
            request.env["ir.ui.view"]
            .with_context(lang=lang)
            ._render_template(
                "vihat_esms_rating.rating_web_page_done",
                {
                    "web_base_url": request.env["ir.config_parameter"]
                    .sudo()
                    .get_param("web.base.url"),
                    "rating": rating,
                },
            )
        )
