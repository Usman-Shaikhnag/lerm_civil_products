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
            'brick_temperature',
            'brick_humidity',
            'visual_observation_1'
        ]

        one2many_fields = [
            'water_absorbtion_line_ids',
            'compressive_strength_line_ids',
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        # for field in one2many_fields:
        #     lines = getattr(copy_product, field)
        #     if lines:
        #         update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        for field in one2many_fields:
          lines = getattr(copy_product, field)
          if lines:
              commands = [(5, 0, 0)]  # Remove all existing lines
              commands += [(0, 0, line.copy_data()[0])for line in lines]
              update_vals[field] = commands

        

        if not current_product.water_absorbtion_visible:
            update_vals.pop('water_absorbtion_line_ids', None)

        if not current_product.compressive_strength_visible:
            update_vals.pop('compressive_strength_line_ids', None)


        


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
