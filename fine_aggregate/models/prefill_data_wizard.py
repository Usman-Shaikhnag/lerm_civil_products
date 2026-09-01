from odoo import api, fields, models
from odoo.exceptions import UserError




class FinePrefillWizard(models.TransientModel):
    _name = 'fine.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active fine record
        current_product = self.env['mechanical.fine.aggregate'].sudo().browse(self._context['active_id'])

        # Fetch previous fine  record for selected sample
        copy_product = self.env['mechanical.fine.aggregate'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous GGBS record.")

        # List of direct fields to copy
        normal_fields = [
            'temp_specific',
            'wt_sample_finer75','wt_dry_sample_finer75','humidity_finer75_visible',
            'temp_finer75_visible','temp_sieve_analysis',
            'humidity_sieve_analysis','temp_specific_gravity_water_absorption',
            'humidity_temp_specific_gravity_water_absorption','wt_sample_inwater',
            'wt_surface_dry','oven_dried_wt','wt_oven_dry_d','wt_surface_dry_2',
            'wt_sample_inwater_2','oven_dried_wt_2','wt_oven_dry_d_2','specific_gravity',
            'temp_density','humidity_density','capacity_of_cylinderr',
            'wtt_of_empty_cylinder_compacted','wtt_cylinder_aggregate_compacted',
            'temp_density','humidity_density','capacity_of_cylinder_loose','wtt_of_empty_cylinder_loose',
            'wtt_cylinder_aggregate_loose', 'temp_density','humidity_density',
            'specific_gravity_voids','soudness_child_lines','temp_soudness','humidity_soudness',
            'wt_of_sample','sieve_analysis_soundness_lines','total_percent_retained',
            'ouantitative_soundness_lines','quantitative_soundness_lines',

        ]

        one2many_fields = [
            'sieve_analysis_child_lines',
            'soudness_child_lines',
            'sieve_analysis_soundness_lines',
            'ouantitative_soundness_lines',
            'quantitative_soundness_lines',
        ]

        update_vals = {}

        # Copy simple fields
        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        # Copy one2many fields
        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, line.copy_data()[0]) for line in lines]

        # Check visibility and remove fields if not visible
        if not current_product.sieve_visible:
            update_vals.pop('sieve_analysis_child_lines', None)

        if not current_product.soudness_visible:
            update_vals.pop('soudness_child_lines', None)

        if not current_product.soudness_visible:
            update_vals.pop('sieve_analysis_soundness_lines', None)

        if not current_product.soudness_visible:
            update_vals.pop('ouantitative_soundness_lines', None)
        
        if not current_product.soudness_visible:
            update_vals.pop('quantitative_soundness_lines', None)



        # Apply copied data to current GGBS record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
