from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class ApprovalRequest(models.Model):
    _name = 'approval.request'
    _description = 'Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    _check_company_auto = True

    name = fields.Char(string='Reference', required=True, readonly=True, default=lambda self: _('New'))
    category_id = fields.Many2one('approval.category', string='Category', required=True)
    request_owner_id = fields.Many2one('res.users', string='Request Owner', required=True, default=lambda self: self.env.user)
    state = fields.Selection([
        ('new', 'To Submit'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Canceled'),
    ], default="new", compute="_compute_state",
        store=True, index=True, tracking=True,
        group_expand=True)
    company_id = fields.Many2one(
        string='Company', related='category_id.company_id',
        store=True, readonly=True, index=True)
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
    approver_ids = fields.One2many('approval.approver', 'request_id', string="Approvers", check_company=True,
            compute='_compute_approver_ids', store=True, readonly=False)
    # Company
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Canceled')], compute="_compute_user_status")
    approver_sequence = fields.Boolean(related="category_id.approver_sequence")
    approval_minimum = fields.Integer(related="category_id.approval_minimum")

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'approval.request'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('approvals_community.mail_activity_data_approval').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities
    
    def _cancel_activities(self):
        approval_activity = self.env.ref('approvals_community.mail_activity_data_approval')
        activities = self.activity_ids.filtered(lambda a: a.activity_type_id == approval_activity)
        activities.unlink()

    @api.depends('approver_ids.status', 'approver_ids.required')
    def _compute_state(self):
        for request in self:
            status_lst = request.mapped('approver_ids.status')
            required_approved = all(a.status == 'approved' for a in request.approver_ids.filtered('required'))
            minimal_approver = request.approval_minimum if len(status_lst) >= request.approval_minimum else len(status_lst)
            if status_lst:
                if status_lst.count('cancel'):
                    status = 'cancel'
                elif status_lst.count('refused'):
                    status = 'refused'
                elif status_lst.count('new'):
                    status = 'new'
                elif status_lst.count('approved') >= minimal_approver and required_approved:
                    status = 'approved'
                else:
                    status = 'submitted'
            else:
                status = 'new'
            request.state = status

        self.filtered_domain([('state', 'in', ['approved', 'refused', 'cancel'])])._cancel_activities()

    @api.depends_context('uid')
    @api.depends('approver_ids.status')
    def _compute_user_status(self):
        for approval in self:
            approval.user_status = approval.approver_ids.filtered(lambda approver: approver.user_id == self.env.user).status
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'approval.request'), ('res_id', 'in', self.ids)], 
            ['res_id'], ['res_id']
        )
        attachment_dict = {data['res_id']: data['res_id_count'] for data in attachment_data}
        for request in self:
            request.attachment_number = attachment_dict.get(request.id, 0)

    @api.depends('category_id', 'request_owner_id')
    def _compute_approver_ids(self):
        for request in self:
            users_to_category_approver = {}
            for approver in request.category_id.approver_ids:
                users_to_category_approver[approver.user_id.id] = approver
                
            approver_id_vals = [Command.clear()]

            for user_id in users_to_category_approver:
                approver_id_vals.append(Command.create({
                    'user_id': user_id,
                    'status': 'new',
                    'required': users_to_category_approver[user_id].required,
                }))
            request.update({'approver_ids': approver_id_vals})
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('approval.request') or _('New')
        return super().create(vals)
    
    def action_submit(self):
        self.ensure_one()
        for request in self:
            if not request.approver_ids:
                raise UserError(_('Please add at least one approver.'))
            request.write({'state': 'submitted'})
        approvers = self.approver_ids
        if self.approver_sequence:
            approvers = approvers.filtered(lambda a: a.status in ['new', 'submitted', 'waiting'])

            approvers[1:].sudo().write({'status': 'waiting'})
            approvers = approvers[0] if approvers and approvers[0].status != 'pending' else self.env['approval.approver']
        else:
            approvers = approvers.filtered(lambda a: a.status == 'new')

        approvers._create_activity()
        approvers.sudo().write({'status': 'pending'})
        self.sudo().write({'date_confirmed': fields.Datetime.now()})
    
    def _ensure_can_approve(self):
        if any(approval.approver_sequence and approval.user_status == 'waiting' for approval in self):
            raise ValidationError(_('You cannot approve before the previous approver.'))
    
    def action_approve(self, approver=None):
        self._ensure_can_approve()
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'approved'})
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
        self.sudo()._update_next_approvers('pending', approver, only_next_approver=True)
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    def _update_next_approvers(self, new_status, approver, only_next_approver, cancel_activities=False):
        approvers_updated = self.env['approval.approver']
        for approval in self.filtered('approver_sequence'):
            current_approver = approval.approver_ids & approver
            approvers_to_update = approval.approver_ids.filtered(lambda a: a.status not in ['approved', 'refused'] and (a.sequence > current_approver.sequence or (a.sequence == current_approver.sequence and a.id > current_approver.id)))

            if only_next_approver and approvers_to_update:
                approvers_to_update = approvers_to_update[0]
            approvers_updated |= approvers_to_update

        approvers_updated.sudo().status = new_status
        if new_status == 'pending':
            approvers_updated._create_activity()
        if cancel_activities:
            approvers_updated.request_id._cancel_activities()
    
    def action_refuse(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'refused'})

        # Send approval refused message
        for approval in self:
            if approval.request_owner_id.partner_id:
                body = _("The request created on %(create_date)s by %(request_owner)s has been refused.",
                         create_date=approval.create_date.date(),
                         request_owner=approval.request_owner_id.name)
                subject = _("The request %(request_name)s for %(request_owner)s has been refused",
                            request_name=approval.name,
                            request_owner=approval.request_owner_id.name)
                approval.message_notify(
                    body=body,
                    subject=subject,
                    partner_ids=approval.request_owner_id.partner_id.ids,
                )

        self.sudo()._update_next_approvers('refused', approver, only_next_approver=False, cancel_activities=True)
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    def action_reset_to_draft(self):
        self.mapped('approver_ids').write({'status': 'new'})

    def action_cancel(self):
        self.sudo()._get_user_approval_activities(user=self.env.user).unlink()
        self.mapped('approver_ids').write({'status': 'cancel'})

    def write(self, vals):
        if 'request_owner_id' in vals:
            for approval in self:
                approval.message_unsubscribe(partner_ids=approval.request_owner_id.partner_id.ids)

        res = super().write(vals)

        if 'request_owner_id' in vals:
            for approval in self:
                approval.message_subscribe(partner_ids=approval.request_owner_id.partner_id.ids)

        if 'approver_ids' in vals:
            to_resequence = self.filtered_domain([('approver_sequence', '=', True), ('state', '=', 'pending')])
            for approval in to_resequence:
                if not approval.approver_ids.filtered(lambda a: a.status == 'pending'):
                    approver = approval.approver_ids.filtered(lambda a: a.status == 'waiting')
                    if approver:
                        approver[0].status = 'pending'
                        approver[0]._create_activity()

        return res
    
    @api.constrains('approver_ids')
    def _check_approver_ids(self):
        for request in self:
            # make sure the approver_ids are unique per request
            if len(request.approver_ids) != len(request.approver_ids.user_id):
                raise UserError(_("You cannot assign the same approver multiple times on the same request."))
    
class ApprovalApprover(models.Model):
    _name = 'approval.approver'
    _description = 'Approval Approver'

    _check_company_auto = True
    
    sequence = fields.Integer('Sequence', default=10)
    request_id = fields.Many2one('approval.request', string='Approval Request')
    company_id = fields.Many2one(
        string='Company', related='request_id.company_id',
        store=True, readonly=True, index=True)
    approver_category_id = fields.Many2one('approval.category', string='Approval Category', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Approver', required=True)
    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], string="Status", default="new", readonly=True)
    required = fields.Boolean(default=False)
    
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