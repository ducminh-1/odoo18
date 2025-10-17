import json
import logging
import re
import unicodedata

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SMS(models.Model):
    _inherit = "sms.sms"

    state = fields.Selection(
        selection_add=[("waiting_server", "Waiting Server")],
        ondelete={"waiting_server": "cascade"},
    )
    vihat_sms_id = fields.Char()
    sms_brandname_id = fields.Many2one("sms.brandname", string="SMS Brandname")
    date_exec = fields.Datetime(string="Execute Date", default=fields.Datetime.now())
    zns_template_id = fields.Char()
    zns_template_val_ids = fields.One2many("zns.template.val", "sms_id")
    only_sms = fields.Boolean(default=False)

    def no_accent_vietnamese(self, s):
        s = re.sub("Đ", "D", s)
        s = re.sub("đ", "d", s)
        return (unicodedata.normalize("NFKD", s).encode("ASCII", "ignore")).decode(
            "utf-8"
        )

    def _build_data_send_sms(self):
        ApiKey = (
            self.env["ir.config_parameter"].sudo().get_param("vihat_api_key", False)
        )
        SecretKey = (
            self.env["ir.config_parameter"].sudo().get_param("vihat_secret_key", False)
        )
        CallbackUrl = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("vihat_sms_callback_url", False)
        )
        # multi channel
        Channels = ["sms"]
        if not self.only_sms and self.sms_brandname_id.zalo_oa_id:
            Channels = ["zalo", "sms"]
        Data = [
            {
                "Content": self.no_accent_vietnamese(self.body) if self.body else "",
                "IsUnicode": "0",
                "SmsType": "2",
                "Brandname": self.sms_brandname_id
                and self.sms_brandname_id.name
                or False,
                # "RequestId": "686868",
                # "campaignid": "Tên chiến dịch gửi tin",
                "CallbackUrl": CallbackUrl,
            }
        ]
        if (
            self.sms_brandname_id.zalo_oa_id
            and self.zns_template_id
            and self.zns_template_val_ids
            and not self.only_sms
        ):
            Data = [
                {
                    "OAID": self.sms_brandname_id.zalo_oa_id.oa_id,
                    "TempID": self.zns_template_id,
                    "Params": [str(val.value) for val in self.zns_template_val_ids],
                    # "campaignid": "Tên chiến dịch gửi tin",
                    "CallbackUrl": CallbackUrl,
                }
            ] + Data
        return {
            "ApiKey": ApiKey,
            "SecretKey": SecretKey,
            "Phone": self.number,
            "Channels": Channels,
            "Data": Data,
        }

    # def _vihat_get_status_sms_send(self):
    #     if self.env.context.get('payment_reminder_sms'):
    #         body_msg_post = 'Send Payment Reminder SMS: <a href=# data-oe-model=sms.sms data-oe-id=%d>%s-%s</a>' % (self.id, self.partner_id.name, self.number)
    #         self.partner_id.message_post(body=body_msg_post)
    #     ApiKey = self.env['ir.config_parameter'].sudo().get_param('vihat_api_key', False)
    #     SecretKey = self.env['ir.config_parameter'].sudo().get_param('vihat_secret_key', False)
    #     url_get_sms_status = 'http://rest.esms.vn/MainService.svc/json/GetSendStatus?RefId=%s&ApiKey=%s&SecretKey=%s' %(self.vihat_sms_id,ApiKey,SecretKey)
    #     try:
    #         _logger.info('================Vihat Request Get SMS Status=============')
    #         resp = requests.get(url_get_sms_status, headers={'Content-Type': 'application/json'})
    #         result = json.loads(resp.text)
    #         _logger.info(result)
    #         if result.status_code == 200:
    #             _logger.info('================Vihat Request Get SMS Status Success=============')
    #             if result['SendStatus'] and result['SendStatus'] == '5':
    #                 self.update({'state': 'sent', 'error_code': False})
    #             else:
    #                 self.update({'state': 'error', 'error_code': 'sms_server'})
    #         else:
    #             _logger.info('================Vihat Request Get SMS Status Fail=============')
    #             self.update({'state': 'error', 'error_code': 'sms_server'})
    #     except Exception as e:
    #         _logger.info('================Vihat Request Get SMS Status Fail=============')
    #         self.update({'state': 'error', 'error_code': 'sms_server'})

    def send_vihat_esms(self):
        for rec in self:
            if rec.number and rec.body:
                rec.update({"state": "waiting_server"})
                vihat_sms_url = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param(
                        "vihat_sms_url",
                        "https://rest.esms.vn/MainService.svc/json/MultiChannelMessage/",
                    )
                )
                data = rec._build_data_send_sms()
                try:
                    _logger.info("================Vihat Request Send SMS=============")
                    _logger.info(json.dumps(data))
                    resp = requests.post(
                        vihat_sms_url,
                        data=json.dumps(data),
                        headers={"Content-Type": "application/json"},
                    )
                    output = json.loads(resp.text)
                    if resp.status_code == 200:
                        _logger.info("================Request Success=============")
                        _logger.info(output)
                        # cập nhật SMS ID
                        if output["SMSID"]:
                            rec.update({"vihat_sms_id": output["SMSID"]})
                        if (
                            output["CodeResult"] == "100"
                        ):  # Request đã được nhận và xử lý thành công.
                            _logger.info(
                                "================Send SMS Success============="
                            )
                            # gửi thành công
                            # time.sleep(1)
                            # rec._vihat_get_status_sms_send()
                        else:
                            # lỗi do request
                            _logger.info(
                                "================Send SMS Fail============= %s "
                                % resp.content.decode()
                            )
                            rec.update({"state": "error", "failure_type": "sms_server"})
                    else:
                        _logger.info(
                            "================Request Fail============= %s " % output
                        )
                except Exception as e:
                    _logger.info("================Send SMS Error=============\n %s" % e)
                    rec.update({"state": "error", "failure_type": "sms_server"})

    @api.model
    def _process_queue(self, ids=None):
        filtered_ids = self.search(
            [
                ("state", "=", "outgoing"),
                ("date_exec", "<=", fields.Datetime.now().strftime("%Y-%m-%d")),
            ],
            limit=10000,
        )
        # filtered_ids = filtered_ids.filtered(lambda rec: not rec.day_need_action or rec.day_need_action < fields.Datetime.now())
        if ids:
            ids = list(set(filtered_ids.ids) & set(ids))
        else:
            ids = filtered_ids.ids
        ids.sort()
        res = None
        try:
            res = self.browse(ids).send_vihat_esms()
        except Exception as e:
            _logger.error("======================== Fail to send SMS outgoing: %s" % e)
        return res
