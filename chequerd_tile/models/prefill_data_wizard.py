from odoo import api, fields, models
from odoo.exceptions import UserError



class ChequerdPrefillWizard(models.TransientModel):
    _name = 'mechanical.chequered.tiles.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.chequered.tiles'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.chequered.tiles'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'cement_sample_size',
            'length',
            'thickness',
            'width',

            'deviation_flatness',
            'deviation_perpendicularity',
            'deviation_length_straightness',

         

        ]

        one2many_fields = [
            'chequered_water_absorption_lines',
            'chequered_wet_transver_lines',
            'chequered_tiles_lines',
         
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.chequered_water_absorption_visible:
            update_vals.pop('chequered_water_absorption_lines', None)

        if not current_product.chequeredwet_transver_visible:
            update_vals.pop('chequered_wet_transver_lines', None)

        if not current_product.chequered_tiles_visible:
            update_vals.pop('chequered_tiles_lines', None)

        

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
