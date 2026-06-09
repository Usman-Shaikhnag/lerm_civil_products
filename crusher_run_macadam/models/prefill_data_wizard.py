# from odoo import api, fields, models
# from odoo.exceptions import UserError



# class CoarseAggregatePrefillWizard(models.TransientModel):
#     _name = 'coarse.aggregate.prefill.data'
#     _description = 'Prefill Data'

#     product_id = fields.Many2one('product.template',string="Product")
#     sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


#     def prefill_data(self):
#         current_product = self.env['mechanical.coarse.aggregate'].sudo().browse(self._context['active_id'])
#         copy_product = self.env['mechanical.coarse.aggregate'].sudo().search([
#             ('eln_ref.sample_id.id', '=', self.sample_id.id)
#         ], limit=1)

#         normal_fields = [
#             'total_weight_sample_abrasion',
#             'weight_passing_sample_abrasion',
#             'wt_surface_dry',
#             'wt_sample_inwater',
#             'oven_dried_wt',
#             'wt_surface_dry_2',
#             'wt_sample_inwater_2',
#             'oven_dried_wt_2',
#             'wt_sample_10fine',
#             'wt_sample_passing_10fine',
#             'load_applied_10fine',
#             'wt_sample_finer75',
#             'wt_dry_sample_finer75',
#             'wt_sample_clay_lumps',
#             'wt_dry_sample_clay_lumps',
#             'wt_sample_light_weight',
#             'wt_dry_sample_light_weight',
#             'volume_of_bucket_loose',
#             'weight_empty_bucket_loose',
#             'sample_plus_bucket_loose',
#             'sample_plus_bucket_rodded',
#             'weight_of_sample',
#             'mean_wt_aggregate',
#             'wt_water_required_angularity',
#             'specific_gravity_aggregate_angularity',
#             'wt_of_compact',
#             'weight_empty_cylender',
#             'volume_of_cylender',
#             'volume_of_cylender1',
#             'weight_empty_cylender1',
#             'wt_of_compact1',
#             'specific_gravity2',
#             'specific_gravity3',
#             'wt_of_loose',
#             'wt_of_loose1',
#             'specific_gravity4',
#             'specific_gravity5'

#         ]

#         one2many_fields = [
#             'crushing_value_child_lines',
#             'impact_value_child_lines',
#             'soundness_na2so4_child_lines',
#             'soundness_mgso4_child_lines',
#             'elongation_table',
#             'sieve_analysis_child_lines',
#             'aggregate_grading_child_lines'
#         ]

#         update_vals = {}

#         for field in normal_fields:
#             if hasattr(copy_product, field):
#                 update_vals[field] = getattr(copy_product, field)

#         for field in one2many_fields:
#             lines = getattr(copy_product, field)
#             if lines:
#                 update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

#         if not current_product.crushing_visible:
#             update_vals.pop('crushing_value_child_lines', None)

#         if not current_product.impact_visible:
#             update_vals.pop('impact_value_child_lines', None)

#         if not current_product.soundness_na2so4_visible:
#             update_vals.pop('soundness_na2so4_child_lines', None)

#         if not current_product.soundness_mgso4_visible:
#             update_vals.pop('soundness_mgso4_child_lines', None)

#         if not current_product.elongation_visible:
#             update_vals.pop('elongation_table', None)

#         if not current_product.sieve_visible:
#             update_vals.pop('sieve_analysis_child_lines', None)

#         if not current_product.aggregate_grading_visible:
#             update_vals.pop('aggregate_grading_child_lines', None)


#         if update_vals:
#             current_product.sudo().write(update_vals)

#         return {'type': 'ir.actions.act_window_close'}
