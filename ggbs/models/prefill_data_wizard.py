from odoo import api, fields, models
from odoo.exceptions import UserError




# class GGBSPrefillWizard(models.TransientModel):
#     _name = 'ggbs.prefill.data'
#     _description = 'Prefill Data'

#     product_id = fields.Many2one('product.template', string="Product")
#     sample_id = fields.Many2one(
#         'lerm.srf.sample',
#         domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
#         string="Sample"
#     )

#     def prefill_data(self):
#         current_product = self.env['mechanical.ggbs'].sudo().browse(self._context['active_id'])
#         copy_product = self.env['mechanical.ggbs'].sudo().search([
#             ('eln_ref.sample_id.id', '=', self.sample_id.id)
#         ], limit=1)

#         if not copy_product:
#             raise UserError("Selected sample does not have any previous GGBS record.")

#         normal_fields = [
#             'temp_specific', 'humidity_specific', 'temp_water1', 'temp_water2',
#             'temp_water_after1', 'temp_water_after2', 'initial_kerosene1',
#             'initial_kerosene2', 'mass1', 'mass2', 'temp_water_flask1',
#             'temp_water_flask2', 'temp_water_one1', 'temp_water_one2',
#             'final_kerosene1', 'final_kerosene2', 'displaced1', 'displaced2',
#             'density1', 'density2', 'average_density', 'average_strength1',
#             'average_strength2', 'sai1', 'temp_7day', 'humidity_7day',
#             'sai2', 'temp_28day', 'humidity_28day',
#             'average_cement_strength1', 'average_cement_strength2',
#             'temp_fineness', 'humidity_fineness', 'density_cement',
#             'first_bed_reading1', 'first_bed_reading2',
#             'second_bed_reading1', 'second_bed_reading2',
#             'avg_time_first', 'apparatus_constant_first', 'specific_surface_first',
#         ]

#         one2many_fields = [
#             'slag_index_ids',
#             'slag_index_cement_ids',
#         ]

#         update_vals = {}

#         # normal fields copy
#         for field in normal_fields:
#             if hasattr(copy_product, field):
#                 update_vals[field] = getattr(copy_product, field)

#         # one2many fields
#         for field in one2many_fields:
#             lines = getattr(copy_product, field)
#             if lines:
#                 update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

#         # visibility check
#         if not current_product.slag_activity_7_visible:
#             update_vals.pop('slag_index_ids', None)

#         if not current_product.slag_activity_28_visible:
#             update_vals.pop('slag_index_cement_ids', None)

#         # finally write
#         current_product.sudo().write(update_vals)

#         return {'type': 'ir.actions.act_window_close'}


class GGBSPrefillWizard(models.TransientModel):
    _name = 'ggbs.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active GGBS record
        current_product = self.env['mechanical.ggbs'].sudo().browse(self._context['active_id'])

        # Fetch previous GGBS record for selected sample
        copy_product = self.env['mechanical.ggbs'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous GGBS record.")

        # List of direct fields to copy
        normal_fields = [
            'temp_specific', 'humidity_specific', 'temp_water1', 'temp_water2',
            'temp_water_after1', 'temp_water_after2', 'initial_kerosene1',
            'initial_kerosene2', 'mass1', 'mass2', 'temp_water_flask1',
            'temp_water_flask2', 'temp_water_one1', 'temp_water_one2',
            'final_kerosene1', 'final_kerosene2', 'displaced1', 'displaced2',
            'density1', 'density2', 'average_density', 'average_strength1',
            'average_strength2', 'sai1', 'temp_7day', 'humidity_7day',
            'sai2', 'temp_28day', 'humidity_28day',
            'average_cement_strength1', 'average_cement_strength2',
            'temp_fineness', 'humidity_fineness', 'density_cement',
            'first_bed_reading1', 'first_bed_reading2',
            'second_bed_reading1', 'second_bed_reading2',
            'avg_time_first', 'apparatus_constant_first', 'specific_surface_first',
        ]

        one2many_fields = [
            'slag_index_ids',
            'slag_index_cement_ids',
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
        if not current_product.slag_activity_7_visible:
            update_vals.pop('slag_index_ids', None)

        if not current_product.slag_activity_7_visible:
            update_vals.pop('slag_index_cement_ids', None)

        # Apply copied data to current GGBS record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
