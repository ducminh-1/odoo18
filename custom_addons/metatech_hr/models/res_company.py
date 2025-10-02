from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    acronym = fields.Char()

    @api.constrains("acronym")
    def _check_acronym_case(self):
        for record in self:
            if record.acronym and not record.acronym.isupper():
                raise ValidationError(
                    _("The acronym must be in uppercase (e.g., 'ABC').")
                )

    @api.model
    def write(self, vals):
        if "acronym" in vals and vals["acronym"] != self.acronym:
            sequence = self.env["ir.sequence"].search(
                [("code", "=", f"employee.sequence.{self.id}")], limit=1
            )
            if sequence:
                new_prefix = vals["acronym"].upper() + "."
                if sequence.prefix != new_prefix:
                    sequence.write({"prefix": new_prefix})
        return super().write(vals)
