# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
from datetime import datetime

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OmiController(http.Controller):
    def validate_omicall_data_webhook(self, json_data):
        data = json.loads(json_data)
        if data.get("state", False) != "cdr":
            return False
        if data.get("direction", False) not in ("outbound", "inbound"):
            return False
        call_values = {
            "tenant_id": data.get("tenant_id"),
            "transaction_id": data.get("transaction_id"),
            "direction": data.get("direction"),
            "source_number": data.get("source_number"),
            "destination_number": data.get("destination_number"),
            "disposition": data.get("disposition"),
            "bill_sec": data.get("bill_sec"),
            "time_start_to_answer": datetime.fromtimestamp(
                data.get("time_start_to_answer")
            ),
            "duration": data.get("duration"),
            "record_seconds": data.get("record_seconds"),
            "recording_file": data.get("recording_file"),
            "sip_user": data.get("sip_user"),
            # 'created_date': datetime.fromtimestamp(data.get('created_date')/1000),
            # 'last_updated_date': datetime.fromtimestamp(data.get('last_updated_date')/1000),  # noqa
            "provider": data.get("provider"),
            "is_auto_call": data.get("is_auto_call"),
            "call_out_price": data.get("call_out_price"),
        }
        customer = data.get("customer", False)
        if customer:
            call_values["customer_fullname"] = customer.get("customer_fullname", "")
            call_values["customer_fullname_unsigned"] = customer.get(
                "customer_fullname_unsigned", ""
            )

        usr_names = []
        notes = []
        text_tags = []
        for usr in data.get("user", []):
            usr_names.append(usr.get("full_name", ""))
            notes.append(usr.get("note", ""))
            tags = usr.get("tag", "")
            text_tags = [el.get("name") for el in tags]
        call_values["user_fullname"] = " ".join(usr_names)
        call_values["note"] = " ".join(notes)
        call_values["text_tag"] = " ".join(text_tags)

        VoipCallLog = request.env["voip.call.log"].sudo()
        Partner = request.env["res.partner"].sudo()
        ResUsers = request.env["res.users"].sudo()
        exist_call = VoipCallLog.search(
            [("transaction_id", "=", call_values["transaction_id"])], limit=1
        )
        if data.get("direction") == "outbound":
            customer_phone = data.get("destination_number")
        else:
            customer_phone = data.get("source_number")
        if len(customer_phone) >= 10:
            customer_phone = customer_phone[-10:]
        partner = Partner.search(
            [
                "|",
                ("phone", "like", customer_phone),
                ("mobile", "like", customer_phone),
            ],
            limit=1,
        )
        if partner:
            call_values["partner_id"] = partner.id

        sip_user = data.get("sip_user")
        if sip_user:
            user = ResUsers.search([("sip_login", "=", sip_user)], limit=1)
            if user:
                call_values["user_id"] = user.id
        if exist_call:
            result = exist_call.write(call_values)
        else:
            result = VoipCallLog.create(call_values)
        return True

    @http.route(
        "/webhook/omicall",
        methods=["POST"],
        type="json",
        auth="public",
        csrf=False,
        cors="*",
    )
    def payload_omicall_data(self):
        try:
            json_data = request.httprequest.get_data()
            rlst = self.validate_omicall_data_webhook(json_data)
            if rlst:
                _logger.info(
                    "==================== WEBHOOK: UPDATE FROM OMICALL SUCCESSFULLY: \n %s"
                    % json_data.decode("utf-8")
                )
            else:
                _logger.info(
                    "==================== WEBHOOK: NO UPDATE FROM OMICALL: \n %s"
                    % json_data.decode("utf-8")
                )
            return "OK"

        except Exception as e:
            _logger.info(
                "==================== WEBHOOK DATA FROM OMICALL: FAIL ! Cause: \n"
                " %s" % e
            )
            return "FAIL"
