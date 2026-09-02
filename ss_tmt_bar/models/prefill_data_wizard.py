from odoo import api, fields, models
from odoo.exceptions import UserError



class SsTmtCementPrefillWizard(models.TransientModel):
    _name = 'stainless.steel.tmt.bar.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.stainless.steel.tmt.bar'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.stainless.steel.tmt.bar'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'lentgh',
            'weight',
            'elongated_gauge_length',
            'yeild_load',
            'ultimate_load',
            'fracture',
            'variation',
            'bend_test1',
            're_bend_test1'
        ]

        one2many_fields = [
            'bar_test_line_ids'
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
