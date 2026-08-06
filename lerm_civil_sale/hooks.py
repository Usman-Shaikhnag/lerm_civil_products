# -*- coding: utf-8 -*-


def post_init_hook(env):
    """Backfill historical price changes recorded on the legacy
    sale.order.pricelist.log model into the new generic audit log."""
    Log = env['sale.order.pricelist.log']
    AuditLog = env['lerm.pricelist.audit.log'].sudo()
    old_records = Log.search([])
    if not old_records:
        return
    for rec in old_records:
        AuditLog.create({
            'source': 'sale_order',
            'sale_order_id': rec.sale_order_id.id,
            'pricelist_id': rec.pricelist_id.id,
            'product_tmpl_id': rec.product_tmpl_id.id,
            'parameter_id': rec.parameter_id.id,
            'action': rec.action or 'update',
            'old_price': rec.old_price,
            'new_price': rec.new_price,
            'user_id': rec.user_id.id,
            'timestamp': rec.timestamp,
        })
