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
    financer_id = fields.Many2one('res.users', string="Financer")

    ### OVERRIDE ###

    def action_reset_to_draft(self):
        self.sudo().write({'state': 'draft'})
        return True

    def action_submit_to_finance(self):
        res = super().action_submit_to_finance()
        self.sudo().write({'state': 'before_f_approve'})
        user_id = self.financer_id
        self._create_activity(user_id=user_id)
        return res

    def action_manager_approve(self):
        self.sudo().write({'state': 'f_approve'})
        user_id = self.manager_id
        self._create_activity(user_id=user_id)
        return True
    
    def action_cancel(self):
        self.sudo().write({'state': 'cancel'})
        return True

    @api.onchange('overtime_type_id')
    def _get_hour_amount(self):
        if self.duration_type == 'hours':
            if self.contract_id and self.contract_id.over_hour:
                self.cash_hrs_amount = self.contract_id.over_hour * self.days_no_tmp
        elif self.duration_type == 'days':
            if self.contract_id and self.contract_id.over_day:
                self.cash_day_amount = self.contract_id.over_day * self.days_no_tmp

    def _create_activity(self, user_id):
        for overtime in self:
            overtime.activity_schedule(
                'mhd_ohrms_overtime.mail_activity_data_overtime',
                user_id=user_id.id)
            
