import requests
import json
from odoo import models, fields, api

class ViettelInvoiceSync(models.Model):
    _name = "viettel.invoice.sync"
    _description = "Sync Viettel Invoices to Purchase Orders"

    @api.model
    def sync_invoices_to_po(self, supplier_tax_code):
        url = f"https://hoadondientu.gdt.gov.vn/invoice-sync-tax/search-by-tax/{supplier_tax_code}"
        headers = {
            "Authorization": "Basic username:password",  # hoặc Bearer token
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json={})
        if response.status_code != 200:
            raise Exception(f"API error: {response.text}")

        data = response.json().get("data", [])
        for inv in data:
            seller_tax = inv.get("sellerTaxCode")
            seller_name = inv.get("sellerUnitName")
            issue_date = inv.get("issueDate")
            total = inv.get("totalAmountAfterTax")

            # 1. Tìm hoặc tạo vendor
            partner = self.env["res.partner"].search([("vat", "=", seller_tax)], limit=1)
            if not partner:
                partner = self.env["res.partner"].create({
                    "name": seller_name,
                    "vat": seller_tax,
                    "supplier_rank": 1,
                })

            # 2. Parse listProduct
            product_lines = []
            list_product = inv.get("listProduct")
            if list_product:
                list_product = json.loads(list_product)
                for item in list_product.get("itemInfo", []):
                    product_name = item.get("itemName")
                    qty = item.get("quantity", 1)
                    price = item.get("unitPrice", 0.0)
                    uom = item.get("unitName") or "Unit"

                    # tìm hoặc tạo product
                    product = self.env["product.product"].search([("default_code", "=", item.get("itemCode"))], limit=1)
                    if not product:
                        product = self.env["product.product"].create({
                            "name": product_name,
                            "default_code": item.get("itemCode"),
                            "uom_id": self.env.ref("uom.product_uom_unit").id,
                            "uom_po_id": self.env.ref("uom.product_uom_unit").id,
                        })

                    product_lines.append((0, 0, {
                        "product_id": product.id,
                        "name": product_name,
                        "product_qty": qty,
                        "price_unit": price,
                        "product_uom": product.uom_id.id,
                        "date_planned": fields.Datetime.now(),
                    }))

            # 3. Tạo PO
            po = self.env["purchase.order"].create({
                "partner_id": partner.id,
                "date_order": issue_date,
                "order_line": product_lines,
                "origin": f"ViettelInvoice-{inv.get('invoiceNumber')}",
            })

            # confirm PO nếu cần
            # po.button_confirm()
            # self.env.cr.commit()
