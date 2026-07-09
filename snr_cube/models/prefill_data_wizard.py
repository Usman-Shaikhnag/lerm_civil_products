from odoo import api, fields, models
from odoo.exceptions import UserError



class ProductGradeWizard(models.TransientModel):
    _name = 'snr.cube.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['snr.cube'].sudo().browse(self._context['active_id'])
        copy_product = self.env['snr.cube'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        child_lines_vals = [(0, 0, line.copy_data()[0]) for line in copy_product.child_lines]

        current_product.sudo().write({
            'child_lines': child_lines_vals
        })

        return {'type': 'ir.actions.act_window_close'}