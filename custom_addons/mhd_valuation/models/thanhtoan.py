# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from odoo.exceptions import UserError, ValidationError

# Module lấy số hợp đồng ngẫu nhiên
class MHDThanhtoan(models.Model):
    _name = "mhd.thanhtoan"
    _inherit = ['mail.thread']
    _description = "MHD - Thanh toán"
    _order = "id desc"

    name = fields.Text(string='Nội dung thanh toán', tracking=True)
    chungthu = fields.Many2one('mhd.chungthu', related='datalist_id.chungthu_id', string='Chứng thư', readonly=True, tracking=True)
    nhanvien_tao = fields.Many2one('res.users', string='Người tạo', tracking=True)
    nhanvien_xacnhan = fields.Many2one('res.users', string='Người xác nhận', tracking=True)
    date = fields.Date(string='Ngày TT', tracking=True)
    sotien = fields.Float(string='Số tiền thanh toán', required=True, digits=(15, 0), tracking=True)
    hinhthuc = fields.Selection([
        ('tien_mat', 'Tiền mặt'),
        ('chuyen_khoan', 'Chuyển khoản'),
    ],
        string="Hình thức", tracking=True)
    taikhoan = fields.Selection([
        ('ca_nhan', 'TK Cá nhân'),
        ('chi_ha', 'TK Chị Hà'),
        ('cong_ty_688', 'TK Công ty 688'),
        ('cong_ty_815', 'TK Công ty 815'),
        ('cong_ty_acb', 'TK Công ty ACB'),
    ],
        string="Loại TK", tracking=True)

    lanthanhtoan = fields.Selection([
        ('lan_mot', 'Tạm ứng lần 1'),
        ('lan_hai', 'Tạm ứng lần 2'),
        ('lan_ba', 'Tạm ứng lần 3'),
        ('phan_con_lai', 'Phần còn lại'),
        ('thu_full', 'Thu Full'),
    ],
        string="Tiến độ thanh toán")
    tinhtrang = fields.Selection([
        ('chua_xac_nhan', 'Chưa xác nhận'),
        ('da_xac_nhan', 'Đã xác nhận'),
    ],
        string="Xác nhận thanh toán", default='chua_xac_nhan', tracking=True)
    full_phi = fields.Boolean(string='Thu Full', related='datalist_id.full_phi', readonly=False, compute='_full_phi')
    thanhtoan_thoidiem = fields.Date(string='Thời điểm thanh toán', related='datalist_id.thanhtoan_thoidiem', readonly=False, compute='_thoidiem_thanhtoan')
    thanhtoan_tongphi = fields.Float(string='Tổng phí', digits=(15, 0), related='datalist_id.thanhtoan_tongphi')
    thanhtoan_dathanhtoan = fields.Float(string='Đã thanh toán', digits=(15, 0), related='datalist_id.thanhtoan_dathanhtoan')
    datalist_id = fields.Many2one('mhd.datalist', string='Tên tài sản', tracking=True)
    project_task_id = fields.Many2one('project.task', string='Nhiệm vụ')
    ghichu = fields.Char(string='Ghi chú', tracking=True)

    @api.onchange('date', 'full_phi')
    def _thoidiem_thanhtoan(self):
        for rec in self:
            full_phi = rec.full_phi
            if full_phi == True:
                rec.thanhtoan_thoidiem = rec.date
            elif full_phi != True:
                rec.thanhtoan_thoidiem = None

    @api.onchange('thanhtoan_dathanhtoan', 'thanhtoan_tongphi', 'sotien')
    def _full_phi(self):
        for rec in self:
            thanhtoan_dathanhtoan = rec.thanhtoan_dathanhtoan
            thanhtoan_tongphi = rec.thanhtoan_tongphi
            sotien = rec.sotien
            if sotien + thanhtoan_dathanhtoan == thanhtoan_tongphi:
                rec.full_phi = True
            elif sotien + thanhtoan_dathanhtoan != thanhtoan_tongphi:
                rec.full_phi = False