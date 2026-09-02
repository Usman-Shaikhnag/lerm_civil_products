from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import _
from odoo.osv.expression import AND
from collections import OrderedDict

class LermSrfSample(models.Model):
    _inherit = 'lerm.srf.sample'

    billing_customer = fields.Many2one('res.partner', related='srf_id.billing_customer', string="Billing Customer", store=True)

    invoice_status = fields.Selection([
        ('1-uninvoiced', 'Uninvoiced'),
        ('2-draft', 'Draft'),
        ('3-invoiced', 'Invoiced'),
        ('4-partially_paid', 'Partially Paid'),
        ('5-paid', 'Paid'),
    ], string='Invoice Status', compute='_compute_invoice_status', store=True)

    @api.depends('invoice_number', 'invoice_number.state', 'invoice_number.invoice_payment_term_id', 'invoice_number.amount_residual', 'invoice_number.amount_total')
    def _compute_invoice_status(self):
        for rec in self:
            inv = rec.invoice_number
            if not inv or not inv.id or inv.state == 'cancel':
                rec.invoice_status = '1-uninvoiced'
            elif inv.state == 'draft':
                rec.invoice_status = '2-draft'
            elif inv.state == 'posted':
                if inv.amount_residual == 0:
                    rec.invoice_status = '5-paid'
                elif inv.amount_residual < inv.amount_total:
                    rec.invoice_status = '4-partially_paid'
                else:
                    rec.invoice_status = '3-invoiced'
            else:
                rec.invoice_status = '1-uninvoiced'

    @api.model
    def _search_panel_domain_image(self, field_name, domain, set_count=False, limit=False):
        if field_name == 'invoice_status':
            try:
                return super()._search_panel_domain_image(field_name, domain, set_count, limit)
            except KeyError:
                field = self._fields[field_name]
                desc = self.fields_get([field_name])[field_name]
                field_name_selection = dict(desc['selection'])
                full_domain = AND([domain, [(field_name, '!=', False)]])
                groups = self.read_group(full_domain, [field_name], [field_name], limit=limit)
                domain_image = OrderedDict()
                for group in groups:
                    value = group[field_name]
                    display_name = field_name_selection.get(value, value)
                    values = {'id': value, 'display_name': display_name}
                    if set_count:
                        values['__count'] = group[field_name + '_count']
                    domain_image[value] = values
                return domain_image
        return super()._search_panel_domain_image(field_name, domain, set_count, limit)

    def action_open_invoice(self):
        self.ensure_one()
        if not self.invoice_number:
            raise ValidationError(_("No invoice linked to this sample."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_number.id,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'target': 'current',
        }
