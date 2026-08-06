# -*- coding: utf-8 -*-
import json

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLineLermCivilSale(models.Model):
    _inherit = 'sale.order.line'

    grade_id = fields.Many2one('lerm.grade.line', string='Grade', ondelete='restrict')
    size_id = fields.Many2one('lerm.size.line', string='Size', ondelete='restrict')
    conformity = fields.Boolean(string='Conformity Requested')
    price_breakdown = fields.Text(
        string='Price Breakdown',
        compute='_compute_price_breakdown',
        store=True,
    )

    @api.constrains('parameters')
    def _check_single_parameter(self):
        for line in self:
            if len(line.parameters) > 1:
                raise ValidationError(_(
                    'Only one parameter is allowed per Sales Order line. '
                    'Product "%s" currently has %s parameters selected.')
                    % (line.product_id.display_name or '', len(line.parameters)))

    @api.depends('parameters', 'product_id', 'order_id.pricelist_id')
    def _compute_price_unit(self):
        res = super()._compute_price_unit()
        for line in self:
            pricelist = line.order_id.pricelist_id
            product_tmpl = line.product_id.product_tmpl_id if line.product_id else self.env['product.template']
            if pricelist and line.product_id and (line.parameters or product_tmpl.is_sample):
                breakdown = pricelist._lerm_compute_parameter_price(product_tmpl, line.parameters)
                line.price_unit = breakdown['total']
        return res

    @api.depends('parameters', 'product_id', 'order_id.pricelist_id', 'price_unit')
    def _compute_price_breakdown(self):
        for line in self:
            pricelist = line.order_id.pricelist_id
            product_tmpl = line.product_id.product_tmpl_id if line.product_id else self.env['product.template']
            if not (pricelist and line.product_id and (line.parameters or product_tmpl.is_sample)):
                line.price_breakdown = False
                continue
            breakdown = pricelist._lerm_compute_parameter_price(product_tmpl, line.parameters)
            breakdown['was_override'] = abs((line.price_unit or 0.0) - breakdown['total']) > 0.01
            line.price_breakdown = json.dumps(breakdown)
