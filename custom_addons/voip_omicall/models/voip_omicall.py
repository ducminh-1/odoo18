from odoo import fields, models


class VOIPTransaction(models.Model):
    _name = "voip.transaction.log"
    _description = "voip.transaction.log"
    _order = "transaction_id"

    name = fields.Char(related="transaction_id")
    transaction_id = fields.Char(readonly=True)
    partner_id = fields.Many2one("res.partner", "Customer", readonly=True)
    commercial_partner_id = fields.Many2one(
        "res.partner", related="partner_id.commercial_partner_id", store=True
    )
    user_id = fields.Many2one("res.users", "Receipt User", readonly=True)
    phone = fields.Char(readonly=True)
    user_login = fields.Char()
    sip_login = fields.Char()


class VoipCallLog(models.Model):
    _name = "voip.call.log"
    _description = "VOIP Call Log"
    _order = "write_date desc"

    name = fields.Char(compute="_compute_name")
    tenant_id = fields.Char()
    transaction_id = fields.Char()
    direction = fields.Selection(
        [("outbound", "outbound"), ("inbound", "inbound"), ("local", "local")]
    )
    source_number = fields.Char()
    destination_number = fields.Char()
    disposition = fields.Char()
    bill_sec = fields.Integer()
    record_seconds = fields.Integer()
    time_start_to_answer = fields.Datetime()
    duration = fields.Integer()
    recording_file = fields.Char()
    sip_user = fields.Integer()
    created_date = fields.Datetime()
    last_updated_date = fields.Datetime()
    provider = fields.Char()
    is_auto_call = fields.Boolean()
    call_out_price = fields.Float()
    customer_fullname = fields.Char()
    customer_fullname_unsigned = fields.Char()
    # USER
    user_fullname = fields.Char()
    note = fields.Text()
    text_tag = fields.Text()

    partner_id = fields.Many2one("res.partner")
    user_id = fields.Many2one("res.users")
    commercial_partner_id = fields.Many2one(
        "res.partner", related="partner_id.commercial_partner_id", store=True
    )
    request_count = fields.Integer()

    def _compute_name(self):
        for log in self:
            name = log.source_number
            if log.partner_id:
                name = "%s - %s" % (log.partner_id.name or "", name)
            log.name = name
