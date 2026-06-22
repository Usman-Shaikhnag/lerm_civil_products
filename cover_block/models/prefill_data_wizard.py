from odoo import api, fields, models
from odoo.exceptions import UserError



class CoverBlockPrefillWizard(models.TransientModel):
    _name = 'mechanical.cover.block.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.cover.block'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.cover.block'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'temprature',
            'humidity',
            'week_no',
            'other_details',
            'condition',
            'description_work',

            'wt_surface_dry',
            'wt_sample_inwater',
            'oven_dried_wt',
            'wt_surface_dry_2',
            'wt_sample_inwater_2',
            'oven_dried_wt_2',


        ]

        one2many_fields = [
            'crushing_child_lines',
          
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.crushing_visible:
            update_vals.pop('crushing_child_lines', None)

       


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
