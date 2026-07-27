from odoo import api, fields, models
from odoo.exceptions import UserError



class CoarseAggregatePrefillWizard(models.TransientModel):
    _name = 'coarse.aggregate.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.coarse.aggregate'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.coarse.aggregate'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'temperature',
            'weight_of_sample',

        ]

        one2many_fields = [
            'sieve_analysis_child_lines',
            'loose_line_ids',
            'rodded_line_ids',
            'crushing_value_child_lines',
            'elongation_fl_table',
            'impact_value_child_lines',
            'specific_water_line_ids',
            'deleterious_coal_lignite_line_ids',
            'abrasion_value_line_ids',
            'finer75_line_ids',
            'fine10_line_ids',
            'clay_lumps_percent_line_ids',
            'stripping_value_line_ids',
            'wet_impact_line_ids',
            'soundness_sod_line_ids',
            'soundness_sodtwo_line_ids',
            'soundness_mag_line_ids',
            'soundness_magtwo_line_ids'


        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        # for field in one2many_fields:
        #     lines = getattr(copy_product, field)
        #     if lines:
        #         update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        for field in one2many_fields:
          lines = getattr(copy_product, field)
          if lines:
              commands = [(5, 0, 0)]  # Remove all existing lines
              commands += [(0, 0, line.copy_data()[0])for line in lines]
              update_vals[field] = commands

        

        if not current_product.sieve_visible:
            update_vals.pop('sieve_analysis_child_lines', None)

        if not current_product.loose_bulk_density_visible:
            update_vals.pop('loose_line_ids', None)

        if not current_product.rodded_bulk_density_visible:
            update_vals.pop('rodded_line_ids', None)

        if not current_product.crushing_visible:
            update_vals.pop('crushing_value_child_lines', None)

        if not current_product.elongation_fl_visible:
            update_vals.pop('elongation_fl_table', None)

        if not current_product.impact_visible:
            update_vals.pop('impact_value_child_lines', None)

        if not current_product.deleterious_coal_lignite_visible:
            update_vals.pop('deleterious_coal_lignite_line_ids', None)

        if not current_product.abrasion_visible:
            update_vals.pop('abrasion_value_line_ids', None)

        if not current_product.finer75_visible:
            update_vals.pop('finer75_line_ids', None)

        if not current_product.fine10_visible:
            update_vals.pop('fine10_line_ids', None)

        if not current_product.clay_lump_visible:
            update_vals.pop('clay_lumps_percent_line_ids', None)

        if not current_product.stripping_value_visible:
            update_vals.pop('stripping_value_line_ids', None)

        if not current_product.wet_impact_visible:
            update_vals.pop('wet_impact_line_ids', None)

        if not current_product.soundness_na2so4_visible:
            update_vals.pop('soundness_sod_line_ids', None)

        if not current_product.soundness_na2so4_visible:
            update_vals.pop('soundness_sodtwo_line_ids', None)

        if not current_product.soundness_mgso4_visible:
            update_vals.pop('soundness_mag_line_ids', None)

        if not current_product.soundness_mgso4_visible:
            update_vals.pop('soundness_magtwo_line_ids', None)

        


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
