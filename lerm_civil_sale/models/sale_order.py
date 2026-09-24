# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleOrderLermCivilSale(models.Model):
    _inherit = 'sale.order'

    srf_id = fields.Many2one(
        'lerm.civil.srf',
        string='SRF',
        readonly=True,
        copy=False,
        help='SRF generated from this sales order.',
    )

    @api.model
    def _lerm_pricelist_validation_enabled(self):
        """Return True when the LERM Civil Sale pricelist validations are enabled.

        Configured from Settings > LERM CIVIL > Pricelist Validation (disabled
        by default).
        """
        value = self.env['ir.config_parameter'].sudo().get_param(
            'lerm_civil_sale.pricelist_validation', 'False')
        return str(value).lower() in ('1', 'true', 'yes', 'on')

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
        if self._lerm_pricelist_validation_enabled():
            if not pricelist:
                raise ValidationError(_(
                    'No pricelist is attached to customer %s. Please set a pricelist '
                    'on the customer contact first.') % (partner.name or ''))
            if self._lerm_is_default_pricelist(pricelist):
                raise ValidationError(_(
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

    def _lerm_get_srf(self):
        """Return the SRF action (existing one if already generated)."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'lerm_civil.srf_form_id')
        action['res_id'] = self.srf_id.id
        action['view_mode'] = 'form'
        action['views'] = [(False, 'form')]
        action['target'] = 'current'
        return action

    def action_view_srf(self):
        """Open the SRF generated from this sales order."""
        return self._lerm_get_srf()

    def action_create_srf(self):
        """Create an SRF (draft) from this confirmed sales order.

        One SRF is created per sales order; all sales order lines sharing the
        same product are merged into a single sample (with the combined
        parameter selection) under that SRF.
        """
        self.ensure_one()
        if self.state != 'sale':
            raise UserError(_(
                'An SRF can only be created from a sales order in the '
                '"Sales Order" state.'))
        if self.srf_id:
            return self._lerm_get_srf()

        srf_vals = {
            'billing_customer': self.partner_id.id or False,
            'srf_date': fields.Date.context_today(self),
            'client_refrence': self.name,
            'sale_order_id': self.id,
        }
        srf = self.env['lerm.civil.srf'].create(srf_vals)

        for product in self.order_line.product_tmpl_id:
            if not product:
                continue

            lines = self.order_line.filtered(
                lambda l: l.product_tmpl_id == product)
            parameters = lines.mapped('parameters')

            group = product.group
            group_id = group.id if len(group) == 1 else False
            grade = product.grade_table
            grade_id = grade.id if len(grade) == 1 else False
            size = product.size_table
            size_id = size.id if len(size) == 1 else False

            sample_vals = {
                'srf_id': srf.id,
                'customer_id': self.partner_id.id or False,
                'discipline_id': product.discipline.id or False,
                'group_id': group_id,
                'material_id': product.id,
                'grade_id': grade_id,
                'size_id': size_id,
                'parameters': [(6, 0, parameters.ids)],
                'sample_qty': 1,
            }

            sample_range = self.env['sample.range.line'].create(dict(
                sample_vals,
                srf_id=srf.id,
            ))
            self.env['lerm.srf.sample'].create(dict(
                sample_vals,
                sample_range_id=sample_range.id,
            ))

        self.write({'srf_id': srf.id})

        srf.message_post(body=_(
            'SRF created from Sales Order %s.') % self.name)
        self.message_post(body=_(
            'SRF %s created from this Sales Order.')
            % (srf.srf_id or srf.display_name))

        return self._lerm_get_srf()
