from odoo import api, fields, models
from odoo.exceptions import UserError


class BitumenConcretePrefillWizard(models.TransientModel):
    _name = 'concrete.cube.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active Concrete cube record
        current_product = self.env['mechanical.concrete.cube'].sudo().browse(self._context['active_id'])

        # Fetch previous Concrete cube record for selected sample
        copy_product = self.env['mechanical.concrete.cube'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous Bitumen Concrete record.")

        # List of direct fields to copy
        normal_fields = [

            
        ]

        one2many_fields = [
            'child_lines',
            'grade_child_lines',
        ]

        update_vals = {}

        # Copy simple fields
        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        # Copy one2many fields
        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, line.copy_data()[0]) for line in lines]

        # Check visibility and remove fields if not visible
        if not current_product.concrete_visible:
            update_vals.pop('child_lines', None)

        if not current_product.concrete_visible:
            update_vals.pop('grade_child_lines', None)
        

      


        # Apply copied data to current GGBS record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}