import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import Website

_logger = logging.getLogger(__name__)

# SendStatus = {
#     '1': 'Chờ duyệt',
#     '2': 'Đang chờ gửi',
#     '3': 'Đang gửi',
#     '4': 'Bị từ chối',
#     '5': 'Đã gửi xong',
#     '6': 'Đã bị xoá',
# }


class VihatSMSWebhook(Website):
    @http.route(
        ["/sms/receivecallback"],
        type="http",
        auth="public",
        methods=["GET", "POST"],
        website=True,
        csrf=False,
        cors="*",
    )
    def VihatSMSAPIListener(self, **kw):
        _logger.info("==============================WEBHOOK==================")
        _logger.info(kw)
        if kw.get("SMSID"):
            SMS_ENV = request.env["sms.sms"].sudo()
            sms = SMS_ENV.search([("vihat_sms_id", "=", kw.get("SMSID"))])
            if sms:
                _logger.info(
                    "==============================WEBHOOK UPDATE SMS STATE=================="
                )
                if kw.get("SendStatus") in [5, "5"]:
                    # đã gửi xong, Cập nhật trạng thái tin nhắn
                    sms.sudo().write({"state": "sent", "error_code": False})
                elif kw.get("SendStatus") in [1, 2, 3, "1", "2", "3"]:
                    sms.sudo().write({"state": "waiting_server", "error_code": False})
                elif kw.get("SendStatus") in [4, "4"]:
                    sms.sudo().write({"state": "error", "error_code": "sms_server"})
                _logger.info(
                    "==============================WEBHOOK UPDATE SMS DONE=================="
                )
        return request.make_response(
            data=json.dumps({"result": "ok"}),
            headers=[("Content-Type", "application/json")],
        )
