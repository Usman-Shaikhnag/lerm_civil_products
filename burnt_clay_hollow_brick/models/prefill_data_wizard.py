from odoo import api, fields, models

class BurntClayHollowBrickPrefillData(models.TransientModel):
    _name = "burnt.clay.hollow.brick.prefill.data"
    _description = "Prefill Data"

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one('lerm.srf.sample', domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")

    def prefill_data(self):
        current_product = self.env['mechanical.burnt.clay.hollow.brick'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.burnt.clay.hollow.brick'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = ['grade']

        one2many_fields = ['crushing_value_child_lines', 'dimension_child_lines']

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.crushing_visible:
            update_vals.pop('crushing_value_child_lines', None)

        if not current_product.dimension_visible:
            update_vals.pop('dimension_child_lines', None)

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
