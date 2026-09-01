from odoo import api, fields, models
from odoo.exceptions import UserError




class PPCPrefillWizard(models.TransientModel):
    _name = 'ppc.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active ppc record
        current_product = self.env['cement.ppc'].sudo().browse(self._context['active_id'])

        # Fetch previous ppc record for selected sample
        copy_product = self.env['cement.ppc'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous ppc record.")

        # List of direct fields to copy
        normal_fields = [
            'temp_specific', 'temp_specific','humidity_specific','temp_water1','temp_water2',
            'temp_water_after1','temp_water_after2','initial_kerosene1','initial_kerosene2',
            'mass1','mass2','temp_water_flask1','temp_water_flask2','temp_water_one1',
            'temp_water_one2','final_kerosene1','final_kerosene2','displaced1','displaced2',
            'temp_consistency','humidity_consistency','consistency_cement_lines','avg_consistency',
            'intial_time_lines','temp_time','humidity_time','avg_initial_time','temp_time_final',
            'humidity_time_final','temp_fineness','humidity_fineness','density_cement',
            'first_bed_reading1','first_bed_reading2','second_bed_reading1','second_bed_reading2',
            'apparatus_constant_first','ppc_compressive_ids','temp_3_days','humidity_3_days',
            'temp_7_days','humidity_7_days','temp_28_days','humidity_28_days','temp_soundness_autoclave',
            'humidity_soundness_autoclave','ppc_autoclave_ids','temp_soundness_le_method',
            'humidity_soundness_le_method','ppc_le_method_ids','avg_expantion1',
        ]

        one2many_fields = [
            'consistency_cement_lines',
            'intial_time_lines',
            'ppc_compressive_ids',
            'ppc_autoclave_ids',
            'ppc_le_method_ids'
           
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
        if not current_product.consistency_cement_visible:
            update_vals.pop('consistency_cement_lines', None)

        if not current_product.initial_setting_time_visible:
            update_vals.pop('intial_time_lines', None)

        if not current_product.compressive_visible:
            update_vals.pop('ppc_compressive_ids', None)

        if not current_product.soundness_autoclave_visible:
            update_vals.pop('ppc_autoclave_ids', None)
        
        if not current_product.soundness_le_method_visible:
            update_vals.pop('ppc_le_method_ids', None)

        # Apply copied data to current ppc record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
