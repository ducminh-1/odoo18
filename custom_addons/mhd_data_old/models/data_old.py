# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


# Module Data List
class MHDDataOld(models.Model):
    _name = "mhd.data.old"
    _description = "Dữ liệu MHD từ 2016 - 2021"
    _order = 'id asc'

    # Thông tin hồ sơ
    name = fields.Char(string='Địa chỉ tài sản', tracking=True)
    # id = fields.Char(string='Mã tài sản', tracking=True)
    customer_longitude = fields.Float(
        string='Kinh độ', digits=(16, 5), tracking=True)
    customer_latitude = fields.Float(
        string='Vĩ độ', digits=(16, 5), tracking=True)
    vitri = fields.Selection([
        ('VT1', '3 mặt tiền'),
        ('VT2', '2 mặt tiền'),
        ('VT3', '1 mặt tiền'),
        ('VT4', 'Hẻm > 5m'),
        ('VT5', 'Hẻm từ 3m đến 5m'),
        ('VT6', 'Hẻm từ 2m đến dưới 3m'),
        ('VT7', 'Hẻm < 2m'),
    ],
        string="Vị trí")
    huong = fields.Selection([
        ('01', 'Đông Nam'),
        ('02', 'Tây'),
        ('03', 'Nam'),
        ('04', 'Bắc'),
        ('05', 'Tây Nam'),
        ('06', 'Tây Bắc'),
        ('07', 'Đông Bắc'),
        ('08', 'Đông'),
        ('09', 'Không xác định'),
    ],
        string="Hướng")
    hinhdang = fields.Selection([
        ('01', 'Vuông vức'),
        ('02', 'Không vuông vức'),
        ('03', 'Nở hậu'),
        ('04', 'Tóp hậu'),
        ('05', 'Chữ L'),
    ],
        string="Hình dáng")
    thoidiemthamdinh = fields.Char(string='Thời điểm thẩm định', tracking=True)
    sochungthu = fields.Char(string='Số chứng thư', tracking=True)
    giatridat = fields.Float(string='Giá trị đất', tracking=True)
    dientichdat = fields.Float(string='Diện tích đất', tracking=True)
    dongiadat = fields.Float(string='Đơn giá đất (Tr/m2)', group_operator='avg', digits=(16, 3), tracking=True)
    tenduong = fields.Char(string='Tên đường', tracking=True)
    tenphuong = fields.Char(string='Phường/ xã', tracking=True)
    tenquan = fields.Char(string='Quận/ Huyện', tracking=True)

