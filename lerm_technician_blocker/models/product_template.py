from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ownership_ids = fields.Many2many(
        'res.users',
        'lerm_product_ownership_rel',
        'product_id',
        'user_id',
        string='Ownership',
        help='Technicians responsible for the tests of this material. They are '
             'notified when a confirmed sample of this material becomes pending work.',
    )
