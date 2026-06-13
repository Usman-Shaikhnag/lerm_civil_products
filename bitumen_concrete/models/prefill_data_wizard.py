from odoo import api, fields, models
from odoo.exceptions import UserError



class BitumenConcretePrefillWizard(models.TransientModel):
    _name = 'mechanical.bitumen.concrete.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.bitumen.concrete'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.bitumen.concrete'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'location',
            'location_heding',

            'wt_of_samplew1',
            'wt_of_intial',
            'wt_of_aggregate',
            'wt_of_extraction',
            'wt_of_filter',

            'wt_of_sample',

           
            

        ]

        one2many_fields = [
            'specific_gravity_lines',

            'flash_and_fire_lines',
            'softining_point_lines',
            # 'soundness_cement_lines',
            'penetration_lines',
            'sieve_analysis_child_lines',
         
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.specific_gravity_visible:
            update_vals.pop('specific_gravity_lines', None)

        if not current_product.flash_and_fire_visible:
            update_vals.pop('flash_and_fire_lines', None)

        if not current_product.softining_point_visible:
            update_vals.pop('softining_point_lines', None)

        if not current_product.penetration_visible:
            update_vals.pop('penetration_lines', None)

        if not current_product.sieve_visible:
            update_vals.pop('sieve_analysis_child_lines', None)

       
        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
