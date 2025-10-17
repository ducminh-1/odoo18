from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_size = fields.Many2one(
        "res.size",
        string="Product Size",
        compute="_compute_product_size",
        inverse="_set_product_size",
        store=True,
    )
    carton_size = fields.Many2many(
        "res.size",
        "product_tmpl_carton_size_rel",
        "product_tmpl_id",
        "size_id",
        string="Carton Size",
        compute="_compute_product_size",
        inverse="_set_product_size",
        store=True,
    )
    product_report_category = fields.Many2one(
        "product.public.category", string="Product Report Category"
    )

    @api.depends("product_variant_ids", "product_variant_ids.product_size")
    def _compute_product_size(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.product_size = template.product_variant_ids.product_size
            template.carton_size = template.product_variant_ids.carton_size
        for template in self - unique_variants:
            template.product_size = False
            template.carton_size = False

    def _set_product_size(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.product_size = template.product_size
                template.product_variant_ids.carton_size = template.carton_size

    @api.constrains("default_code")
    def _check_no_duplicate_defalt_code(self):
        for record in self:
            prod_id = record._origin.id
            if record.company_id:
                domain = [
                    ("id", "!=", prod_id),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", record.company_id.id),
                ]
            else:
                domain = [("id", "!=", prod_id)]
            if record.default_code:
                domain += [("default_code", "ilike", record.default_code)]
                ilike_exist_products = self.env["product.template"].search(domain)
                if ilike_exist_products:
                    product_refs = [
                        el.default_code.lower() for el in ilike_exist_products
                    ]
                    if record.default_code.lower() in product_refs:
                        raise UserError(
                            "Duplication Error: The Internal Reference is already existed!"
                        )


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_size = fields.Many2one("res.size", string="Product Size")
    carton_size = fields.Many2many(
        "res.size",
        "variant_carton_size_rel",
        "product_id",
        "size_id",
        string="Product Size",
    )
