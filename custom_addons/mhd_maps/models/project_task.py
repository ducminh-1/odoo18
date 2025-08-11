# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class project_task(models.Model):
    _inherit = 'project.task'

    # Thêm trường tọa độ
    customer_longitude = fields.Float(
        string='Vĩ độ', digits=(16, 5), related='tentaisan.customer_longitude', readonly=False, tracking=True)
    customer_latitude = fields.Float(
        string='Kinh độ', digits=(16, 5), related='tentaisan.customer_latitude', readonly=False, tracking=True)