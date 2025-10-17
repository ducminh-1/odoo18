# class CouponGenerate(models.TransientModel):
#     _inherit = 'coupon.generate.wizard'
#
#     program_id = fields.Many2one('coupon.program', required=True, default=lambda self: self.env.context.get('active_id', False) or self.env.context.get('default_program_id', False))
#     program_coupon_prefix = fields.Char(related='program_id.coupon_prefix')
#
#
#     def generate_coupon(self):
#         return super(CouponGenerate, self.with_context(coupon_prefix=self.program_coupon_prefix)).generate_coupon()
