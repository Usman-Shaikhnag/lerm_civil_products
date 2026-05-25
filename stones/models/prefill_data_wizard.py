from odoo import api, fields, models
from odoo.exceptions import UserError


class StonePrefillWizard(models.TransientModel):
    _name = 'stone.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active GGBS record
        current_product = self.env['mechanical.stones'].sudo().browse(self._context['active_id'])

        # Fetch previous GGBS record for selected sample
        copy_product = self.env['mechanical.stones'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous GGBS record.")

        # List of direct fields to copy
        normal_fields = [
            'lab_id1', 'room_temp1', 'relative_humidity1', 

            'depth', 'stone_type1', 'observations1', 
            'observations2', 'observations3', 'observations4', 
            'observations5', 'scratch_hardness_avg', 'factor_a', 
            'factor_b', 'compressive_perpendiculer_avg', 'compressive_parallel_avg', 
            'wet_factor_a', 'wet_factor_b', 'compressive_perpendiculer_wet_avg', 
            'compressive_parallel_wet_avg',

            'weight_oven_dried', 'weight_saturated_surface_dry', 'water_added', 
            'app_porosity', 'wet_of_oven_water', 'wet_of_satureted_water', 
            'water_absorption', 'wet_of_oven_specific', 'water_addes_specifc', 
            'app_specific_gravity', 'wet_true_specific', 'wt_stop_true_specifc', 
            'wt_bottle_true_specifc', 'wt_bottle_stope_true_specifc', 'true_specific_gravity', 
            'true_porosity',
           
        ]

        one2many_fields = [
            'compressive_dry_ids',
            'compressive_wet_ids',
           
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
        if not current_product.compressive_dry_visible:
            update_vals.pop('compressive_dry_ids', None)

        if not current_product.compressive_wet_visible:
            update_vals.pop('compressive_wet_ids', None)

       
        # Apply copied data to current GGBS record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
