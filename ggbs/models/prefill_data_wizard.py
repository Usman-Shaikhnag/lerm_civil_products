from odoo import api, fields, models
from odoo.exceptions import UserError



class GGBSPrefillWizard(models.TransientModel):
    _name = 'mechanical.ggbs.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.ggbs'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.ggbs'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'wt_of_cement_trial1',
            'wt_of_ggbs_trial1',
            'wt_water_req',
            'penetration_vicat',
            'temp_normal_cement',
            'humidity_normal_cement',
            'start_date_normal_cement',
            'end_date_normal_cement',
            'wt_cement',
            'wt_water_req_cement',
            'penetration_vicat_cement',
            'wt_of_ggbs_sg_trial1',
            'wt_of_ggbs_sg_trial2'



            'initial_volume_kerosine_trial1',
            'initial_volume_kerosine_trial2',
            'final_volume_kerosine_trial1',
            'final_volume_kerosine_trial2',
            'wt_of_cement_slag',
            'wt_of_ggbs_slag',
            'wt_of_standard_sand_grade1',
            'wt_of_standard_sand_grade2',

            'wt_of_cement_slag_opc',
            'wt_of_standard_sand_grade1_opc',
            'wt_of_standard_sand_grade2_opc',
            'wt_of_standard_sand_grade3_opc',


             'fineness_temp',
            'weight_of_mercury_before_trial1',
            'weight_of_mercury_before_trial2',
            'weight_of_mercury_after_trail1',
            'weight_of_mercury_after_trail2',
            'density_of_mercury',
            'time_fineness_trial1',
            'time_fineness_trial2',

            # tt
            'time_fineness_trial3',
            'specific_surface_of_reference_sample',
            'air_viscosity_of_three_temp',
            'density_of_reference_sample',




               'time_sample_trial1',
            'time_sample_trial2',
            'time_sample_trial3',
            'temp_fineness_calculated_trial1',
            'temp_fineness_calculated_trial2',
            'temp_fineness_calculated_trial3',
            'temp_percent_setting',
            'humidity_percent_setting',

            # tt
            'start_date_setting',
            'end_date_setting',
            
        ]

        one2many_fields = [
            'slag_7days_table',
            'slag_28days_table',
            'slag_7days_table_opc',
            # 'soundness_cement_lines',
            'slag_28days_table_opc',


            'intial_time_lines',
            'final_time_lines',
            'moisture_content_child_lines',
            'soundness_child_lines',
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.slag_activity_7_visible:
            update_vals.pop('slag_7days_table', None)

        if not current_product.slag_activity_28_visible:
            update_vals.pop('slag_28days_table', None)

        if not current_product.slag_activity_7_visible:
            update_vals.pop('slag_7days_table_opc', None)

        if not current_product.slag_activity_28_visible:
            update_vals.pop('slag_28days_table_opc', None)




        if not current_product.initial_setting_time_visible:
            update_vals.pop('intial_time_lines', None)

        if not current_product.final_setting_time_visible:
            update_vals.pop('final_time_lines', None)

        # if not current_product.soundness_cement_visible:
        #     update_vals.pop('soundness_cement_lines', None)

        if not current_product.moisture_content_visible:
            update_vals.pop('moisture_content_child_lines', None)

        if not current_product.soundness_visible:
            update_vals.pop('soundness_child_lines', None)
        
        

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
