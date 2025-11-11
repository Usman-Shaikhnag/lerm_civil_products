from odoo import api, fields, models
from odoo.exceptions import UserError



class SoilPrefillWizard(models.TransientModel):
    _name = 'soil.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id)]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.soil'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.soil'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        # List of One2many fields to always copy
        one2many_fields = [
            'sieve_analysis_child_lines',
            'child_liness',
            'plastic_limit_table',
            'heavy_table',
            'omc_table',
            'triaxial_table',
            'internal_fraction_table',
            'soil_table',
            'shrinkage_limit_table',
            'volume_dry_table',
            'volume_wet_table',
            'test_line_ids',
            'direct_shear_ids',
            'ucs_ids',
            'consolidation_name_ids',
            'consolidation_pc_ids',
            'angleshear_line_ids',
            'swelling_pressure_line_ids',
            'uu_triaxial_angle_line_ids',
            'uu_triaxial_cohesion_line_ids',
        ]

        update_vals = {}

        for field in one2many_fields:
            # only copy if the record has values
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        # Apply visibility filters here
        if not current_product.sieve_visible:
            update_vals.pop('sieve_analysis_child_lines', None)

        if not current_product.liquid_limit_visible:
            update_vals.pop('child_liness', None)
        
        if not current_product.plastic_limit_visible:
            update_vals.pop('plastic_limit_table', None)

        if not current_product.heavy_visible:
            update_vals.pop('heavy_table', None)

        if not current_product.omc_visible:
            update_vals.pop('omc_table', None)
        
        if not current_product.triaxial_visible:
            update_vals.pop('triaxial_table', None)


        # Write once, not many times
        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}