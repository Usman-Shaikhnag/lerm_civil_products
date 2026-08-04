from odoo import api, fields, models
from odoo.exceptions import UserError



class RcptPrefillWizard(models.TransientModel):
    _name = 'rcpt.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.rcpt'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.rcpt'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'date_of_testing',
            'temp_conc_surface',
            'temp_around_specimen',
            'date_conditioning',
            'current_apply',
            'int_temp_naoh',
            'int_temp_nacl',
            'date_specimen_prepared',
            'date_conditioning_started',
            'date_vaccum_started',
            'date_water_added',
            'date_vaccum_turn_of',
            'date_soaking_started',
            'date_soaking_completed'

        ]

        one2many_fields = [
            'child_lines'
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
