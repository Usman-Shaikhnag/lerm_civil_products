from odoo import api, fields, models
from odoo.exceptions import UserError



class AdmixturePrefillWizard(models.TransientModel):
    _name = 'mechanical.admixture.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.admixture'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.admixture'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'density_a',
            'density_b',
            'density_c',
            'density_d',
            'density_e',

            'dry_content_bottlew1_1',
            'dry_content_bottlew1_2',
            'dry_content_bottlew1_3',

            'dry_content_bottlew1_4',
            'dry_content_bottlew1_5',


            'dry_content_bottlew2_1',
            'dry_content_bottlew2_2',
            'dry_content_bottlew2_3',
            'dry_content_bottlew2_4',
            'dry_content_bottlew2_5',

            'dry_content_wt_w2_w1_1',
            'dry_content_wt_w2_w1_2',
            'dry_content_wt_w2_w1_3',
            'dry_content_wt_w2_w1_4',
            'dry_content_wt_w2_w1_5',


            'dry_content_driedw3_1',
            'dry_content_driedw3_2',
            'dry_content_driedw3_3',
            'dry_content_driedw3_4',
            'dry_content_driedw3_5',


            'dry_content_dried_w3_w1_1',
            'dry_content_dried_w3_w1_2',
            'dry_content_dried_w3_w1_3',
            'dry_content_dried_w3_w1_4',
            'dry_content_dried_w3_w1_5',


            'dry_content_residue1',
            'dry_content_residue2',
            'dry_content_residue3',
            'dry_content_residue4',
            'dry_content_residue5',


            'ash_content_crucible1_1',
            'ash_content_crucible1_2',
            'ash_content_crucible1_3',
            'ash_content_crucible1_4',
            'ash_content_crucible1_5',
            

            'ash_content_cruciblew2_1',
            'ash_content_cruciblew2_2',
            'ash_content_cruciblew2_3',
            'ash_content_cruciblew2_4',
            'ash_content_cruciblew2_5',

            'ash_content_cruciblew3_1',
            'ash_content_cruciblew3_2',
            'ash_content_cruciblew3_3',
            'ash_content_cruciblew3_4',
            'ash_content_cruciblew3_5',



            'chloride_samplew_1',
            'chloride_samplew_2',
            'chloride_samplew_3',
            'chloride_samplew_4',
            'chloride_samplew_5',



            'chloride_nitratew1_1',
            'chloride_nitratew1_2',
            'chloride_nitratew1_3',
            'chloride_nitratew1_4',
            'chloride_nitratew1_5',


            'chloride_ammoniumw2_1',
            'chloride_ammoniumw2_2',
            'chloride_ammoniumw2_3',
            'chloride_ammoniumw2_4',
            'chloride_ammoniumw2_5',


            'ph_a',
            'ph_b',
            'ph_c',
            'ph_d',
            'ph_e',


          

         

        ]

        one2many_fields = [
            # 'chequered_tiles_cement_lines',
            # 'chequered_cement_water_absorption_lines',
            # 'chequeredwet_cement_transver_lines',
         
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        # if not current_product.chequered_tiles_cement_visible:
        #     update_vals.pop('chequered_tiles_cement_lines', None)

        # if not current_product.chequered_cement_water_absorption_visible:
        #     update_vals.pop('chequered_cement_water_absorption_lines', None)

        # if not current_product.chequeredwet_cement_transver_visible:
        #     update_vals.pop('chequeredwet_cement_transver_lines', None)

        

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
