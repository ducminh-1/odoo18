import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.employee'

    date_of_issue_id = fields.Date(string='Date of Issue CCCD Card', groups='hr.group_hr_user', tracking=True)
    place_of_issue_id = fields.Char(string='Place of Issue CCCD Card', groups='hr.group_hr_user', tracking=True)
    bank_id = fields.Many2one('res.bank', string='Bank')
    bank_accc_number = fields.Char(string='Account Number')