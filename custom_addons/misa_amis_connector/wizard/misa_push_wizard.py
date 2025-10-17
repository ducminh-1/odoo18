import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MisaPushWizard(models.TransientModel):
    _name = 'misa.push.wizard'
    _description = 'MISA Push Configuration Wizard'

    # Selection fields
    misa_app_id = fields.Many2one(
        'misa.app', 
        string='MISA Application',
        required=True,
        help='Select the MISA application to push data to'
    )
    misa_branch_id = fields.Many2one(
        'misa.branch',
        string='MISA Branch',
        required=True,
        help='Select the branch to push data to'
    )
    
    # Product information
    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        help='Products to be pushed to MISA'
    )
    product_count = fields.Integer(
        string='Product Count',
        compute='_compute_product_count'
    )
    
    # Preview/summary fields
    summary_info = fields.Html(
        string='Push Summary',
        compute='_compute_summary_info'
    )

    @api.depends('product_ids')
    def _compute_product_count(self):
        for record in self:
            record.product_count = len(record.product_ids)

    @api.depends('misa_app_id', 'misa_branch_id', 'product_ids')
    def _compute_summary_info(self):
        for record in self:
            summary = '<div class="o_form_label">'
            if record.misa_app_id:
                summary += f'<p><strong>MISA App:</strong> {record.misa_app_id.org_company_code}</p>'
            if record.misa_branch_id:
                summary += f'<p><strong>Branch:</strong> {record.misa_branch_id.name}</p>'
            else:
                summary += '<p><strong>Branch:</strong> <span class="text-danger">Branch required for push</span></p>'
            if record.product_ids:
                summary += f'<p><strong>Products:</strong> {len(record.product_ids)} items</p>'
                summary += '<ul>'
                for product in record.product_ids[:5]:  # Show up to 5 products
                    summary += f'<li>{product.name}</li>'
                if len(record.product_ids) > 5:
                    summary += f'<li>... and {len(record.product_ids) - 5} more</li>'
                summary += '</ul>'
            summary += '</div>'
            record.summary_info = summary

    @api.onchange('misa_app_id')
    def _onchange_misa_app_id(self):
        """Update branch domain when MISA app changes"""
        if self.misa_app_id:
            self.misa_branch_id = False
            return {
                'domain': {
                    'misa_branch_id': [('misa_app_id', '=', self.misa_app_id.id)]
                }
            }
        else:
            return {'domain': {'misa_branch_id': []}}

    @api.model
    def default_get(self, fields_list):
        """Set default values when wizard is opened"""
        defaults = super().default_get(fields_list)
        
        # Get context
        context = self.env.context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids', [])
        
        # Check if any MISA apps exist
        misa_apps = self.env['misa.app'].search([])
        if not misa_apps:
            raise UserError(_('No MISA applications configured. Please configure at least one MISA application first.'))
        
        # Auto-select MISA app if only one available
        if len(misa_apps) == 1:
            defaults['misa_app_id'] = misa_apps.id
            branches = misa_apps.branch_ids
            if len(branches) == 1:
                defaults['misa_branch_id'] = branches.id
        
        # Set products based on context
        if active_model == 'product.product' and active_ids:
            defaults['product_ids'] = [(6, 0, active_ids)]
        elif active_model == 'product.template' and active_ids:
            templates = self.env['product.template'].browse(active_ids)
            variant_ids = templates.mapped('product_variant_ids.id')
            defaults['product_ids'] = [(6, 0, variant_ids)]
        
        return defaults

    def action_push_to_misa(self):
        """Execute the push to MISA with selected configuration"""
        self.ensure_one()
        
        # Validation
        if not self.misa_app_id:
            raise UserError(_('Please select a MISA application.'))
        
        if not self.misa_branch_id:
            raise UserError(_('Please select a MISA branch.'))
        
        if not self.product_ids:
            raise UserError(_('No products selected for push.'))
        
        # Validate MISA app has valid connection
        try:
            self.misa_app_id._fetch_access_token()
        except Exception as e:
            raise UserError(_('Cannot connect to MISA app "%s". Please check the configuration.\nError: %s') % (self.misa_app_id.org_company_code, str(e)))
        
        _logger.info("=== Starting MISA bulk push ===")
        _logger.info("MISA App: %s", self.misa_app_id.org_company_code)
        _logger.info("Branch: %s", self.misa_branch_id.name if self.misa_branch_id else "No branch selected")
        _logger.info("Products: %s", len(self.product_ids))
        
        success_count = 0
        error_count = 0
        errors = []
        
        for product in self.product_ids:
            try:
                # Use the selected configuration
                product._push_to_misa_with_config(
                    self.misa_app_id, 
                    self.misa_branch_id
                )
                success_count += 1
                _logger.info("Successfully pushed product: %s", product.name)
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                errors.append(f"{product.name}: {error_msg}")
                _logger.error("Failed to push product %s: %s", product.name, error_msg)
        
        # Prepare result message
        if success_count > 0:
            branch_info = f" - {self.misa_branch_id.name}"
            message = f"Đã đẩy thành công {success_count} sản phẩm lên MISA ({self.misa_app_id.org_company_code}{branch_info})"
            if error_count > 0:
                message += f"\n{error_count} sản phẩm lỗi:"
                for i, error in enumerate(errors[:3]):  # Show first 3 errors
                    message += f"\n- {error}"
                if len(errors) > 3:
                    message += f"\n... và {len(errors) - 3} lỗi khác"
                notification_type = 'warning'
            else:
                notification_type = 'success'
        else:
            message = "Không có sản phẩm nào được đẩy thành công"
            if errors:
                message += "\nLỗi:"
                for i, error in enumerate(errors[:3]):
                    message += f"\n- {error}"
                if len(errors) > 3:
                    message += f"\n... và {len(errors) - 3} lỗi khác"
            notification_type = 'danger'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Kết quả Push MISA',
                'message': message,
                'type': notification_type,
                'sticky': error_count > 0  # Keep error notifications visible
            }
        }

    def action_cancel(self):
        """Cancel the wizard"""
        return {'type': 'ir.actions.act_window_close'}