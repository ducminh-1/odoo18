# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime


# Module Data List
class MHDTaohoso(models.Model):
    _name = "mhd.hoso"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "MHD Tạo hồ sơ"
    _order = "id desc"

    name = fields.Char(string='Tên tài sản', tracking=True)
    hoso_id = fields.Char(string='Mã hồ sơ', required=True, copy=False, readonly=True,
                              default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        # seq_date = None
        # if 'datalist_date' in vals:
        #     seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['datalist_date']))
        if vals.get('hoso_id', _('New')) == _('New'):
            vals['hoso_id'] = self.env['ir.sequence'].next_by_code('mhd.hoso') or _('New')
        res = super(MHDTaohoso, self).create(vals)
        return res
# Module Data List
class MHDDataList(models.Model):
    _name = "mhd.datalist"
    _inherit = ['mail.thread']
    _description = "MHD Data List"
    _order = 'chungthu_date desc, chungthu_id asc'

    # Thông tin hồ sơ
    name = fields.Char(string='Tên tài sản', tracking=True)
    chungthu_id = fields.Many2one('mhd.chungthu', string='Số chứng thư', tracking=True, copy=False, domain="[('datalist_id', '=', name)]")
    chungthu_date = fields.Date(string='Ngày phát hành', related='chungthu_id.chungthu_date', store=True, tracking=True)
    hopdong_id = fields.Many2one('mhd.hopdong', string='Số hợp đồng', tracking=True, copy=False, domain="[('datalist_id', '=', name)]")
    hopdong_ids = fields.Many2many('mhd.hopdong', 'mhd_datalist_ref', 'datalist_id_rec', 'hopdong_id_rec', string='Số hợp đồng', tracking=True)
    # hopdong_line = fields.One2many('mhd.hopdong', 'name', string='Hợp đồng')
    hopdong_date = fields.Date(string='Ngày ký', related='hopdong_id.hopdong_date', store=True, tracking=True)
    project_task_line = fields.One2many('project.task', 'hopdong_id', string='Nhiệm vụ', tracking=True)
    project_task_id = fields.Many2one('project.task', string='Nhiệm vụ', tracking=True)
    # Thông tin khách hàng & trung gian
    khachhang_type = fields.Selection([
        ('ca_nhan', 'Cá nhân'),
        ('cong_ty', 'Doanh nghiệp tư nhân'),
        ('cong_ty_nha_nuoc', 'Doanh nghiệp nhà nước'),
        ('to_chuc_tin_dung', 'Tổ chức tín dụng'),
        ('don_vi_nha_nuoc', 'Cơ quan/ đơn vị nhà nước'),
        ('phap_che', 'Pháp chế'),
        ('to_chuc_khac', 'Tổ chức khác'),
    ],
        string="Loại khách hàng")
    khachhang_id = fields.Many2one('res.partner', string='Tên khách hàng', tracking=True)
    khachhang_phone = fields.Char(string='Điện thoại', related='khachhang_id.phone', readonly=False, tracking=True)
    khachhang_email = fields.Char(string='Email', related='khachhang_id.email', readonly=False, tracking=True)
    khachhang_diachi = fields.Char(string='Địa chỉ', related='khachhang_id.contact_address', tracking=True)
    khachhang_cmnd = fields.Char(string='CMND', related='khachhang_id.cmnd', readonly=False, tracking=True)
    khachhang_cmnd_ngaycap = fields.Date(string='Ngày cấp', related='khachhang_id.cmnd_ngaycap', readonly=False, tracking=True)
    khachhang_cmnd_noicap = fields.Char(string='Nơi cấp', related='khachhang_id.cmnd_noicap', readonly=False, tracking=True)
    khachhang_vat = fields.Char(string='Mã số thuế', related='khachhang_id.vat', readonly=False, tracking=True)
    khachhang_daidien = fields.Char(string='Người đại diện', related='khachhang_id.daidien', readonly=False,
                                    tracking=True)
    khachhang_daidien_chucvu = fields.Char(string='Chức vụ', related='khachhang_id.daidien_chucvu', readonly=False,
                                           tracking=True)
    # Thêm địa chỉ đầy đủ khách hàng
    khachhang_diachi_street = fields.Char(string='Số nhà, tên đường', related='khachhang_id.street')
    khachhang_diachi_street2 = fields.Char(string='Tên xã/phường', related='khachhang_id.street2')
    khachhang_diachi_city = fields.Char(string='Tên quận/ huyện', related='khachhang_id.city')
    khachhang_diachi_state_id = fields.Many2one(string='Tên tỉnh/TP', related='khachhang_id.state_id')
    khachhang_diachi_country_id = fields.Many2one(string='Tên tỉnh/TP', related='khachhang_id.country_id')
    # Thông tin đối tác
    doitac_id = fields.Many2one('res.partner', string='Tên tín dụng/ Đối tác', tracking=True)
    doitac_phone = fields.Char(string='Điện thoại ĐT', related='doitac_id.phone', readonly=False, tracking=True)
    doitac_email = fields.Char(string='Email ĐT', related='doitac_id.email', readonly=False, store=True, tracking=True)
    doitac_relative_partner_id = fields.Many2one(string='Đối tác liên quan', related='doitac_id.relative_partner_id', readonly=False, tracking=True)
    doitac_relative_partner_id_email = fields.Char(string='Email liên quan', related='doitac_relative_partner_id.email', tracking=True)
    doitac_groups = fields.Many2one(string='Nhóm khách hàng', related='doitac_area.khachhang_groups', readonly=False, store=True, tracking=True)
    doitac_name = fields.Many2one(string='Đối tượng khách hàng', related='doitac_area.khachhang_name', readonly=False, store=True, tracking=True)
    doitac_area = fields.Many2one(string='Trụ sở/ Chi nhánh', related='doitac_id.parent_id', readonly=False, store=True, tracking=True)
    doitac_relative = fields.Many2one(string='Khách hàng liên quan', related='doitac_area.relative_partner_id', readonly=False, store=True, tracking=True)
    # congty = fields.Many2one(string="Đơn vị", related='doitac_id.parent_id' )
    # Thông tin nhân viên MHD
    kinhdoanh = fields.Many2one('res.users', string='Kinh doanh', tracking=True)
    nhanvien = fields.Many2one('res.users', string='Nhân viên', tracking=True)
    thamdinhvien = fields.Many2one('res.users', string='Thẩm định viên', tracking=True)
    quanly = fields.Many2one('res.users', string='Quản lý', tracking=True)

    # Thông tin địa chỉ tài sản
    vitri_chungcu_macan = fields.Char(string='Mã căn hộ', tracking=True)
    vitri_chungcu_block = fields.Char(string='Block', tracking=True)
    vitri_chungcu = fields.Many2one('mhd.vitri.chungcu', string='Tên chung cư', tracking=True)
    vitri_sonha = fields.Char(string='Địa chỉ', tracking=True)
    vitri_duong = fields.Many2one('mhd.vitri.duong', string='Tên đường', tracking=True)
    vitri_phuong = fields.Many2one('mhd.vitri.phuong', string='Tên Phường/ Xã', tracking=True)
    vitri_quan = fields.Many2one('mhd.vitri.quan', string='Tên Quận/ Huyện', tracking=True)
    vitri_tinh = fields.Many2one('mhd.vitri.tinh', string='Tên Tỉnh/ TP', tracking=True)
    # Đặc điểm vị trí
    dacdiem_vitri_bds = fields.Selection([
        ('ba_mat_tien', '3 MT'),
        ('hai_mat_tien', '2 MT'),
        ('mot_mat_tien', '1 MT'),
        ('hem', 'Hẻm'),
    ],
        string="Đặc điểm vị trí", tracking=True)
    dacdiem_vitri_canho = fields.Selection([
        ('can_goc', 'Căn góc'),
        ('can_thuong', 'Căn thường'),
        ('can_shop', 'Căn Shop'),
        ('penthouse', 'Penthouse'),
    ],
        string="Vị trí căn hộ", tracking=True)
    dacdiem_ketcauduong = fields.Selection([
        ('duong_nhua', 'Đường nhựa'),
        ('be_tong', 'Đường bê tông'),
        ('duong_dat', 'Đường đất'),
    ],
        string="Kết cấu đường", tracking=True)
    dacdiem_dorongduong = fields.Char(string='Độ rộng đường/hẻm', tracking=True)

    # Đặc điểm tài sản
    loaitaisan = fields.Selection([
        ('bat_dong_san', 'Bất động sản'),
        ('dong_san', 'Động sản'),
        ('du_an', 'Dự án đầu tư'),
        ('doanh_nghiep', 'Doanh nghiệp'),
        ('thuong_hieu', 'Thương hiệu'),
        ('khoan_no', 'Khoản nợ'),
        ],
        string="Loại tài sản", tracking=True)
    loaibatdongsan = fields.Selection([
        ('can_ho', 'Căn hộ'),
        ('dat_trong', 'Đất trống'),
        ('nha_pho', 'Nhà phố'),
        ('biet_thu', 'Biệt thự'),
        ('nha_xuong', 'Nhà xưởng'),
        ('khach_san', 'Khách sạn'),
        ('nha_van_phong', 'Nhà văn phòng'),
    ],
        string="Loại Bất động sản", tracking=True)
    phuongphapthamdinh = fields.Many2one('mhd.phuongphap', string='Phương pháp thẩm định', tracking=True)
    mucdichthamdinh = fields.Many2one('mhd.mucdichthamdinh', string='Mục đích thẩm định', tracking=True)
    motataisan = fields.Text(string='Mô tả tài sản', tracking=True)

    # Thông tin giá đất
    dat_loaidat = fields.Selection([
        ('dat_o', 'Đất ở'),
        ('dat_nongnghiep', 'Đất nông nghiệp'),
        ('dat_sxkd', 'Đất sxkd'),
        ('dat_tmdv', 'Đất thương mại dịch vụ'),
        ('dat_khac', 'Đất khác'),
    ],
        string="Loại đất", tracking=True)
    dat_dientich = fields.Float(string='Diện tích', tracking=True)
    dat_dongia = fields.Float(string='Đơn giá', group_operator='avg', digits=(15, 0), tracking=True)
    dat_giatri_chinh = fields.Float(string='Giá trị đất', compute='_dat_giatri_chinh', readonly=False, digits=(15, 0), tracking=True)
    dat_giatri_khac = fields.Float(string='Giá trị đất khác', digits=(15, 0), tracking=True)
    dat_giatri_total = fields.Float(string='Tổng giá trị QSD đất', compute='_dat_giatri_total', readonly=False, digits=(15, 0), tracking=True)
    # Thông tin giá công trình xây dựng
    ctxd_loaicongtrinh = fields.Selection([
        ('nha_pho', 'Nhà phố'),
        ('biet_thu', 'Biệt thự'),
        ('van_phong', 'Nhà văn phòng'),
        ('khach_san', 'Khách sạn'),
        ('nha_xuong', 'Nhà xưởng'),
    ],
        string="Loại CTXD", tracking=True)
    ctxd_dientich = fields.Float(string='Diện tích CTXD', tracking=True)
    ctxd_dongia = fields.Float(string='Đơn giá CTXD', digits=(15, 0), tracking=True)
    ctxd_clcl = fields.Float(string='CLCL', tracking=True)
    ctxd_giatri_chinh = fields.Float(string='Giá trị CTXD', compute='_ctxd_giatri_chinh', digits=(15, 0), readonly=False, tracking=True)
    ctxd_giatri_khac = fields.Float(string='Giá trị CTXD khác', digits=(15, 0), tracking=True)
    ctxd_giatri_total = fields.Float(string='Tổng giá trị CTXD', compute='_ctxd_giatri_total', readonly=False, digits=(15, 0), tracking=True)
    # Tổng giá trị tài sản
    total_tstd = fields.Float(string='Tổng giá trị TSTĐ', readonly=False, digits=(15, 0), tracking=True)
    # Thông tin thanh toán
    thanhtoan_phidichuyen = fields.Float(string='Phí di chuyển', digits=(15, 0), tracking=True)
    thanhtoan_tongphi = fields.Float(string='Tổng phí', digits=(15, 0), tracking=True)
    thanhtoan_vat = fields.Selection([
        ('10', 'Gồm VAT 10%'),
        ('8', 'Gồm VAT 8%'),
        ('0', 'Chưa VAT'),
        ],
        default='10', string='Thuế VAT', tracking=True)
    thanhtoan_dathanhtoan = fields.Float(string='Đã thanh toán', digits=(15, 0), store=True, compute='_thanhtoan_total', tracking=True)
    thanhtoan_chuathanhtoan = fields.Float(string='Chưa thanh toán', digits=(15, 0), compute='_thanhtoan_chuathanhtoan', store=True, tracking=True)
    thanhtoan_thoidiem = fields.Date(string='Thời điểm thanh toán', tracking=True)
    full_phi = fields.Boolean(string='Thu Full', tracking=True)

    # Thông tin hoa hồng
    hoahong_tienke = fields.Float(string='Tiền kê', digits=(15, 0), tracking=True)
    hoahong_tyle = fields.Float(string='Tỷ lệ hoa hồng', tracking=True)
    hoahong_thanhtien = fields.Float(string='Tiền hoa hồng', compute='_hoahong_thanhtien', digits=(15, 0), store=True, tracking=True)
    hoahong_tinhtrang = fields.Selection([
        ('chua_chi', 'Chưa chi'),
        ('da_chi', 'Đã chi')],
        default='chua_chi', string="Tình trạng chi trả hoa hồng", tracking=True)

    # Thông tin phụ cấp
    tyle_hoahongnoibo = fields.Float(string='Tỷ lệ HH Nội bộ', tracking=True)
    tyle_kinhdoanh = fields.Float(string='Tỷ lệ PC Kinh doanh', tracking=True)
    tyle_nhanvien = fields.Float(string='Tỷ lệ PC NV',default='0.05', tracking=True)
    tyle_thamdinhvien = fields.Float(string='Tỷ lệ PC TĐV', default='0.015', tracking=True)
    tyle_quanly = fields.Float(string='Tỷ lệ PC BGĐ', default='0.01', tracking=True)
    tyle_backoffice = fields.Float(string='Tỷ lệ PC BO', default='0.01', tracking=True)
    sotien_hoahongnoibo = fields.Float(string='Tiền hoa hồng nội bộ', compute='_hoahong_thanhtien', digits=(15, 0), tracking=True)
    sotien_kinhdoanh = fields.Float(string='Tiền Phụ cấp KD', compute='_phucap_thanhtien', digits=(15, 0), tracking=True)
    sotien_khuvuc = fields.Float(string='Phụ cấp khu vực', digits=(15, 0), tracking=True)
    sotien_nhanvien = fields.Float(string='Tiền Phụ cấp NV', compute='_phucap_thanhtien', digits=(15, 0), store=True, tracking=True)
    sotien_thamdinhvien = fields.Float(string='Tiền Phụ cấp TĐV', compute='_phucap_thanhtien', digits=(15, 0), store=True, tracking=True)
    sotien_quanly = fields.Float(string='Tiền Phụ cấp BGĐ', compute='_phucap_thanhtien', digits=(15, 0), store=True, tracking=True)
    sotien_backoffice = fields.Float(string='Tiền Phụ cấp BO', compute='_phucap_thanhtien', digits=(15, 0), store=True, tracking=True)
    tinhtrang_phucap = fields.Selection([
        ('chua_chi', 'Chưa chi'),
        ('da_chi', 'Đã chi')],
        default='chua_chi', string='Tình trạng chi trả phụ cấp', tracking=True)
    # Ghi chú
    ghichu_hopdong = fields.Selection([
        ('chua_ky', 'Chưa ký'),
        ('da_ky', 'Đã ký'),
        ('chua_thu_hoi', 'Chưa thu hồi'),
        ('da_luu', 'Đã lưu trữ'),
        ('huy', 'Hủy'),
    ], default='chua_ky', string='Tình trạng hợp đồng', tracking=True)
    ghichu_chungthu = fields.Selection([
        ('chua_in', 'Chưa in'),
        ('da_in', 'Đã in'),
        ('da_gui', 'Đã gửi'),
        ('da_luu', 'Đã lưu trữ'),
    ], default='chua_in', string='Tình trạng chứng thư', tracking=True)
    ghichu_lanphathanh = fields.Char(string='Lần phát hành', tracking=True)
    ghichu_hoahong = fields.Char(string='Ghi chú hoa hồng', tracking=True)
    ghichu_mabill = fields.Char(string='Mã Bill gửi thư', tracking=True)
    ghichu_mabill_ngay = fields.Date(string='Ngày gửi thư', tracking=True)
    ghichu_hoadon = fields.Char(string='Số Hóa đơn', tracking=True)
    ghichu_hoadon_ngay = fields.Date(string='Ngày Hóa đơn', tracking=True)
    ghichu_hoadon_tinhtrang = fields.Selection([
        ('khong_lay_hoa_don', 'Khách hàng không lấy hóa đơn'),
        ('lay_hoa_don', 'Khách hàng lấy hóa đơn'),
    ], string='Ghi chú hóa đơn', tracking=True)
    ghichu_congno = fields.Selection([
        ('da_hoan_thanh', 'Đã hoàn thành'),
        ('con_phai_thu', 'Còn phải thu'),
    ], string='Công nợ', compute='_congno', tracking=True)
    ghichu_khac = fields.Char(string='Ghi chú khác', tracking=True)
    ghichu_ketoan = fields.Char(string='Ghi chú kế toán', tracking=True)
    note = fields.Text(string='Ghi chú', tracking=True)
    luutru = fields.Char(string='Thư mục lưu trữ', tracking=True)
    chiphithang = fields.Float(string='Chi phí tháng', digits=(15, 0), tracking=True)
    active = fields.Boolean('Active', default=True)

    # Thông tin thanh toán
    thanhtoan_line = fields.One2many('mhd.thanhtoan', 'datalist_id', string='Thông tin thanh toán')
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, check_company=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, required=False, index=True,
        default=lambda self: self.env.company)
    # tính trung bình thị trường, liên kết với sơ bộ giá
    realestate_draft_id = fields.Many2one('mhd.realestate.draft', string='Liên kết giá sơ bộ')

    # Bổ sung pháp lý căn hộ
    phaply_taisan = fields.Selection([
        ('gcn', 'Đã cấp GCN'),
        ('hdmb', 'Hợp đồng mua bán'),
    ], string='Pháp lý tài sản', tracking=True)

    # Hàm tính toán

    @api.depends('thanhtoan_chuathanhtoan', 'thanhtoan_tongphi', 'thanhtoan_dathanhtoan')
    def _congno(self):
        for rec in self:
            thanhtoan_chuathanhtoan = rec.thanhtoan_tongphi - rec.thanhtoan_dathanhtoan
            if thanhtoan_chuathanhtoan == 0:
                rec.ghichu_congno = 'da_hoan_thanh'
            elif thanhtoan_chuathanhtoan != 0:
                rec.ghichu_congno = 'con_phai_thu'

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

    @api.depends('thanhtoan_tongphi', 'thanhtoan_dathanhtoan')
    def _thanhtoan_chuathanhtoan(self):
        for rec in self:
            rec.thanhtoan_chuathanhtoan = rec.thanhtoan_tongphi - rec.thanhtoan_dathanhtoan


    @api.depends('thanhtoan_line.sotien')
    def _thanhtoan_total(self):
        for rec in self:
            rec.thanhtoan_dathanhtoan = sum(line.sotien for line in rec.thanhtoan_line)


    @api.depends('thanhtoan_dathanhtoan', 'hoahong_tyle', 'thanhtoan_vat', 'hoahong_tienke', 'thanhtoan_phidichuyen')
    def _hoahong_thanhtien(self):
        for rec in self:
            vat = rec.thanhtoan_vat
            if vat == '10':
                rec.hoahong_thanhtien = round((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.1 * rec.hoahong_tyle + rec.hoahong_tienke, 0)
                rec.sotien_hoahongnoibo = round((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.1 * rec.tyle_hoahongnoibo, 0)
            elif vat == '8':
                rec.hoahong_thanhtien = round((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.08 * rec.hoahong_tyle + rec.hoahong_tienke, 0)
                rec.sotien_hoahongnoibo = round((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.08 * rec.tyle_hoahongnoibo, 0)
            elif vat == '0':
                rec.hoahong_thanhtien = round((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) * rec.hoahong_tyle + rec.hoahong_tienke, 0)
                rec.sotien_hoahongnoibo = round((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) * rec.tyle_hoahongnoibo, 0)
            else:
                rec.hoahong_thanhtien = round((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) * rec.hoahong_tyle + rec.hoahong_tienke, 0)
                rec.sotien_hoahongnoibo = round((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) * rec.tyle_hoahongnoibo, 0)


    @api.onchange('vitri_phuong', 'vitri_quan')
    def _phucap_khuvuc(self):
        for rec in self:
            danhmucphuong = ['Phường Long Bình', 'Phường Long Phước', 'Xã Lê Minh Xuân', 'Xã Phạm Văn Hai',
                             'Xã Bình Lợi', 'Xã Đa Phước', 'Xã Tân Nhựt', 'Xã Tân Túc', 'Xã Quy Đức',
                             'Xã Hưng Long', 'Xã Tân Quý Tây', 'Xã Hiệp Phước']
            danhmucquan = ['Huyện Củ Chi', 'Huyện Cần Giờ']
            if rec.vitri_quan.name in danhmucquan:
                rec.sotien_khuvuc = 200000
                print(rec.create_date)
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


    @api.depends('thanhtoan_dathanhtoan', 'hoahong_tyle', 'thanhtoan_vat', 'hoahong_thanhtien', 'tyle_kinhdoanh', 'tyle_nhanvien', 'tyle_thamdinhvien', 'tyle_quanly', 'tyle_backoffice')
    def _phucap_thanhtien(self):
        for rec in self:
            vat = rec.thanhtoan_vat
            if vat == '10':
                rec.sotien_kinhdoanh = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.1 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_kinhdoanh, 0)
                rec.sotien_nhanvien = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.1 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_nhanvien, 0)
                rec.sotien_thamdinhvien = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.1 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_thamdinhvien, 0)
                rec.sotien_quanly = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.1 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_quanly, 0)
                rec.sotien_backoffice = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.1 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_backoffice, 0)
            elif vat == '8':
                rec.sotien_kinhdoanh = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.08 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_kinhdoanh, 0)
                rec.sotien_nhanvien = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.08 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_nhanvien, 0)
                rec.sotien_thamdinhvien = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.08 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_thamdinhvien, 0)
                rec.sotien_quanly = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.08 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_quanly, 0)
                rec.sotien_backoffice = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) / 1.08 - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_backoffice, 0)
            elif vat == '0':
                rec.sotien_kinhdoanh = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_kinhdoanh, 0)
                rec.sotien_nhanvien = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_nhanvien, 0)
                rec.sotien_thamdinhvien = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_thamdinhvien, 0)
                rec.sotien_quanly = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_quanly, 0)
                rec.sotien_backoffice = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_backoffice, 0)
            else:
                rec.sotien_kinhdoanh = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_kinhdoanh, 0)
                rec.sotien_nhanvien = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_nhanvien, 0)
                rec.sotien_thamdinhvien = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_thamdinhvien, 0)
                rec.sotien_quanly = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_quanly, 0)
                rec.sotien_backoffice = round(((rec.thanhtoan_dathanhtoan - rec.thanhtoan_phidichuyen) - rec.hoahong_thanhtien - rec.sotien_hoahongnoibo) * rec.tyle_backoffice, 0)


    def action_send_mail(self):
        self.ensure_one()
        template_id = self.env.ref('mhd_valuation.mail_template_ket_qua').id
        ctx = {
            'default_model': 'mhd.datalist',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': 'mhd_valuation.mail_bank',
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': ctx,
        }


# Module phương pháp
class MHDPhuongphap(models.Model):
    _name = "mhd.phuongphap"
    _description = "Phương pháp thẩm định"
    _order = "id asc"

    name = fields.Char(string='Phương pháp thẩm định', required=True, tracking=True)

# Module Mục đích thẩm định
class MHDMucdichthamdinh(models.Model):
    _name = "mhd.mucdichthamdinh"
    _description = "Mục đích thẩm định"
    _order = "id asc"

    name = fields.Char(string='Mục đích thẩm định', required=True, tracking=True)