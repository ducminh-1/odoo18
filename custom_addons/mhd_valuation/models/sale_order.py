# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    land_line = fields.One2many('sale.order.line', 'hoso_id', string='Quyền sử dụng đất')

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    hoso_id = fields.Many2one('sale.order', string='Mã hồ sơ')
    sequence = fields.Integer('Sequence')
    # Đất trống
    dat_loaidat = fields.Selection([
        ('dat_o', 'Đất ở'),
        ('dat_nongnghiep', 'Đất nông nghiệp'),
        ('dat_sxkd', 'Đất SXKD'),
        ('dat_tmdv', 'Đất TMDV'),
    ],
        string="Loại đất")
    dat_quyhoach = fields.Selection([
        ('ngoai_lo_gioi', 'Ngoài lộ giới/ QH'),
        ('trong_lo_gioi', 'Trong lộ giới/ QH'),
    ],
        string="Diện tích quy hoạch")
    dat_dongia = fields.Float(string='Đơn giá')
    dat_dientich = fields.Float(string='Diện tích')
    dat_subtotal = fields.Float(string='Giá trị đất', compute='_dat_subtotal')
    note = fields.Text(string='Ghi chú')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    @api.depends('dat_dongia', 'dat_dientich')
    def _dat_subtotal(self):
        for rec in self:
            rec.dat_subtotal = rec.dat_dongia * rec.dat_dientich
