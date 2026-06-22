from odoo import api, fields, models
from odoo.exceptions import UserError



class FlyChemicalPrefillWizard(models.TransientModel):
    _name = 'chemical.fly.ash.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['chemical.fly.ash'].sudo().browse(self._context['active_id'])
        copy_product = self.env['chemical.fly.ash'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'loass_ingnition_sampleb_1',
            'loass_ingnition_sampleb_2',
            'loass_ingnition_sampleb_3',
            'loass_ingnition_sampleb_4',
            'loass_ingnition_sampleb_5',

            'loass_ingnition_cruciblew2_1',
            'loass_ingnition_cruciblew2_2',
            'loass_ingnition_cruciblew2_3',

            'loass_ingnition_cruciblew2_4',
            'loass_ingnition_cruciblew2_5',


            'loass_ingnition_cruciblew3_1',
            'loass_ingnition_cruciblew3_2',
            'loass_ingnition_cruciblew3_3',
            'loass_ingnition_cruciblew3_4',
            'loass_ingnition_cruciblew3_5',

            'silica_samplew_1',
            'silica_samplew_2',
            'silica_samplew_3',
            'silica_samplew_4',
            'silica_samplew_5',


            'silica_cruciblew2_1',
            'silica_cruciblew2_2',
            'silica_cruciblew2_3',
            'silica_cruciblew2_4',
            'silica_cruciblew2_5',


            'silica_cruciblew1_1',
            'silica_cruciblew1_2',
            'silica_cruciblew1_3',
            'silica_cruciblew1_4',
            'silica_cruciblew1_5',


            'ferric_alumina_samplew_1',
            'ferric_alumina_samplew_2',
            'ferric_alumina_samplew_3',
            'ferric_alumina_samplew_4',
            'ferric_alumina_samplew_5',


            'ferric_alumina_cruciblew1_1',
            'ferric_alumina_cruciblew1_2',
            'ferric_alumina_cruciblew1_3',
            'ferric_alumina_cruciblew1_4',
            'ferric_alumina_cruciblew1_5',
            

            'ferric_alumina_cruciblew2_1',
            'ferric_alumina_cruciblew2_2',
            'ferric_alumina_cruciblew2_3',
            'ferric_alumina_cruciblew2_4',
            'ferric_alumina_cruciblew2_5',

            'ferric_oxide_potassiumv_1',
            'ferric_oxide_potassiumv_2',
            'ferric_oxide_potassiumv_3',
            'ferric_oxide_potassiumv_4',
            'ferric_oxide_potassiumv_5',



            'ferric_oxide_potassiumn_1',
            'ferric_oxide_potassiumn_2',
            'ferric_oxide_potassiumn_3',
            'ferric_oxide_potassiumn_4',
            'ferric_oxide_potassiumn_5',



            'ferric_oxide_samplew_1',
            'ferric_oxide_samplew_2',
            'ferric_oxide_samplew_3',
            'ferric_oxide_samplew_4',
            'ferric_oxide_samplew_5',


            'al2o3_1',
            'al2o3_2',
            'al2o3_3',
            'al2o3_4',
            'al2o3_5',


            'alumina_oxide_1',
            'alumina_oxide_2',
            'alumina_oxide_3',
            'alumina_oxide_4',
            'alumina_oxide_5',

    # FFFff
            'magnesia_samplew_1',
            'magnesia_samplew_2',
            'magnesia_samplew_3',
            'magnesia_samplew_4',
            'magnesia_samplew_5',

             'magnesia_cruciblew1_1',
            'magnesia_cruciblew1_2',
            'magnesia_cruciblew1_3',
            'magnesia_cruciblew1_4',
            'magnesia_cruciblew1_5',

             'magnesia_cruciblew2_1',
            'magnesia_cruciblew2_2',
            'magnesia_cruciblew2_3',
            'magnesia_cruciblew2_4',
            'magnesia_cruciblew2_5',

             'calcium_oxide_samplew_1',
            'calcium_oxide_samplew_2',
            'calcium_oxide_samplew_3',
            'calcium_oxide_samplew_4',
            'calcium_oxide_samplew_5',

             'calcium_oxide_cruciblew1_1',
            'calcium_oxide_cruciblew1_2',
            'calcium_oxide_cruciblew1_3',
            'calcium_oxide_cruciblew1_4',
            'calcium_oxide_cruciblew1_5',

             'calcium_oxide_cruciblew2_1',
            'calcium_oxide_cruciblew2_2',
            'calcium_oxide_cruciblew2_3',
            'calcium_oxide_cruciblew2_4',
            'calcium_oxide_cruciblew2_5',

             'sulpuric_so3_samplew_1',
            'sulpuric_so3_samplew_2',
            'sulpuric_so3_samplew_3',
            'sulpuric_so3_samplew_4',
            'sulpuric_so3_samplew_5',

             'sulpuric_so3_cruciblew1_1',
            'sulpuric_so3_cruciblew1_2',
            'sulpuric_so3_cruciblew1_3',
            'sulpuric_so3_cruciblew1_4',
            'sulpuric_so3_cruciblew1_5',

             'sulpuric_so3_cruciblew2_1',
            'sulpuric_so3_cruciblew2_2',
            'sulpuric_so3_cruciblew2_3',
            'sulpuric_so3_cruciblew2_4',
            'sulpuric_so3_cruciblew2_5',

            

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
