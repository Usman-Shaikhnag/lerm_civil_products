from odoo import api, fields, models
from odoo.exceptions import UserError



class AdmixturePrefillWizard(models.TransientModel):
    _name = 'admixture.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.admixture'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.admixture'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'admixture_temp',
            'admixture_humidity',
            'span_length',

        ]

        one2many_fields = [
            'bleeding_lines_ids',
            'slump_test_line_ids',
            'compressive_strength_line_ids',
            'flexural_strength_line_ids',
            'loss_work_line_ids',
            'flowhigh_work_line_ids',


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

        

        if not current_product.bleeding_visible:
            update_vals.pop('bleeding_lines_ids', None)

        if not current_product.slump_test_visible:
            update_vals.pop('slump_test_line_ids', None)

        if not current_product.compressive_strength_visible:
            update_vals.pop('compressive_strength_line_ids', None)

        if not current_product.flexural_strength_visible:
            update_vals.pop('flexural_strength_line_ids', None)

        if not current_product.loss_work_visible:
            update_vals.pop('loss_work_line_ids', None)

        if not current_product.flowhigh_work_visible:
            update_vals.pop('flowhigh_work_line_ids', None)

        


        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
