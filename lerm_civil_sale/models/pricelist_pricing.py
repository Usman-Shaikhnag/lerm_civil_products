# -*- coding: utf-8 -*-
from odoo import models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _lerm_compute_parameter_price(self, product_tmpl, parameters):
        """Compute the LERM parameter-based price for a product.

        Canonical fallback chain (mirrors the lerm_accountant bulk invoice
        wizard) so that Sales Order, SRF snapshot and Invoice all agree:

          1. per-parameter pricelist item (parameter_id match)
          2. whole-product pricelist item (no parameter_id)
          3. product default price (list_price) split across parameters

        Returns a dict:
          {
            'items': [{'parameter_id': int or False, 'price': float, 'source': str}],
            'total': float,
            'was_fallback': bool,
            'source': str,   # 'parameter' | 'product' | 'default'
          }
        """
        self.ensure_one()
        PricelistItem = self.env['product.pricelist.item'].sudo()
        if not product_tmpl:
            return {'items': [], 'total': 0.0, 'was_fallback': True, 'source': 'default'}
        pt_id = product_tmpl.id

        param_items = PricelistItem.search([
            ('pricelist_id', '=', self.id),
            ('parameter_id', '!=', False),
            '|',
            ('product_tmpl_id', '=', pt_id),
            ('applied_on', '=', '3_global'),
        ])
        product_items = PricelistItem.search([
            ('pricelist_id', '=', self.id),
            ('parameter_id', '=', False),
            '|',
            ('product_tmpl_id', '=', pt_id),
            ('applied_on', '=', '3_global'),
        ])

        items = []
        total = 0.0
        was_fallback = False
        source = 'parameter'

        if parameters:
            param_count = len(parameters)
            for param in parameters:
                p_id = param._origin.id if param._origin else param.id
                matching = param_items.filtered(
                    lambda i: i.parameter_id.id == p_id or (
                        i.parameter_id.parameter_name and param.parameter_name and
                        i.parameter_id.parameter_name.strip().lower() == param.parameter_name.strip().lower()
                    )
                )
                if matching:
                    price = matching[0].fixed_price
                    items.append({'parameter_id': p_id, 'price': price, 'source': 'parameter'})
                else:
                    prod_match = product_items[:1]
                    if prod_match:
                        price = prod_match.fixed_price
                        items.append({'parameter_id': p_id, 'price': price, 'source': 'product'})
                    else:
                        price = product_tmpl.list_price / param_count if param_count else 0.0
                        items.append({'parameter_id': p_id, 'price': price, 'source': 'default'})
                    was_fallback = True
                total += items[-1]['price']
        else:
            prod_match = product_items[:1]
            if prod_match:
                total = prod_match.fixed_price
                source = 'product'
                items.append({'parameter_id': False, 'price': total, 'source': 'product'})
            else:
                total = product_tmpl.list_price
                source = 'default'
                was_fallback = True
                items.append({'parameter_id': False, 'price': total, 'source': 'default'})

        return {
            'items': items,
            'total': round(total, 2),
            'was_fallback': was_fallback,
            'source': source,
        }
