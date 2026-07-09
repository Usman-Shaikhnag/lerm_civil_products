from odoo import api, fields, models
from odoo.exceptions import UserError



class CoreCutterPrefillWizard(models.TransientModel):
    _name = 'mechanical.core.cutter.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template',string="Product")
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample")
    


    def prefill_data(self):
        current_product = self.env['mechanical.core.cutter'].sudo().browse(self._context['active_id'])
        copy_product = self.env['mechanical.core.cutter'].sudo().search([
            ('eln_ref.sample_id.id', '=', self.sample_id.id)
        ], limit=1)

        normal_fields = [
            'wt_of_modul',
            'vl_of_modul',

            
            'bulk_density_1',
            'bulk_density_2',
            'bulk_density_3',

            'moisture_content_1',
            'moisture_content_2',
             'moisture_content_3',

             'dry_density_1',
            'dry_density_2',
             'dry_density_3',

           

         

        ]

        one2many_fields = [
            'density_relation_table',
        
        ]

        update_vals = {}

        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, vals) for vals in (line.copy_data()[0] for line in lines)]

        if not current_product.density_relation_visible:
            update_vals.pop('density_relation_table', None)

       
        

        if update_vals:
            current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}
