from odoo import fields, models


class MauticConfirmMigration(models.TransientModel):
    _name = "mautic.confirm.migration"
    _description = "Mautic Confirm Migration"

    config_id = fields.Many2one(
        "mautic.migrate.config", readonly=True, string="Mautic Config"
    )
    config_state = fields.Selection(
        related="config_id.state", readonly=True, string="Config Status"
    )
    lead_count = fields.Integer()
    response_ok = fields.Boolean(readonly=1)
    error_content = fields.Text()

    def process_migrate_contact(self):
        config_id = self.env["mautic.migrate.config"].browse(
            self.env.context.get("active_id")
        )
        config_id.action_process_migrate_leads()
        return {"type": "ir.actions.act_window_close"}
