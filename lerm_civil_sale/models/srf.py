# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SrfFormLermCivilSale(models.Model):
    _inherit = 'lerm.civil.srf'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Source Sales Order',
        readonly=True,
        copy=False,
        ondelete='set null',
        help='Sales order this SRF was generated from.',
    )
    source = fields.Selection([
        ('manual', 'Manual'),
        ('sale_order', 'Sales Order'),
        ('customer_portal', 'Customer Portal'),
    ], string='Source', compute='_compute_source', store=True, copy=False)

    @api.depends('sale_order_id', 'customer_portal_request')
    def _compute_source(self):
        for record in self:
            if record.sale_order_id:
                record.source = 'sale_order'
            elif record.customer_portal_request:
                record.source = 'customer_portal'
            else:
                record.source = 'manual'
