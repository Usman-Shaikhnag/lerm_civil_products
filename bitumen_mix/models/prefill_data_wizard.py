from odoo import api, fields, models
from odoo.exceptions import UserError


class BitumenMixPrefillWizard(models.TransientModel):
    _name = 'bitumen.mix.aggregate.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active Bitumen Mix record
        current_product = self.env['mechanical.bitumen.mix'].sudo().browse(self._context['active_id'])

        # Fetch previous Bitumen Mix record for selected sample
        copy_product = self.env['mechanical.bitumen.mix'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous Bitumen Mix record.")

        # List of direct fields to copy
        normal_fields = [
            'location' , 'location_heding' , 'wt_of_samplew1' , 'wt_of_intial' ,  'wt_of_aggregate' , 'wt_of_extraction' ,  'wt_of_sample' ,  
        ]

        one2many_fields = [
            'sieve_analysis_child_lines',

        ]

        update_vals = {}

        # Copy simple fields
        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        # Copy one2many fields
        # for field in one2many_fields:
        #     lines = getattr(copy_product, field)
        #     if lines:
        #         update_vals[field] = [(0, 0, line.copy_data()[0]) for line in lines]

        for field in one2many_fields:
             lines = getattr(copy_product, field)
             if lines:
               update_vals[field] = [(5, 0, 0)]  # clear
               update_vals[field] += [(0, 0, line.copy_data()[0]) for line in lines]

        # Check visibility and remove fields if not visible
        if not current_product.sieve_visible:
            update_vals.pop('sieve_analysis_child_lines', None)


        # Apply copied data to current GGBS record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}