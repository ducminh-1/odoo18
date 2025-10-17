import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    guarantee_registers_sms_brand_name_id = fields.Many2one(
        "sms.brandname",
        string="Guarantee Register SMS Brand Name",
        config_parameter="guarantee_registers_sms_brand_name_id",
    )
    guarantee_registers_zalo_oa_id = fields.Many2one(
        "zalo.oa",
        string="Zalo OA",
        related="guarantee_registers_sms_brand_name_id.zalo_oa_id",
    )
    guarantee_register_zns_template_id = fields.Many2one(
        "ir.ui.view",
        string="Guarantee Register ZNS Template",
        domain="[('type','=','qweb'),('name','ilike', 'ĐĂNG KÝ BẢO HÀNH'),('zalo_oa_id','=',guarantee_registers_zalo_oa_id)]",
        related="guarantee_registers_zalo_oa_id.guarantee_register_zns_template_id",
        readonly=False,
    )
