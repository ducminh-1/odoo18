from lxml import etree

from odoo import fields, models


class View(models.Model):
    _inherit = "ir.ui.view"

    zns_template_id = fields.Char(string="ZNS Template ID")
    zalo_oa_id = fields.Many2one("zalo.oa", string="Zalo OA")

    def get_val_esc_in_xml(self):
        arch_tree = etree.fromstring(str(self.arch_base))
        keys = []
        for descendant in arch_tree.iterdescendants(tag=etree.Element):
            if descendant.get("t-esc") and descendant.get("t-esc") not in keys:
                keys.append(descendant.get("t-esc"))
            if descendant.get("t-field") and descendant.get("t-field") not in keys:
                keys.append(descendant.get("t-field"))
        return keys

    def get_val_esc_in_xml_zns(self):
        arch_tree = etree.fromstring(str(self.arch_base))
        keys = []
        for descendant in arch_tree.iterdescendants(tag=etree.Element):
            t_set = descendant.get("t-set")
            if t_set and (t_set not in keys and t_set.startswith("zns_")):
                keys.append(
                    {
                        "name": t_set.replace("zns_", ""),
                        "value": descendant.get("t-value"),
                    }
                )
        return keys
