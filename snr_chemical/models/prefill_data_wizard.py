from odoo import api, fields, models
from odoo.exceptions import UserError



class SNRChemicalPrefillWizard(models.TransientModel):
    _name = 'snr.chemical.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['snr.chemical'].sudo().browse(self._context['active_id'])
        copy_product = self.env['snr.chemical'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'customer_name',
            'sample_description',
            'project_name',
            'no_of_samples',
            'date_received',
            'brand_grade',
            'size',
            'week_no',
            'test_method',
            'source_sample',
            'specification',

            'customer_ref',
            'letter_date',
            'test_init_date',
            'test_comp_date',
            'sample',
            
            

        ]

        one2many_fields = [
            'line_ids',
            
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.nan_nabl_visible:
            update_vals.pop('line_ids', None)

        
        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
