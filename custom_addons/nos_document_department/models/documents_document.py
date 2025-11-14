import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _inherit = "documents.document"

    department_id = fields.Many2one(
        "hr.department", compute="_compute_department_id", store=True, readonly=False
    )

    @api.depends("owner_id")
    def _compute_department_id(self):
        for record in self:
            if record.owner_id and record.owner_id.employee_ids:
                record.department_id = record.owner_id.employee_ids[0].department_id
            else:
                record.department_id = False
