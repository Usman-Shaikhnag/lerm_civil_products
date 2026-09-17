# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class SaleOrderLermCivilSale(models.Model):
    _inherit = 'sale.order'

    def _lerm_get_customer_pricelist(self):
        """Return the pricelist attached to the customer (billing partner)."""
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            return self.env['product.pricelist']
        return partner.property_product_pricelist

    def _lerm_is_default_pricelist(self, pricelist):
        """Return True if the pricelist is the inherited company default rather
        than a pricelist explicitly assigned to the customer."""
        self.ensure_one()
        partner = self.partner_id
        if not partner or not pricelist:
            return False
        prop = self.env['ir.property'].sudo().search([
            ('name', '=', 'property_product_pricelist'),
            ('res_id', '=', 'res.partner,%s' % partner.id),
        ], limit=1)
        return not prop

    def action_pricelist(self):
        """Open the pricelist update wizard for the customer's attached
        pricelist. Only updates — it never creates a pricelist, and the
        default pricelist cannot be updated."""
        self.ensure_one()
        pricelist = self._lerm_get_customer_pricelist()
        partner = self.partner_id
        if not pricelist:
            raise UserError(_(
                'No pricelist is attached to customer %s. Please set a pricelist '
                'on the customer contact first.') % (partner.name or ''))
        if self._lerm_is_default_pricelist(pricelist):
            raise UserError(_(
                'The pricelist "%s" is the default pricelist and cannot be updated. '
                'Please assign a customer-specific pricelist to %s first.')
                % (pricelist.name, partner.name or ''))
        action = self.env['ir.actions.act_window']._for_xml_id(
            'lerm_civil_sale.action_sale_order_pricelist_wizard')
        action['context'] = {
            'default_sale_order_id': self.id,
            'default_pricelist_id': pricelist.id,
        }
        return action
