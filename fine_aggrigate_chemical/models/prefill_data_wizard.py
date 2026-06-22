from odoo import api, fields, models
from odoo.exceptions import UserError



class FineChemicalPrefillWizard(models.TransientModel):
    _name = 'chemical.fine.aggregate.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['chemical.fine.aggregate'].sudo().browse(self._context['active_id'])
        copy_product = self.env['chemical.fine.aggregate'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'ph_1_percent_a',
            'ph_1_percent_b',
            'ph_1_percent_c',
            

            'wt_blank_crucible_after_ignition',
            'wt_blank_crucible_after_hf',

            'wt_crucible_after_ignition_a',
            'wt_crucible_after_hf_a',


            'wt_crucible_after_ignition_b',

            'wt_crucible_after_hf_b',
            'wt_crucible_after_ignition_c',
            'wt_crucible_after_hf_c',

            'blank_reading1',
            'blank_reading2',
            'blank_reading3',
            'burette_reading1',
            'burette_reading2',


            'burette_reading3',
            'normality1',
            'normality2',
            'normality3',
            'sample_wt_chloride',


            'volume_make_upto_chloride',
            'aliqote_taken_chloride',
            'volume_silver_nitrate_added',
            'volume_ammonia_blank',
            'volume_ammonia_sample',


            'normality_of_ammonia',
            'sample_wt_sulphate',
            'volume_make_upto_sulphate',
            'aliqote_taken_sulphate',
            'wt_empty_crucible_after_ignition',


            'wt_empty_crucible',
            'sample_wt_na2O',
            'dilution_na2O',
            'sidium_reading_na2O',
            

            'sample_wt_k2O',
            'dilution_k2O',
            'sidium_reading_k2O',
            'factor_graph_k2O',
           
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
