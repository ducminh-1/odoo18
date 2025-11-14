import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrOvertime(models.Model):
    _name = 'hr.overtime'
    _inherit = ['hr.overtime', 'mail.activity.mixin']

    state = fields.Selection(selection_add=[
        ('before_f_approve', 'Waiting for Manager Approval'), ("f_approve",),
        ('cancel', 'Cancel')],
        ondelete={'before_f_approve': 'set default'},
        tracking=True)
    type_manager_id = fields.Many2one('res.users', string="Manager", related='overtime_type_id.manager_id', store=True)
    type = fields.Selection([('cash', 'Cash'), ('leave', 'Leave')], default="cash", required=True, string="Type", help="Type of the overtime request")

    ### OVERRIDE ###

    def action_reset_to_draft(self):
        self.sudo().write({'state': 'draft'})
        self.activity_update()

    def action_submit_to_finance(self):
        res = super().action_submit_to_finance()
        self.sudo().write({'state': 'before_f_approve'})
        self.activity_update()
        return res

    def action_manager_approve(self):
        self.sudo().write({'state': 'f_approve'})
        self.activity_update()
    
    def action_cancel(self):
        self.sudo().write({'state': 'cancel'})
        self.activity_update()

    @api.onchange('overtime_type_id')
    def _get_hour_amount(self):
        if self.duration_type == 'hours':
            if self.contract_id and self.contract_id.over_hour:
                self.cash_hrs_amount = self.contract_id.over_hour * self.days_no_tmp
        elif self.duration_type == 'days':
            if self.contract_id and self.contract_id.over_day:
                self.cash_day_amount = self.contract_id.over_day * self.days_no_tmp

    def activity_update(self):
        hr_overtime_feedback = self.env['hr.overtime']
        hr_overtime_activity_unlink = self.env['hr.overtime']
        for overtime in self:
            if overtime.state in ['before_f_approve', 'f_approve']:
                overtime.activity_schedule(
                    'mhd_ohrms_overtime.mail_activity_data_overtime',
                    user_id=overtime.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif overtime.state == 'approved':
                hr_overtime_feedback |= overtime
            elif overtime.state in ['draft', 'cancel']:
                hr_overtime_activity_unlink |= overtime
        if hr_overtime_feedback:
            hr_overtime_feedback.activity_feedback(['mhd_ohrms_overtime.mail_activity_data_overtime'])
        if hr_overtime_activity_unlink:
            hr_overtime_activity_unlink.activity_unlink(['mhd_ohrms_overtime.mail_activity_data_overtime'])
    
    def _get_responsible_for_approval(self):
        self.ensure_one()
        if self.state == 'before_f_approve':
            return self.manager_id
        elif self.state == 'f_approve':
            return self.type_manager_id
        return None
