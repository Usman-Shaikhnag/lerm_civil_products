from odoo import api, fields, models
from odoo.exceptions import UserError



class PpcCementPrefillWizard(models.TransientModel):
    _name = 'cement.ppc.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['cement.ppc'].sudo().browse(self._context['active_id'])
        copy_product = self.env['cement.ppc'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'time_water_added',
            'time_needle_fails',
            'time_needle_make_impression',
            'wt_of_empty_bottle',
            'wt_of_bottle_cement',
            'wt_of_specific_bpttle',
            'wt_of_kerosene',
            'wt_of_bottle_water',
            'wt_of_empty_bottle1',
            'wt_of_bottle_cement1',
            'wt_of_specific_bpttle1',
            'wt_of_kerosene1',
            'wt_of_bottle_water1'
            

        ]

        one2many_fields = [
            'fneness_cement_lines',
            'density_cement_lines',
            'fineness_blaine_lines',
            'soundness_cement_lines',
            'consistency_cement_lines',
            'intial_time_lines',
            'final_time_lines',
            'compressive_lines',
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.compressive_visible:
            update_vals.pop('compressive_lines', None)

        if not current_product.initial_setting_time_visible:
            update_vals.pop('intial_time_lines', None)

        if not current_product.final_setting_time_visible:
            update_vals.pop('final_time_lines', None)

        if not current_product.fineness_cement_visible:
            update_vals.pop('fneness_cement_lines', None)

        if not current_product.density_cement_visible:
            update_vals.pop('density_cement_lines', None)

        if not current_product.fineness_blaine_visible:
            update_vals.pop('fineness_blaine_lines', None)

        if not current_product.soundness_cement_visible:
            update_vals.pop('soundness_cement_lines', None)

        if not current_product.consistency_cement_visible:
            update_vals.pop('consistency_cement_lines', None)

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
