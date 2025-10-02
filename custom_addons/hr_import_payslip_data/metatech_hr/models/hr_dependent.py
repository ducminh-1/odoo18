import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrDependent(models.Model):
    _name = "hr.dependent"
    _description = "HR Dependent"

    name = fields.Char(required=True)
    relationship = fields.Char(required=True)
    birthday = fields.Date(required=True)
    identification_id = fields.Char(string="Identification No", required=True)
    address = fields.Char()
    ssnid = fields.Char(string="SSN No")
    tax_code = fields.Char()
    employee_id = fields.Many2one("hr.employee", ondelete="cascade")
