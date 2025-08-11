# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class project_task(models.Model):
    _inherit = 'project.task'

    # Thông tin giao việc cơ bản
    tentaisan = fields.Many2one('mhd.datalist', string='Tên tài sản', tracking=True)
    kinhdoanh_id = fields.Many2one(string='Kinh doanh', related='tentaisan.kinhdoanh', readonly=False, tracking=True)
    user_id = fields.Many2one(string='Người thực hiện', related='tentaisan.nhanvien', store=True, readonly=False, tracking=True)
    # nhanvien = fields.Many2one(string='Người thực hiện', related='tentaisan.nhanvien', readonly=False)
    thamdinhvien_id = fields.Many2one(string='Kiểm soát viên', related='tentaisan.thamdinhvien', readonly=False, tracking=True)
    quanly_id = fields.Many2one(string='Quản lý', related='tentaisan.quanly', readonly=False, tracking=True)
    # Kết nối liên hệ
    partner_id = fields.Many2one(string='Khách hàng', related='tentaisan.khachhang_id', readonly=False, tracking=True)
    doitac_id = fields.Many2one(string='Đối tác', related='tentaisan.doitac_id', readonly=False, tracking=True)
    doitac_email = fields.Char(string='Email ĐT', related='doitac_id.email', readonly=True, tracking=True)
    khachhang_type = fields.Selection(string="Loại khách hàng", related='tentaisan.khachhang_type', readonly=False, tracking=True)
    # Kết nối và tạo hợp đồng
    hopdong_id = fields.Many2one(related='tentaisan.hopdong_id', string='Số hợp đồng', domain="[('datalist_id', '=', tentaisan)]", readonly=False, tracking=True)
    hopdong_line = fields.One2many('mhd.datalist', 'project_task_id', string='Nhiệm vụ')
    ghichu_hopdong = fields.Selection(related='tentaisan.ghichu_hopdong', default='chua_ky', string='Tình trạng hợp đồng', tracking=True, readonly=False)
    chungthu_id = fields.Many2one(related='tentaisan.chungthu_id', string='Số chứng thư', domain="[('datalist_id', '=', tentaisan)]", readonly=False, tracking=True)
    ghichu_chungthu = fields.Selection(related='tentaisan.ghichu_chungthu', default='chua_in', string='Tình trạng chứng thư', tracking=True, readonly=False)
    # Kết nối thanh toán
    thanhtoan_line = fields.One2many('mhd.thanhtoan', related='tentaisan.thanhtoan_line', string='Thông tin thanh toán', readonly=False)
    note = fields.Text(string='Ghi chú', related='tentaisan.note')
    thanhtoan_tongphi = fields.Float(string='Tổng phí', digits=0, related='tentaisan.thanhtoan_tongphi', readonly=False, tracking=True)
    thanhtoan_dathanhtoan = fields.Float(string='Đã thanh toán', digits=0, related='tentaisan.thanhtoan_dathanhtoan', tracking=True)
    thanhtoan_vat = fields.Selection(string='Thuế VAT', related='tentaisan.thanhtoan_vat', readonly=False, tracking=True)
    thanhtoan_phidichuyen = fields.Float(string='Phí di chuyển', digits=0, related='tentaisan.thanhtoan_phidichuyen', readonly=False, tracking=True)
    sotien_khuvuc = fields.Float(string='Phụ cấp khu vực', digits=0, related='tentaisan.sotien_khuvuc', readonly=False, tracking=True)
    # Mô tả tài sản
    loaitaisan = fields.Selection(related='tentaisan.loaitaisan', string="Loại tài sản", readonly=False, tracking=True)
    loaibatdongsan = fields.Selection(related='tentaisan.loaibatdongsan', string="Loại Bất động sản", readonly=False, tracking=True)
    motataisan = fields.Text(string='Mô tả tài sản', related='tentaisan.motataisan', readonly=False, tracking=True)
    # Thông tin địa chỉ tài sản
    vitri_chungcu_macan = fields.Char(string='Mã căn hộ', related='tentaisan.vitri_chungcu_macan', readonly=False, tracking=True)
    vitri_chungcu_block = fields.Char(string='Block', related='tentaisan.vitri_chungcu_block', readonly=False, tracking=True)
    vitri_chungcu = fields.Many2one(string='Tên chung cư', related='tentaisan.vitri_chungcu', readonly=False, tracking=True)
    vitri_sonha = fields.Char(string='Địa chỉ', related='tentaisan.vitri_sonha', tracking=True, readonly=False)
    vitri_duong = fields.Many2one(related='tentaisan.vitri_duong', string='Tên đường', readonly=False, tracking=True)
    vitri_phuong = fields.Many2one(related='tentaisan.vitri_phuong', string='Tên Phường/ Xã', readonly=False, tracking=True)
    vitri_quan = fields.Many2one(related='tentaisan.vitri_quan', string='Tên Quận/ Huyện', readonly=False, tracking=True)
    vitri_tinh = fields.Many2one(related='tentaisan.vitri_tinh', string='Tên Tỉnh/ TP', readonly=False, tracking=True)
    # Đặc điểm tài sản
    dacdiem_vitri_bds = fields.Selection(related='tentaisan.dacdiem_vitri_bds', string="Đặc điểm vị trí", readonly=False, tracking=True)
    dacdiem_vitri_canho = fields.Selection(related='tentaisan.dacdiem_vitri_canho', string="Vị trí căn hộ", readonly=False, tracking=True)
    dacdiem_ketcauduong = fields.Selection(related='tentaisan.dacdiem_ketcauduong', string="Kết cấu đường", readonly=False, tracking=True)
    dacdiem_dorongduong = fields.Char(related='tentaisan.dacdiem_dorongduong', string='Độ rộng đường/hẻm', readonly=False, tracking=True)
    # Bổ sung pháp lý căn hộ
    phaply_taisan = fields.Selection(related='tentaisan.phaply_taisan', string='Pháp lý tài sản', readonly=False, tracking=True)
    # Thông tin giá đất
    dat_loaidat = fields.Selection(related='tentaisan.dat_loaidat', string="Loại đất", readonly=False, tracking=True)
    dat_dientich = fields.Float(string='Diện tích', related='tentaisan.dat_dientich', readonly=False, tracking=True)
    dat_dongia = fields.Float(string='Đơn giá', related='tentaisan.dat_dongia', readonly=False, tracking=True)
    dat_giatri_chinh = fields.Float(string='Giá trị đất', related='tentaisan.dat_giatri_chinh', compute='_dat_giatri_chinh', readonly=False, tracking=True)
    dat_giatri_khac = fields.Float(string='Giá trị đất khác', related='tentaisan.dat_giatri_khac', readonly=False, tracking=True)
    dat_giatri_total = fields.Float(string='Tổng giá trị QSD đất', related='tentaisan.dat_giatri_total', compute='_dat_giatri_total', readonly=False, tracking=True)
    # Thông tin giá CTXD
    ctxd_loaicongtrinh = fields.Selection(related='tentaisan.ctxd_loaicongtrinh', string="Loại CTXD", readonly=False, tracking=True)
    ctxd_dientich = fields.Float(related='tentaisan.ctxd_dientich', readonly=False, string='Diện tích', tracking=True)
    ctxd_dongia = fields.Float(related='tentaisan.ctxd_dongia', readonly=False, string='Đơn giá', tracking=True)
    ctxd_clcl = fields.Float(related='tentaisan.ctxd_clcl', readonly=False, string='CLCL', tracking=True)
    ctxd_giatri_chinh = fields.Float(related='tentaisan.ctxd_giatri_chinh', string='Giá trị CTXD', readonly=False, compute='_ctxd_giatri_chinh', tracking=True)
    ctxd_giatri_khac = fields.Float(related='tentaisan.ctxd_giatri_khac', string='Giá trị CTXD khác', readonly=False, tracking=True)
    ctxd_giatri_total = fields.Float(string='Tổng giá trị CTXD', related='tentaisan.ctxd_giatri_total', compute='_ctxd_giatri_total', readonly=False, tracking=True)
    # Tổng giá trị tài sản
    total_tstd = fields.Float(string='Tổng giá trị TSTĐ', related='tentaisan.total_tstd', readonly=False, tracking=True)
    # Ghi chú
    ghichu_mabill = fields.Char(string='Mã Bill gửi thư', related='tentaisan.ghichu_mabill', readonly=False, tracking=True)
    ghichu_mabill_ngay = fields.Date(string='Ngày gửi thư', related='tentaisan.ghichu_mabill_ngay', readonly=False, tracking=True)
    ghichu_hoadon = fields.Char(string='Số Hóa đơn', related='tentaisan.ghichu_hoadon', readonly=False, tracking=True)
    ghichu_hoadon_ngay = fields.Date(string='Ngày Hóa đơn', related='tentaisan.ghichu_hoadon_ngay', readonly=False, tracking=True)
    ghichu_hoadon_tinhtrang = fields.Selection(string='Ghi chú hóa đơn', related='tentaisan.ghichu_hoadon_tinhtrang', readonly=False,
                                     tracking=True)
    luutru = fields.Char(string='Thư mục lưu trữ', related='tentaisan.luutru', readonly=False, tracking=True)

    @api.onchange('ctxd_giatri_total', 'dat_giatri_total')
    def _giatritaisan_total(self):
        for rec in self:
            rec.total_tstd = round(rec.ctxd_giatri_total + rec.dat_giatri_total, -3)

    @api.onchange('ctxd_giatri_chinh', 'ctxd_giatri_khac')
    def _ctxd_giatri_total(self):
        for rec in self:
            rec.ctxd_giatri_total = rec.ctxd_giatri_chinh + rec.ctxd_giatri_khac

    @api.onchange('ctxd_dongia', 'ctxd_dientich', 'ctxd_clcl')
    def _ctxd_giatri_chinh(self):
        for rec in self:
            rec.ctxd_giatri_chinh = round(rec.ctxd_dongia * rec.ctxd_dientich * rec.ctxd_clcl, 0)

    @api.onchange('dat_giatri_chinh', 'dat_giatri_khac')
    def _dat_giatri_total(self):
        for rec in self:
            rec.dat_giatri_total = rec.dat_giatri_chinh + rec.dat_giatri_khac

    @api.onchange('dat_dientich', 'dat_dongia')
    def _dat_giatri_chinh(self):
        for rec in self:
            rec.dat_giatri_chinh = round(rec.dat_dientich * rec.dat_dongia, 0)

    @api.onchange('thanhtoan_line')
    def _thanhtoan_total(self):
        for rec in self:
            rec.thanhtoan_dathanhtoan = sum(line.sotien for line in rec.thanhtoan_line)

    @api.onchange('vitri_phuong', 'vitri_quan')
    def _phucap_khuvuc(self):
        for rec in self:
            danhmucphuong = ['Phường Long Bình', 'Phường Long Phước', 'Xã Lê Minh Xuân', 'Xã Phạm Văn Hai',
                             'Xã Bình Lợi', 'Xã Đa Phước', 'Xã Tân Nhựt', 'Xã Tân Túc', 'Xã Quy Đức',
                             'Xã Hưng Long', 'Xã Tân Quý Tây', 'Xã Hiệp Phước']
            danhmucquan = ['Huyện Củ Chi', 'Huyện Cần Giờ']
            if rec.vitri_quan.name in danhmucquan:
                rec.sotien_khuvuc = 200000
            elif rec.vitri_phuong.name in danhmucphuong:
                rec.sotien_khuvuc = 100000
            else:
                rec.sotien_khuvuc = 0

    @api.onchange('vitri_phuong', 'vitri_quan')
    def _thanhtoan_phidichuyen(self):
        for rec in self:
            danhmucphuong = ['Phường Long Bình', 'Phường Long Phước', 'Xã Lê Minh Xuân', 'Xã Phạm Văn Hai',
                             'Xã Bình Lợi', 'Xã Đa Phước', 'Xã Tân Nhựt', 'Xã Tân Túc', 'Xã Quy Đức',
                             'Xã Hưng Long', 'Xã Tân Quý Tây', 'Xã Hiệp Phước']
            danhmucquan = ['Huyện Củ Chi', 'Huyện Cần Giờ']
            if rec.vitri_quan.name in danhmucquan:
                rec.thanhtoan_phidichuyen = 500000
            elif rec.vitri_phuong.name in danhmucphuong:
                rec.thanhtoan_phidichuyen = 100000
            else:
                rec.thanhtoan_phidichuyen = 0

    # Kiểm tra tài sản trùng lặp
    @api.constrains('tentaisan')
    def _check_unique_asset_number(self):
        for record in self:
            for tentaisan in record.tentaisan:
                existing_records = self.env['project.task'].search([
                    ('tentaisan', 'in', tentaisan.ids),
                    ('id', '!=', record.id)  # Exclude the current record from the search
                ])
                if existing_records:
                    raise ValidationError('Tên tài sản này đã được tạo hoặc sử dụng trước đây, hãy kiểm tra lại để tránh trùng lặp! \n\n'
                                          'Nếu làm hồ sơ tái thẩm định vui lòng tạo tên tài sản kèm thêm hậu tố để phân biệt.')