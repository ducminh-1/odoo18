import json
import logging
import pprint
from datetime import timedelta, timezone
from dateutil.parser import isoparse

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MisaProduct(models.Model):
    """MISA Product Integration"""
    _name = "misa.product"
    _description = "MISA Product"
    _rec_name = "inventory_item_name"
    _order = "inventory_item_name"

    # Core fields
    misa_app_id = fields.Many2one("misa.app", string="MISA App", required=True, ondelete="cascade")
    branch_id = fields.Many2one("misa.branch", string="MISA Branch", ondelete="set null")
    
    # MISA product info
    inventory_item_id = fields.Char(string="MISA ID", required=True, index=True)
    inventory_item_code = fields.Char(string="Mã hàng", required=True, index=True)
    inventory_item_name = fields.Char(string="Tên hàng", required=True)
    inventory_item_type = fields.Selection([
        ('0', 'Hàng hóa'), ('1', 'Khác'), ('2', 'Dịch vụ')
    ], string="Loại hàng", default='0')
    
    # Basic info
    description = fields.Text(string="Mô tả")
    unit_name = fields.Char(string="Đơn vị tính")
    minimum_stock = fields.Float(string="Tồn kho tối thiểu", default=0.0)
    inactive = fields.Boolean(string="Ngừng sử dụng", default=False)
    
    # Pricing
    unit_price = fields.Float(string="Giá vốn", default=0.0)
    sale_price1 = fields.Float(string="Giá bán 1", default=0.0)
    sale_price2 = fields.Float(string="Giá bán 2", default=0.0)
    sale_price3 = fields.Float(string="Giá bán 3", default=0.0)
    fixed_sale_price = fields.Float(string="Giá bán cố định", default=0.0)
    fixed_unit_price = fields.Float(string="Giá vốn cố định", default=0.0)
    
    # Tax rates
    import_tax_rate = fields.Float(string="Thuế suất nhập khẩu (%)", default=0.0)
    export_tax_rate = fields.Float(string="Thuế suất xuất khẩu (%)", default=0.0)
    
    # Accounts
    inventory_account = fields.Char(string="TK Hàng tồn kho")
    cogs_account = fields.Char(string="TK Giá vốn")
    sale_account = fields.Char(string="TK Doanh thu")
    
    # Category
    inventory_item_category_code_list = fields.Char(string="Mã nhóm hàng")
    inventory_item_category_name_list = fields.Char(string="Tên nhóm hàng")
    unit_list = fields.Text(string="Danh sách đơn vị")
    
    # Tracking
    created_date = fields.Datetime(string="Ngày tạo")
    created_by = fields.Char(string="Người tạo")
    modified_date = fields.Datetime(string="Ngày sửa")
    modified_by = fields.Char(string="Người sửa")
    last_sync_time = fields.Datetime(string="Lần sync cuối", default=fields.Datetime.now)
    
    # Mapping
    odoo_product_id = fields.Many2one("product.product", string="Odoo Product", ondelete="set null")
    mapping_method = fields.Selection([
        ('not_found', 'Không tìm thấy'),
        ('misa_inventory_item_code', 'MISA Code'),
        ('barcode', 'Barcode'),
        ('default_code', 'Default Code'),
        ('manual', 'Manual')
    ], string="Phương thức mapping", default='not_found')
    mapping_notes = fields.Text(string="Ghi chú mapping")

    
    _sql_constraints = [
        ('unique_misa_product', 'unique(misa_app_id, inventory_item_id)', 'MISA Product ID must be unique per app!'),
        ('unique_misa_code', 'unique(misa_app_id, inventory_item_code)', 'MISA Product Code must be unique per app!'),
    ]

    @api.model
    def sync_products_from_misa(self, misa_app_id, branch_id=None, last_sync_time=None):
        """Sync products from MISA API"""
        misa_app = self.env['misa.app'].browse(misa_app_id)
        if not misa_app.exists():
            raise UserError(_("MISA App not found"))

        # Prepare payload
        payload = {
            "app_id": misa_app.app_id,
            "data_type": 2,
            "skip": 0,
            "take": 1000,
        }
        
        if last_sync_time:
            payload["last_sync_time"] = last_sync_time
        if branch_id:
            branch = self.env['misa.branch'].browse(branch_id)
            if branch.exists():
                payload["branch_id"] = branch.misa_id

        _logger.info("Syncing products from MISA: %s", pprint.pformat(payload))

        try:
            response = misa_app._make_request("/apir/sync/actopen/get_dictionary", payload=payload)
            data = json.loads(response.get("Data", "[]"))

            _logger.info('data from payload: %s', pprint.pformat(data))

            synced_count = mapped_count = 0
            
            for product_data in data:
                misa_product = self._process_product_data(misa_app, product_data, branch_id)
                if misa_product:
                    synced_count += 1
                    if self._map_with_odoo_product(misa_product):
                        mapped_count += 1
            
            message = _("Synced %d products. %d mapped.") % (synced_count, mapped_count)
            _logger.info(message)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': _("Sync Completed"), 'message': message, 'type': 'success'}
            }
            
        except Exception as e:
            _logger.error("Sync error: %s", str(e), exc_info=True)
            raise UserError(_("Error syncing products: %s") % str(e))

    def _process_product_data(self, misa_app, product_data, branch_id=None):
        """Process single product data"""
        inventory_item_id = product_data.get("inventory_item_id")
        if not inventory_item_id:
            return None

        try:
            # Find existing
            existing = self.search([
                ('misa_app_id', '=', misa_app.id),
                ('inventory_item_id', '=', inventory_item_id)
            ], limit=1)

            # Extract unit name
            unit_name = product_data.get("unit_name", "")
            if not unit_name:
                try:
                    unit_list = json.loads(product_data.get("unit_list", "[]"))
                    if unit_list and isinstance(unit_list, list):
                        unit_name = unit_list[0].get("unit_name", "") if isinstance(unit_list[0], dict) else ""
                except:
                    pass

            def parse_misa_datetime(dateString):
                if not dateString:
                    return None
                dt = isoparse(dateString)
                if dt.microsecond >= 500_000:
                    dt += timedelta(seconds=1)
                return dt.astimezone(timezone.utc).replace(microsecond=0, tzinfo=None)

            # Parse dates from MISA format
            created_date = parse_misa_datetime(product_data.get('created_date'))
            modified_date = parse_misa_datetime(product_data.get('modified_date'))

            _logger.info("Parsed dates - Created: %s, Modified: %s", created_date, modified_date)

            # Prepare values
            values = {
                'misa_app_id': misa_app.id,
                'inventory_item_id': inventory_item_id,
                'inventory_item_code': product_data.get("inventory_item_code", ""),
                'inventory_item_name': product_data.get("inventory_item_name", ""),
                'inventory_item_type': str(product_data.get("inventory_item_type", 0)),
                'description': product_data.get("description", ""),
                'unit_name': unit_name,
                'minimum_stock': float(product_data.get("minimum_stock", 0.0) or 0.0),
                'inactive': product_data.get("inactive", False),
                'unit_price': float(product_data.get("unit_price", 0.0) or 0.0),
                'sale_price1': float(product_data.get("sale_price1", 0.0) or 0.0),
                'sale_price2': float(product_data.get("sale_price2", 0.0) or 0.0),
                'sale_price3': float(product_data.get("sale_price3", 0.0) or 0.0),
                'fixed_sale_price': float(product_data.get("fixed_sale_price", 0.0) or 0.0),
                'fixed_unit_price': float(product_data.get("fixed_unit_price", 0.0) or 0.0),
                'import_tax_rate': float(product_data.get("import_tax_rate", 0.0) or 0.0),
                'export_tax_rate': float(product_data.get("export_tax_rate", 0.0) or 0.0),
                'inventory_account': product_data.get("inventory_account", ""),
                'cogs_account': product_data.get("cogs_account", ""),
                'sale_account': product_data.get("sale_account", ""),
                'inventory_item_category_code_list': product_data.get("inventory_item_category_code_list", ""),
                'inventory_item_category_name_list': product_data.get("inventory_item_category_name_list", ""),
                'unit_list': product_data.get("unit_list", "[]"),
                'created_date': created_date,
                'created_by': product_data.get('created_by', ''),
                'modified_date': modified_date,
                'modified_by': product_data.get('modified_by', ''),
            }

            # Handle branch_id from payload or parameter
            product_branch_id = product_data.get('branch_id')
            if product_branch_id:
                # Find branch by MISA ID
                branch = self.env['misa.branch'].search([
                    ('misa_app_id', '=', misa_app.id),
                    ('misa_id', '=', product_branch_id)
                ], limit=1)
                if branch:
                    values['branch_id'] = branch.id
            elif branch_id:
                values['branch_id'] = branch_id

            # Luôn update last_sync_time mỗi lần sync
            values['last_sync_time'] = fields.Datetime.now()
            
            if existing:
                existing.write(values)
                _logger.info("Updated product: %s", existing.inventory_item_code)
                return existing
            else:
                _logger.info("Creating new product: %s", values.get('inventory_item_code'))
                return self.create(values)

        except Exception as e:
            _logger.error("Error processing product %s: %s", product_data.get("inventory_item_name"), str(e))
            return None

    def _map_with_odoo_product(self, misa_product):
        """Map MISA product with Odoo product - Priority: misa_code -> barcode -> default_code"""
        if not misa_product.inventory_item_code:
            misa_product.write({
                'mapping_method': 'not_found',
                'mapping_notes': 'Không có mã hàng MISA để mapping'
            })
            return False

        # Priority 1: misa_inventory_item_code
        odoo_product = self.env['product.product'].search([
            ('misa_inventory_item_code', '=', misa_product.inventory_item_code)
        ], limit=1)
        
        if odoo_product:
            return self._create_mapping(misa_product, odoo_product, 'misa_inventory_item_code')

        # Priority 2: barcode
        odoo_product = self.env['product.product'].search([
            ('barcode', '=', misa_product.inventory_item_code)
        ], limit=1)
        
        if odoo_product:
            return self._create_mapping(misa_product, odoo_product, 'barcode')

        # Priority 3: default_code
        odoo_product = self.env['product.product'].search([
            ('default_code', '=', misa_product.inventory_item_code)
        ], limit=1)
        
        if odoo_product:
            return self._create_mapping(misa_product, odoo_product, 'default_code')

        misa_product.write({
            'mapping_method': 'not_found',
            'mapping_notes': f'Không tìm thấy sản phẩm Odoo với mã: {misa_product.inventory_item_code}'
        })
        return False

    def _create_mapping(self, misa_product, odoo_product, method):
        """Create mapping between MISA and Odoo product"""
        try:
            misa_product.write({
                'odoo_product_id': odoo_product.id,
                'mapping_method': method,
                'mapping_notes': f'Auto-mapped by {method}: {misa_product.inventory_item_code}'
            })
            _logger.info("Mapped %s with %s via %s", misa_product.inventory_item_name, odoo_product.name, method)
            return True
        except Exception as e:
            _logger.error("Mapping failed: %s", str(e))
            return False

    def action_open_odoo_product(self):
        """Open mapped Odoo product"""
        self.ensure_one()
        if not self.odoo_product_id:
            raise UserError(_("Not mapped to any Odoo product"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Odoo Product'),
            'res_model': 'product.product',
            'res_id': self.odoo_product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def get_products_summary(self, misa_app_id, branch_id=None):
        """Get products summary"""
        domain = [('misa_app_id', '=', misa_app_id)]
        if branch_id:
            domain.append(('branch_id', '=', branch_id))
        
        total = self.search_count(domain)
        mapped = self.search_count(domain + [('odoo_product_id', '!=', False)])
        not_found = self.search_count(domain + [('mapping_method', '=', 'not_found')])
        
        return {
            'total_products': total,
            'mapped_products': mapped,
            'unmapped_products': total - mapped,
            'not_found_products': not_found,
            'mapping_percentage': round((mapped / total * 100) if total > 0 else 0, 2)
        }