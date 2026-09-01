from odoo import api, fields, models
from odoo.exceptions import UserError


class FlyashPrefillWizard(models.TransientModel):
    _name = 'flyash.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active Flyash record
        current_product = self.env['mechanical.flyasch.normalconsistency'].sudo().browse(self._context['active_id'])

        # Fetch previous Flyash record for selected sample
        copy_product = self.env['mechanical.flyasch.normalconsistency'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous Flyash record.")

        # List of direct fields to copy
        normal_fields = [
            'temp_percent_consistency', 'humidity_percent_consistency', 'temp_setting_time', 'humidity_setting_time', 'temp_soundness', 'humidity_soundness', 'temp_sound_auto', 'humidity_sound_auto', 'temp_specific_gravity', 'humidity_specific_gravity',
            'temp_water_1', 'temp_water_2',
            'temp_water_after_1', 'temp_water_after_2', 'initial_kerosene_1', 'initial_kerosene_2', 'mass_flyash_1', 'mass_flyash_2', 'temp_waterflask_1', 'temp_waterflask_2', 'temp_waterflask_after_1', 'temp_waterflask_after_2', 'final_kerosene_1', 'final_kerosene_2', 'temp_fineness_blain', 'humidity_fineness_blain', 'density_pozzolana', 'first_bed_reading1', 'first_bed_reading2', 'second_bed_reading1', 'second_bed_reading2' , 'temp_fineness', 'humidity_fineness', 'temp_compressive_strength', 'humidity_compressive_strength', 'temp_lime', 'humidity_lime', 'temp_drying_shrinkage', 'humidity_drying_shrinkage', 
        ]

        one2many_fields = [
            'consistency_child_lines',
            'intial_time_lines',
            'soundness_child_lines',
            'sound_auto_child_lines',
            'fineness_child_lines',
            'compressive_strength_child_lines',
            'compressive_cement_child_lines',
            'lime_child_lines',
            'drying_shrinkage_child_lines',
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
        if not current_product.normal_consistency_visible:
            update_vals.pop('consistency_child_lines', None)

        if not current_product.initial_setting_time_visible:
            update_vals.pop('intial_time_lines', None)

        if not current_product.final_setting_time_visible:
            update_vals.pop('intial_time_lines', None)

        if not current_product.soundness_visible:
            update_vals.pop('soundness_child_lines', None)
        
        if not current_product.sound_auto_visible:
            update_vals.pop('sound_auto_child_lines', None)
        
        if not current_product.fineness_visible:
            update_vals.pop('fineness_child_lines', None)
        
        if not current_product.compressive_strength_visible:
            update_vals.pop('compressive_strength_child_lines', None)
        
        if not current_product.compressive_strength_visible:
            update_vals.pop('compressive_cement_child_lines', None)

        if not current_product.lime_visible:
            update_vals.pop('lime_child_lines', None)

        if not current_product.drying_shrinkage_visible:
            update_vals.pop('drying_shrinkage_child_lines', None)







        # Apply copied data to current GGBS record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
