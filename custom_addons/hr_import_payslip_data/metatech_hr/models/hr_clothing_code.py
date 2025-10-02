from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HRClothingCode(models.Model):
    _name = "hr.clothing.code"
    _description = "HR Clothing Code"
    _rec_name = "code"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    code = fields.Char(string="Clothing Code", tracking=True)
    employee_id = fields.Many2one(
        "hr.employee",
        ondelete="set null",
        tracking=True,
        domain=[("clothing_code_id", "=", False)],
    )

    _sql_constraints = [("unique_code", "UNIQUE(code)", "The code must be unique!")]

    @api.constrains("code")
    def _check_code_is_numeric(self):
        for record in self:
            if record.code and not record.code.isdigit():
                raise ValidationError(_("This field only allows numbers!"))

    @api.model
    def create(self, vals):
        if self.env.context.get("default_employee_id", False):
            vals.update({"employee_id": False})
        res = super().create(vals)
        if "employee_id" in vals and vals["employee_id"]:
            employee = self.env["hr.employee"].browse(vals["employee_id"])
            if employee:
                employee.write({"clothing_code_id": res.id})
        return res

    def write(self, vals):
        if "employee_id" in vals:
            old_employee = self.employee_id
            result = super().write(vals)
            if old_employee:
                old_employee.write({"clothing_code_id": False})
            if "employee_id" in vals:
                new_employee = self.env["hr.employee"].browse(vals["employee_id"])
                if new_employee:
                    new_employee.write({"clothing_code_id": self.id})
            return result
        return super().write(vals)
