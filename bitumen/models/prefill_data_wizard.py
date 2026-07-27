from odoo import api, fields, models
from odoo.exceptions import UserError



class BitumenPrefillWizard(models.TransientModel):
    _name = 'bitumen.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.bitumen'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.bitumen'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        if not copy_product:
         raise UserError("No Bitumen record found for the selected sample.")

        normal_fields = [
            'temperature',
            'soft_cool_temp',
            'bill_no_1',
            'bill_no_2',
            'room_temperature',
            'pouring_temperature',
            'cooling_before_trim',
            'cooling_after_trim',
            'actual_test_temperature',
            'rate_of_pull',
        ]

        one2many_fields = [
            'penetration_value_line_ids',
            'specific_water_line_ids',
            'soft_point_line_ids',
            'ductility_line_ids',
            'absolute_line_ids',
            'kinematic_line_ids',
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

        

        if not current_product.penetration_value_visible:
            update_vals.pop('penetration_value_line_ids', None)

        if not current_product.specific_gravity_visible:
            update_vals.pop('specific_water_line_ids', None)

        if not current_product.soft_point_visible:
            update_vals.pop('soft_point_line_ids', None)

        if not current_product.ductility_visible:
            update_vals.pop('ductility_line_ids', None)

        if not current_product.absolute_vis_visible:
            update_vals.pop('absolute_line_ids', None)

        if not current_product.kinematic_vis_visible:
            update_vals.pop('kinematic_line_ids', None)


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
