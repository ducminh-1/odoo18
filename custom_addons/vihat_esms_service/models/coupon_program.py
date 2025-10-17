LOYALTY_PARTNER_FIELDS = ["loyalty_level_id", "loyalty_point_amount"]


# class CouponProgram(models.Model):
#     _inherit = 'coupon.program'
#
#     def _get_translated_discount_apply_on(self):
#         labels = dict(self.fields_get(['discount_apply_on'])['discount_apply_on']['selection'])
#         return labels[self.discount_apply_on].lower()
