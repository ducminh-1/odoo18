from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class ApprovalRequest(models.Model):
    _name = 'approval.request'
    _description = 'Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, readonly=True, default=lambda self: _('New'))
    category_id = fields.Many2one('approval.category', string='Category', required=True)
    request_owner_id = fields.Many2one('res.users', string='Request Owner', required=True, default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Canceled')
    ], string='Status', default='draft', tracking=True)
    date = fields.Datetime(string='Request Date', default=fields.Datetime.now)
    date_confirmed = fields.Datetime(string='Date Confirmed', readonly=True)
    date_approved = fields.Datetime(string='Approved Date', readonly=True)
    date_refused = fields.Datetime(string='Refused Date', readonly=True)
    
    # Calendar View required fields
    date_start = fields.Datetime(string='Start Date', store=True)
    date_end = fields.Datetime(string='End Date', store=True)
    
    # Request content
    quantity = fields.Float(string='Quantity')
    amount = fields.Float(string='Amount')
    description = fields.Text(string='Description', required=True)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    
    # Approval process
    approver_ids = fields.One2many('approval.approver', 'request_id', string='Approvers')
    approval_count = fields.Integer(compute='_compute_approval_count', string='Approval Count')
    
    # Company
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    # Computed fields
    is_approved = fields.Boolean(compute='_compute_is_approved', string='Is Approved')
    is_refused = fields.Boolean(compute='_compute_is_refused', string='Is Refused')
    
    
    @api.depends('approver_ids.status')
    def _compute_is_approved(self):
        for request in self:
            if request.approver_ids:
                request.is_approved = all(approver.status == 'approved' for approver in request.approver_ids)
            else:
                request.is_approved = False
    
    @api.depends('approver_ids.status')
    def _compute_is_refused(self):
        for request in self:
            request.is_refused = any(approver.status == 'refused' for approver in request.approver_ids)
    
    @api.depends('approver_ids')
    def _compute_approval_count(self):
        for request in self:
            request.approval_count = len(request.approver_ids)
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'approval.request'), ('res_id', 'in', self.ids)], 
            ['res_id'], ['res_id']
        )
        attachment_dict = {data['res_id']: data['res_id_count'] for data in attachment_data}
        for request in self:
            request.attachment_number = attachment_dict.get(request.id, 0)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('approval.request') or _('New')
        return super().create(vals)
    
    def action_submit(self):
        for request in self:
            if not request.approver_ids:
                raise UserError(_('Please add at least one approver.'))
            request.write({'state': 'submitted'})
            approvers = self.approver_ids
            for approver in approvers:
                approver.action_pending()
            approvers._create_activity()
        self.sudo().write({'date_confirmed': fields.Datetime.now()})
    
    def action_approve(self):
        self.write({'state': 'approved', 'date_approved': fields.Datetime.now()})
        for approval in self:
            if approval.request_owner_id.partner_id:
                body = _("The request created on %(create_date)s by %(request_owner)s has been accepted.",
                         create_date=approval.create_date.date(),
                         request_owner=approval.request_owner_id.name)
                subject = _("The request %(request_name)s for %(request_owner)s has been accepted",
                            request_name=approval.name,
                            request_owner=approval.request_owner_id.name)
                approval.message_notify(
                    body=body,
                    subject=subject,
                    partner_ids=approval.request_owner_id.partner_id.ids,
                )
        for approver in self.approver_ids:
            approver.action_approve()
        self.activity_ids.unlink()
    
    def action_refuse(self):
        self.write({'state': 'refused', 'date_refused': fields.Datetime.now()})
        self.activity_ids.unlink()
    
    def action_cancel(self):
        self.write({'state': 'cancel'})
        self.activity_ids.unlink()
    
    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
    
class ApprovalApprover(models.Model):
    _name = 'approval.approver'
    _description = 'Approval Approver'
    
    request_id = fields.Many2one('approval.request', string='Approval Request', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Approver', required=True)
    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], string="Status", default="new", readonly=True)
    required = fields.Boolean(default=False, readonly=True)
    
    def action_pending(self):
        self.write({'status': 'pending'})
    
    def action_approve(self):
        self.write({'status': 'approved'})
    
    def action_refuse(self):
        self.write({'status': 'refused'})

    def _create_activity(self):
        for approver in self:
            approver.request_id.activity_schedule(
                'approvals_community.mail_activity_data_approval',
                user_id=approver.user_id.id)