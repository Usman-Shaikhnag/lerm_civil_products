from odoo import api, fields, models
from odoo.exceptions import UserError



class RockPrefillWizard(models.TransientModel):
    _name = 'mechanical.rock.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.rock'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.rock'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            # 'time_water_added',
            # 'time_needle_fails',
            # 'time_needle_make_impression',
            # 'wt_of_empty_bottle',
            # 'wt_of_bottle_cement',
            # 'wt_of_specific_bpttle',
            # 'wt_of_kerosene',
            # 'wt_of_bottle_water',
            # 'wt_of_empty_bottle1',
            # 'wt_of_bottle_cement1',
            # 'wt_of_specific_bpttle1',
            # 'wt_of_kerosene1',
            # 'wt_of_bottle_water1'
            

        ]

        one2many_fields = [
            'child_lines',
            'child_lines1',
            'child_lines_cerchar_abrsivity',
            # 'soundness_cement_lines',
            'modulus_of_elasticity_line_ids',
            'ponit_load_ids',
            'poison_ratio_line_ids',
            'slake_index_line_ids',
            'tensile_strength_line_ids',
            'uu_triaxial_angle_line_ids',

             'uu_triaxial_cohesion_line_ids',
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.porosity_visible:
            update_vals.pop('child_lines', None)

        if not current_product.usc_visible:
            update_vals.pop('child_lines1', None)

        if not current_product.cerchar_abrsivity_visible:
            update_vals.pop('child_lines_cerchar_abrsivity', None)

        if not current_product.modulus_of_elasticity_visible:
            update_vals.pop('modulus_of_elasticity_line_ids', None)

        if not current_product.ponit_load_visible:
            update_vals.pop('ponit_load_ids', None)

        if not current_product.poison_ratio_visible:
            update_vals.pop('poison_ratio_line_ids', None)

        # if not current_product.soundness_cement_visible:
        #     update_vals.pop('soundness_cement_lines', None)

        if not current_product.slake_index_visible:
            update_vals.pop('slake_index_line_ids', None)

        if not current_product.tensile_strength_visible:
            update_vals.pop('tensile_strength_line_ids', None)
        
        if not current_product.uu_triaxial_angle_visible:
            update_vals.pop('uu_triaxial_angle_line_ids', None)

        if not current_product.uu_triaxial_cohesion_visible:
            update_vals.pop('uu_triaxial_cohesion_line_ids', None)

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
