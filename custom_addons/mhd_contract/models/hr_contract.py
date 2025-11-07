import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = "hr.contract"

    is_ssnid = fields.Boolean("SSNID", tracking=True)
    is_trade_union = fields.Boolean("Trade Union", tracking=True)
    # Chỉ đóng BHYT
    is_bhyt_only = fields.Boolean("Chỉ đóng BHYT", tracking=True)
    # Chỉ đóng BH Tai nạn nghề nghiệp
    is_bhtnn_only = fields.Boolean("Chỉ đóng BH Tai nạn nghề nghiệp", tracking=True)

    ssnid_amount = fields.Monetary(tracking=True)
    phu_cap_tien_an = fields.Monetary(tracking=True)
    phu_cap_cong_viec = fields.Monetary(tracking=True)
    phu_cap_xang_xe = fields.Monetary(tracking=True)
    phu_cap_trach_nhiem = fields.Monetary(tracking=True)
    phu_cap_khac = fields.Monetary(tracking=True)
    nguoi_phu_thuoc = fields.Integer()
    phu_cap_dien_thoai = fields.Monetary(tracking=True)
    phu_cap_tien_nha = fields.Monetary(tracking=True)
    date_of_issue_id = fields.Date(string='Date of Issue CCCD Card', groups='hr.group_hr_user', tracking=True)
    place_of_issue_id = fields.Char(string='Place of Issue CCCD Card', groups='hr.group_hr_user', tracking=True)
    bank_id = fields.Many2one('res.bank', string='Bank')
    bank_accc_number = fields.Char(string='Account Number')
