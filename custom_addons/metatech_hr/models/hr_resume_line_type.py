from odoo import _, fields, models
from odoo.exceptions import UserError

DEFAULT_RESUME_TYPE = [
    "metatech_hr.resume_type_working_process",
    "metatech_hr.resume_type_learning_process",
    "metatech_hr.resume_type_reward",
    "metatech_hr.resume_type_discipline",
    "metatech_hr.resume_type_pros_and_cons",
]


class ResumeLineType(models.Model):
    _inherit = "hr.resume.line.type"

    name = fields.Char(required=True, translate=True)

    def unlink(self):
        for record in self:
            external_id = record.get_external_id().get(record.id)
            if external_id and external_id in DEFAULT_RESUME_TYPE:
                raise UserError(_("Unable to delete record %s") % record.name)
        return super().unlink()
