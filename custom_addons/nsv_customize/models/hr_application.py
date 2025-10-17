from odoo import fields, models


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    interview_address = fields.Char("Interview Address")
    interview_time = fields.Char("Interview Time")
    interviewer = fields.Many2one("hr.employee", "Interviewer")
