from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class BulkInvoiceWizardLine(models.TransientModel):
    _name = 'bulk.invoice.wizard.line'

    wizard_id = fields.Many2one('bulk.invoice.wizard', string='Wizard')
    sample_id = fields.Many2one('lerm.srf.sample', string='Sample')
    kes_no = fields.Char(string='UID', readonly=True)
    material_id = fields.Many2one('product.template', string='Material', readonly=True)
    pricing_preview = fields.Char(string='Parameter Pricing', readonly=True)
    has_fallback = fields.Boolean(string='Has Fallback', default=False)
    total_price = fields.Float(string='Price', readonly=True)


class BulkInvoiceWizard(models.TransientModel):
    _name = 'bulk.invoice.wizard'
    _description = 'Bulk Invoice Generation Wizard'

    active_sample_ids = fields.Text(string='Selected Sample IDs', readonly=True)
    billing_customer = fields.Many2one('res.partner', string='Billing Customer', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', readonly=True)
    line_ids = fields.One2many('bulk.invoice.wizard.line', 'wizard_id', string='Invoice Lines')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount')
    has_fallback_pricing = fields.Boolean(string='Has Fallback Pricing', compute='_compute_has_fallback')
    fallback_warning_message = fields.Text(string='Warning', compute='_compute_fallback_warning')

    @api.depends('line_ids.total_price')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('total_price'))

    @api.depends('line_ids.has_fallback')
    def _compute_has_fallback(self):
        for rec in self:
            rec.has_fallback_pricing = any(rec.line_ids.mapped('has_fallback'))

    @api.depends('line_ids')
    def _compute_fallback_warning(self):
        for rec in self:
            if not rec.has_fallback_pricing:
                rec.fallback_warning_message = ''
                continue
            fallback_lines = rec.line_ids.filtered('has_fallback')
            msgs = ['%s: %s' % (l.kes_no, l.pricing_preview) for l in fallback_lines]
            rec.fallback_warning_message = (
                'Some parameters have no per-parameter pricelist entry. '
                'Using product-level pricelist price or default price:\n' +
                '\n'.join('\u2022 ' + m for m in msgs)
            )

    def _populate_lines(self, samples):
        self.line_ids.unlink()
        PricelistItem = self.env['product.pricelist.item'].sudo()
        pricelist = self.pricelist_id
        for sample in samples:
            total = 0.0
            has_fallback = False
            pricing_parts = []
            product = sample.material_id.product_variant_id if sample.material_id else False

            if product and sample.parameters:
                pt_id = product.product_tmpl_id.id
                param_count = len(sample.material_id.parameter_table1) or 1
                pl_items = PricelistItem.search([
                    ('pricelist_id', '=', pricelist.id if pricelist else False),
                    ('parameter_id', '!=', False),
                    '|',
                    ('product_tmpl_id', '=', pt_id),
                    ('applied_on', '=', '3_global'),
                ]) if pricelist else PricelistItem

                pl_product_items = PricelistItem.search([
                    ('pricelist_id', '=', pricelist.id if pricelist else False),
                    ('parameter_id', '=', False),
                    '|',
                    ('product_tmpl_id', '=', pt_id),
                    ('applied_on', '=', '3_global'),
                ]) if pricelist else PricelistItem

                for param in sample.parameters:
                    matching = pl_items.filtered(lambda i: i.parameter_id.id == param.id) if pricelist else PricelistItem
                    if matching:
                        price = matching[0].fixed_price
                        tag = ''
                    else:
                        prod_match = pl_product_items[:1] if pricelist else PricelistItem
                        if prod_match and prod_match.fixed_price:
                            price = prod_match.fixed_price
                            tag = ' (product price)'
                            has_fallback = True
                        else:
                            price = product.list_price / param_count if product.list_price else 0.0
                            tag = ' (default)'
                            has_fallback = True
                    total += price
                    pricing_parts.append('%s: \u20b9%.2f%s' % (param.parameter_name or param.name, price, tag))

            self.env['bulk.invoice.wizard.line'].create({
                'wizard_id': self.id,
                'sample_id': sample.id,
                'kes_no': sample.kes_no,
                'material_id': sample.material_id.id,
                'pricing_preview': ', '.join(pricing_parts),
                'has_fallback': has_fallback,
                'total_price': total,
            })

    @api.model
    def open_wizard(self):
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise UserError('Please select at least one sample.')
        samples = self.env['lerm.srf.sample'].browse(active_ids)
        billing_customer = False
        pricelist = False
        billing_customers = samples.mapped('billing_customer').filtered(lambda c: c.id)
        if billing_customers:
            first_customer = billing_customers[0]
            billing_customer = first_customer.id
            pricelist = first_customer.property_product_pricelist.id if first_customer.property_product_pricelist else False

        wizard = self.create({
            'active_sample_ids': ','.join(str(id) for id in active_ids),
            'billing_customer': billing_customer,
            'pricelist_id': pricelist,
        })
        wizard._populate_lines(samples)
        return {
            'name': 'Generate Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.invoice.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generate_invoice(self):
        self.ensure_one()
        sample_ids = [int(x) for x in self.active_sample_ids.split(',') if x]
        samples = self.env['lerm.srf.sample'].sudo().browse(sample_ids)
        samples.invalidate_recordset(['invoice_status', 'invoice_number'])

        already_invoiced = samples.filtered(
            lambda s: s.invoice_status not in ('1-uninvoiced',)
        )
        if already_invoiced:
            kes_list = ', '.join(already_invoiced.mapped('kes_no'))
            raise UserError(
                'The following samples have already been invoiced: %s. '
                'Please remove them from the selection and try again.' % kes_list
            )

        billing_customers = samples.mapped('billing_customer').filtered(lambda c: c.id)
        if not billing_customers:
            raise UserError('No Billing Customer found on the selected samples.')
        if len(billing_customers) > 1:
            customer_names = ', '.join(billing_customers.mapped('name'))
            raise UserError(
                'Invoices can only be generated for a single Billing Customer at a time. '
                'The selected records belong to different Billing Customers: %s.' % customer_names
            )
        billing_customer = billing_customers[0]

        pricelist = billing_customer.property_product_pricelist
        if not pricelist:
            raise UserError(
                'No Pricelist is configured for Billing Customer "%s". '
                'Please set a Pricelist on the customer before generating invoices.'
                % billing_customer.name
            )

        samples_by_material = {}
        for sample in samples:
            mat = sample.material_id
            if mat not in samples_by_material:
                samples_by_material[mat] = self.env['lerm.srf.sample']
            samples_by_material[mat] |= sample

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': billing_customer.id,
            'pricelist_id': pricelist.id,
            'invoice_user_id': billing_customer.user_id.id if billing_customer.user_id else self.env.user.id,
            'state': 'draft',
            'invoice_line_ids': [],
        }

        for material, mat_samples in samples_by_material.items():
            product = material.product_variant_id
            if not product:
                continue
            all_params = mat_samples.mapped('parameters')
            unique_params = all_params
            invoice_line_vals = {
                'product_id': product.id,
                'quantity': len(mat_samples),
                'report_no1': [(6, 0, mat_samples.ids)],
                'parameters': [(6, 0, unique_params.ids)],
                'name': material.name,
            }
            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        invoice = self.env['account.move'].create(invoice_vals)
        invoice.button_update_prices_from_pricelist()

        samples.write({
            'invoice_number': invoice.id,
        })
        samples._compute_invoice_status()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'target': 'current',
        }
