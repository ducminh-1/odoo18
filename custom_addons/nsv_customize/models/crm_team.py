from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        "Analytic Account",
        copy=False,
        check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account related to a sales team.",
    )
    member_ids = fields.Many2many(
        "res.users",
        "crm_team_user_rel",
        "team_id",
        "user_id",
        string="Channel Members",
        check_company=True,
        domain=[("share", "=", False)],
        help="Add members to automatically assign their documents to this sales team. You can only be member of one team.",
    )

    def _get_default_team_id(self, user_id=None, domain=None):
        user_id = user_id or self.env.uid
        # user_salesteam_id = self.env['res.users'].browse(user_id).sale_team_id.id
        # Avoid searching on member_ids (+1 query) when we may have the user salesteam already in cache.
        team = self.env["crm.team"].search(
            [
                ("company_id", "in", [False, self.env.company.id]),
                "|",
                ("user_id", "=", user_id),
                ("member_ids", "=", user_id),
            ],
            limit=1,
        )
        if not team and "default_team_id" in self.env.context:
            team = self.env["crm.team"].browse(self.env.context.get("default_team_id"))
        return team or self.env["crm.team"].search(domain or [], limit=1)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    employee_id = fields.Many2one("hr.employee", string="Employee", check_company=True)

    def _convert_opportunity_data(self, customer, team_id=False):
        res = super()._convert_opportunity_data(customer, team_id)
        lead2opportunity_stage_id = self.env.context.get("stage_id")
        if self.env.context.get("lead2opportunity") and lead2opportunity_stage_id:
            res.update({"stage_id": lead2opportunity_stage_id})
        return res


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = "crm.lead2opportunity.partner"

    stage_id = fields.Many2one(
        "crm.stage",
        string="Stage",
        ondelete="restrict",
        domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]",
    )

    def _convert_and_allocate(self, leads, user_ids, team_id=False):
        self.ensure_one()

        for lead in leads:
            if lead.active and self.action != "nothing":
                self._convert_handle_partner(
                    lead, self.action, self.partner_id.id or lead.partner_id.id
                )

            lead.with_context(
                lead2opportunity=True,
                stage_id=self.stage_id.id if self.stage_id else False,
            ).convert_opportunity(lead.partner_id, False, False)

        leads_to_allocate = leads
        if not self.force_assignment:
            leads_to_allocate = leads_to_allocate.filtered(
                lambda lead: not lead.user_id
            )

        if user_ids:
            leads_to_allocate._handle_salesmen_assignment(user_ids, team_id=team_id)
