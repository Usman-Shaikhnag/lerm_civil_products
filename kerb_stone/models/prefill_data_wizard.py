from odoo import api, fields, models
from odoo.exceptions import UserError



class KerbPrefillWizard(models.TransientModel):
    _name = 'mechanical.precast.kerb.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.precast.kerb'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.precast.kerb'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'temprature',
            'humidity',
            'week_no',
            'other_details',
            'condition',
            'description_work',
            'length',
            'thickness',
            'width',
           
            

        ]

        one2many_fields = [
            'transverse_table',
            'water_absorbtion_table',
            
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.transverse_visible:
            update_vals.pop('transverse_table', None)

        if not current_product.water_absorbtion_visible:
            update_vals.pop('water_absorbtion_table', None)

       

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
