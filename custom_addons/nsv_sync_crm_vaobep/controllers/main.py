# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
from datetime import date, datetime

from odoo import fields, http
from odoo.http import request
from odoo.tools.misc import consteq

_logger = logging.getLogger(__name__)

DATE_FORMAT = "%d-%m-%Y"


class VaoBepController(http.Controller):
    @http.route(
        "/webhook/vaobep/<token>",
        methods=["POST"],
        type="json",
        auth="public",
        csrf=False,
        cors="*",
    )
    def payload_vaobep_data(self, token):
        valid_token = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("token.access.webhooks.vaobep")
        )
        if not consteq(str(token), str(valid_token)):
            _logger.info("Wrong Token Key")
            _logger.info("====================================================")
            return request.not_found()
        try:
            data = request.httprequest.data.decode("utf-8")
            request.env["vaobep.event"].sudo().create(
                {"name": fields.Datetime.to_string(fields.Datetime.now()), "data": data}
            )
            dict_data = json.loads(data)
            contact = dict_data.get("Contact", {})
            vaobep_contact_id = contact.get("ContactId", 0)
            vaobep_user_id = contact.get("UserId", 0)
            contact_name = contact.get("ContactName")
            phone = contact.get("Mobile", "").strip()
            gender = contact.get("Gender")
            custom_fields = contact.get("CustomFields", [{}, {}, {}, {}])
            address = buy_date_str = lot_name = sku = buy_from = ""
            for el in custom_fields:
                if el.get("CustomFieldName", "") == "Address":
                    address = el.get("CustomFieldValue", "")
                if el.get("CustomFieldName") == "Buyfrom":
                    buy_date_str = el.get("CustomFieldValue", "")
                if el.get("CustomFieldName") == "Serialno":
                    lot_name = el.get("CustomFieldValue", "")
                if el.get("CustomFieldName") == "Model":
                    sku = el.get("CustomFieldValue", "")

                if el.get("CustomFieldName") == "Buyfrom":
                    buy_from = el.get("CustomFieldValue", "")

            try:
                buy_date = datetime.strptime(buy_date_str, DATE_FORMAT)
            except Exception:
                buy_date = False

            product = (
                request.env["product.product"]
                .sudo()
                .search([("default_code", "=", sku)], limit=1)
            )
            partner = (
                request.env["res.partner"]
                .sudo()
                .search([("phone", "=", phone), ("mobile", "=", phone)], limit=1)
            )
            Guarantee = request.env["guarantee.registers"].sudo()

            values = {
                "vaobep_contact_id": vaobep_contact_id,
                "vaobep_user_id": vaobep_user_id,
                "contact_name": contact_name,
                "phone": phone,
                "street": address,
                "buy_date": buy_date,
                "buy_at": buy_from,
                "description": sku + "\n Mua tại: %s" % buy_from,
                "sku": sku,
                "lot_name": lot_name,
                "product_id": product and product.id or False,
                "partner_id": partner and partner.id or False,
            }
            guarantee = Guarantee.search(
                ["|", ("sku", "=", sku), ("lot_name", "=", lot_name)]
            )

            if guarantee:
                guarantee.write(values)
                body = """
<strong>Update from Vao bep App</strong>
<p>Data: %s</p>
                """ % json.dumps(contact)
                guarantee.message_post(body=body)
            else:
                values["name"] = contact_name + " " + sku
                Guarantee.create(values)
            _logger.info(
                "==================== WEBHOOK DATA FROM VAO BEP APP: \n %s" % data
            )
        except Exception as e:
            print(e)
            pass

        return True

    @http.route(
        "/api/create_crm",
        methods=["POST"],
        type="json",
        auth="user",
        csrf=False,
        cors="*",
    )
    def crm_lead_update(self):
        if not request.session.uid:
            return False
        try:
            data = request.httprequest.data.decode("utf-8")
            _logger.info("==================== API VAO BEP: CREATE CRM: \n %s" % data)
            # TODO: Remove me after debug
            request.env["vaobep.crm"].sudo().create(
                {
                    "name": "CRM - " + fields.Datetime.to_string(fields.Datetime.now()),
                    "data": data,
                }
            )
            # ===========================
            dict_data = json.loads(data)
            name = dict_data.get("name", "").strip()
            phone = dict_data.get("phone", "").strip()
            description = dict_data.get("description", "")
            email = dict_data.get("email", "").strip()
            if not name or not phone:
                return False
            if not phone and not email:
                return False
            val = {"name": name, "phone": phone, "description": description}
            CRM = request.env["crm.lead"].sudo()
            sub_domain = ("phone", "=", phone)
            if email:
                val["email_from"] = email
                domain = ["|", sub_domain, ("email_from", "=", email)]
            else:
                domain = [sub_domain]
            lead = CRM.sudo().search(domain, limit=1)
            if lead:
                result_lead = lead.sudo().write(val)
            else:
                val["type"] = "lead"
                result_lead = CRM.sudo().create(val)
            return True
        except Exception as e:
            _logger.info("CRM CREATE: ========= \n%s" % e)
            return False

    # TODO: Check 18.0
    @http.route("/dang-ky-bao-hanh", type="http", auth="public", website=True)
    def sanpham(self, **post):
        country_code = request.geoip.country_code
        if country_code:
            def_country_id = request.env["res.country"].search(
                [("code", "=", country_code)], limit=1
            )
        else:
            def_country_id = request.website.user_id.sudo().country_id
        if not def_country_id:
            def_country_id = request.env.ref("base.vn")

        country = def_country_id

        res = {
            "country": country,
            "country_cities": country.get_partner_addres_vn_base_city(),
            "countries": country.get_partner_addres_vn_base_countries(),
            "today": date.today().strftime("%Y-%m-%d"),
        }
        _logger.info("==================== DANG KY BAO HAHNH: \n %s" % res)
        return request.render("nsv_sync_crm_vaobep.form_guarantee_registers", res)

    @http.route(["/js/guarantee-registers"], auth="public", type="json", website=True)
    def guarantee_registers(self, **post):
        # FIXME: If error occurred, no way return False
        if (
            post.get("contact_name")
            and post.get("phone")
            and post.get("sku")
            and post.get("buy_date")
            and post.get("buy_at")
        ):
            Partner = request.env["res.partner"].sudo()
            if post.get("phone"):
                phone_number = post.get("phone").strip()
                Partner = Partner.search(
                    ["|", ("phone", "=", phone_number), ("mobile", "=", phone_number)],
                    limit=1,
                )
            if not Partner:
                Partner = (
                    request.env["res.partner"]
                    .sudo()
                    .create(
                        {
                            "name": post.get("contact_name", "").strip(),
                            "phone": post.get("phone").strip(),
                            "email": post.get("email").strip(),
                            "city_id": int(post.get("city_id"))
                            if post.get("city_id")
                            else False,
                            "district_id": int(post.get("district_id"))
                            if post.get("district_id")
                            else False,
                            "ward_id": int(post.get("ward_id"))
                            if post.get("ward_id")
                            else False,
                            "street": post.get("street", "").strip(),
                        }
                    )
                )
            values = {
                "contact_name": post.get("contact_name", "").strip(),
                "phone": post.get("phone").strip(),
                "email": post.get("email").strip(),
                "city_id": int(post.get("city_id")) if post.get("city_id") else False,
                "district_id": int(post.get("district_id"))
                if post.get("district_id")
                else False,
                "ward_id": int(post.get("ward_id")) if post.get("ward_id") else False,
                "street": post.get("street", "").strip(),
                "buy_date": post.get("buy_date"),
                "buy_at": post.get("buy_at"),
                "sku": post.get("sku").strip(),
                "total_amount": post.get("total_amount"),
                "partner_id": Partner.id,
                "bill_img": post.get("bill_img"),
                "filename": str(post.get("img_name")) or "Bill Image",
            }
            if post.get("birthday"):
                values["birthday"] = post.get("birthday")
            registers = request.env["guarantee.registers"].sudo().create(values)
            return True
        return False
