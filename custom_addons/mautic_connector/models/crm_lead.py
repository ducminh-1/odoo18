from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    mautic_id = fields.Integer("Mautic ID", index=True, readonly=True, copy=False)
    mautic_config_id = fields.Many2one(
        "mautic.migrate.config",
        index=True,
        readonly=True,
        copy=False,
        string="Mautic Config",
        ondelete="set null",
    )
