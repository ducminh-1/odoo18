# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MHDHopDongWizard(models.TransientModel):
    _name = "mhd.hopdong.wizard"
    _description = "MHD - Số hợp đồng - Wizard"

    name = fields.Char(string='Số hợp đồng', required=True)

    def create_hop_dong(self):
        self.env['mhd.hopdong.wizard'].browse(self._context.get('active_ids', []))
        return False