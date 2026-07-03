import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderLineInherited(models.Model):
    _inherit = 'sale.order.line'

    parameters = fields.Many2many('lerm.parameter.master', string='Parameters')
    product_tmpl_id = fields.Many2one(
        'product.template',
        related='product_id.product_tmpl_id',
        string='Product Template',
    )

    @api.depends('parameters', 'product_id', 'order_id.pricelist_id')
    def _compute_price_unit(self):
        res = super()._compute_price_unit()
        for line in self:
            if line.parameters and line.order_id.pricelist_id and line.product_id:
                total = line._get_parameter_pricelist_total()
                line.price_unit = total
            elif not line.parameters and line.order_id.pricelist_id and line.product_id:
                # No parameters selected — check if pricelist has a whole-product price
                pt_id = line.product_id.product_tmpl_id.id
                prod_id = line.product_id.id

                # Look for whole-product pricelist items (no parameter_id)
                whole_product_price = line.order_id.pricelist_id.item_ids.filtered(
                    lambda i: (
                        (i.product_tmpl_id.id == pt_id or i.product_id.id == prod_id)
                        and not i.parameter_id
                    )
                )
                if whole_product_price:
                    line.price_unit = whole_product_price[0].fixed_price
                else:
                    # Check if ONLY parameter-specific prices exist (no whole-product entry)
                    has_param_prices = line.order_id.pricelist_id.item_ids.filtered(
                        lambda i: (
                            (i.product_tmpl_id.id == pt_id or i.product_id.id == prod_id)
                            and i.parameter_id
                        )
                    )
                    if has_param_prices:
                        # Only parameter-specific prices exist, no whole-product price — force 0
                        line.price_unit = 0.0
        return res

    def _get_parameter_pricelist_total(self):
        """Calculate total price from parameter-specific pricelist items."""
        self.ensure_one()
        _logger.info(f"--- _get_parameter_pricelist_total called for SO line {self.id} ---")
        _logger.info(f"Parameters: {self.parameters.ids if self.parameters else 'None'}")

        pricelist = self.order_id.pricelist_id
        _logger.info(f"Pricelist: {pricelist.id if pricelist else 'None'} | Name: {pricelist.name if pricelist else 'None'}")
        _logger.info(f"Product: {self.product_id.id if self.product_id else 'None'}")

        if self.parameters and pricelist and self.product_id:
            total = 0.0
            pt_id = self.product_id.product_tmpl_id.id

            # Search pricelist items directly from DB for reliability
            PricelistItem = self.env['product.pricelist.item'].sudo()
            pricelist_items = PricelistItem.search([
                ('pricelist_id', '=', pricelist.id),
                ('parameter_id', '!=', False),
                '|',
                ('product_tmpl_id', '=', pt_id),
                ('applied_on', '=', '3_global'),
            ])

            _logger.info(f"Found {len(pricelist_items)} pricelist items for pricelist {pricelist.id}")
            for debug_item in pricelist_items:
                _logger.info(f"  Item ID: {debug_item.id} | param: {debug_item.parameter_id.id} | price: {debug_item.fixed_price}")

            for param in self.parameters:
                p_id = param._origin.id if param._origin else param.id

                matching = pricelist_items.filtered(
                    lambda i: i.parameter_id.id == p_id or (
                        i.parameter_id.parameter_name and param.parameter_name and
                        i.parameter_id.parameter_name.strip().lower() == param.parameter_name.strip().lower()
                    )
                )
                if matching:
                    _logger.info(f"Match found for param {p_id}! Adding {matching[0].fixed_price}")
                    total += matching[0].fixed_price
                else:
                    _logger.info(f"No match found for param {p_id}.")

            _logger.info(f"Final calculated total: {total}")
            return total

        # Fallback to standard pricelist behavior
        return self.price_unit
