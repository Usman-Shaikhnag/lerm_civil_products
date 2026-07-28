from odoo import api, fields, models

class BurntClayHollowBrickPrefillData(models.TransientModel):
    _name = "burnt.clay.hollow.brick.prefill.data"

    product_id = fields.Many2one('product.template', string="Product",required=True)
    sample_id = fields.Many2one('lerm.srf.sample',domain="[('material_id', '=', product_id), ('id', '!=', context.get('exclude_sample_id'))]", string="Sample") 

    def prefill_data(self):
        current_product = self.env['mechanical.burnt.clay.hollow.brick'].search([('eln_ref.sample_id','=',self.sample_id.id)])
        previous_product = self.env['mechanical.burnt.clay.hollow.brick'].search([('eln_ref.sample_id','!=',self.sample_id.id),('eln_ref.product_id','=',self.product_id.id)]).sorted(key=lambda r: r.id, reverse=True)

        previous_product = previous_product[0] if previous_product else None

        normal_fields = ['grade']

        one2many_fields = ['crushing_value_child_lines','dimension_child_lines']

        update_vals = {}
        if previous_product:
            for field in normal_fields:
                if hasattr(previous_product, field):
                    update_vals[field] = previous_product[field]

            for field in one2many_fields:
                if hasattr(current_product, field):
                    if not getattr(current_product, field):
                        if hasattr(previous_product, field):
                            lines = previous_product[field]
                            if lines:
                                update_vals[field] = [(0,0,line.copy_data()[0]) for line in lines]

            if not current_product.crushing_visible:
                update_vals.pop('crushing_value_child_lines', None)
            if not current_product.dimension_visible:
                update_vals.pop('dimension_child_lines', None)

        if current_product:
            current_product.write(update_vals)

        return {
            'type': 'ir.actions.act_window_close'
        }
