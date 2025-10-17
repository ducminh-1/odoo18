from odoo import api, fields, models


class Rating(models.Model):
    _inherit = "rating.rating"

    employee_id = fields.Many2one("hr.employee", string="Employee")
    rating_seller = fields.Selection(
        selection=[("bad", "Bad"), ("good", "Good")], string="Rating Sale Service"
    )
    rating_delivery = fields.Selection(
        selection=[("bad", "Bad"), ("good", "Good")], string="Rating Delivery Service"
    )
    res_create_date = fields.Datetime(string="Resource Creation Date", readonly=True)
    res_create_uid = fields.Many2one(
        "res.users", string="Resource Creation User", readonly=True
    )

    @api.model
    def create(self, values):
        if values.get("res_model_id") and values.get("res_id"):
            current_model_name = (
                self.env["ir.model"].sudo().browse(values["res_model_id"]).model
            )
            current_record = self.env[current_model_name].browse(values["res_id"])
            values.update(
                {
                    "res_create_date": current_record.create_date,
                    "res_create_uid": current_record.create_uid.id,
                }
            )
        return super().create(values)
