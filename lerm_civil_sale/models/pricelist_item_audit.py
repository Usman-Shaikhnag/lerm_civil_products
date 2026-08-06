# -*- coding: utf-8 -*-
from odoo import api, models


class ProductPricelistItemAudit(models.Model):
    _inherit = 'product.pricelist.item'

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


class ProductTemplateAudit(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        old_prices = {rec.id: rec.list_price for rec in self}
        res = super().write(vals)
        if 'list_price' in vals:
            audit_env = self.env['lerm.pricelist.audit.log'].sudo()
            if self.env.context.get('no_pricelist_audit') or self.env.context.get('install_mode'):
                return res
            for rec in self:
                old = old_prices.get(rec.id, 0.0)
                new = vals.get('list_price') or 0.0
                if abs(old - new) < 0.0001:
                    continue
                audit_env.create({
                    'source': self.env.context.get('audit_source', 'product'),
                    'sale_order_id': self.env.context.get('audit_sale_order_id'),
                    'product_tmpl_id': rec.id,
                    'parameter_id': False,
                    'action': 'update',
                    'old_price': old,
                    'new_price': new,
                    'user_id': self.env.context.get('audit_user_id') or self.env.user.id,
                })
        return res
