# -*- coding: utf-8 -*-
from odoo import fields, models


class SrfFormLermCivilSale(models.Model):
    _inherit = 'lerm.civil.srf'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        ondelete='set null',
        index=True,
        help='Sales Order this SRF was created from.',
    )
    price_snapshot = fields.Text(string='Price Snapshot (JSON)')
