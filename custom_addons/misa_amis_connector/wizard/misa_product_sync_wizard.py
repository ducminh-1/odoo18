import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MisaProductSyncWizard(models.TransientModel):
    _name = "misa.product.sync.wizard"
    _description = "MISA Product Sync Wizard"

    misa_app_id = fields.Many2one("misa.app", string="MISA App", required=True)
    branch_id = fields.Many2one("misa.branch", string="MISA Branch", 
                               domain="[('misa_app_id', '=', misa_app_id)]",
                               help="Leave empty to sync all products, or select specific branch")
    
    use_last_sync_time = fields.Boolean(string="Incremental Sync", default=True,
                                       help="Only sync products modified since last sync time")
    last_sync_time = fields.Datetime(string="Last Sync Time")

    @api.onchange('misa_app_id')
    def _onchange_misa_app_id(self):
        """Update domain for branch_id and set last sync time"""
        if self.misa_app_id:
            if self.misa_app_id.last_product_sync_time:
                self.last_sync_time = self.misa_app_id.last_product_sync_time
            else:
                self.use_last_sync_time = False

    def action_sync_products(self):
        """Execute the product sync"""
        self.ensure_one()
        
        if not self.misa_app_id:
            raise UserError(_("Please select a MISA App"))

        # Prepare sync parameters
        last_sync_time = self.last_sync_time if self.use_last_sync_time else None
        branch_id = self.branch_id.id if self.branch_id else None

        _logger.info("Starting product sync, app: %s, branch: %s, last_sync: %s", 
                    self.misa_app_id.org_company_code, 
                    self.branch_id.name if self.branch_id else "All", last_sync_time)

        try:
            # Step 1: Sync products from MISA
            result = self.env['misa.product'].sync_products_from_misa(
                misa_app_id=self.misa_app_id.id,
                branch_id=branch_id,
                last_sync_time=last_sync_time.isoformat() if last_sync_time else None
            )

            # Step 2: Auto-mapping
            self._perform_auto_mapping()

            # Step 3: Update app's last sync time
            self.misa_app_id.write({
                'last_product_sync_time': fields.Datetime.now()
            })

            summary = self._get_sync_summary()
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Sync Results',
                'res_model': 'misa.product.sync.result',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_misa_app_id': self.misa_app_id.id,
                    'default_branch_id': branch_id,
                    'default_summary': summary,
                }
            }

        except Exception as e:
            _logger.error("Error during product sync: %s", str(e), exc_info=True)
            raise UserError(_("Error during sync: %s") % str(e))

    def _perform_auto_mapping(self):
        """Perform automatic mapping for unmapped products"""
        domain = [('misa_app_id', '=', self.misa_app_id.id), ('odoo_product_id', '=', False)]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))

        unmapped_products = self.env['misa.product'].search(domain)
        mapped_count = 0
        
        for misa_product in unmapped_products:
            if misa_product._map_with_odoo_product(misa_product):
                mapped_count += 1

        _logger.info("Auto-mapped %d products out of %d unmapped products", mapped_count, len(unmapped_products))

    def _get_sync_summary(self):
        """Get sync summary statistics"""
        domain = [('misa_app_id', '=', self.misa_app_id.id)]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))

        return self.env['misa.product'].get_products_summary(self.misa_app_id.id, self.branch_id.id if self.branch_id else None)


class MisaProductSyncResult(models.TransientModel):
    _name = "misa.product.sync.result"
    _description = "MISA Product Sync Result"

    misa_app_id = fields.Many2one("misa.app", string="MISA App", readonly=True)
    branch_id = fields.Many2one("misa.branch", string="MISA Branch", readonly=True)
    
    total_products = fields.Integer(string="Total MISA Products", readonly=True)
    mapped_products = fields.Integer(string="Mapped with Odoo", readonly=True)
    unmapped_products = fields.Integer(string="Unmapped Products", readonly=True)
    mapping_percentage = fields.Float(string="Mapping Percentage (%)", readonly=True)
    
    summary = fields.Text(string="Summary", readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Set default values from context"""
        defaults = super().default_get(fields_list)
        
        summary_data = self.env.context.get('default_summary', {})
        defaults.update({
            'total_products': summary_data.get('total_products', 0),
            'mapped_products': summary_data.get('mapped_products', 0),
            'unmapped_products': summary_data.get('unmapped_products', 0),
            'mapping_percentage': summary_data.get('mapping_percentage', 0.0),
        })
        
        # Create summary text
        summary_text = f"""
Sync completed successfully!

Total MISA Products: {defaults['total_products']}
Mapped with Odoo: {defaults['mapped_products']}
Unmapped Products: {defaults['unmapped_products']}
Mapping Percentage: {defaults['mapping_percentage']}%

{defaults['unmapped_products']} products could not be automatically mapped.
You can review them in the MISA Products list and map them manually.
        """.strip()
        
        defaults['summary'] = summary_text
        
        return defaults

    def action_view_misa_products(self):
        """View MISA products"""
        domain = [('misa_app_id', '=', self.misa_app_id.id)]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))

        return {
            'type': 'ir.actions.act_window',
            'name': 'MISA Products',
            'res_model': 'misa.product',
            'view_mode': 'list,form',
            'domain': domain,
            'target': 'current',
        }

    def action_view_unmapped_products(self):
        """View unmapped MISA products"""
        domain = [('misa_app_id', '=', self.misa_app_id.id), ('odoo_product_id', '=', False)]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Unmapped MISA Products',
            'res_model': 'misa.product',
            'view_mode': 'list,form',
            'domain': domain,
            'target': 'current',
        }