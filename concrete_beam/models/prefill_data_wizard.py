from odoo import api, fields, models
from odoo.exceptions import UserError



class ConcreteBeamPrefillWizard(models.TransientModel):
    _name = 'mechanical.concrete.beam.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.concrete.beam'].sudo().browse(self._context.get('active_id'))

        copy_product = self.env['mechanical.concrete.beam'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        if not copy_product:
            return {'type': 'ir.actions.act_window_close'}

        normal_fields = [
            'date_of_testing',
            'age_of_test',
        ]

        one2many_fields = [
            'child_lines',
        ]

        update_vals = {}

        # ✅ Copy normal fields
        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        # ✅ Copy one2many fields (ALWAYS copy, no condition)
        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [
                    (0, 0, line.copy_data()[0]) for line in lines
                ]

        # ✅ Write values to current record
        current_product.write(update_vals)

        return {'type': 'ir.actions.act_window_close'}