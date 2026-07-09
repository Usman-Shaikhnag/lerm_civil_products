from odoo import api, fields, models
from odoo.exceptions import UserError



class AACPrefillWizard(models.TransientModel):
    _name = 'mechanical.aac.block.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.aac.block'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.aac.block'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'length_grade1',
            'length_grade2',
            'width_grade1',
            'width_grade2',
            'height_grade1',
            'height_grade2',
            'moisture_grade1',
            'moisture_grade2',
            'density_grade1',
            'density_grade2',
            'density_unit',
            'drying_grade1',
            'drying_grade2'


            'compressive_grade1',
            'compressive_grade2',
            

        ]

        one2many_fields = [
            'dimension_table',
            'moisture_content_table',
            'density_table',
            'drying_shrinkage_table',
            'compressive_strength_table',
           
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.dimension_visible:
            update_vals.pop('dimension_table', None)

        if not current_product.moisture_visible:
            update_vals.pop('moisture_content_table', None)

        if not current_product.density_visible:
            update_vals.pop('density_table', None)

        if not current_product.drying_shrinkage_visible:
            update_vals.pop('drying_shrinkage_table', None)

        if not current_product.compressive_strength_visible:
            update_vals.pop('compressive_strength_table', None)

       

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
