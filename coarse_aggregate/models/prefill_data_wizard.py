from odoo import api, fields, models
from odoo.exceptions import UserError


class CoarseAggregatePrefillWizard(models.TransientModel):
    _name = 'coarse.aggregate.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active Coarse Aggregate record
        current_product = self.env['mechanical.coarse.aggregate'].sudo().browse(self._context['active_id'])

        # Fetch previous Coarse Aggregate record for selected sample
        copy_product = self.env['mechanical.coarse.aggregate'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous Coarse Aggregate record.")

        # List of direct fields to copy
        normal_fields = [
            'humidity_crushing_value' , 'temp_crushing_value' , 'wt_of_empty_cylinder', 'wt_of_cylinder_aggregate' ,  'wt_of_aggregate_passing_sieve' , 'wt_of_empty_cylinder_2' , 'wt_of_cylinder_aggregate_2' ,  'wt_of_aggregate_passing_sieve_2' , 'temp_specific_water' , 'humidity_specific_water' , 'wt_basket_and_sample' , 'wt_empty_basket' , 'wt_surface_dry' , 'oven_dried_wt' , 'wt_basket_and_sample_2' , 'wt_empty_basket_2' , 'wt_surface_dry_2' , 'oven_dried_wt_2' , 'temp_impact_value' , 'humidity_impact_value' , 'wt_of_empty_cup' , 'wt_of_cup_aggregate' , 'wt_of_aggregate_passing' , 'wt_of_empty_cup_2' , 'wt_of_cup_aggregate_2' ,  'wt_of_aggregate_passing_2' , 'temp_fine_value' , 'humidity_fine_value' , 'wt_of_empty_cylinder_10fine' , 'wt_of_cylinder_aggregate_10fine' , 'wt_of_aggregate_passing_sieve_10fine' , 'load_for_penetration_kn' , 'wt_of_empty_cylinder_10fine_2' , 'wt_of_cylinder_aggregate_10fine_2' , 'wt_of_aggregate_passing_sieve_10fine_2' , 'load_for_penetration_kn_2' , 'temp_elongation' , 'humidity_elongation' , 'temp_flakiness' , 'humidity_flakiness' , 'temp_density' , 'humidity_density' , 'capacity_of_cylinderr' , 'wtt_of_empty_cylinder_compacted' , 'wtt_cylinder_aggregate_compacted' , 'capacity_of_cylinder_loose' , 'wtt_of_empty_cylinder_loose' , 'wtt_cylinder_aggregate_loose' , 'specific_gravity_voids' , 'temp_evaporation' , 'humidity_evaporation' , 'temp_abrasion_value' , 'humidity_abrasion_value' , 'wt_of_agg_ab' , 'wt_of_agg_retained_ab' ,  'wt_of_agg_ab_1' , 'wt_of_agg_retained_ab_1' , 'weight_of_sample', 'temp_sieve_analysis' , 'humidity_sieve_analysis' , 'temp_soudness' , 'humidity_soudness' , 'wt_of_sample' ,
        ]

        one2many_fields = [
            'elongation_table',
            'flakiness_table',
            'rate_of_evaporation_table',
            'abrasion_value_child_lines',
            'abrasion_value_child_lines_second',
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
        if not current_product.elongation_visible:
            update_vals.pop('elongation_table', None)

        if not current_product.flakiness_visible:
            update_vals.pop('flakiness_table', None)
        
        if not current_product.rate_of_evaporation_visible:
            update_vals.pop('rate_of_evaporation_table', None)

        if not current_product.abrasion_value_visible:
            update_vals.pop('abrasion_value_child_lines', None)

        if not current_product.abrasion_value_visible:
            update_vals.pop('abrasion_value_child_lines_second', None)

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