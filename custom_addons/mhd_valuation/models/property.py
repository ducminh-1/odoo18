# -*- coding: utf-8 -*-

from odoo import api, fields, models

# Module loại tài sản
class MHDVitriDuong(models.Model):
    _name = "mhd.taisan.loai"
    _description = "Loại tài sản thẩm định"
    _order = "id desc"

    name = fields.Char(string='Loại tài sản thẩm định', required=True, tracking=True)