import base64

from xlrd import open_workbook

from odoo import Command, _, fields, models
from odoo.exceptions import UserError


class HrProductPayslipImport(models.TransientModel):
    _name = "hr.payslip.import"
    _description = "Hr Payslip Import"

    file = fields.Binary(string="Xlsx File")

    def action_import(self):
        active_model = self._context.get("active_model")
        active_model_id = self.env[active_model].browse(self._context.get("active_id"))
        HrPayslip = self.env["hr.payslip"]
        HrWorkEntryType = self.env["hr.work.entry.type"]
        HrSalaryRuleCategory = self.env["hr.salary.rule.category"]
        payslips = active_model_id.slip_ids.filtered(
            lambda slip: slip.state in ("draft", "verify")
        )
        wb = open_workbook(file_contents=base64.decodebytes(self.file))
        sheet1 = wb.sheet_by_index(0)
        payslips_to_compute_payslip = HrPayslip
        work_days_data = {}
        other_input_data = {}
        update_work_days_data = {}
        update_other_input_data = {}

        def _get_workday_vals(f_work_days, f_work_hours, f_payslip_name, f_type_name, payslip_id):
            return {
                "number_of_days": f_work_days,
                "number_of_hours": f_work_hours,
                "name":f_payslip_name,
                "code": f_type_name,
                "contract_id": payslip_id.contract_id.id
            }

        def _get_input_vals(f_amount, f_type_name, payslip_id):
            return {
                "amount": f_amount,
                "code": f_payslip_name,
                "name":f_type_name,
                "contract_id": payslip_id.contract_id.id
            }
        # Process each row, except the first row (header)
        for row in range(1, sheet1.nrows):
            col_value = [sheet1.cell(row, col).value for col in range(sheet1.ncols)]
            # Get values from each column
            (
                f_payslip_name,
                f_employee_name,
                f_type,
                f_type_name,
                f_work_days,
                f_work_hours,
                f_amount,
            ) = col_value
            payslip_id = payslips.filtered(
                lambda slip, slip_name=f_payslip_name: slip.number == slip_name.strip()
            )
            if not payslip_id:
                raise UserError(
                    _("Some thing wrong ! Check data input in line  %s !") % row
                )
            if f_type.strip() == "WORK_DAYS":
                work_entry_type_id = HrWorkEntryType.search(
                    [("name", "=", f_type_name.strip())]
                )
                if not work_entry_type_id:
                    raise UserError(
                        _(
                            "Work entry type: %(f_type_name)s is not existed in the line %(row)s !",  # noqa
                            f_type_name=f_type_name,
                            row=row + 1,
                        )
                    )

                update_work_days_line_id = payslip_id.worked_days_line_ids.filtered(
                    lambda line,
                    work_entry_type_id=work_entry_type_id: line.code
                    == work_entry_type_id.code
                )
                workday_vals = _get_workday_vals(f_work_days, f_work_hours, f_payslip_name, f_type_name, payslip_id)
                if update_work_days_line_id:
                    update_work_days_data.update(
                        {update_work_days_line_id: workday_vals}
                    )
                else:
                    work_days_data[payslip_id] = work_days_data.get(payslip_id, []) + [
                        Command.create(
                            {
                                **workday_vals,
                            }
                        )
                    ]
                payslips_to_compute_payslip |= payslip_id

            elif f_type.strip() == "INPUT":
                input_type_id = HrSalaryRuleCategory.search(
                    [("name", "=", f_type_name.strip())]
                )
                if not input_type_id:
                    raise UserError(
                        _(
                            "Input type: %(f_type_name)s is not existed in the line %(row)s !",  # noqa
                            f_type_name=f_type_name,
                            row=row + 1,
                        )
                    )
                update_input_type_id = payslip_id.input_line_ids.filtered(
                    lambda line, input_type_id=input_type_id: line.code
                    == input_type_id.code
                )
                input_vals = _get_input_vals(f_amount, f_type_name, payslip_id)
                if update_input_type_id:
                    update_other_input_data.update({update_input_type_id: input_vals})
                else:
                    other_input_data[payslip_id] = other_input_data.get(
                        payslip_id, []
                    ) + [
                        Command.create(
                            {
                                **input_vals,
                            }
                        )
                    ]
                payslips_to_compute_payslip |= payslip_id
            else:
                raise UserError(_('Invalid "Type". Must be "WORK_DAYS" or "INPUT" !'))

        # Update or create new lines in the payslip details
        for line in update_work_days_data:
            line.update(update_work_days_data[line])

        for line in update_other_input_data:
            line.update(update_other_input_data[line])

        for payslip in work_days_data:
            payslip.write(
                {"worked_days_line_ids": work_days_data[payslip], "imported": True}
            )

        for payslip in other_input_data:
            payslip.write(
                {"input_line_ids": other_input_data[payslip], "imported": True}
            )

        if payslips_to_compute_payslip:
            payslips_to_compute_payslip.action_compute_sheet()
            active_model_id.write(
                {"imported": True, "last_import_date": fields.Datetime.now()}
            )
