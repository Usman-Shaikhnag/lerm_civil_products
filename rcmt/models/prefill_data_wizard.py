from odoo import api, fields, models
from odoo.exceptions import UserError



class RcmtPrefillWizard(models.TransientModel):
    _name = 'rcmt.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.rcmt'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.rcmt'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'date_of_testing',
            'sample_condition',
            'specime_prepared',
            'conditioning_started',
            'Vaccum_starte',
            'water_added',
            'vaccum_turn_off',
            'soaking_started',
            'soaking_completed',
            'dimension_name',
            'observed_value_name',
            'initial_voltage1',
            'initial_voltage2',
            'initial_voltage3',
            'initial_current1',
            'initial_current2',
            'initial_current3',
            'initial_temprrature1',
            'initial_temprrature2',
            'initial_temprrature3',
            'final_voltage1',
            'final_voltage2',
            'final_voltage3',
            'final_curent1',
            'final_curent2',
            'final_curent3',
            'final_tempreture1',
            'final_tempreture2',
            'final_tempreture3',
            'thickness_specimen1',
            'thickness_specimen2',
            'thickness_specimen3',
            'diameter_specimen1',
            'diameter_specimen2',
            'diameter_specimen3'

        ]

        one2many_fields = [
            'child_lines',
            'child_lines1'
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
