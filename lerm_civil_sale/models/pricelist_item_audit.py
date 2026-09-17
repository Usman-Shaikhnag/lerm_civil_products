# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductPricelistItemAudit(models.Model):
    _inherit = 'product.pricelist.item'

    last_sale_order_id = fields.Many2one(
        'sale.order',
        string='Source',
        readonly=True,
        ondelete='set null',
        help='Sales Order from which this price was last updated.',
    )

    def action_open_sale_order(self):
        self.ensure_one()
        if not self.last_sale_order_id:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env['ir.actions.act_window']._for_xml_id('sale.action_orders')
        action['res_id'] = self.last_sale_order_id.id
        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        return action

    def _lerm_audit_context(self):
        """Build the common audit log values from the environment.

        Attribution is read from the context so that programmatic writers
        (e.g. the Sales Order wizard) can record the real actor and source;
        direct form edits fall back to the current user.
        """
        return {
            'source': self.env.context.get('audit_source', 'pricelist'),
            'sale_order_id': self.env.context.get('audit_sale_order_id'),
            'user_id': self.env.context.get('audit_user_id') or self.env.user.id,
        }

    def _lerm_should_skip_audit(self):
        """Skip audit logging during module install/upgrade or when explicitly
        requested (e.g. a bulk sync that must not be recorded)."""
        if self.env.context.get('no_pricelist_audit'):
            return True
        return bool(self.env.context.get('install_mode'))

    def _lerm_log_audit(self, action, old_price, new_price, **extra):
        if self._lerm_should_skip_audit():
            return False
        audit_vals = self._lerm_audit_context()
        audit_vals.update({
            'pricelist_id': self.pricelist_id.id if self.pricelist_id else False,
            'pricelist_item_id': self.id or False,
            'product_tmpl_id': self.product_tmpl_id.id if self.product_tmpl_id else False,
            'parameter_id': self.parameter_id.id if self.parameter_id else False,
            'action': action,
            'old_price': old_price,
            'new_price': new_price,
        })
        audit_vals.update(extra)
        self.env['lerm.pricelist.audit.log'].sudo().create(audit_vals)
        return True

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec, vals in zip(records, vals_list):
            if 'fixed_price' not in vals:
                continue
            rec._lerm_log_audit('create', 0.0, vals.get('fixed_price') or 0.0)
        return records

    def write(self, vals):
        old_prices = {rec.id: rec.fixed_price for rec in self}
        res = super().write(vals)
        if 'fixed_price' in vals:
            for rec in self:
                old = old_prices.get(rec.id, 0.0)
                new = vals.get('fixed_price') or 0.0
                if abs(old - new) < 0.0001:
                    continue
                rec._lerm_log_audit('update', old, new)
        return res
