# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderLermCivilSale(models.Model):
    _inherit = 'sale.order'

    customer_id = fields.Many2one(
        'res.partner',
        string='Reporting Customer',
        help='Customer whose materials are being tested.',
    )
    name_work_id = fields.Many2one('res.partner.project', string='Name of Work')
    srf_ids = fields.One2many('lerm.civil.srf', 'sale_order_id', string='SRFs')
    srf_count = fields.Integer(string='SRF Count', compute='_compute_srf_count')

    @api.depends('srf_ids')
    def _compute_srf_count(self):
        for rec in self:
            rec.srf_count = len(rec.srf_ids)

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

    def action_view_srfs(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('lerm_civil.srf_form_id')
        action['domain'] = [('sale_order_id', '=', self.id)]
        return action

    def action_open_srf_wizard(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'lerm_civil_sale.action_sale_order_srf_wizard')
        action['context'] = {
            'default_sale_order_id': self.id,
        }
        return action
