from odoo import api, fields, models
from odoo.exceptions import UserError


class BitumenMacadamPrefillWizard(models.TransientModel):
    _name = 'bitumen.macadam.prefill.data'
    _description = 'Prefill Data'

    product_id = fields.Many2one('product.template', string="Product")
    sample_id = fields.Many2one(
        'lerm.srf.sample',
        domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]",
        string="Sample"
    )

    def prefill_data(self):
        # Current active Bitumen Macadam record
        current_product = self.env['bituminous.macadam'].sudo().browse(self._context['active_id'])

        # Fetch previous Bitumen Macadam record for selected sample
        copy_product = self.env['bituminous.macadam'].sudo().search([
            ('eln_ref.sample_id', '=', self.sample_id.id)   # <<< FIXED
        ], limit=1)

        if not copy_product:
            raise UserError("Selected sample does not have any previous Bitumen Macadam record.")

        # List of direct fields to copy
        normal_fields = [
            'weight_of_sample' , 'wt_of_sample' ,  'init_wt_filter_paper' , 'wt_agg_extraction' , 'wt_filter_paper_after_extraction' , 
        ]

        one2many_fields = [
            'combined_gradation_child_lines',

        ]

        update_vals = {}

        # Copy simple fields
        for field in normal_fields:
            if hasattr(copy_product, field):
                update_vals[field] = getattr(copy_product, field)

        # Copy one2many fields
        for field in one2many_fields:
            lines = getattr(copy_product, field)
            if lines:
                update_vals[field] = [(0, 0, line.copy_data()[0]) for line in lines]

        # Check visibility and remove fields if not visible
        if not current_product.combined_gradation_visible:
            update_vals.pop('combined_gradation_child_lines', None)


        # if not current_product.bitumen_content_visible:
        #     update_vals.pop('combined_gradation_child_lines', None)


        # Apply copied data to current GGBS record
        current_product.sudo().write(update_vals)

        return {'type': 'ir.actions.act_window_close'}