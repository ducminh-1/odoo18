# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from datetime import date

# Module lấy số hợp đồng ngẫu nhiên
class MHDSohopdong(models.Model):
    _name = "mhd.hopdong"
    _inherit = ['mail.thread']
    _description = "MHD - Số hợp đồng"
    _order = "id desc"

    name = fields.Char(string='Số hợp đồng', tracking=True, required=True, copy=False, readonly=False, default=lambda self: _('New'))
    datalist_id = fields.Many2many('mhd.datalist', string='Tên tài sản', tracking=True, required=True)
    chungthu_id = fields.Many2one(string='Chứng thư liên quan', related='datalist_id.chungthu_id', tracking=True)
    hopdong_date = fields.Date(string='Ngày ký HĐ', required=True, tracking=True)
    hopdong_type = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('cong_ty', 'Doanh nghiệp tư nhân'),
        ('cong_ty_nha_nuoc', 'Doanh nghiệp nhà nước'),
        ('to_chuc_tin_dung', 'Tổ chức tín dụng'),
        ('don_vi_nha_nuoc', 'Cơ quan/ đơn vị nhà nước'),
        ('phap_che', 'Pháp chế'),
        ('to_chuc_khac', 'Tổ chức khác'),
    ],
        related='datalist_id.khachhang_type', readonly=False, string="Kiểu hợp đồng")
    # Khách hàng trên chứng thư
    khachhang_id = fields.Many2one('res.partner', string='Tên khách hàng', related='datalist_id.khachhang_id', readonly=False, tracking=True)
    khachhang_street = fields.Char(string='Số nhà', related='khachhang_id.street', readonly=False, tracking=True)
    khachhang_street2 = fields.Char(string='Đường', related='khachhang_id.street2', readonly=False, tracking=True)
    khachhang_city = fields.Char(string='Quận', related='khachhang_id.city', readonly=False, tracking=True)
    state_id = fields.Many2one(string='Tỉnh/ TP', related='khachhang_id.state_id', readonly=False, tracking=True)
    country_id = fields.Many2one(string='Quốc gia', related='khachhang_id.country_id', readonly=False, tracking=True)
    zip = fields.Char(string='Mã bưu điện', related='khachhang_id.zip', readonly=False, tracking=True)
    khachhang_phone = fields.Char(string='Điện thoại', related='khachhang_id.phone', readonly=False, tracking=True)
    khachhang_email = fields.Char(string='Email', related='khachhang_id.email', store=True, readonly=False,
                                  tracking=True)
    khachhang_cmnd = fields.Char(string='CMND/ CCCD', related='khachhang_id.cmnd', readonly=False, tracking=True)
    khachhang_cmnd_ngaycap = fields.Date(string='Ngày cấp', related='khachhang_id.cmnd_ngaycap', readonly=False, tracking=True)
    khachhang_cmnd_noicap = fields.Char(string='Nơi cấp', related='khachhang_id.cmnd_noicap', readonly=False, tracking=True)
    khachhang_vat = fields.Char(string='Mã số thuế', related='khachhang_id.vat', readonly=False, tracking=True)
    khachhang_daidien = fields.Char(string='Người đại diện', related='khachhang_id.daidien', readonly=False, tracking=True)
    khachhang_daidien_chucvu = fields.Char(string='Chức vụ', related='khachhang_id.daidien_chucvu', readonly=False, tracking=True)

    # Đối tác giới thiệu/ Môi giới hồ sơ
    doitac_id = fields.Many2one('res.partner', string='Tên đối tác', related='datalist_id.doitac_id', readonly=False, tracking=True)
    doitac_groups = fields.Many2one(string='Nhóm khách hàng', related='doitac_area.khachhang_groups', readonly=False,
                              tracking=True)
    doitac_name = fields.Many2one(string='Đối tượng khách hàng', related='doitac_area.khachhang_name', readonly=False, tracking=True)
    doitac_area = fields.Many2one(string='Trụ sở/ Chi nhánh', related='doitac_id.parent_id', readonly=False,
                                  tracking=True)
    nhanvien = fields.Many2one(string='Người thực hiện', related='datalist_id.nhanvien', readonly=False)
    project_task_id = fields.Many2one('project.task', string='Nhiệm vụ')
    project_task_line = fields.One2many('project.task', 'hopdong_id', string='Nhiệm vụ')
    # datalist_id = fields.Many2one('mhd.datalist', string='Tên tài sản')
    datalist_ids = fields.Many2many('mhd.datalist', 'mhd_datalist_ref', 'hopdong_id_rec', 'datalist_id_rec', string='Tên tài sản')
    # Thông tin thanh toán
    thanhtoan_tongphi = fields.Float(string='Tổng phí', related='datalist_id.thanhtoan_tongphi', readonly=False, digits=0)
    thanhtoan_vat = fields.Selection([
        ('10', 'Gồm VAT 10%'),
        ('8', 'Gồm VAT 8%'),
        ('0', 'Chưa VAT'),
    ],
        default='10', related='datalist_id.thanhtoan_vat', readonly=False, string='Thuế VAT')
    tinhtrangkyket = fields.Selection(related='datalist_id.ghichu_hopdong', default='chua_ky', readonly=False, string='Tình trạng ký kết')
    active = fields.Boolean('Active', default=True)

    # Kiểm tra trùng lặp số hợp đồng
    @api.onchange('datalist_id')
    def _onchange_datalist_id(self):
        if self.datalist_id:
            message = None
            for datalist in self.datalist_id:
                domain = [
                    ('datalist_id', 'in', datalist.ids)
                ]
                if self.id:  # Check if the record has a valid ID
                    domain.append(('id', '!=', self.id))

                existing_numbers = self.env['mhd.hopdong'].search(domain)
                if existing_numbers:
                    message = {
                        'title': 'Cảnh báo!',
                        'message': '- Bạn thấy cảnh báo này vì một trong những tài sản bạn lựa chọn đã được cấp số hợp đồng.'
                                   'Hãy chắc rằng bạn không lấy 2 số hợp đồng cho cùng 1 tài sản. Hãy tiếp tục với lựa chọn sau:\n\n'
                                   '+ Trường hợp 1: Bạn muốn cấp số hợp đồng thứ 2 cho tài sản thì bấm "Đồng ý" và nhập đầy đủ các mục khác.\n\n'
                                   '+ Trường hợp 2: Bạn chọn nhầm hoặc thao tác sai, hãy bấm "Đồng ý" và "Hủy bỏ" việc lấy số này. Đồng thời kiểm tra lại Tab "Hợp đồng chứng thư" trong Nhiệm vụ, số hợp đồng sẽ hiển thị tại đó.\n'
                    }
                if message:
                    return {'warning': message}

    # Tạo số hợp đồng ngẫu nhiên
    def create_hop_dong(self):
        self.env['mhd.hopdong'].browse(self._context.get('active_ids', []))
        return True


    @api.model
    def create(self, vals):
        seq_date = None
        if 'hopdong_date' in vals and vals.get('hopdong_date') != False:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['hopdong_date']))
        if vals.get('name', _('New')) == _('New') and seq_date != None:
            vals['name'] = self.env['ir.sequence'].next_by_code('mhd.hopdong', sequence_date=seq_date) or _('New')
        res = super(MHDSohopdong, self).create(vals)
        if res.datalist_id:  # Cập nhập tự động số hợp đồng qua Datalist
            res.datalist_id.write({'hopdong_id': res.id})  # Cập nhập tự động chứng thư qua Datalist
        return res

    # Tự động cập nhập số hợp đồng qua Datalist
    def write(self, vals):
        res = super(MHDSohopdong, self).write(vals)
        for res in self:
            if 'datalist_id' in vals and res.datalist_id:
                res.datalist_id.write({'hopdong_id': res.id})
        return res


