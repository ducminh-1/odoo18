# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    # Thêm trường dữ liệu mới
    relationship = fields.Char(string='Mối quan hệ')
    relative_partner_id = fields.Many2one('res.partner', string="Khách hàng liên quan")
    khachhang_groups = fields.Many2one('mhd.customer.groups', string='Nhóm khách hàng')
    khachhang_name = fields.Many2one('mhd.customer.name', string='Đối tượng khách hàng')
    cmnd = fields.Char(string='CMND/ CCCD')
    cmnd_ngaycap = fields.Date(string='Ngày cấp')
    cmnd_noicap = fields.Char(string='Nơi cấp')
    daidien = fields.Char(string='Người đại diện')
    daidien_chucvu = fields.Char(string='Chức vụ')



    # Edit trưỡng dữ liệu cũ

# Module phân loại khách hàng
class MHDCustomer(models.Model):
    _name = "mhd.customer.groups"
    _description = "Nhóm khách hàng MHD"
    _order = "id asc"

    name = fields.Char(string='Nhóm khách hàng', required=True, tracking=True)
    khachhang_name = fields.One2many('mhd.customer.name', 'khachhang_groups', string='Đối tượng khách hàng')

class MHDNameCustomer(models.Model):
    _name = "mhd.customer.name"
    _description = "Đối tượng khách hàng"
    _order = "id asc"


    name = fields.Char(string='Đối tượng khách hàng', required=True, tracking=True)
    khachhang_groups = fields.Many2one('mhd.customer.groups', string='Nhóm khách hàng')
    # khachhang_area = fields.One2many('mhd.customer.area', 'khachhang_name', string='Trụ sở/ Chi nhánh')

# class MHDAreaCustomer(models.Model):
#     _name = "mhd.customer.area"
#     _description = "Trụ sở/ Chi nhánh khách hàng"
#     _order = "id desc"
#
#     name = fields.Char(string='Trụ sở/ Chi nhánh', required=True, tracking=True)
#     khachhang_name = fields.Many2one('mhd.customer.name', string='Đối tượng khách hàng')