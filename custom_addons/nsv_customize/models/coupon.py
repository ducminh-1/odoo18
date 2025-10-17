# from uuid import uuid4


# COUPON_LENGTH = 10


# class Coupon(models.Model):
#     _inherit = 'coupon.coupon'
#
#     @api.model
#     def _generate_code(self):
#         prefix = self.env.context.get('coupon_prefix', '') or ''
#         # start_at = 8 if prefix else 7
#         # return prefix + str(uuid4())[start_at:start_at+COUPON_LENGTH]
#         return prefix + str(random.getrandbits(32))
#
#     code = fields.Char(default=_generate_code, required=True, readonly=True)
