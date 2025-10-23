from odoo import models, fields, api

class ApprovalCategory(models.Model):
    _name = 'approval.category'
    _description = 'Approval Category'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
    approval_type = fields.Selection([
        ('generic', 'Generic'),
        ('purchase', 'Purchase'),
        ('expense', 'Expense'),
        ('leave', 'Leave'),
        ('custom', 'Custom')
    ], string='Type', default='generic', required=True) 
    requires_attachment = fields.Boolean(string='Requires Attachment')
    requires_quantity = fields.Boolean(string='Requires Quantity')
    requires_amount = fields.Boolean(string='Requires Amount')
    approval_minimum = fields.Integer(string='Minimum Approvers', default=1)
    approval_maximum = fields.Integer(string='Maximum Approvers', default=5)
    auto_approval = fields.Boolean(string='Auto Approval')
    double_validation = fields.Boolean(string='Double Validation')
    user_id = fields.Many2one('res.users', string='Approval Responsible')
    approver_ids = fields.Many2many(
        'res.users', 
        'approval_category_approver_rel',
        'category_id', 
        'user_id', 
        string='Approvers'
    )
    group_ids = fields.Many2many(
        'res.groups',
        'approval_category_group_rel',
        'category_id',
        'group_id',
        string='Authorized Groups'
    )
    request_fields = fields.Text(string='Request Fields Configuration')
    pending_count = fields.Integer(string="To Review", compute="_compute_pending_count")
    image = fields.Binary(string='Image')

    def _compute_pending_count(self):
        domain = [('state', '=', 'submitted'), ('approver_ids.user_id', '=', self.env.user.id)]
        requests_data = self.env['approval.request']._read_group(domain, ['category_id'], ['__count'])
        requests_mapped_data = {category.id: count for category, count in requests_data}
        for category in self:
            category.pending_count = requests_mapped_data.get(category.id, 0)

    def action_new_request(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Request',
            'res_model': 'approval.request',
            'view_mode': 'form',
            'context': {'default_category_id': self.id},
            'target': 'current',
        }
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Category name must be unique!'),
    ]

    