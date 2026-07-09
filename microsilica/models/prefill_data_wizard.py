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
            'temp_percent_compressive',
            'humidity_percent_compressive',
            'start_date_compressive',
            'end_date_compressive',
            'high_range_compressive',
            'wt_of_microsilica',
            'wt_of_cement_compressive',
            'wt_of_standerd_comp1',
            'wt_of_standerd_comp2',
            'wt_of_standerd_comp3',
            'quantity_water',
            'measured_value1',
            'measured_value2',
            'measured_value3',
            'measured_value4',
            'high_range_control_comp',
            'wt_of_cement',
            'wt_of_sand1',
            'wt_of_sand2',
            'wt_of_sand3',
            'quanity_of_water',
            'sample_measured_value1',
            'sample_measured_value2',
            'sample_measured_value3',
            'sample_measured_value4',
            'control_compressive_strength_7_days',
            'n_is',
            'microsilica_wt',
            'cement_wt',
            'wt_of_standerd_sand1',
            'wt_of_standerd_sand2',
            'wt_of_standerd_sand3',
            'water_quantity',
            'comp_measured_value1',
            'comp_measured_value2',
            'comp_measured_value3',
            'comp_measured_value4',
            'comp_average_casting_7days',
            'comp_control_cement_wt',
            'comp_control_wt_of_standerd_sand1',
            'comp_control_wt_standerd_sand2',
            'comp_control_wt_standerd_sand3',
            'comp_control_total_wt',
            'comp_control_water_quantity',
            'comp_control_measured_value1',
            'comp_control_measured_value2',
            'comp_control_measured_value3',
            'comp_control_measured_value4'
        ]

        one2many_fields = [
            'casting_7_days_tables',
            'control_casting_7_days_tables',
            'oversize_retained_tables',
            'specific_gravity_tables',
            'comp_casting_7_days_tables',
            'comp_control_casting_7days_tables',
            'oversize_percent_tables',
            'bulk_density_tables'
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]


        if not current_product.oversize_retain_visible:
            update_vals.pop('oversize_retained_tables', None)

        if not current_product.specific_gravity_visible:
            update_vals.pop('specific_gravity_tables', None)

        if not current_product.oversize_percent_retain_visible:
            update_vals.pop('oversize_percent_tables', None)

        if not current_product.bulk_density_visible:
            update_vals.pop('bulk_density_tables', None)


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
