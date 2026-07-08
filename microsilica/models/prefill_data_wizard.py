from odoo import api, fields, models
from odoo.exceptions import UserError



class MicrosilicaPrefillWizard(models.TransientModel):
    _name = 'mech.microsilica.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")

    def prefill_data(self):
        current_product = self.env['mechanical.microsilica'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.microsilica'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'sample_weight_ws',
            'temp_cs',
            'humidity_cs',
            'start_date_cs',
            'end_date_cs',
            'wt_of_sand_cs',
            'wt_of_cement_silica_cs',
            'std_consistency_p',
            'temp_pozzolanic',
            'humidity_pozzolanic',
            'start_date_pozzolanic',
            'end_date_pozzolanic',
            'tm_high_range_water',
            'tm_wt_microsilica',
            'tm_wt_cement',
            'tm_wt_sand_grade1',
            'tm_wt_sand_grade2',
            'tm_wt_sand_grade3',
            'tm_quantity_water',
            'tm_measured_val1',
            'tm_measured_val2',
            'tm_measured_val3',
            'tm_measured_val4',
            'cs_high_range_water',
            'cs_wt_cement',
            'cs_wt_sand_grade1',
            'cs_wt_sand_grade2',
            'cs_wt_sand_grade3',
            'cs_quantity_water',
            'cs_measured_val1',
            'cs_measured_val2',
            'cs_measured_val3',
            'cs_measured_val4',
        ]

        one2many_fields = [
            'wet_sieving_line_ids',
            'comp_str_line_ids',
            'specific_gravity_tables',
            'tm_casting_line_ids',
            'cs_casting_line_ids',
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.wet_sieving_visible:
            update_vals.pop('wet_sieving_line_ids', None)

        if not current_product.compressive_strength_visible:
            update_vals.pop('comp_str_line_ids', None)

        if not current_product.specific_gravity_visible:
            update_vals.pop('specific_gravity_tables', None)

        if not current_product.pozzolanic_visible:
            update_vals.pop('tm_casting_line_ids', None)
            update_vals.pop('cs_casting_line_ids', None)

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
