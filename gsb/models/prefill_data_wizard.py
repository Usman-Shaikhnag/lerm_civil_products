from odoo import api, fields, models
from odoo.exceptions import UserError



class GsbPrefillWizard(models.TransientModel):
    _name = 'gsb.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.gsb'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.gsb'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'wt_ssd_sample',
            'oven_dried_wt',
            'total_weight_sample_abrasion',
            'weight_passing_sample_abrasion',
            'wt_of_modul',
            'vl_of_modul'

        ]

        one2many_fields = [
            'dry_gradation_table',
            'elongation_table',
            'impact_value_child_lines',
            'liquid_limit_table',
            'plastic_table',
            'density_relation_table',
            'cbr_table'
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.dry_gradation_visible:
            update_vals.pop('dry_gradation_table', None)

        if not current_product.elongation_visible:
            update_vals.pop('elongation_table', None)

        if not current_product.impact_visible:
            update_vals.pop('impact_value_child_lines', None)

        if not current_product.liquid_limit_visible:
            update_vals.pop('liquid_limit_table', None)

        if not current_product.plastic_visible:
            update_vals.pop('plastic_table', None)

        if not current_product.density_relation_visible:
            update_vals.pop('density_relation_table', None)

        if not current_product.cbr_visible:
            update_vals.pop('cbr_table', None)


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
