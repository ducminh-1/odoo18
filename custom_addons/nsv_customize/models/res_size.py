from odoo import api, fields, models
from odoo.osv import expression


class ResSize(models.Model):
    _name = "res.size"
    _description = "Product Size"

    length = fields.Float("Length")
    width = fields.Float("Width")
    height = fields.Float("Height")
    name = fields.Char(compute="_compute_name", store=True)

    @api.depends("length", "width", "height")
    def _compute_name(self):
        for rec in self:
            name = ""
            if rec.length:
                name = "%s" % rec.length
            if rec.width:
                name += " x %s" % rec.width
            if rec.height:
                name += " x %s" % rec.height
            rec.name = name

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        if operator == "ilike" and not (name or "").strip():
            domain = []
        else:
            domain = [
                "|",
                "|",
                "|",
                ("name", operator, name),
                ("length", operator, name),
                ("width", operator, name),
                ("height", operator, name),
            ]
        return self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )
