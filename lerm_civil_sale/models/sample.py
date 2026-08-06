# -*- coding: utf-8 -*-
from odoo import fields, models


class LermSampleFormLermCivilSale(models.Model):
    _inherit = 'lerm.srf.sample'

    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sales Order Line',
        ondelete='set null',
        index=True,
        help='Sales Order line this sample was created from.',
    )
