from odoo import api, fields, models


class MisaSAVoucherLine(models.Model):
    _name = "misa.sa_voucher.line"
    _description = "Misa SA Voucher Line"

    sequence = fields.Integer()
    voucher_id = fields.Many2one("misa.sa_voucher", string="Voucher")

    credit_account = fields.Char(
        compute="_compute_account", store=True, string="TK Doanh thu"
    )
    debit_account = fields.Char(
        compute="_compute_account", store=True, string="TK Công nợ"
    )
    exchange_rate_operator = fields.Char()
    product_id = fields.Many2one("product.product")
    inventory_item_code = fields.Char(
        string="Mã hàng", compute="_compute_inventory_item_code", store=True
    )
    description = fields.Char(
        compute="_compute_inventory_item_code",
        string="Tên hàng",
        store=True,
        readonly=False,
    )
    unit_name = fields.Char(
        compute="_compute_inventory_item_code", store=True, string="ĐVT"
    )
    main_unit_name = fields.Char(compute="_compute_inventory_item_code", store=True)
    inventory_item_type = fields.Selection(
        [
            ("0", "Vật tư hàng hóa"),
            ("1", "Thành phẩm"),
            ("2", "Dịch vụ"),
            ("3", "Nguyên vật liệu"),
        ],
        string="Loại hàng hóa/dịch vụ",
    )

    main_unit_price = fields.Float()
    main_quantity = fields.Float()
    quantity = fields.Float(string="Số lượng")
    unit_price = fields.Float(string="Đơn giá")
    amount_oc = fields.Float()
    amount = fields.Float(string="Thành tiền")
    discount_rate = fields.Float(string="Tỷ lệ chiết khấu")
    discount_amount_oc = fields.Float()
    discount_amount = fields.Float(string="Chiết khấu")
    vat_rate = fields.Float(string="% Thuế GTGT")
    vat_amount_oc = fields.Float()
    vat_amount = fields.Float(string="Tiền thuế GTGT")
    vat_account = fields.Char(string="TK Thuế GTGT")

    warehouse_id = fields.Many2one(
        "stock.warehouse",
        related="voucher_id.warehouse_id",
    )
    stock_code = fields.Char(
        compute="_compute_stock_code",
        string="Kho",
    )

    main_convert_rate = fields.Float()

    invoice_line_ids = fields.Many2many(
        "account.move.line",
        "account_move_line_sa_voucher_rel",
        "sa_voucher_line_id",
        "account_move_line_id",
        string="Invoice Lines",
    )

    @api.depends(
        "product_id",
        "product_id.misa_inventory_item_code",
        "product_id.misa_inventory_item_name",
        "product_id.misa_inventory_unit_name",
    )
    def _compute_inventory_item_code(self):
        for line in self:
            if line.voucher_id.state != "draft":
                line.inventory_item_code = line.inventory_item_code
                line.description = line.description
                line.unit_name = line.unit_name
                line.main_unit_name = line.main_unit_name
            else:
                line.inventory_item_code = line.product_id.misa_inventory_item_code
                line.description = line.product_id.misa_inventory_item_name
                line.unit_name = line.product_id.misa_inventory_unit_name
                line.main_unit_name = line.product_id.misa_inventory_unit_name

    @api.depends(
        "product_id.categ_id",
        "product_id.categ_id.property_account_income_categ_id",
        "product_id.categ_id.property_account_expense_categ_id",
        "product_id.categ_id.property_account_income_categ_id.misa_account_number",
        "product_id.categ_id.property_account_expense_categ_id.misa_account_number",
    )
    def _compute_account(self):
        for line in self:
            if line.voucher_id.state != "draft":
                line.credit_account = line.credit_account
                line.debit_account = line.debit_account
            else:
                if line.product_id.categ_id.property_account_income_categ_id:
                    line.credit_account = line.product_id.categ_id.property_account_income_categ_id.misa_account_number
                else:
                    line.credit_account = False

                line.debit_account = "131"

    # @api.depends("product_id", "product_id.uom_id", "product_id.uom_id.misa_unitname")
    # def _compute_unit(self):
    #     for line in self:
    #         if line.voucher_id.state != "draft":
    #             line.unit_name = line.unit_name
    #             line.main_unit_name = line.main_unit_name
    #         else:
    #             if line.product_id.uom_id:
    #                 line.unit_name = line.product_id.uom_id.misa_unitname
    #                 line.main_unit_name = line.product_id.uom_id.misa_unitname
    #             else:
    #                 line.unit_name = False
    #                 line.main_unit_name = False

    @api.depends(
        "warehouse_id",
        "warehouse_id.out_type_id",
        "warehouse_id.out_type_id.default_location_src_id",
        "warehouse_id.out_type_id.default_location_src_id.misa_stock_code",
    )
    def _compute_stock_code(self):
        for line in self:
            if line.voucher_id.state != "draft":
                line.stock_code = line.stock_code
            else:
                line.stock_code = line.warehouse_id.out_type_id.default_location_src_id.misa_stock_code

    def _prepare_voucher_line_data(self):
        data = {
            "inventory_item_code": self.inventory_item_code,
            "description": self.description,
            "credit_account": self.credit_account,
            "debit_account": self.debit_account,
            "main_unit_name": self.main_unit_name,
            "unit_name": self.unit_name,
            "main_unit_price": self.main_unit_price,
            "main_quantity": self.main_quantity,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "amount_oc": self.amount_oc,
            "amount": self.amount,
            "discount_rate": self.discount_rate,
            "discount_amount_oc": self.discount_amount_oc,
            "discount_amount": self.discount_amount,
            "vat_rate": self.vat_rate,
            "vat_amount_oc": self.vat_amount_oc,
            "vat_amount": self.vat_amount,
            # "vat_account": self.vat_account,
            "main_convert_rate": self.main_convert_rate,
            "exchange_rate_operator": self.exchange_rate_operator,
        }
        if self.voucher_id.is_sale_with_outward:
            data["stock_code"] = self.stock_code
        if self.vat_account:
            data["vat_account"] = self.vat_account
        if self.voucher_id.account_object_code:
            data["account_object_code"] = self.voucher_id.account_object_code
        if self.voucher_id.account_object_name:
            data["account_object_name"] = self.voucher_id.account_object_name

        return data
