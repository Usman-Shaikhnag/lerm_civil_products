# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderPricelistLog(models.Model):
    _name = 'sale.order.pricelist.log'
    _description = 'Sales Order Pricelist Log'
    _order = 'id desc'

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', ondelete='cascade', index=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    product_tmpl_id = fields.Many2one('product.template', string='Product')
    parameter_id = fields.Many2one('lerm.parameter.master', string='Parameter')
    action = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
    ], string='Action', default='update')
    old_price = fields.Float(string='Old Price')
    new_price = fields.Float(string='New Price')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
