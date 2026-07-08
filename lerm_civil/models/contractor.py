from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError

class ContactsInherited(models.Model):
    _inherit = "res.partner"

    contractor_table = fields.One2many('lerm.contractor.line','partner_id',string="Contractor")
    signature = fields.Binary(string="Signature")
    stamp = fields.Binary(string="Stamps")
    global_location_number = fields.Char(string="Global Location Number")
    billing_customers = fields.Many2many(
        'res.partner',
        relation='res_partner_billing_customer_rel',
        column1='partner_id',
        column2='billing_customer_id',
        string='Billing Customer'
    )


class ContractorLine(models.Model):
    _name = 'lerm.contractor.line'

    partner_id = fields.Many2one('res.partner')
    name = fields.Char(string='Contractor Name')