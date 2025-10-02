from odoo import api, fields, models


class ResumeLine(models.Model):
    _inherit = "hr.resume.line"

    resume_type = fields.Char()

    course_name = fields.Char(string="Course name")
    result = fields.Selection(
        [
            ("point", "Point"),
            ("certificate", "Certificate"),
            ("pass_failed", "Pass/Failed"),
        ],
    )
    point = fields.Float()
    certificate = fields.Char()
    pass_failed = fields.Selection(
        [
            ("pass", "Pass"),
            ("failed", "Failed"),
        ],
        string="Pass/Failed",
    )

    type_of_pros_and_cons = fields.Selection(
        [
            ("pros", "Pros"),
            ("cons", "Cons"),
        ],
        string="Pros/Cons",
    )
    sequence = fields.Integer(default=10)

    @api.onchange("result", "point", "certificate", "pass_failed")
    @api.depends("result", "point", "certificate", "pass_failed")
    def _compute_description(self):
        for rec in self:
            if rec.result == "point":
                description = "Point: " + str(rec.point)
            elif rec.result == "certificate":
                description = (
                    "Certificate: " + rec.certificate if rec.certificate else ""
                )
            else:
                description = rec.pass_failed
            rec.description = description