# Module lấy số chứng thư ngẫu nhiên
class MHDSochungthu(models.Model):
    _name = "mhd.chungthu"
    _inherit = ['mail.thread']
    _description = "MHD - Số chứng thư"
    _order = "chungthu_date desc, name asc"

    name = fields.Char(string='Số chứng thư', tracking=True, required=True, copy=False, readonly=True, default=lambda self: _('New'))
    datalist_id = fields.Many2one('mhd.datalist', string='Tên tài sản', required=True, tracking=True)
    nhanvien = fields.Many2one(string='Người thực hiện', related='datalist_id.nhanvien', readonly=False, tracking=True)
    chungthu_date = fields.Date(string='Ngày phát hành', required=True, tracking=True)
    hopdong_id = fields.Many2one(string='Hợp đồng liên quan', related='datalist_id.hopdong_id', tracking=True)
    phuongphapthamdinh = fields.Many2one(string='Phương pháp thẩm định', related='datalist_id.phuongphapthamdinh', required=True, readonly=False, tracking=True)
    mucdichthamdinh = fields.Many2one(string='Mục đích thẩm định', related='datalist_id.mucdichthamdinh', required=True, readonly=False, tracking=True)
    loaitaisan = fields.Selection([
        ('bat_dong_san', 'Bất động sản'),
        ('dong_san', 'Động sản'),
        ('du_an', 'Dự án đầu tư'),
        ('doanh_nghiep', 'Doanh nghiệp'),
        ('thuong_hieu', 'Thương hiệu'),
        ('khoan_no', 'Khoản nợ'),
    ],
        string="Loại tài sản", related='datalist_id.loaitaisan', required=True, readonly=False)
    tinhtrangphathanh = fields.Selection([
        ('chua_in', 'Chưa in'),
        ('da_in', 'Đã in'),
        ('da_gui', 'Đã gửi'),
        ('da_luu', 'Đã lưu trữ'),
    ],
        default='chua_in', readonly=False, related='datalist_id.ghichu_chungthu', string='Tình trạng phát hành')
    thanhtoan_line = fields.One2many('mhd.thanhtoan', 'chungthu', string='Chứng thư', tracking=True)
    active = fields.Boolean('Active', default=True)

    # Kiểm tra trùng lặp số chứng thư
    @api.onchange('datalist_id')
    def _onchange_datalist_id(self):
        if self.datalist_id:
            message = None
            for datalist in self.datalist_id:
                domain = [
                    ('datalist_id', 'in', datalist.ids)
                ]
                if self.id:  # Check if the record has a valid ID
                    domain.append(('id', '!=', self.id))

                existing_numbers = self.env['mhd.chungthu'].search(domain)
                if existing_numbers:
                    message = {
                        'title': 'Cảnh báo!',
                        'message': '- Bạn thấy cảnh báo này vì một trong những tài sản bạn lựa chọn đã được cấp số chứng thư.'
                                   'Hãy chắc rằng bạn không lấy 2 số chứng thư cho cùng 1 tài sản. Hãy tiếp tục với lựa chọn sau:\n\n'
                                   '+ Trường hợp 1: Bạn muốn cấp số chứng thư thứ 2 cho tài sản thì bấm "Đồng ý" và nhập đầy đủ các mục khác.\n\n'
                                   '+ Trường hợp 2: Bạn chọn nhầm hoặc thao tác sai, hãy bấm "Đồng ý" và "Hủy bỏ" việc lấy số này. Đồng thời kiểm tra lại Tab "Hợp đồng chứng thư" trong Nhiệm vụ, số chứng thư sẽ hiển thị tại đó.\n'
                    }
                if message:
                    return {'warning': message}
    # Tạo số chứng thư ngẫu nhiên
    def create_chung_thu(self):
        self.env['mhd.chungthu'].browse(self._context.get('active_ids', []))
        return True

    @api.model
    def create(self, vals):
        seq_date = None
        if 'chungthu_date' in vals:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['chungthu_date']))
        if vals.get('name', _('New')) == _('New'):
            if 'chungthu_date' in vals:
                try:
                    chungthu_date = datetime.strptime(vals['chungthu_date'], '%Y-%m-%d').date()
                except ValueError:
                    chungthu_date = datetime.strptime(vals['chungthu_date'], '%d-%m-%Y').date()
                cutoff_date = datetime.strptime('01-07-2024', '%d-%m-%Y').date()
                if chungthu_date < cutoff_date:
                    vals['name'] = self.env['ir.sequence'].next_by_code('mhd.chungthu', sequence_date=seq_date) or _(
                        'New')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('mhd.chungthu.lan2',
                                                                        sequence_date=seq_date) or _('New')
            else:
                vals['name'] = 'New'  # Hoặc xử lý trường hợp không có ngày chứng thư
        res = super(MHDSochungthu, self).create(vals)
        if res.datalist_id:  # Cập nhập tự động chứng thư qua Datalist
            res.datalist_id.write({'chungthu_id': res.id})  # Cập nhập tự động chứng thư qua Datalist
        return res

    # Tự động cập nhập số chứng thư qua Datalist
    def write(self, vals):
        res = super(MHDSochungthu, self).write(vals)
        for res in self:
            if 'datalist_id' in vals and res.datalist_id:
                res.datalist_id.write({'chungthu_id': res.id})
        return res

    # Cảnh báo ngày lấy số chứng thư
    @api.onchange('chungthu_date')
    def _onchange_canh_bao_ngay_chung_thu(self):
        message = None
        for rec in self:
            chungthu_date = rec.chungthu_date
            today = date.today()
            if chungthu_date != today and chungthu_date != False:
                message = {
                    'title': 'Xem lại ngày phát hành!',
                    'message': '- Bạn thấy cảnh báo này vì ngày phát hành bạn chọn có ảnh hưởng tới hệ thống số chứng thư. \nNgày phát hành bạn đang chọn không phải là ngày hôm nay\n\n'
                               '+ Kiểm tra lại ngày đang chọn có chèn vào trước ngày của số chứng thư gần nhất hay không? (Nếu lấy lùi ngày) .\n\n'
                               '+ Kiểm tra lại ngày đang chọn có lấy sau ngày hiện tại không? Việc này sẽ ảnh hưởng tới số chứng thư hồ sơ khác từ hôm nay cho đến ngày bạn chọn.\n\n'
                               'Hạn chế tối đa việc lấy lùi ngày hoặc lấy trước số chứng thư. Cần xin ý kiến quản lý trước khi thực hiện.\n\n'
                }
            if message:
                return {'warning': message}

# Module lấy số chứng thư ngẫu nhiên
class MHDSohopdongLine(models.Model):
    _name = "mhd.hopdong.line"
    _description = "MHD - Dòng hợp đồng"

    hopdong_id = fields.Many2one('mhd.hopdong', string='Số hợp đồng')
    hopdong_date = fields.Date(string='Ngày ký', related='hopdong_id.hopdong_date')
