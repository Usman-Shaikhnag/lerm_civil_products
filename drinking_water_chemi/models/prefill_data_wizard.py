from odoo import api, fields, models
from odoo.exceptions import UserError



class DrinkingWaterPrefillWizard(models.TransientModel):
    _name = 'chemical.drinking.water.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['chemical.drinking.water'].sudo().browse(self._context['active_id'])
        copy_product = self.env['chemical.drinking.water'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'ph_1_percent_a',
            'ph_1_percent_b',
            'ph_1_percent_c',
            'ph_1_percent_d',
            'ph_1_percent_e',

            'conductivity_1',
            'conductivity_2',
            'conductivity_3',

            'conductivity_4',
            'conductivity_5',


            'sample_taken1',
            'sample_taken2',
            'sample_taken3',
            'sample_taken4',
            'sample_taken5',

            'initial_dish1',
            'initial_dish2',
            'initial_dish3',
            'initial_dish4',
            'initial_dish5',


            'final_dish1',
            'final_dish2',
            'final_dish3',
            'final_dish4',
            'final_dish5',


            'mass_residue1',
            'mass_residue2',
            'mass_residue3',
            'mass_residue4',
            'mass_residue5',


            'turbidity_1',
            'turbidity_2',
            'turbidity_3',
            'turbidity_4',
            'turbidity_5',


            'chloride_sample_taken1',
            'chloride_sample_taken2',
            'chloride_sample_taken3',
            'chloride_sample_taken4',
            'chloride_sample_taken5',
            

            'chloride_normality1',
            'chloride_normality2',
            'chloride_normality3',
            'chloride_normality4',
            'chloride_normality5',

            'chloride_nitratev2_1',
            'chloride_nitratev2_2',
            'chloride_nitratev2_3',
            'chloride_nitratev2_4',
            'chloride_nitratev2_5',



            'chloride_nitratev1_1',
            'chloride_nitratev1_2',
            'chloride_nitratev1_3',
            'chloride_nitratev1_4',
            'chloride_nitratev1_5',



            'cf',

            'hardness_sample_takenv3_1',
             'hardness_sample_takenv3_2',
            'hardness_sample_takenv3_3',
            'hardness_sample_takenv3_4',
            'hardness_sample_takenv3_5',


            'hardness_titrationv2_1',
            'hardness_titrationv2_2',
            'hardness_titrationv2_3',
            'hardness_titrationv2_4',
            'hardness_titrationv2_5',


            'hardness_titrationv1_1',
            'hardness_titrationv1_2',
            'hardness_titrationv1_3',
            'hardness_titrationv1_4',
            'hardness_titrationv1_5',


             'hardness1',
            'hardness2',
            'hardness3',
            'hardness4',
            'hardness5',

            'alkalinity_sample_takenv3_1',
            'alkalinity_sample_takenv3_2',
            'alkalinity_sample_takenv3_3',
            'alkalinity_sample_takenv3_4',
            'alkalinity_sample_takenv3_5',

            'alkalinity_titrationx1_1',
            'alkalinity_titrationx1_2',
            'alkalinity_titrationx1_3',
            'alkalinity_titrationx1_4',
            'alkalinity_titrationx1_5',


            'alkalinity_normality_1',
            'alkalinity_normality_2',
            'alkalinity_normality_3',
            'alkalinity_normality_4',
            'alkalinity_normality_5',


            'calcium_sample_takenv_1',
            'calcium_sample_takenv_2',
            'calcium_sample_takenv_3',
            'calcium_sample_takenv_4',
            'calcium_sample_takenv_5',

            'calcium_titrationv1_1',
            'calcium_titrationv1_2',
            'calcium_titrationv1_3',
            'calcium_titrationv1_4',
            'calcium_titrationv1_5',

            'cf_magnesium',

            'magnesium_sample_taken_1',
            'magnesium_sample_taken_2',
            'magnesium_sample_taken_3',
            'magnesium_sample_taken_4',
            'magnesium_sample_taken_5',

            'magnesium_calcium_titre_1',
            'magnesium_calcium_titre_2',
            'magnesium_calcium_titre_3',
            'magnesium_calcium_titre_4',
            'magnesium_calcium_titre_5',

            'magnesium_th_1',
            'magnesium_th_2',
            'magnesium_th_3',
            'magnesium_th_4',
            'magnesium_th_5',

            'sulphate_1',
            'sulphate_2',
            'sulphate_3',
            'sulphate_4',
            'sulphate_5',

            'nitrate_1',
            'nitrate_2',
            'nitrate_3',
            'nitrate_4',
            'nitrate_5',

            'silica_1',
            'silica_2',
            'silica_3',
            'silica_4',
            'silica_5',

            'phosphorus_1',
            'phosphorus_2',
            'phosphorus_3',
            'phosphorus_4',
            'phosphorus_5',

            'sodium_1',
            'sodium_2',
            'sodium_3',
            'sodium_4',
            'sodium_5',

             'potassium_1',
            'potassium_2',
            'potassium_3',
            'potassium_4',
            'potassium_5',
          

         

        ]

        one2many_fields = [
            # 'chequered_tiles_cement_lines',
            # 'chequered_cement_water_absorption_lines',
            # 'chequeredwet_cement_transver_lines',
         
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        # if not current_product.chequered_tiles_cement_visible:
        #     update_vals.pop('chequered_tiles_cement_lines', None)

        # if not current_product.chequered_cement_water_absorption_visible:
        #     update_vals.pop('chequered_cement_water_absorption_lines', None)

        # if not current_product.chequeredwet_cement_transver_visible:
        #     update_vals.pop('chequeredwet_cement_transver_lines', None)

        

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
