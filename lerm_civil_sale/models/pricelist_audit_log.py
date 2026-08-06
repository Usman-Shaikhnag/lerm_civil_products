# -*- coding: utf-8 -*-
from odoo import api, fields, models


class LermPricelistAuditLog(models.Model):
    _name = 'lerm.pricelist.audit.log'
    _description = 'Pricelist Price Audit Log'
    _order = 'id desc'

    source = fields.Selection([
        ('sale_order', 'Sales Order'),
        ('pricelist', 'Pricelist (direct)'),
        ('product', 'Product Default Price'),
    ], string='Source', default='pricelist', index=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', ondelete='set null', index=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', index=True)
    pricelist_item_id = fields.Many2one('product.pricelist.item', string='Pricelist Item', ondelete='set null')
    product_tmpl_id = fields.Many2one('product.template', string='Product', index=True)
    parameter_id = fields.Many2one('lerm.parameter.master', string='Parameter')
    action = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
    ], string='Action', default='update')
    old_price = fields.Float(string='Old Price')
    new_price = fields.Float(string='New Price')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, index=True)
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, index=True)

    def action_open_sale_order(self):
        self.ensure_one()
        if not self.sale_order_id:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env['ir.actions.act_window']._for_xml_id('sale.action_orders')
        action['res_id'] = self.sale_order_id.id
        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        return action


class ProductPricelistAudit(models.Model):
    _inherit = 'product.pricelist'

    lerm_audit_log_ids = fields.One2many('lerm.pricelist.audit.log', 'pricelist_id', string='Price Audit Entries')
    lerm_audit_log_count = fields.Integer(
        string='Price Audit Entries',
        compute='_compute_lerm_audit_log_count',
    )

    @api.depends('lerm_audit_log_ids')
    def _compute_lerm_audit_log_count(self):
        for rec in self:
            rec.lerm_audit_log_count = len(rec.lerm_audit_log_ids)

    def action_view_lerm_audit_log(self):
        self.ensure_one()
        return {
            'name': 'Price Audit Log',
            'type': 'ir.actions.act_window',
            'res_model': 'lerm.pricelist.audit.log',
            'view_mode': 'tree',
            'domain': [('pricelist_id', '=', self.id)],
            'context': {'search_default_pricelist_id': self.id},
        }

