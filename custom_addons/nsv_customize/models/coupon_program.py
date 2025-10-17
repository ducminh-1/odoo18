LOYALTY_PARTNER_FIELDS = ["loyalty_level_id", "loyalty_point_amount"]


# class CouponProgram(models.Model):
#     _inherit = 'coupon.program'
#
#     is_loyalty_program = fields.Boolean(string='Is Loyalty Program', compute='_compute_is_loyalty_program', store=True, readonly=False)
#     show_coupon_prefix = fields.Boolean(compute='_compute_show_coupon_prefix', store=True)
#     coupon_prefix = fields.Char()
#
#     @api.constrains('coupon_prefix')
#     def _check_coupon_prefix_constraint(self):
#         """ Coupon prefix must be unique """
#         for program in self.filtered(lambda p: p.coupon_prefix):
#             domain = [('id', '!=', program.id), ('coupon_prefix', '=', program.coupon_prefix)]
#             if self.search(domain):
#                 raise ValidationError(_('The coupon prefix must be unique!'))
#
#     @api.depends('rule_id', 'rule_id.rule_partners_domain')
#     def _compute_is_loyalty_program(self):
#         for program in self:
#             if program.rule_id and program.rule_id.rule_partners_domain:
#                 program.is_loyalty_program = any(field in program.rule_id.rule_partners_domain for field in LOYALTY_PARTNER_FIELDS)
#             else:
#                 program.is_loyalty_program = False
#
#     @api.depends('promo_applicability', 'program_type')
#     def _compute_show_coupon_prefix(self):
#         for program in self:
#             program.show_coupon_prefix = program.promo_applicability == 'on_next_order' or program.program_type == 'coupon_program'
