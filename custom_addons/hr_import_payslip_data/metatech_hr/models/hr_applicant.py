import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    interview_type = fields.Selection([
        ('offline', 'Offline'),
        ('online', 'Online'),
    ], string='Interview Type', required=True, default='offline')
    interview_time = fields.Char('Interview Time')
    interview_address = fields.Char('Interview Address')
