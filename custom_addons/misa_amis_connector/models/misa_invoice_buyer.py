from odoo import models, fields, api

class MisaInvoiceBuyer(models.Model):
    _name = "misa.invoice.buyer"
    _description = "MISA Invoice Buyer"

    name = fields.Char(string="Tên người mua hàng", required=True)

