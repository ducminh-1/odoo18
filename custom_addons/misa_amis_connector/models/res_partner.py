import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    misa_account_object_code = fields.Char(string="Mã khách hàng Misa")
    misa_account_object_name = fields.Char(string="Tên khách hàng Misa")
    misa_account_object_address = fields.Char(string="Địa chỉ khách hàng Misa")
    misa_account_object_tax_code = fields.Char(string="Mã số thuế Misa")

    is_retail_no_invoice = fields.Boolean(string="Khách lẻ không lấy hóa đơn")
    misa_invoice_buyer_id = fields.Many2one("misa.invoice.buyer", string="Người mua hàng")
 
    @api.onchange("is_retail_no_invoice")
    def onchange_is_retail_no_invoice(self):
        if self.is_retail_no_invoice:     
            default_buyer = self.env['misa.invoice.buyer'].search([
                ("name", "=", "Người mua không cung cấp (đầy đủ) thông tin - Không lấy hóa đơn")
            ], limit=1)
            if default_buyer:      
                self.misa_invoice_buyer_id = default_buyer 
        else:
            self.misa_invoice_buyer_id = False
 
    @api.model
    def create(self, vals):
        ref = vals.get("ref", "")
        if "khachle" in ref.lower():
            vals["is_retail_no_invoice"] = True

        if vals.get('is_retail_no_invoice'):
            default_buyer = self.env['misa.invoice.buyer'].search([
                ("name", "=", "Người mua không cung cấp (đầy đủ) thông tin - Không lấy hóa đơn")
            ], limit=1)
            if default_buyer:
                vals["misa_invoice_buyer_id"] = default_buyer.id

        return super().create(vals)

    def write(self, vals):
        if vals.get('is_retail_no_invoice'):
            default_buyer = self.env['misa.invoice.buyer'].search([
                ("name", "=", "Người mua không cung cấp (đầy đủ) thông tin - Không lấy hóa đơn")
            ], limit=1)
            if default_buyer:
                vals["misa_invoice_buyer_id"] = default_buyer.id

        return super().write(vals)
            
