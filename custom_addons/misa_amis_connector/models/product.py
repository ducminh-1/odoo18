from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import re
import uuid

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    misa_inventory_item_code = fields.Char(string="Mã hàng Misa")
    misa_inventory_item_name = fields.Char(string="Tên hàng Misa")
    misa_inventory_unit_name = fields.Char(string="ĐVT Misa")
    
    # MISA integration relationship - 1 product can have many MISA records
    misa_product_ids = fields.One2many('misa.product', 'odoo_product_id', string="MISA Products")
    misa_app_ids = fields.Many2many(
        "misa.app",
        "product_misa_app_rel", "product_id", "misa_app_id",
        string="MISA Apps",
        compute="_compute_misa_app_ids",
        store=True,
        readonly=True,
    )
    misa_branch_ids = fields.Many2many(
        "misa.branch",
        "product_misa_branch_rel", "product_id", "branch_id",
        string="MISA Branches",
        compute="_compute_misa_branch_ids",
        store=True,
        readonly=True,
    )
    
    misa_pushed = fields.Boolean(string="Đã đẩy lên MISA", default=False)
    misa_last_push_date = fields.Datetime(string="Lần đẩy cuối")

    def action_push_inventory_item_to_misa(self):
        """Open wizard for MISA configuration selection"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Push to MISA',
            'res_model': 'misa.push.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_ids': [(6, 0, self.ids)],
                'active_model': 'product.product',
                'active_ids': self.ids,
            }
        }

    @api.depends('misa_product_ids.misa_app_id')
    def _compute_misa_app_ids(self):
        """Get all MISA apps from linked misa.product records"""
        for product in self:
            misa_apps = product.misa_product_ids.mapped('misa_app_id')
            product.misa_app_ids = misa_apps

    @api.depends('misa_product_ids.branch_id')
    def _compute_misa_branch_ids(self):
        """Get all MISA branches from linked misa.product records"""
        for product in self:
            misa_branches = product.misa_product_ids.mapped('branch_id')
            product.misa_branch_ids = misa_branches

    def is_pushed_to_misa_config(self, misa_app, misa_branch):
        """Check if product is already pushed to specific MISA app/branch combination"""
        existing_misa_product = self.misa_product_ids.filtered(
            lambda mp: mp.misa_app_id == misa_app and mp.branch_id == misa_branch
        )
        return bool(existing_misa_product)
    
    def get_misa_product_for_config(self, misa_app, misa_branch):
        """Get misa.product record for specific app/branch combination"""
        return self.misa_product_ids.filtered(
            lambda mp: mp.misa_app_id == misa_app and mp.branch_id == misa_branch
        )

    def _push_to_misa_with_config(self, misa_app, misa_branch):
        """Push product to MISA with specified configuration"""
        _logger.info("=== Starting MISA push for product: %s (ID: %s) ===", self.name, self.id)
        _logger.info("Using MISA app: %s, Branch: %s", misa_app.org_company_code, misa_branch.name)
        
        # Validate required parameters
        if not misa_branch:
            raise UserError(_("Branch is required for pushing products to MISA"))
        
        try:
            inventory_data = self._prepare_inventory_item_data(
                misa_app.app_id, 
                misa_app.org_company_code,
                misa_branch.misa_id
            )
            _logger.info("Inventory data prepared: %s", inventory_data)
            
            response = misa_app._make_request("/apir/sync/actopen/save_dictionary", payload=inventory_data)
            _logger.info("MISA API response: %s", response)
            
            if response.get('Success'):
                self.write({
                    'misa_pushed': True, 
                    'misa_last_push_date': fields.Datetime.now()
                })
                return True
            else:
                error_msg = response.get('Message', 'Không xác định')
                _logger.error("MISA push failed: %s", error_msg)
                raise UserError(_("Lỗi: %s") % error_msg)
        except Exception as e:
            _logger.error("Exception during MISA push: %s", str(e), exc_info=True)
            raise UserError(_("Lỗi: %s") % str(e))

    def _prepare_inventory_item_data(self, app_id, org_company_code, branch_id):
        """Prepare inventory_item data for MISA API"""
        
        # Map Odoo product type to MISA inventory item type
        type_mapping = {
            'product': '0',  # Storable Product → Vật tư hàng hóa
            'consu': '0',    # Consumable → Vật tư hàng hóa  
            'service': '2',  # Service → Dịch vụ
        }
        
        # Required fields
        item_data = {
            "dictionary_type": 3,
            "inventory_item_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"odoo.product.{self.id}")),
            "inventory_item_name": self.misa_inventory_item_name or self.name,
            "inventory_item_code": self.misa_inventory_item_code or self.default_code or f"SP{self.id}",
            "inventory_item_type": type_mapping.get(self.type, '0'),
            "State": 2 if self.misa_pushed else 1,
            "is_unit_price_after_tax": False,
        }
        
        item_data["branch_id"] = branch_id
        item_data["inactive"] = not self.active
        
        # Handle description - convert HTML to plain text
        if self.description:
            description_text = re.sub(r'<[^>]+>', '', str(self.description)).strip()
            item_data["description"] = description_text or self.name
        else:
            item_data["description"] = self.name
            
        if self.list_price:
            item_data["sale_price1"] = self.list_price
            
        if self.categ_id:
            categ_path = []
            current_categ = self.categ_id
            while current_categ:
                categ_path.insert(0, current_categ.name)
                current_categ = current_categ.parent_id
            item_data["inventory_item_category_name_list"] = " / ".join(categ_path)
            
        if self.uom_id:
            item_data["unit_name"] = self.misa_inventory_unit_name or self.uom_id.name
            
        # Fixed unit price from first supplier
        supplier_price = self._get_supplier_fixed_price()
        if supplier_price:
            item_data["fixed_unit_price"] = supplier_price

        # Tax rates
        if self.supplier_taxes_id:
            import_tax = self.supplier_taxes_id.filtered(lambda t: t.amount_type == 'percent')
            if import_tax:
                item_data["import_tax_rate"] = import_tax[0].amount
        
        if self.taxes_id:
            export_tax = self.taxes_id.filtered(lambda t: t.amount_type == 'percent')
            if export_tax:
                item_data["export_tax_rate"] = export_tax[0].amount
        
        # Sale account
        sale_account = self._get_product_account('income')
        if sale_account:
            item_data["sale_account"] = sale_account.code
            
        # COGS account
        cogs_account = self._get_product_account('expense')
        if cogs_account:
            item_data["cogs_account"] = cogs_account.code
        
        # Audit fields
        item_data.update({
            "created_date": fields.Datetime.to_string(self.create_date),
            "created_by": self.create_uid.name if self.create_uid else "",
            "modified_date": fields.Datetime.to_string(self.write_date),
            "modified_by": self.write_uid.name if self.write_uid else "",
        })
        
        final_data = {"app_id": app_id, "org_company_code": org_company_code, "dictionary": [item_data]}
        _logger.info("Final inventory_item data: %s", final_data)
        
        return final_data

    def _get_product_account(self, account_type):
        """Get product account with fallback to category"""
        try:
            if account_type == 'income':
                # Sale account: product property → category property
                account = self.property_account_income_id
                if not account and self.categ_id:
                    account = self.categ_id.property_account_income_categ_id
                return account
                
            elif account_type == 'expense':
                # COGS account: product property → category property
                account = self.property_account_expense_id
                if not account and self.categ_id:
                    account = self.categ_id.property_account_expense_categ_id
                return account
                    
        except Exception as e:
            _logger.warning("Error getting %s account for product %s: %s", account_type, self.name, str(e))
        return None

    def _get_supplier_fixed_price(self):
        """Get fixed unit price from first supplier"""
        try:
            supplier_info = self.seller_ids.filtered(lambda s: s.partner_id and s.price > 0).sorted('sequence')
            if supplier_info:
                return supplier_info[0].price
        except Exception as e:
            _logger.warning("Error getting supplier fixed price for product %s: %s", self.name, str(e))
        return None

class ProductTemplate(models.Model):
    _inherit = "product.template"

    misa_inventory_item_code = fields.Char(
        compute="_compute_misa_inventory_item_code",
        inverse="_inverse_misa_inventory_item_code",
        string="Mã hàng Misa",
        store=True,
        readonly=False,
    )
    misa_inventory_item_name = fields.Char(
        compute="_compute_misa_inventory_item_name",
        inverse="_inverse_misa_inventory_item_name",
        string="Tên hàng Misa",
        store=True,
        readonly=False,
    )
    misa_inventory_unit_name = fields.Char(
        compute="_compute_misa_inventory_unit_name",
        inverse="_inverse_misa_inventory_unit_name",
        string="ĐVT Misa",
        store=True,
        readonly=False,
    )
    
    # Tracking fields with compute/inverse for template-variant sync
    misa_pushed = fields.Boolean(
        compute="_compute_misa_pushed", inverse="_inverse_misa_pushed",
        string="Đã đẩy lên MISA", store=True, readonly=False,
    )
    misa_last_push_date = fields.Datetime(
        compute="_compute_misa_last_push_date", inverse="_inverse_misa_last_push_date",
        string="Lần đẩy cuối", store=True, readonly=False,
    )

    @api.depends("product_variant_ids.misa_inventory_item_code")
    def _compute_misa_inventory_item_code(self):
        self._compute_template_field_from_variant_field("misa_inventory_item_code")

    def _inverse_misa_inventory_item_code(self):
        self._set_product_variant_field("misa_inventory_item_code")

    @api.depends("product_variant_ids.misa_inventory_item_name")
    def _compute_misa_inventory_item_name(self):
        self._compute_template_field_from_variant_field("misa_inventory_item_name")

    def _inverse_misa_inventory_item_name(self):
        self._set_product_variant_field("misa_inventory_item_name")

    @api.depends("product_variant_ids.misa_inventory_unit_name")
    def _compute_misa_inventory_unit_name(self):
        self._compute_template_field_from_variant_field("misa_inventory_unit_name")

    def _inverse_misa_inventory_unit_name(self):
        self._set_product_variant_field("misa_inventory_unit_name")

    # Compute and inverse methods for tracking fields
    @api.depends("product_variant_ids.misa_pushed")
    def _compute_misa_pushed(self):
        self._compute_template_field_from_variant_field("misa_pushed")

    def _inverse_misa_pushed(self):
        self._set_product_variant_field("misa_pushed")

    @api.depends("product_variant_ids.misa_last_push_date")
    def _compute_misa_last_push_date(self):
        self._compute_template_field_from_variant_field("misa_last_push_date")

    def _inverse_misa_last_push_date(self):
        self._set_product_variant_field("misa_last_push_date")
