from odoo import api, fields, models
from odoo.exceptions import UserError



class OpcCementPrefillWizard(models.TransientModel):
    _name = 'fine.aggregate.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.fine.aggregate'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.fine.aggregate'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'wt_of_sample',
            'wt_sample_finer75',
            'wt_dry_sample_finer75',
            'weight_bucket',
            'empty_bucket',
            'bucket_compact',
            'bucket_loos',
            'wt_of_loose',
            'wt_of_loose1',
            'specific_gravity4',
            'specific_gravity5',
            'wt_of_compact',
            'weight_empty_cylender',
            'volume_of_cylender',
            'volume_of_cylender1',
            'weight_empty_cylender1',
            'wt_of_compact1'            
        ]

        one2many_fields = [
            'sieve_analysis_child_lines',
            'specific_gravity_child_lines',
            'bulking_sand_child_lines',
            'site_content_child_lines',
            'moisture_content_child_lines'
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.sieve_visible:
            update_vals.pop('sieve_analysis_child_lines', None)

        if not current_product.specific_gravity_visible:
            update_vals.pop('specific_gravity_child_lines', None)

        if not current_product.bulking_sand_visible:
            update_vals.pop('bulking_sand_child_lines', None)

        if not current_product.site_content_visible:
            update_vals.pop('site_content_child_lines', None)

        if not current_product.moisture_content_visible:
            update_vals.pop('moisture_content_child_lines', None)


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
