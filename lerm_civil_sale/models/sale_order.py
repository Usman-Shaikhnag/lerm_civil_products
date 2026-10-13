# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_normalize


class SaleOrderLermCivilSale(models.Model):
    _inherit = 'sale.order'

    srf_id = fields.Many2one(
        'lerm.civil.srf',
        string='SRF',
        readonly=True,
        copy=False,
        help='SRF generated from this sales order.',
    )

    # Not required so a quotation can be made for a temporary customer; the
    # rule is enforced by _check_lerm_temp_customer instead.
    partner_id = fields.Many2one(required=False)
    partner_invoice_id = fields.Many2one(required=False)
    partner_shipping_id = fields.Many2one(required=False)

    is_temp_customer = fields.Boolean(
        string='Temporary Customer',
        tracking=True,
        help='Quote a customer without creating a contact. The contact is '
             'created (or an existing one reused) when the quotation is '
             'confirmed.',
    )
    temp_customer_name = fields.Char(string='Customer Name')
    temp_customer_company_type = fields.Selection(
        [('person', 'Individual'), ('company', 'Company')],
        string='Customer Type',
        default='company',
    )
    temp_customer_email = fields.Char(string='Customer Email')
    temp_customer_phone = fields.Char(string='Customer Phone')
    temp_customer_street = fields.Char(string='Customer Street')
    temp_customer_street2 = fields.Char(string='Customer Street 2')
    temp_customer_city = fields.Char(string='Customer City')
    temp_customer_zip = fields.Char(string='Customer ZIP')
    temp_customer_state_id = fields.Many2one(
        'res.country.state',
        string='Customer State',
        domain="[('country_id', '=?', temp_customer_country_id)]",
    )
    temp_customer_country_id = fields.Many2one(
        'res.country',
        string='Customer Country',
        default=lambda self: self.env.company.country_id,
    )
    temp_customer_vat = fields.Char(string='Customer GSTIN')

    @api.constrains('partner_id', 'partner_invoice_id', 'partner_shipping_id',
                    'is_temp_customer', 'temp_customer_name', 'state')
    def _check_lerm_temp_customer(self):
        for order in self:
            if order.partner_id:
                if not (order.partner_invoice_id and order.partner_shipping_id):
                    raise ValidationError(_(
                        'Invoice and delivery addresses are required on %s.')
                        % order.name)
                continue
            if not order.is_temp_customer:
                raise ValidationError(_(
                    'Customer is required on %s. Select a customer or tick '
                    '"Temporary Customer".') % order.name)
            if not (order.temp_customer_name or '').strip():
                raise ValidationError(_(
                    'Customer name is required for the temporary customer '
                    'on %s.') % order.name)
            if order.state == 'sale':
                raise ValidationError(_(
                    'Sales order %s has no customer contact.') % order.name)

    @api.onchange('is_temp_customer')
    def _onchange_lerm_is_temp_customer(self):
        if self.is_temp_customer:
            self.partner_id = False

    @api.onchange('temp_customer_country_id')
    def _onchange_lerm_temp_customer_country_id(self):
        if self.temp_customer_country_id \
                and self.temp_customer_state_id.country_id != self.temp_customer_country_id:
            self.temp_customer_state_id = False

    def _lerm_temp_customer_orders(self):
        """Return the orders quoted to a temporary customer that has no
        contact yet."""
        return self.filtered(lambda o: o.is_temp_customer and not o.partner_id)

    def _lerm_temp_customer_virtual_partner(self):
        """Return an unsaved partner built from the temporary customer
        address, used to get the pricelist and fiscal position a real contact
        would get."""
        self.ensure_one()
        company = self.company_id
        country = self.temp_customer_country_id or company.country_id
        state = self.temp_customer_state_id
        if not state and country == company.country_id:
            state = company.state_id
        return self.env['res.partner'].with_company(company).new({
            'country_id': country.id,
            'state_id': state.id,
            'vat': self.temp_customer_vat,
        })

    @api.depends('is_temp_customer')
    def _compute_pricelist_id(self):
        super()._compute_pricelist_id()
        for order in self._lerm_temp_customer_orders():
            if order.state != 'draft' or order.pricelist_id:
                continue
            order.pricelist_id = \
                order._lerm_temp_customer_virtual_partner().property_product_pricelist

    @api.depends('is_temp_customer', 'temp_customer_state_id',
                 'temp_customer_country_id', 'temp_customer_vat')
    def _compute_fiscal_position_id(self):
        temp_orders = self._lerm_temp_customer_orders()
        super(SaleOrderLermCivilSale, self - temp_orders)._compute_fiscal_position_id()
        FiscalPosition = self.env['account.fiscal.position']
        for order in temp_orders:
            order.fiscal_position_id = FiscalPosition.with_company(
                order.company_id)._get_fiscal_position(
                order._lerm_temp_customer_virtual_partner())

    @api.depends('is_temp_customer', 'temp_customer_vat',
                 'temp_customer_country_id')
    def _compute_l10n_in_gst_treatment(self):
        super()._compute_l10n_in_gst_treatment()
        for order in self._lerm_temp_customer_orders():
            if order.country_code != 'IN':
                continue
            country = order.temp_customer_country_id
            if country and country.code != 'IN':
                order.l10n_in_gst_treatment = 'overseas'
            else:
                order.l10n_in_gst_treatment = \
                    'regular' if order.temp_customer_vat else 'consumer'

    def _lerm_find_temp_customer_partner(self):
        """Return (partner, matched_by) for an existing contact matching the
        temporary customer by GSTIN, then email, then phone."""
        self.ensure_one()
        Partner = self.env['res.partner']
        domain = [
            ('type', '=', 'contact'),
            ('company_id', 'in', (False, self.company_id.id)),
        ]
        vat = (self.temp_customer_vat or '').strip()
        email = email_normalize(self.temp_customer_email or '')
        phone = (self.temp_customer_phone or '').strip()
        checks = [
            (_('GSTIN'), vat and [('vat', '=ilike', vat)]),
            (_('email'), email and [('email_normalized', '=', email)]),
            (_('phone'), phone and ['|', ('phone', '=', phone), ('mobile', '=', phone)]),
        ]
        for matched_by, match_domain in checks:
            if not match_domain:
                continue
            partner = Partner.search(domain + match_domain, limit=1)
            if partner:
                return partner, matched_by
        return Partner, False

    def _lerm_prepare_temp_partner_vals(self):
        """Return the values of the contact created from the temporary
        customer."""
        self.ensure_one()
        return {
            'name': self.temp_customer_name.strip(),
            'is_company': self.temp_customer_company_type != 'person',
            'email': self.temp_customer_email,
            'phone': self.temp_customer_phone,
            'street': self.temp_customer_street,
            'street2': self.temp_customer_street2,
            'city': self.temp_customer_city,
            'zip': self.temp_customer_zip,
            'state_id': self.temp_customer_state_id.id,
            'country_id': self.temp_customer_country_id.id,
            'vat': (self.temp_customer_vat or '').strip().upper() or False,
            'customer_rank': 1,
            'user_id': self.user_id.id,
            'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
        }

    def _lerm_convert_temp_customer(self):
        """Create (or reuse) the contact of a temporary-customer quotation and
        set it as the customer, keeping the quoted pricelist, taxes and
        payment terms."""
        self.ensure_one()
        # Changing the customer recomputes these, which would re-price the
        # lines and change the taxes the customer was quoted.
        quoted_vals = {
            'pricelist_id': self.pricelist_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
            'l10n_in_gst_treatment': self.l10n_in_gst_treatment,
        }
        if self.payment_term_id:
            quoted_vals['payment_term_id'] = self.payment_term_id.id

        partner, matched_by = self._lerm_find_temp_customer_partner()
        if partner:
            body = _('Temporary customer linked to existing contact %s '
                     '(matched by %s).') % (partner.display_name, matched_by)
        else:
            partner = self.env['res.partner'].create(
                self._lerm_prepare_temp_partner_vals())
            body = _('Contact %s created from the temporary customer.') \
                % partner.display_name

        self.write(dict(quoted_vals, partner_id=partner.id))
        self.message_post(body=body)

    def action_confirm(self):
        for order in self._lerm_temp_customer_orders():
            order._lerm_convert_temp_customer()
        return super().action_confirm()

    def action_quotation_send(self):
        if self._lerm_temp_customer_orders():
            raise UserError(_(
                'A quotation for a temporary customer cannot be emailed, as '
                'the customer has no contact yet. Print the quotation instead, '
                'or confirm it to create the contact.'))
        return super().action_quotation_send()

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
        pricelist. The wizard can create and attach a new customer-specific
        pricelist when the customer has none (or uses the default one)."""
        self.ensure_one()
        pricelist = self._lerm_get_customer_pricelist()
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
