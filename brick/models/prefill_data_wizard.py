from odoo import api, fields, models
from odoo.exceptions import UserError


class ClayBrickPrefillWizard(models.TransientModel):
    _name = 'brick.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active GGBS record
        current_product = self.env['mechanical.bricks'].sudo().browse(self._context['active_id'])

        # Fetch previous GGBS record for selected sample
        copy_product = self.env['mechanical.bricks'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous GGBS record.")

        # List of direct fields to copy
        normal_fields = [
            'temp_compressive_strength', 'humidity_compressive_strength', 'avg_compressive_strength', 

            'temp_water_absorption', 'humidity_water_absorption', 'avg_water_absorption', 
            'temp_dimension', 'humidity_dimension', 'length1', 
            'length2', 'length3', 'avg_length', 
            'width1', 'width2', 'width3', 
            'avg_width', 'height1', 'height2', 
            'height3', 'avg_height', 
           
        ]

        one2many_fields = [
            'compressive_strength_child_lines',

            'water_absorption_child_lines',
           
           
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
        if not current_product.compressive_strength_visible:
            update_vals.pop('compressive_strength_child_lines', None)

        if not current_product.water_absorption_visible:
            update_vals.pop('water_absorption_child_lines', None)

       
       
        # Apply copied data to current GGBS record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
