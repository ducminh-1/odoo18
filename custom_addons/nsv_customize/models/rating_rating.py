# class RatingMixin(models.AbstractModel):
#     _inherit = 'rating.mixin'
#
#     def rating_apply(self, rate, token=None, feedback=None, subtype_xmlid=None):
#         """ Apply a rating given a token. If the current model inherits from
#         mail.thread mixin, a message is posted on its chatter. User going through
#         this method should have at least employee rights because of rating
#         manipulation (either employee, either sudo-ed in public controllers after
#         security check granting access).
#
#         :param float rate : the rating value to apply
#         :param string token : access token
#         :param string feedback : additional feedback
#         :param string subtype_xmlid : xml id of a valid mail.message.subtype
#
#         :returns rating.rating record
#         """
#         rating = None
#         if token:
#             rating = self.env['rating.rating'].search([('access_token', '=', token)], limit=1)
#         else:
#             rating = self.env['rating.rating'].search([('res_model', '=', self._name), ('res_id', '=', self.ids[0])], limit=1)
#         if rating:
#             rating.write({'rating': rate, 'feedback': feedback, 'consumed': True})
#             if hasattr(self, 'message_post'):
#                 feedback = tools.plaintext2html(feedback or '')
#                 self.message_post(
#                     body="<img src='/nsv_customize/static/src/img/rating_%s.png' alt=':%s/10' style='width:18px;height:18px;float:left;margin-right: 5px;'/>%s"
#                     % (rate, rate, feedback),
#                     subtype_xmlid=subtype_xmlid or "mail.mt_comment",
#                     author_id=rating.partner_id and rating.partner_id.id or None  # None will set the default author in mail_thread.py
#                 )
#             if hasattr(self, 'stage_id') and self.stage_id and hasattr(self.stage_id, 'auto_validation_kanban_state') and self.stage_id.auto_validation_kanban_state:
#                 if rating.rating > 2:
#                     self.write({'kanban_state': 'done'})
#                 else:
#                     self.write({'kanban_state': 'blocked'})
#         return rating


# class RatingRating(models.Model):
#     _inherit = 'rating.rating'
#
#     def _get_rating_image_filename(self):
#         self.ensure_one()
#         rating_int = int(self.rating)
#         if self.rating == 0:
#             rating_int = 3
#         return 'rating_%s.png' % rating_int
#
#     def _compute_rating_image(self):
#         for rating in self:
#             try:
#                 image_path = get_resource_path('nsv_customize', 'static/src/img',  rating._get_rating_image_filename())
#                 rating.rating_image = base64.b64encode(open(image_path, 'rb').read()) if image_path else False
#             except (IOError, OSError):
#                 rating.rating_image = False
