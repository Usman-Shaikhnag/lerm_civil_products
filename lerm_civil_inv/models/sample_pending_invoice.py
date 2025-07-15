from odoo import api, fields, models
from odoo.exceptions import UserError


class SamplePendingInvoice(models.Model):
    _name = "sample.pending.invoice"

    srf_id = fields.Many2one('lerm.civil.srf',string='SRF ID')
    kes_no = fields.Many2one('lerm.srf.sample',string='KES NO')
    customer = fields.Many2one('res.partner',string="Customer")
    pricelist = fields.Many2one('product.pricelist',string='Pricelist')
    amount = fields.Float(string="Amount")
    invoiced = fields.Boolean(string='Invoiced',readonly=True)