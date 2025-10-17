import logging

_logger = logging.getLogger(__name__)


# class RepairFee(models.Model):
#     _inherit = 'repair.fee'
#
#     # analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
#
#     # @api.onchange('product_id')
#     # def _onchange_account_tag(self):
#     #     if self.repair_id.pos_account_tag_id:
#     #         self.analytic_tag_ids |= self.repair_id.pos_account_tag_id
#     #     if self.repair_id.channel_account_tag_id:
#     #         self.analytic_tag_ids |= self.repair_id.channel_account_tag_id
