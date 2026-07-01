from odoo import models, fields

class PartnerDocument(models.Model):
    _name = 'partner.document'
    _description = 'Partner Document'

    name = fields.Char(string="Name", required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    document = fields.Binary(string='Document File')
    document_name = fields.Char(string='Document File Name')