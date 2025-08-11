# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from .utils.haversine import haversine  # Đảm bảo import đúng


class MHDRealEstateDraft(models.Model):
    _name = "mhd.realestate.draft"
    _inherit = ['mail.thread']
    _description = "Sơ bộ tài sản"
    _order = "id desc"

    name = fields.Char(string='Mã hồ sơ', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    date = fields.Date(string='Ngày sơ bộ', default=lambda self: fields.Date.today(), copy=False, required=True)
    khachhang = fields.Many2one('res.partner', string='Tên tín dụng', copy=False)
    khachhang_area = fields.Many2one(string='PGD', related='khachhang.parent_id', readonly=False, store=True, tracking=True)
    khachhang_chinhanh = fields.Many2one(string='Chi nhánh', related='khachhang_area.relative_partner_id',
                                      readonly=False, store=True, tracking=True)
    tinhtrang = fields.Boolean(string='Tình trạng thực hiện', tracking=True)
    nhanvien = fields.Many2one('res.partner', string='Người sơ bộ')
    tentaisan = fields.Char(string='Tên tài sản', compute='_compute_tentaisan')

    @api.depends('vitri_sonha', 'vitri_duong',
                  'vitri_phuong', 'vitri_quan', 'vitri_tinh',
                  'vitri_chungcu_macan', 'vitri_chungcu_block', 'vitri_chungcu')
    def _compute_tentaisan(self):
        for record in self:
            # Xử lý địa chỉ căn hộ chung cư
            if record.vitri_chungcu:
                chungcu_address = f"Căn hộ số {record.vitri_chungcu_macan or ''}, Block {record.vitri_chungcu_block or ''}, {record.vitri_chungcu.name or ''}"
                location = ', '.join(
                    filter(None, [record.vitri_phuong.name, record.vitri_quan.name, record.vitri_tinh.name]))
                record.tentaisan = f"{chungcu_address}, {location}"
            # Xử lý địa chỉ nhà mặt đất nếu có số nhà
            elif record.vitri_sonha:
                house_address = f"{record.vitri_sonha or ''} {record.vitri_duong.name or ''}".strip()
                location = ', '.join(
                    filter(None, [record.vitri_phuong.name, record.vitri_quan.name, record.vitri_tinh.name]))
                record.tentaisan = f"{house_address}, {location}".strip().rstrip(',')
            else:
                record.tentaisan = ''

    khuvuc = fields.Char(string='Khu vực, vị trí')
    # Địa chỉ bất động sản
    vitri_chungcu_macan = fields.Char(string='Mã căn hộ', tracking=True)
    vitri_chungcu_block = fields.Char(string='Block', tracking=True)
    vitri_chungcu = fields.Many2one('mhd.vitri.chungcu', string='Tên chung cư')
    vitri_sonha = fields.Char(string='Địa chỉ', tracking=True)
    vitri_duong = fields.Many2one('mhd.vitri.duong', string='Tên đường')
    vitri_phuong = fields.Many2one('mhd.vitri.phuong', string='Tên Phường/ Xã')
    vitri_quan = fields.Many2one('mhd.vitri.quan', string='Tên Quận/ Huyện')
    vitri_tinh = fields.Many2one('mhd.vitri.tinh', string='Tên Tỉnh/ TP')
    toado_kinhdo = fields.Float(string='Kinh độ')
    toado_vido = fields.Float(string='Vĩ độ')
    land_line = fields.One2many('mhd.realestate.land.line', 'hoso_id', string='Quyền sử dụng đất', copy=True)
    build_line = fields.One2many('mhd.realestate.build.line', 'hoso_id', string='Công trình xây dựng', copy=True)
    canho_line = fields.One2many('mhd.realestate.canho.line', 'hoso_id', string='Căn hộ chung cư', copy=True)
    dat_total = fields.Float(string='Tổng giá trị đất', compute='_dat_total', digits=(15, 0))
    build_total = fields.Float(string='Tổng giá CTXD', compute='_build_total', digits=(15, 0))
    tstd_total = fields.Float(string='Tổng giá trị TSTĐ', compute='_tstd_total', digits=(15, 0))
    canho_total = fields.Float(string='Tổng giá trị căn hộ', compute='_canho_total', digits=(15, 0))
    note = fields.Text(string='Ghi chú')
    quyhoach_hinhanh = fields.Binary(string='Hình quy hoạch', attachment=True)
    quyhoach_vanban = fields.Text(string='Thông tin quy hoạch')
    ghichu = fields.Html('Hình ảnh quy hoạch')
    ghichu_sailech = fields.Char(string='Phạm vi sai lệch', default='+/-10%')
    ghichu_phidichuyen = fields.Html(string='Phí di chuyển', default='<p>- Khu vực thuộc các huyện Củ Chi, Cần Giờ, phí định giá sẽ bằng mức phí trên cộng thêm 500 nghìn (chi phí đi lại)</p><p>- Khu vực thuộc huyện Hóc Môn; phường Long Bình, Long Phước thành phố Thủ Đức; xã Lê Minh Xuân, Phạm Văn Hai, Bình Lợi, Đa Phước, Tân Nhựt, Tân Túc, Quy Đức, Hưng Long, Tân Quý Tây huyện Bình Chánh; xã Hiệp Phước huyện Nhà Bè, phí định giá sẽ bằng mức phí trên cộng thêm 100 nghìn (chi phí đi lại)</p>')
    # Loại Bất động sản
    loaibatdongsan = fields.Selection([
        ('nha_pho', 'Nhà phố'),
        ('can_ho', 'Căn hộ'),
        ('biet_thu', 'Biệt thự'),
        ('dat_trong', 'Đất trống'),
        ('nha_xuong', 'Nhà xưởng'),
    ],
        string="Loại Bất động sản")
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    dongiasobo = fields.Float(string='Đơn giá sơ bộ', group_operator='avg', digits=(15, 0))
    phithamdinh = fields.Float(string='Phí tạm tính', digits=(15, 0))
    phithamdinhthuchien = fields.Float(string='Phí thực hiện', digits=(15, 0), readonly=False, store=True, compute='_phithamdinhthuchien')
    khoanggiatri = fields.Char(string='Khoảng giá trị TSTĐ')
    dientich = fields.Float(string='Diện tích', compute='_dientich')
    # Tính trung bình đơn giá
    dacdiem_vitri_bds = fields.Selection([
        ('ba_mat_tien', '3 MT'),
        ('hai_mat_tien', '2 MT'),
        ('mot_mat_tien', '1 MT'),
        ('hem', 'Hẻm'),
    ],
        string="Đặc điểm vị trí", tracking=True)
    average_price = fields.Float(string='Giá gợi ý', digits=(15, 0), store=True)
    properties = fields.One2many('mhd.datalist', 'realestate_draft_id',
                                 string='Danh sách tài sản')
    # Thêm tọa độ tài sản sơ bộ
    center_longitude = fields.Float(string='Kinh độ', digits=(16, 5), compute='_onchange_coordinate_input', store=True)
    center_latitude = fields.Float(string='Vĩ độ', digits=(16, 5), compute='_onchange_coordinate_input', store=True)
    search_radius = fields.Float(string='Phạm vi tìm (km)', default='0.5')
    coordinate_input = fields.Char(string='Tọa độ tài sản')

    @api.depends('coordinate_input')
    def _onchange_coordinate_input(self):
        for record in self:
            if record.coordinate_input:
                try:
                    lat, lon = map(float, record.coordinate_input.split(','))
                    record.center_latitude = lat
                    record.center_longitude = lon
                except ValueError:
                    record.center_latitude = 0.0
                    record.center_longitude = 0.0
            else:
                record.center_latitude = 0.0
                record.center_longitude = 0.0

    @api.onchange('loaibatdongsan', 'vitri_duong', 'vitri_chungcu', 'dacdiem_vitri_bds', 'center_longitude',
                 'center_latitude', 'search_radius')
    def _compute_recent_properties(self):
        for record in self:
            record.properties = self._get_recent_properties()

    def _get_recent_properties(self):
        end_date = self.date
        start_date = end_date - timedelta(days=730)

        for record in self:
            domain = [
                ('vitri_quan', '=', record.vitri_quan.name),
                ('vitri_chungcu', '=', record.vitri_chungcu.name),
                ('chungthu_date', '>=', start_date),
                ('chungthu_date', '<=', end_date),
            ]

            if record.loaibatdongsan == 'can_ho':
                domain.append(('loaibatdongsan', '=', 'can_ho'))
            else:
                domain.append(('loaibatdongsan', 'in', ['nha_pho', 'biet_thu', 'dat_trong', 'nha_xuong']))

            if record.dacdiem_vitri_bds == 'hem':
                domain.append(('dacdiem_vitri_bds', '=', 'hem'))
            else:
                domain.append(('dacdiem_vitri_bds', 'in', ['mot_mat_tien', 'hai_mat_tien', 'ba_mat_tien']))

            # Chỉ lấy bản ghi có tọa độ
            domain += [
                ('customer_longitude', '!=', False),
                ('customer_latitude', '!=', False)
            ]

            # Truy vấn một lần
            properties = self.env['mhd.datalist'].search(domain, limit=300)

            # Nếu không có dữ liệu → bỏ qua
            if not properties:
                record.properties = self.env['mhd.datalist']
                continue

            # Lọc theo khoảng cách (1 lần duy nhất)
            filtered = properties.filtered(
                lambda p: haversine(
                    record.center_longitude, record.center_latitude,
                    p.customer_longitude, p.customer_latitude
                ) <= record.search_radius
            )

            if not filtered:
                record.properties = self.env['mhd.datalist']
                continue

            # Ưu tiên tuyến đường
            same_street = filtered.filtered(lambda p: p.vitri_duong == record.vitri_duong.name)

            record.properties = same_street if same_street else filtered

        return record.properties

    # def _get_recent_properties(self):
    #     self.ensure_one()
    #     end_date = self.date  # Thời điểm thực hiện tính toán
    #     start_date = end_date - timedelta(days=730)  # 2 năm trước đó
    #     for record in self:
    #         domain = [
    #             ('vitri_quan', '=', record.vitri_quan.name),
    #             ('vitri_chungcu', '=', record.vitri_chungcu.name),
    #             ('chungthu_date', '>=', start_date),
    #             ('chungthu_date', '<=', end_date)
    #         ]
    #
    #         if record.loaibatdongsan == 'can_ho':
    #             domain.append(('loaibatdongsan', '=', record.loaibatdongsan))
    #         else:
    #             domain.append(('loaibatdongsan', 'in', ['nha_pho', 'biet_thu', 'dat_trong', 'nha_xuong']))
    #         if record.dacdiem_vitri_bds == 'hem':
    #             domain.append(('dacdiem_vitri_bds', '=', record.dacdiem_vitri_bds))
    #         else:
    #             domain.append(('dacdiem_vitri_bds', 'in', ['mot_mat_tien', 'hai_mat_tien', 'ba_mat_tien']))
    #
    #         properties = self.env['mhd.datalist'].search(domain + [('vitri_duong', '=', record.vitri_duong.name)])
    #         filtered_properties = properties.filtered(
    #             lambda p: haversine(record.center_longitude, record.center_latitude, p.customer_longitude,
    #                                 p.customer_latitude) <= record.search_radius
    #         )
    #         # Nếu không có tài sản nào trên tuyến đường cụ thể trong phạm vi tìm kiếm
    #         if not filtered_properties:
    #             properties = self.env['mhd.datalist'].search(domain + [('vitri_duong', '!=', record.vitri_duong.name)])
    #             filtered_properties = properties.filtered(
    #                 lambda p: haversine(record.center_longitude, record.center_latitude, p.customer_longitude,
    #                                     p.customer_latitude) <= record.search_radius
    #             )
    #
    #         record.properties = filtered_properties
    #     return filtered_properties

    # Tính trung bình đơn giá 4 tài sản lấy ra ở trên
    @api.onchange('properties')
    def _average_price(self):
        for record in self:
            if record.properties:
                total_price = sum(prop.dat_dongia for prop in record.properties)
                record.average_price = total_price / len(record.properties)
            else:
                record.average_price = 0.0

    @api.onchange('land_line', 'canho_line')
    def _dongiasobo(self):
        for land in self:
            loaibatdongsan = land.loaibatdongsan
            for line in land.land_line:
                if loaibatdongsan != 'can_ho':
                    land.dongiasobo = max(line.dat_dongia for line in land.land_line)
            for line in land.canho_line:
                if loaibatdongsan == 'can_ho':
                    land.dongiasobo = max(line.canho_dongia for line in land.canho_line)

    @api.depends('land_line', 'canho_line')
    def _dientich(self):
        for land in self:
            loaibatdongsan = land.loaibatdongsan
            if loaibatdongsan != 'can_ho':
                land.dientich = sum(line.dat_dientich for line in land.land_line)
            elif loaibatdongsan == 'can_ho':
                land.dientich = sum(line.canho_dientich for line in land.canho_line)

    @api.depends('tinhtrang', 'phithamdinh')
    def _phithamdinhthuchien(self):
        for rec in self:
            if rec.tinhtrang != True:
                rec.phithamdinhthuchien = 0
            elif rec.tinhtrang == True:
                rec.phithamdinhthuchien = rec.phithamdinh

    @api.onchange('tstd_total')
    def _phithamdinhnhapho(self):
        for rec in self:
            if rec.tstd_total < 3000000000:
                rec.phithamdinh = 2200000
                rec.khoanggiatri = '< 3 tỷ'
            elif rec.tstd_total < 5000000000:
                rec.phithamdinh = 2500000
                rec.khoanggiatri = '[3 --- 5 tỷ]'
            elif rec.tstd_total < 10000000000:
                rec.phithamdinh = 3000000
                rec.khoanggiatri = '[5 --- 10 tỷ]'
            elif rec.tstd_total < 15000000000:
                rec.phithamdinh = 4000000
                rec.khoanggiatri = '[10 --- 15 tỷ]'
            elif rec.tstd_total < 20000000000:
                rec.phithamdinh = 5000000
                rec.khoanggiatri = '[15 --- 20 tỷ]'
            elif rec.tstd_total < 25000000000:
                rec.phithamdinh = 6000000
                rec.khoanggiatri = '[20 --- 25 tỷ]'
            elif rec.tstd_total < 30000000000:
                rec.phithamdinh = 7000000
                rec.khoanggiatri = '[25 --- 30 tỷ]'
            elif rec.tstd_total < 40000000000:
                rec.phithamdinh = 8000000
                rec.khoanggiatri = '[30 --- 40 tỷ]'
            elif rec.tstd_total < 50000000000:
                rec.phithamdinh = 12000000
                rec.khoanggiatri = '[40 --- 50 tỷ]'
            elif rec.tstd_total < 100000000000:
                rec.phithamdinh = 20000000
                rec.khoanggiatri = '[50 --- 100 tỷ]'
            elif rec.tstd_total < 150000000000:
                rec.phithamdinh = 30000000
                rec.khoanggiatri = '[100 --- 150 tỷ]'
            elif rec.tstd_total < 200000000000:
                rec.phithamdinh = 40000000
                rec.khoanggiatri = '[150 --- 200 tỷ]'
            elif rec.tstd_total < 10000000000000:
                rec.phithamdinh = 0
                rec.khoanggiatri = '> 200 tỷ'

    @api.onchange('canho_total')
    def _phithamdinhcanho(self):
        for rec in self:
            if rec.canho_total < 3000000000:
                rec.phithamdinh = 2200000
                rec.khoanggiatri = '< 3 tỷ'
            elif rec.canho_total < 5000000000:
                rec.phithamdinh = 2500000
                rec.khoanggiatri = '[3 --- 5 tỷ]'
            elif rec.canho_total < 10000000000:
                rec.phithamdinh = 3000000
                rec.khoanggiatri = '[5 --- 10 tỷ]'
            elif rec.canho_total < 15000000000:
                rec.phithamdinh = 4000000
                rec.khoanggiatri = '[10 --- 15 tỷ]'
            elif rec.canho_total < 20000000000:
                rec.phithamdinh = 5000000
                rec.khoanggiatri = '[15 --- 20 tỷ]'
            elif rec.canho_total < 25000000000:
                rec.phithamdinh = 6000000
                rec.khoanggiatri = '[20 --- 25 tỷ]'
            elif rec.canho_total < 30000000000:
                rec.phithamdinh = 7000000
                rec.khoanggiatri = '[25 --- 30 tỷ]'
            elif rec.canho_total < 40000000000:
                rec.phithamdinh = 8000000
                rec.khoanggiatri = '[30 --- 40 tỷ]'
            elif rec.canho_total < 50000000000:
                rec.phithamdinh = 12000000
                rec.khoanggiatri = '[40 --- 50 tỷ]'
            elif rec.canho_total < 100000000000:
                rec.phithamdinh = 20000000
                rec.khoanggiatri = '[50 --- 100 tỷ]'
            elif rec.canho_total < 150000000000:
                rec.phithamdinh = 30000000
                rec.khoanggiatri = '[100 --- 150 tỷ]'
            elif rec.canho_total < 200000000000:
                rec.phithamdinh = 40000000
                rec.khoanggiatri = '[150 --- 200 tỷ]'
            elif rec.canho_total < 10000000000000:
                rec.phithamdinh = 0
                rec.khoanggiatri = '> 200 tỷ'

    @api.onchange('land_line')
    def _dat_total(self):
        for land in self:
            land.dat_total = sum(line.dat_subtotal for line in land.land_line)

    @api.onchange('build_line')
    def _build_total(self):
        for build in self:
            build.build_total = sum(line.build_subtotal for line in build.build_line)

    @api.onchange('canho_line')
    def _canho_total(self):
        for canho in self:
            canho.canho_total = sum(line.canho_subtotal for line in canho.canho_line)

    @api.depends('dat_total', 'build_total')
    def _tstd_total(self):
        for rec in self:
            rec.tstd_total = rec.dat_total + rec.build_total

    @api.model
    def create(self, vals):
        seq_date = None
        if 'date' in vals:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('mhd.realestate.draft', sequence_date=seq_date) or _('New')
        res = super(MHDRealEstateDraft, self).create(vals)
        return res


# Module Land Line
class MHDRealEstateLandLine(models.Model):
    _name = "mhd.realestate.land.line"
    _description = "Trường đất"
    _order = "id desc"

    hoso_id = fields.Many2one('mhd.realestate.draft', string='Mã hồ sơ')
    sequence = fields.Integer('Sequence')
    # Đất trống
    dat_loaidat = fields.Selection([
        ('dat_o', 'Đất ở'),
        ('dat_nongnghiep', 'Đất nông nghiệp'),
        ('dat_sxkd', 'Đất SXKD'),
        ('dat_tmdv', 'Đất TMDV'),
    ],
        default='dat_o', string="Loại đất")
    dat_quyhoach = fields.Selection([
        ('ngoai_lo_gioi', 'Ngoài lộ giới/ QH'),
        ('trong_lo_gioi', 'Trong lộ giới/ QH'),
    ],
        default='ngoai_lo_gioi', string="Diện tích quy hoạch")
    dat_dongia = fields.Float(string='Đơn giá', digits=(15, 0))
    dat_dientich = fields.Float(string='Diện tích')
    dat_subtotal = fields.Float(string='Giá trị đất', compute='_dat_subtotal', digits=(15, 0))
    note = fields.Text(string='Ghi chú')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")


    @api.depends('dat_dongia', 'dat_dientich')
    def _dat_subtotal(self):
        for rec in self:
            rec.dat_subtotal = round(rec.dat_dongia * rec.dat_dientich, 0)

    # @api.model
    # def create(self, values):
    #     if values.get('display_type', self.default_get(['display_type'])['display_type']):
    #         values.update(dat_loaidat=False, dat_quyhoach=False, dat_dientich=0, dat_dongia=0, dat_subtotal=0)
    #     line = super(MHDRealEstateLandLine, self).create(values)
    #     print("Hoạt động")
    #     return line
    #
    # @api.model_create_multi
    # def write(self, values):
    #     if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
    #         raise UserError(
    #             "You cannot change the type of a sale order line. Instead you should delete the current line and create a new line of the proper type.")
    #     result = super(MHDRealEstateLandLine, self).write(values)
    #     print("Hoạt động")
    #     return result
# Module Data Build Line
class MHDRealEstateBuildLine(models.Model):
    _name = "mhd.realestate.build.line"
    _description = "Trường CTXD"
    _order = "id desc"

    hoso_id = fields.Many2one('mhd.realestate.draft', string='Mã hồ sơ')
    # Công trình trên đất
    ctxd_name = fields.Char(string='Tên công trình', default='Nhà ở')
    ctxd_dientich = fields.Float(string='Diện tích')
    ctxd_dongia = fields.Float(string='Đơn giá', digits=(15, 0))
    ctxd_clcl = fields.Float(string='CLCL')
    build_subtotal = fields.Float(string='Giá trị CTXD', compute='_build_total', digits=(15, 0))

    @api.depends('ctxd_dientich', 'ctxd_dongia', 'ctxd_clcl')
    def _build_total(self):
        for rec in self:
            rec.build_subtotal = round(rec.ctxd_dientich * rec.ctxd_dongia * rec.ctxd_clcl, 0)

# Module Data Can Ho Line
class MHDRealEstateCanhoLine(models.Model):
    _name = "mhd.realestate.canho.line"
    _description = "Trường Căn hộ"
    _order = "id desc"

    hoso_id = fields.Many2one('mhd.realestate.draft', string='Mã hồ sơ')
    # Căn hộ
    canho_loaidientich = fields.Selection([
        ('can_ho', 'Diện tích căn hộ'),
        ('san_vuon', 'Diện tích sân vườn'),
    ],
        default='can_ho', string="Tài sản")
    canho_dientich = fields.Float(string='Diện tích')
    canho_dongia = fields.Float(string='Đơn giá', digits=(15, 0))
    canho_subtotal = fields.Float(string='Giá trị căn hộ', compute='_canho_subtotal', digits=(15, 0))

    @api.depends('canho_dientich', 'canho_dongia')
    def _canho_subtotal(self):
        for rec in self:
            rec.canho_subtotal = round(rec.canho_dientich * rec.canho_dongia, 0)
