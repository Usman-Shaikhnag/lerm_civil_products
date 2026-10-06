from odoo import api, fields, models
from odoo.exceptions import UserError



class AACBlockPrefillWizard(models.TransientModel):
    _name = 'aac.block.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.aac.block'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.aac.block'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'aac_temp',
            'aac_humidity',

        ]

        one2many_fields = [
            'length_dimen_line_ids',
            'height_dimen_line_ids',
            'thickness_dimen_line_ids',
            'bulk_density_ids',
            'moisture_content_line_ids',
            'compressive_strength_line_ids',
            'drying_shrinkage_line_ids',
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

        

        if not current_product.length_dimen_visible:
            update_vals.pop('length_dimen_line_ids', None)

        if not current_product.height_dimen_visible:
            update_vals.pop('height_dimen_line_ids', None)

        if not current_product.thickness_dimen_visible:
            update_vals.pop('thickness_dimen_line_ids', None)

        if not current_product.bulk_density_visible:
            update_vals.pop('bulk_density_ids', None)

        if not current_product.moisture_content_visible:
            update_vals.pop('moisture_content_line_ids', None)

        if not current_product.compressive_strength_visible:
            update_vals.pop('compressive_strength_line_ids', None)

        if not current_product.drying_shrinkage_visible:
            update_vals.pop('drying_shrinkage_line_ids', None)

        
        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
