# -*- coding: utf-8 -*-

from odoo import api, fields, models

# Module Vị trí chung cư
class MHDVitriChungcu(models.Model):
    _name = "mhd.vitri.chungcu"
    _description = "Danh mục Chung cư"
    _order = "id desc"

    name = fields.Char(string='Tên Chung cư', required=True, tracking=True)
    # gianhanuoc_dato = fields.Float(string='Giá đất ở NN', required=True, tracking=True)
    # gianhanuoc_cln = fields.Float(string='Giá đất CLN NN', required=True, tracking=True)
    # gianhanuoc_hnk = fields.Float(string='Giá đất HNK NN', required=True, tracking=True)
    # gianhanuoc_nts = fields.Float(string='Giá đất NTS NN', required=True, tracking=True)
    # gianhanuoc_rsx = fields.Float(string='Giá đất RSX NN', required=True, tracking=True)
    # gianhanuoc_lmu = fields.Float(string='Giá đất LMU NN', required=True, tracking=True)
    # gianhanuoc_tmdv = fields.Float(string='Giá đất TMDV NN', required=True, tracking=True)
    # gianhanuoc_sxkd = fields.Float(string='Giá đất SXKD NN', required=True, tracking=True)
    # note = fields.Char(string='Ghi chú', required=True, tracking=True)
    vitri_quan = fields.Many2one('mhd.vitri.quan', string='Quận/ Huyện', required=True)

# Module Vị trí đường
class MHDVitriDuong(models.Model):
    _name = "mhd.vitri.duong"
    _description = "Danh mục đường"
    _order = "id desc"

    name = fields.Char(string='Tên đường', required=True, tracking=True)
    maduong = fields.Char(string='Mã đường', tracking=True)
    # gianhanuoc_dato = fields.Float(string='Giá đất ở NN', required=True, tracking=True)
    # gianhanuoc_cln = fields.Float(string='Giá đất CLN NN', required=True, tracking=True)
    # gianhanuoc_hnk = fields.Float(string='Giá đất HNK NN', required=True, tracking=True)
    # gianhanuoc_nts = fields.Float(string='Giá đất NTS NN', required=True, tracking=True)
    # gianhanuoc_rsx = fields.Float(string='Giá đất RSX NN', required=True, tracking=True)
    # gianhanuoc_lmu = fields.Float(string='Giá đất LMU NN', required=True, tracking=True)
    # gianhanuoc_tmdv = fields.Float(string='Giá đất TMDV NN', required=True, tracking=True)
    # gianhanuoc_sxkd = fields.Float(string='Giá đất SXKD NN', required=True, tracking=True)
    # note = fields.Char(string='Ghi chú', required=True, tracking=True)
    vitri_quan = fields.Many2one('mhd.vitri.quan', string='Quận/ Huyện', required=True)

# Module Vị trí phường
class MHDVitriPhuong(models.Model):
    _name = "mhd.vitri.phuong"
    _description = "Tên phường/ Xã"
    _order = "id desc"

    name = fields.Char(string='Tên phường/ Xã', required=True, tracking=True)
    maphuong = fields.Char(string='Mã Phường/ Xã', tracking=True)
    vitri_quan = fields.Many2one('mhd.vitri.quan', string='Quận/ Huyện', required=True)

# Module Vị trí Quận
class MHDVitriQuan(models.Model):
    _name = "mhd.vitri.quan"
    _description = "Tên Quận/ Huyện"
    _order = "id asc"

    name = fields.Char(string='Tên Quận/ Huyện', required=True, tracking=True)
    maquan = fields.Char(string='Mã Quận/ Huyện', tracking=True)
    vitri_tinh = fields.Many2one('mhd.vitri.tinh', string='Tỉnh/ TP', required=True)
    vitri_phuong = fields.One2many('mhd.vitri.phuong', 'vitri_quan', string='Phường/ Xã')
    vitri_duong = fields.One2many('mhd.vitri.duong', 'vitri_quan', string='Đường phố')
    vitri_chungcu = fields.One2many('mhd.vitri.chungcu', 'vitri_quan', string='Chung cư')
    danso = fields.Float(string='Dân số (người)', tracking=True)
    dientich = fields.Float(string='Diện tích (km²)', tracking=True)
    donvihanhchinh = fields.Char(string='Đơn vị hành chính', tracking=True)

# Module Vị trí tỉnh/ TP
class MHDVitriTinh(models.Model):
    _name = "mhd.vitri.tinh"
    _description = "Tên Tỉnh/ TP"
    _order = "id asc"

    name = fields.Char(string='Tỉnh/ TP', required=True, tracking=True)
    matinh = fields.Char(string='Mã Tỉnh/ TP', tracking=True)
    tinhly = fields.Char(string='Tỉnh lỵ', tracking=True)
    khuvuc = fields.Char(string='Khu vực', tracking=True)
    danso = fields.Float(string='Dân số (người)', tracking=True)
    dientich = fields.Float(string='Diện tích (km²)', tracking=True)
    donvihanhchinh = fields.Char(string='Đơn vị hành chính', tracking=True)
    biensoxe = fields.Char(string='Biển số xe', tracking=True)
    mavung = fields.Char(string='Mã vùng ĐT', tracking=True)
    vitri_quan = fields.One2many('mhd.vitri.quan', 'vitri_tinh', string='Quận/ Huyện')

