from odoo import api, fields, models
from odoo.exceptions import UserError



class BrickPrefillWizard(models.TransientModel):
    _name = 'bricks.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.bricks'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.bricks'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'length_in_mm',
            'width_in_mm',
            'height_in_mm',
            'length',
            'length_2',
            'length_3',
            'length_4',
            'length_5',
            'width',
            'width_2',
            'width_3',
            'width_4',
            'width_5',
            'height',
            'height_2',
            'height_3',
            'height_4',
            'height_5',
            'load',
            'load_2',
            'load_3',
            'load_4',
            'load_5',
            'visual_observation_1',
            'visual_observation_2',
            'visual_observation_3',
            'visual_observation_4',
            'visual_observation_5',
            'avrg_length',
            'avrg_width',
            'avrg_height',
            'initial_wt',
            'initial_wt_2',
            'initial_wt_3',
            'initial_wt_4',
            'initial_wt_5',
            'final_wt',
            'final_wt_2',
            'final_wt_3',
            'final_wt_4',
            'final_wt_5'
        ]

        one2many_fields = [
           
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]


        


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
