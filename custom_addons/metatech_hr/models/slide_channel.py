from odoo import fields, models

class SlideChannel(models.Model):
    _inherit = "slide.channel"

    allowed_department_ids = fields.Many2many('hr.department', string="Department")
    job_ids = fields.Many2many('hr.job', string="Job Position")