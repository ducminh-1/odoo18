from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MAX_VOUCHER_PER_APP = 50


class MisaSAVoucher(models.Model):
    _name = "misa.sa_voucher"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Misa SA Voucher"

    voucher_type = fields.Selection(
        [
            ("13", "SA Voucher"),
        ],
        string="Loại chứng từ",
    )
    org_refid = fields.Char(readonly=True, string="ID chứng từ dữ liệu gốc")
    org_refno = fields.Char(string="Số chứng từ dữ liệu gốc", tracking=True)
    org_reftype_name = fields.Char(string="Tên loại chứng từ dữ liệu gốc")
    refno_finance = fields.Char(readonly=True, string="Số chứng từ")
    # is_sale_with_outward = fields.Boolean(string="Kiêm phiếu xuất")
    is_sale_with_outward = fields.Boolean(
        compute="_compute_is_sale_with_outward", string="Kiêm phiếu xuất", store=True
    )
    include_invoice = fields.Selection(
        [
            ("0", "Không kèm hóa đơn"),
            ("1", "Nhận kèm hóa đơn"),
            ("2", "Không có hoá đơn"),
        ],
        string="Lập kèm hóa đơn",
        default="1",
    )
    posted_date = fields.Datetime(string="Ngày hạch toán", default=fields.Datetime.now, tracking=True)
    refdate = fields.Datetime(string="Ngày chứng từ", default=fields.Datetime.now, tracking=True)
    reftype = fields.Selection(
        [
            ("3530", "Bán hàng hóa, dịch vụ trong nước chưa thu tiền"),
            ("3531", "Bán hàng hóa, dịch vụ trong nước - Tiền mặt"),
            ("3532", "Bán hàng xuất khẩu"),
            ("3534", "Bán hàng đại lý bán đúng giá - Chưa thu tiền"),
            ("3535", "Bán hàng đại lý bán đúng giá - Tiền mặt"),
            ("3536", "Bán hàng nhận ủy thác xuất khẩu"),
            ("3537", "Bán hàng hóa, dịch vụ trong nước - Chuyển khoản"),
            ("3538", "Bán hàng đại lý bán đúng giá - Chuyển khoản"),
            ("3570", "Bán dịch vụ trong nước chưa thu tiền"),
            ("3571", "Bán dịch vụ trong nước - Tiền mặt"),
            ("3572", "Bán dịch vụ trong nước - Chuyển khoản"),
        ],
        compute="_compute_reftype",
        string="Loại chứng từ",
    )
    total_sale_amount_oc = fields.Float()
    total_sale_amount = fields.Float()
    total_amount_oc = fields.Float()
    total_amount = fields.Float()
    total_discount_amount_oc = fields.Float()
    total_discount_amount = fields.Float()
    total_vat_amount_oc = fields.Float()
    total_vat_amount = fields.Float()
    voucher_line_ids = fields.One2many(
        "misa.sa_voucher.line", "voucher_id", string="Voucher Lines"
    )

    move_id = fields.Many2one(
        "account.move",
        required=False,
        ondelete="cascade",
    )
    sale_id = fields.Many2one(
        "sale.order",
        related="move_id.sale_id",
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        related="sale_id.warehouse_id",
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
    )
    partner_id = fields.Many2one("res.partner", string="Customer")
    account_object_code = fields.Char(
        compute="_compute_account_object",
        string="Mã khách hàng",
        store=True,
    )
    account_object_name = fields.Char(
        compute="_compute_account_object",
        string="Tên khách hàng",
        store=True,
        readonly=False,
    )
    account_object_tax_code = fields.Char(
        compute="_compute_account_object",
        string="Mã số thuế",
        store=True,
        readonly=False,
    )
    account_object_address = fields.Char(
        compute="_compute_account_object",
        string="Địa chỉ",
        store=True,
        readonly=False,
    )
    team_id = fields.Many2one(
        "crm.team",
        string="Sales Team",
        related="move_id.team_id",
        store=True,
    )

    # In_outward
    in_outward_account_object_code = fields.Char(
        compute="_compute_in_outward_account_object",
        string="Mã khách hàng",
        store=True,
        readonly=False,
    )
    in_outward_account_object_name = fields.Char(
        compute="_compute_in_outward_account_object",
        string="Tên khách hàng",
        store=True,
        # readonly=False,
    )
    in_outward_account_object_tax_code = fields.Char(
        compute="_compute_in_outward_account_object",
        string="Mã số thuế",
        store=True,
        # readonly=False,
    )
    in_outward_account_object_address = fields.Char(
        compute="_compute_in_outward_account_object",
        string="Địa chỉ",
        store=True,
        # readonly=False,
    )
    in_outward_in_reforder = fields.Datetime(
        string="Giờ nhập xuất kho", compute="_compute_in_outward_dates", store=True
    )
    in_outward_posted_date = fields.Datetime(
        string="Ngày hoạch toán", compute="_compute_in_outward_dates", store=True
    )
    in_outward_refdate = fields.Datetime(
        string="Ngày chứng từ", compute="_compute_in_outward_dates", store=True
    )
    in_outward_reftype = fields.Selection(
        [
            ("2020", "Xuất kho bán hàng"),
        ],
        default="2020",
        required=True,
        string="Loại chứng từ",
    )
    in_outward_refno_finance = fields.Char(string="Số chứng từ", readonly=True)

    # Invoice
    invoice_account_object_code = fields.Char(
        compute="_compute_invoice_account_object",
        string="Mã khách hàng",
        store=True,
    )
    invoice_account_object_name = fields.Char(
        compute="_compute_invoice_account_object",
        string="Tên khách hàng",
        store=True,
        # readonly=False,
    )
    invoice_account_object_tax_code = fields.Char(
        compute="_compute_invoice_account_object",
        string="Mã số thuế",
        store=True,
        # readonly=False,
    )
    invoice_account_object_address = fields.Char(
        compute="_compute_invoice_account_object",
        string="Địa chỉ",
        store=True,
        # readonly=False,
    )
    invoice_inv_date = fields.Datetime(
        string="Ngày hóa đơn",
        compute="_compute_invoice_dates",
        store=True,
    )
    invoice_inv_no = fields.Char(
        string="Số hóa đơn",
    )
    invoice_inv_series = fields.Char(
        string="Ký hiệu hóa đơn",
    )
    invoice_inv_template_no = fields.Char(
        string="Mẫu số hóa đơn",
    )
    # inv_type_id = fields.Integer()
    invoice_is_paid = fields.Boolean()
    invoice_is_posted = fields.Boolean()
    invoice_is_posted_last_year = fields.Boolean()
    invoice_is_invoice_machine = fields.Boolean()
    invoice_payment_method = fields.Char()
    invoice_reftype = fields.Selection(
        [
            ("3560", "Hóa đơn bán hàng hóa, dịch vụ trong nước"),
        ],
        string="Loại chứng từ",
        default="3560",
    )
    invoice_refno_finance = fields.Char(string="Số chứng từ", readonly=True)
    invoice_buyer_id = fields.Many2one("misa.invoice.buyer", string="Người mua hàng")
    misa_app_id = fields.Many2one("misa.app", string="MISA App", tracking=True)
    misa_branch_id = fields.Many2one(
        "misa.branch",
        string="MISA Branch",
        domain="[('misa_app_id', '=', misa_app_id)]",
        tracking=True,
    )

    def _compute_total(self):
        return

    @api.depends(
        "voucher_line_ids",
        "voucher_line_ids.product_id",
        "voucher_line_ids.product_id.type",
        "reftype",
    )
    def _compute_is_sale_with_outward(self):
        """Set is_sale_with_outward based on voucher lines product type."""
        for voucher in self:
            if voucher.reftype == "3570":
                voucher.is_sale_with_outward = False
            else:
                voucher.is_sale_with_outward = True

    @api.depends(
        "voucher_line_ids",
        "voucher_line_ids.product_id",
        "voucher_line_ids.product_id.type",
    )
    def _compute_reftype(self):
        """Set reftype based on voucher lines product type."""
        for voucher in self:
            if all(
                line.product_id.type == "service" for line in voucher.voucher_line_ids
            ):
                voucher.reftype = "3570"
            else:
                voucher.reftype = "3530"

    ##########################
    ### Chứng từ bán hàng ####
    ##########################
    @api.depends(
        "partner_id",
        "partner_id.misa_account_object_code",
        "partner_id.misa_account_object_name",
        "partner_id.misa_account_object_tax_code",
        "partner_id.misa_account_object_address",
    )
    def _compute_account_object(self):
        for voucher in self:
            if voucher.state != "draft":
                voucher.account_object_code = voucher.account_object_code
                voucher.account_object_name = voucher.account_object_name
                voucher.account_object_tax_code = voucher.account_object_tax_code
                voucher.account_object_address = voucher.account_object_address
            else:
                voucher.account_object_code = (
                    voucher.partner_id.misa_account_object_code
                )
                voucher.account_object_name = (
                    voucher.partner_id.misa_account_object_name
                )
                voucher.account_object_tax_code = (
                    voucher.partner_id.misa_account_object_tax_code
                )
                voucher.account_object_address = (
                    voucher.partner_id.misa_account_object_address
                )

    ###################################
    ### Chứng từ xuất kho bán hàng ####
    ###################################

    @api.depends(
        "partner_id",
        "partner_id.misa_account_object_code",
        "partner_id.misa_account_object_name",
        "partner_id.misa_account_object_tax_code",
        "partner_id.misa_account_object_address",
        "account_object_code",
        "account_object_name",
        "account_object_tax_code",
        "account_object_address",
    )
    def _compute_in_outward_account_object(self):
        """Currently use voucher data"""
        for voucher in self:
            voucher.in_outward_account_object_code = voucher.account_object_code
            voucher.in_outward_account_object_name = voucher.account_object_name
            voucher.in_outward_account_object_tax_code = voucher.account_object_tax_code
            voucher.in_outward_account_object_address = voucher.account_object_address

    @api.depends(
        "refdate",
        "posted_date",
    )
    def _compute_in_outward_dates(self):
        """Currently use voucher data"""
        for voucher in self:
            voucher.in_outward_in_reforder = voucher.refdate
            voucher.in_outward_posted_date = voucher.posted_date
            voucher.in_outward_refdate = voucher.refdate

    #########################
    ### Hóa đơn bán hàng ####
    #########################

    @api.depends(
        "partner_id",
        "partner_id.misa_account_object_code",
        "partner_id.misa_account_object_name",
        "partner_id.misa_account_object_tax_code",
        "partner_id.misa_account_object_address",
        "account_object_code",
        "account_object_name",
        "account_object_tax_code",
        "account_object_address",
    )
    def _compute_invoice_account_object(self):
        """Currently use voucher data"""
        for voucher in self:
            voucher.invoice_account_object_code = voucher.account_object_code
            voucher.invoice_account_object_name = voucher.account_object_name
            voucher.invoice_account_object_tax_code = voucher.account_object_tax_code
            voucher.invoice_account_object_address = voucher.account_object_address

    @api.depends("posted_date")
    def _compute_invoice_dates(self):
        """Currently use voucher data"""
        for voucher in self:
            voucher.invoice_inv_date = voucher.posted_date

    ### Business Logic

    def action_post(self):
        if self:
            self._post()
        return False

    def _post(self):
        no_apps = self.mapped("misa_app_id")
        for app in no_apps:
            app_vouchers = self.filtered(
                lambda voucher, app=app: voucher.misa_app_id == app
            )
            if len(app_vouchers) > MAX_VOUCHER_PER_APP:
                raise ValidationError(
                    _(
                        "Cannot post more than %(max)s vouchers for app %(app_name)s.",
                        max=MAX_VOUCHER_PER_APP,
                        app_name=app.app_name,
                    )
                )
            payload = {
                "app_id": app.app_id,
                "org_company_code": app.org_company_code,
                "voucher": [],
            }
            for voucher in app_vouchers:
                payload["voucher"].append(voucher._prepare_voucer_data())

            # Make the API call to post the vouchers
            response = app._make_request(
                "/apir/sync/actopen/save",
                payload=payload,
            )
            app_vouchers.write({"state": "posted"})
            app_vouchers.message_post(body=_("%s" % response.get("Data")))

    def _prepare_voucer_data(self):
        self.ensure_one()
        payload = {
            "voucher_type": self.voucher_type,
            "org_refid": self.org_refid,
            "org_refno": self.org_refno,
            "org_reftype_name": self.org_reftype_name,
            # "refno_finance": self.refno_finance,
            # "include_invoice": self.include_invoice,
            "posted_date": fields.Datetime.to_string(self.posted_date),
            "refdate": fields.Datetime.to_string(self.refdate),
            "reftype": self.reftype,
            "total_sale_amount_oc": self.total_sale_amount_oc,
            "total_sale_amount": self.total_sale_amount,
            "total_amount_oc": self.total_amount_oc,
            "total_amount": self.total_amount,
            "total_discount_amount_oc": self.total_discount_amount_oc,
            "total_discount_amount": self.total_discount_amount,
            "total_vat_amount_oc": self.total_vat_amount_oc,
            "total_vat_amount": self.total_vat_amount,
            "branch_id": self.misa_branch_id.misa_id,
            "detail": [],
            "account_object_code": self.account_object_code,
        }
        if self.account_object_name:
            payload["account_object_name"] = self.account_object_name
        if self.account_object_tax_code:
            payload["account_object_tax_code"] = self.account_object_tax_code
        if self.account_object_address:
            payload["account_object_address"] = self.account_object_address
        # if self.refno_finance:
        #     payload["refno_finance"] = self.refno_finance
        if self.voucher_line_ids:
            payload["detail"] = [
                line._prepare_voucher_line_data() for line in self.voucher_line_ids
            ]
        if self.is_sale_with_outward:
            payload["is_sale_with_outward"] = self.is_sale_with_outward
            payload["in_outward"] = {
                "account_object_code": self.in_outward_account_object_code,
                "reftype": self.in_outward_reftype,
            }
            if self.in_outward_account_object_name:
                payload["in_outward"]["account_object_name"] = (
                    self.in_outward_account_object_name
                )
            if self.in_outward_account_object_tax_code:
                payload["in_outward"]["account_object_tax_code"] = (
                    self.in_outward_account_object_tax_code
                )
            if self.in_outward_account_object_address:
                payload["in_outward"]["account_object_address"] = (
                    self.in_outward_account_object_address
                )
            if self.in_outward_in_reforder:
                payload["in_outward"]["in_reforder"] = fields.Datetime.to_string(
                    self.in_outward_in_reforder
                )
            if self.in_outward_posted_date:
                payload["in_outward"]["posted_date"] = fields.Datetime.to_string(
                    self.in_outward_posted_date
                )
            if self.in_outward_refdate:
                payload["in_outward"]["refdate"] = fields.Datetime.to_string(
                    self.in_outward_refdate
                )
            # if self.in_outward_refno_finance:
            #     payload["in_outward"]["refno_finance"] = self.in_outward_refno_finance

        if self.include_invoice == "1":
            payload["include_invoice"] = self.include_invoice
            payload["sa_invoice"] = {
                "account_object_code": self.invoice_account_object_code,
                # "account_object_name": self.invoice_account_object_name,
                # "account_object_tax_code": self.invoice_account_object_tax_code,
                # "account_object_address": self.invoice_account_object_address,
                "inv_date": fields.Datetime.to_string(self.invoice_inv_date),
                # "inv_no": self.invoice_inv_no,
                # "inv_series": self.invoice_inv_series,
                # "inv_template_no": self.invoice_inv_template_no,
                # 'inv_type_id': self.inv_type_id,
                # "is_paid": self.invoice_is_paid,
                # "is_posted": self.invoice_is_posted,
                # "is_posted_last_year": self.invoice_is_posted_last_year,
                "is_invoice_machine": self.invoice_is_invoice_machine,
                # "payment_method": self.invoice_payment_method,
            }
            if self.invoice_account_object_name:
                payload["sa_invoice"]["account_object_name"] = (
                    self.invoice_account_object_name
                )
            if self.invoice_account_object_tax_code:
                payload["sa_invoice"]["account_object_tax_code"] = (
                    self.invoice_account_object_tax_code
                )
            if self.invoice_account_object_address:
                payload["sa_invoice"]["account_object_address"] = (
                    self.invoice_account_object_address
                )
            if self.invoice_inv_no:
                payload["sa_invoice"]["inv_no"] = self.invoice_inv_no
            if self.invoice_inv_series:
                payload["sa_invoice"]["inv_series"] = self.invoice_inv_series
            if self.invoice_inv_template_no:
                payload["sa_invoice"]["inv_template_no"] = self.invoice_inv_template_no
            # if self.invoice_refno_finance:
            #     payload["invoice"]["refno_finance"] = self.invoice_refno_finance
            if self.invoice_buyer_id:
                payload["sa_invoice"]["buyer"] = self.invoice_buyer_id.name

        return payload

    def action_post_all(self):
        records = self.search([("state", "=", "draft")])
        for record in records:
            record.action_post()

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.misa_invoice_buyer_id:
            self.invoice_buyer_id = self.partner_id.misa_invoice_buyer_id
        else:
            self.invoice_buyer_id = False

    @api.model
    def create(self, vals):
        partner_id = vals.get("partner_id")
        if partner_id:
            partner = self.env["res.partner"].browse(partner_id)
            if partner.misa_invoice_buyer_id:
                vals["invoice_buyer_id"] = partner.misa_invoice_buyer_id.id
        return super().create(vals)

    def write(self, vals):
        for record in self:
            partner = self.env["res.partner"].browse(
                vals.get("partner_id", record.partner_id.id)
            )
            if partner.misa_invoice_buyer_id:
                vals["invoice_buyer_id"] = partner.misa_invoice_buyer_id.id
        return super().write(vals)
