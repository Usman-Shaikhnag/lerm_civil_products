# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderPricelistWizardLine(models.TransientModel):
    _name = 'sale.order.pricelist.wizard.line'
    _description = 'Sales Order Pricelist Wizard Line'

    wizard_id = fields.Many2one('sale.order.pricelist.wizard', string='Wizard', ondelete='cascade')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sales Order Line', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product', readonly=True)
    parameter_id = fields.Many2one('lerm.parameter.master', string='Parameter', readonly=True)
    current_price = fields.Float(string='Current Price', readonly=True)
    new_price = fields.Float(string='New Price')


class SaleOrderPricelistWizard(models.TransientModel):
    _name = 'sale.order.pricelist.wizard'
    _description = 'Sales Order Pricelist Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', required=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', related='sale_order_id.company_id', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='sale_order_id.currency_id', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', readonly=True)
    line_ids = fields.One2many('sale.order.pricelist.wizard.line', 'wizard_id', string='Prices')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        sale_order_id = res.get('sale_order_id') or self.env.context.get('default_sale_order_id')
        if not sale_order_id:
            return res
        order = self.env['sale.order'].browse(sale_order_id)
        pricelist = order._lerm_get_customer_pricelist()
        res['pricelist_id'] = pricelist.id if pricelist else False
        data = self._build_line_data(order)
        res['line_ids'] = [(0, 0, d) for d in data]
        return res

    def _build_line_data(self, order):
        """Rebuild the authoritative pricelist line data from the Sales Order.

        The web client strips readonly fields from wizard lines, so the line
        identifiers (sale_order_line_id / parameter / product) cannot be trusted
        at apply time. This method always reconstructs them from the order, and
        the user-entered prices are merged back positionally.
        """
        data = []
        PricelistItem = self.env['product.pricelist.item'].sudo()
        pricelist = order._lerm_get_customer_pricelist()
        for line in order.order_line:
            product_tmpl = line.product_id.product_tmpl_id if line.product_id else False
            if not product_tmpl or not product_tmpl.is_sample:
                continue
            params = line.parameters
            if params:
                for param in params:
                    current = 0.0
                    if pricelist:
                        item = PricelistItem.search([
                            ('pricelist_id', '=', pricelist.id),
                            ('product_tmpl_id', '=', product_tmpl.id),
                            ('parameter_id', '=', param.id),
                        ], limit=1)
                        if item:
                            current = item.fixed_price
                    data.append({
                        'sale_order_line_id': line.id,
                        'product_tmpl_id': product_tmpl.id,
                        'parameter_id': param.id,
                        'current_price': current,
                        'new_price': line.price_unit / len(params),
                    })
            else:
                current = 0.0
                if pricelist:
                    item = PricelistItem.search([
                        ('pricelist_id', '=', pricelist.id),
                        ('product_tmpl_id', '=', product_tmpl.id),
                        ('parameter_id', '=', False),
                    ], limit=1)
                    if item:
                        current = item.fixed_price
                data.append({
                    'sale_order_line_id': line.id,
                    'product_tmpl_id': product_tmpl.id,
                    'parameter_id': False,
                    'current_price': current,
                    'new_price': line.price_unit,
                })
        return data

    def _merge_client_prices(self, order):
        data = self._build_line_data(order)
        client_lines = self.line_ids
        if len(client_lines) != len(data):
            raise UserError(_(
                'The pricelist lines were modified (lines added or removed). '
                'Please close and reopen the wizard.'))
        for idx, d in enumerate(data):
            d['new_price'] = client_lines[idx].new_price
        return data

    def action_apply(self):
        self.ensure_one()
        order = self.sale_order_id
        if not order:
            raise UserError(_('Sales Order is missing. Please reopen the wizard.'))
        data = self._merge_client_prices(order)
        if not data:
            raise UserError(_('No lines to process. Add sample products on the order first.'))
        self._action_update(order, data)
        return {'type': 'ir.actions.act_window_close'}

    def _action_update(self, order, data):
        pricelist = order._lerm_get_customer_pricelist()
        if not pricelist:
            raise UserError(_(
                'No pricelist is attached to customer %s. Please set a pricelist '
                'on the customer contact first.') % (order.partner_id.name or ''))
        if order._lerm_is_default_pricelist(pricelist):
            raise UserError(_(
                'The pricelist "%s" is the default pricelist and cannot be updated. '
                'Please assign a customer-specific pricelist to %s first.')
                % (pricelist.name, order.partner_id.name or ''))
        audit_ctx = {
            'audit_source': 'sale_order',
            'audit_sale_order_id': order.id,
            'audit_user_id': self.env.user.id,
        }
        PricelistItem = self.env['product.pricelist.item'].sudo().with_context(**audit_ctx)
        for d in data:
            domain = [
                ('pricelist_id', '=', pricelist.id),
                ('product_tmpl_id', '=', d['product_tmpl_id']),
            ]
            if d['parameter_id']:
                domain.append(('parameter_id', '=', d['parameter_id']))
            else:
                domain.append(('parameter_id', '=', False))
            item = PricelistItem.search(domain, limit=1)
            old_price = item.fixed_price if item else 0.0
            if abs(old_price - d['new_price']) < 0.0001:
                continue
            if item:
                item.write({'fixed_price': d['new_price']})
            else:
                PricelistItem.create({
                    'pricelist_id': pricelist.id,
                    'applied_on': '1_product',
                    'product_tmpl_id': d['product_tmpl_id'],
                    'parameter_id': d['parameter_id'],
                    'compute_price': 'fixed',
                    'fixed_price': d['new_price'],
                })
            product_name = self.env['product.template'].browse(d['product_tmpl_id']).display_name
            if d['parameter_id']:
                param_name = self.env['lerm.parameter.master'].browse(d['parameter_id']).parameter_name or ''
            else:
                param_name = _('Whole product')
            pricelist.message_post(body=Markup(
                _('Price updated from Sales Order <b>%s</b>: <b>%s</b> (%s) %s → %s (by %s)'))
                % (order.name, product_name, param_name, old_price, d['new_price'],
                   self.env.user.name or ''))
        order.message_post(body=Markup(
            _('Pricelist <b>%s</b> prices updated from this Sales Order.')) % pricelist.name)
        return pricelist
