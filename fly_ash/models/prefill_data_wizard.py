from odoo import api, fields, models
from odoo.exceptions import UserError



class FlyAshPrefillWizard(models.TransientModel):
    _name = 'mechanical.flyasch.normalconsistency.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.flyasch.normalconsistency'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.flyasch.normalconsistency'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'start_date_normal',
            'end_date_normal',
            'gravity_of_flyash1',
            'gravity_of_cement1',
            'wt_of_cement_1',
            'wt_of_water_required_fly_1',
            'penetration_planger_fly_1',
            'temp_percent_setting',
            'humidity_percent_setting',
            'start_date_setting',
            'end_date_setting',
            'wt_of_fly_settingg_time',
            'time_water_added',
            'time_needle_fails',
            'time_needle_make_impression',
            'temp_percent_retained',
            'humidity_percent_retained',
            'start_date_retained',
            'end_date_retained',
            'temp_percent_soundness',
            'humidity_percent_soundness',
            'start_date_soundness',
            'end_date_soundness',
            'wt_of_cement_soundness',
            'temp_percent_specific',
            'humidity_percent_specific',
            'start_date_specific',
            'end_date_specific',
            'wt_of_flyash_specific1',
            'wt_of_flyash_specific2',
            'intial_volume_specific1',
            'intial_volume_specific2',
            'final_volume_specific1',
            'final_volume_specific2',
            'temp_percent_compressive',

            'humidity_percent_compressive',
            'start_date_compressive',
            'end_date_compressive',
            'wt_of_cement_comp',
            'wt_of_standerd_comp1',
            'wt_of_standerd_comp2',
            'wt_of_standerd_comp3',
            'quantity_water',
            'measured_value1',
            'measured_value2',
            'measured_value3',
            'measured_value4',
            'casting_date_28days',
            'status_28days',
            'wt_of_cement_fly',
            'wt_of_standared_grade1',
            'wt_of_standared_grade2',
            'wt_of_standared_grade3',
            'quantity_water_flyash',
            'measured_values1',
            'measured_values2',
            'measured_values3',
            'measured_values4',
            'casting_dates_28days',
            'testing_dates_28days',
            'temp_percent_lime',
            'humidity_percent_lime',
            'start_date_lime',
            'end_date_lime',
            'wt_of_hydrent',
            'wt_of_standard_grade_lime1',
            'wt_of_standard_grade_lime2',
            'wt_of_standard_grade_lime3',
            'quantity_water_lime',
            'measured_valuess1',
            'measured_valuess2',
            'measured_valuess3',
            'measured_valuess4',
            'casting_dates_28dayss',
            'temp_percent_fineness',
            'humidity_percent_fineness',
            'start_date_fineness',
            'end_date_fineness',
            'weight_of_mercury_before_trial1',
            'weight_of_mercury_before_trial2',
            'weight_of_mercury_after_trail1',
            'weight_of_mercury_after_trail2',
            'density_of_mercury',
            'ss'

        ]

        one2many_fields = [
            'particles_retained_table',
            'soundness_table',
            'casting_28_days_tables',
            'casting_28_dayss_tables',
            'casting_28_dayss_tabless'
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.soundness_visible:
            update_vals.pop('soundness_table', None)

        if not current_product.particles_retained_visible:
            update_vals.pop('particles_retained_table', None)


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
