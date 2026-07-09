from odoo import api, fields, models
from odoo.exceptions import UserError



class BurntClayBrickPrefillWizard(models.TransientModel):
    _name = 'mechanical.bricks.burnt.clay.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.bricks.burnt.clay'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.bricks.burnt.clay'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'compressive_strength_unit',
            'water_absorption_unit',
            'length_in_mm',
            'width_in_mm',
            'height_in_mm',


            'visual_observation_1',
            'visual_observation_2',
            'visual_observation_3',
            'visual_observation_4',
            'visual_observation_5',
            'avrg_length',
            'avrg_width',
            'avrg_height'
            

        ]

        one2many_fields = [
            'absorption_line_ids',
            'compressive_strength_lines',
            'water_absorption_lines',
          
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.ini_rate_absorption_visible:
            update_vals.pop('absorption_line_ids', None)

        if not current_product.compressive_strength_visible:
            update_vals.pop('compressive_strength_lines', None)

        if not current_product.water_absorbtion_visible:
            update_vals.pop('water_absorption_lines', None)

       
        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
