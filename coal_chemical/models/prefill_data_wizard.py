from odoo import api, fields, models
from odoo.exceptions import UserError



class CoalChemicalPrefillWizard(models.TransientModel):
    _name = 'chemical.coal.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['chemical.coal'].sudo().browse(self._context['active_id'])
        copy_product = self.env['chemical.coal'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'moisture_cruciblew1_1',
            'moisture_cruciblew1_2',
            'moisture_cruciblew1_3',
            'moisture_cruciblew1_4',
            'moisture_cruciblew1_5',

            'moisture_cruciblew2_1',
            'moisture_cruciblew2_2',
            'moisture_cruciblew2_3',
            'moisture_cruciblew2_4',
            'moisture_cruciblew2_5',


            'moisture_cruciblew3_1',
            'moisture_cruciblew3_2',
            'moisture_cruciblew3_3',
            'moisture_cruciblew3_4',
            'moisture_cruciblew3_5',


            'ash_dishw1_1',
            'ash_dishw1_2',
            'ash_dishw1_3',
            'ash_dishw1_4',
            'ash_dishw1_5',


            'ash_dishw2_1',
            'ash_dishw2_2',
            'ash_dishw2_3',
            'ash_dishw2_4',
            'ash_dishw2_5',


            'ash_dishw3_1',
            'ash_dishw3_2',
            'ash_dishw3_3',
            'ash_dishw3_4',
            'ash_dishw3_5',


            'ash_dishw4_1',
            'ash_dishw4_2',
            'ash_dishw4_3',
            'ash_dishw4_4',
            'ash_dishw4_5',

            'volatile_matter_cruciblew1_1',
            'volatile_matter_cruciblew1_2',
            'volatile_matter_cruciblew1_3',
            'volatile_matter_cruciblew1_4',
            'volatile_matter_cruciblew1_5',

            'volatile_matter_cruciblew2_1',
            'volatile_matter_cruciblew2_2',
            'volatile_matter_cruciblew2_3',
            'volatile_matter_cruciblew2_4',
            'volatile_matter_cruciblew2_5',


            'volatile_matter_cruciblew3_1',
            'volatile_matter_cruciblew3_2',
            'volatile_matter_cruciblew3_3',
            'volatile_matter_cruciblew3_4',
            'volatile_matter_cruciblew3_5',

            'volatile_matter_driedw4_1',
            'volatile_matter_driedw4_2',
            'volatile_matter_driedw4_3',
            'volatile_matter_driedw4_4',
            'volatile_matter_driedw4_5',


            'carbon_mosturem_1',
            'carbon_mosturem_2',
            'carbon_mosturem_3',
            'carbon_mosturem_4',
            'carbon_mosturem_5',

            'gross_calorific_w_1',
            'gross_calorific_w_2',
            'gross_calorific_w_3',
            'gross_calorific_w_4',
            'gross_calorific_w_5',

            'gross_calorific_t_1',
            'gross_calorific_t_2',
            'gross_calorific_t_3',
            'gross_calorific_t_4',
            'gross_calorific_t_5',

            'gross_calorific_e1_1',
            'gross_calorific_e1_2',
            'gross_calorific_e1_3',
            'gross_calorific_e1_4',
            'gross_calorific_e1_5',

            'gross_calorific_e2_1',
            'gross_calorific_e2_2',
            'gross_calorific_e2_3',
            'gross_calorific_e2_4',
            'gross_calorific_e2_5',

            'gross_calorific_weqv_1',
            'gross_calorific_weqv_2',
            'gross_calorific_weqv_3',
            'gross_calorific_weqv_4',
            'gross_calorific_weqv_5',

         
            

         

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
