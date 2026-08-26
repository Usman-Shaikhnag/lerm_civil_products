from odoo import api, fields, models


class BentonitePrefillData(models.TransientModel):
    _name = 'bentonite.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one('lerm.srf.sample', domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")

    def prefill_data(self):
        current_product = self.env['mechanical.bentonite'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.bentonite'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        vals = {}

        if copy_product.ll_child_lines:
            vals['ll_child_lines'] = [(0, 0, line.copy_data()[0]) for line in copy_product.ll_child_lines]
        if copy_product.wet_fineness_lines:
            vals['wet_fineness_lines'] = [(0, 0, line.copy_data()[0]) for line in copy_product.wet_fineness_lines]
        if copy_product.dry_fineness_lines:
            vals['dry_fineness_lines'] = [(0, 0, line.copy_data()[0]) for line in copy_product.dry_fineness_lines]

        vals['wet_fineness_int_wt'] = copy_product.wet_fineness_int_wt
        vals['dry_fineness_int_wt'] = copy_product.dry_fineness_int_wt
        vals['moisture_m1'] = copy_product.moisture_m1
        vals['moisture_m2'] = copy_product.moisture_m2
        vals['sand_initial_wt'] = copy_product.sand_initial_wt
        vals['sand_final_wt'] = copy_product.sand_final_wt

        current_product.sudo().write(vals)

        return {'type': 'ir.actions.act_window_close'}
