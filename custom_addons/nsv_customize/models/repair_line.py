import logging

_logger = logging.getLogger(__name__)


# class RepairLine(models.Model):
#     _inherit = 'repair.line'
#
#     analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
#
#     @api.onchange('product_id')
#     def _onchange_account_tag(self):
#         if self.repair_id.pos_account_tag_id:
#             self.analytic_tag_ids |= self.repair_id.pos_account_tag_id
#         if self.repair_id.channel_account_tag_id:
#             self.analytic_tag_ids |= self.repair_id.channel_account_tag_id
#
#     @api.onchange('type', 'repair_id')
#     def onchange_operation_type(self):
#         res = super(RepairLine, self).onchange_operation_type()
#         if self.type == 'add':
#             default_src = self.sudo().repair_id.company_id.add_repair_src_location_id
#             default_des = self.sudo().repair_id.company_id.add_repair_des_location_id
#             if default_src:
#                 self.location_id = default_src
#             if default_des:
#                 self.location_dest_id = default_des
#         else:
#             default_src = self.sudo().repair_id.company_id.rm_repair_src_location_id
#             default_des = self.sudo().repair_id.company_id.rm_repair_des_location_id
#             if default_src:
#                 self.location_id = default_src
#             if default_des:
#                 self.location_dest_id = default_des
#         return res
