# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    employee_id = fields.Many2one("hr.employee", "Employee", readonly=True)

    # def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
    #     fields['employee_id'] = ", s.employee_id as employee_id"
    #     groupby += ', s.employee_id'
    #     return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["employee_id"] = "s.employee_id"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += ", s.employee_id"
        return res
