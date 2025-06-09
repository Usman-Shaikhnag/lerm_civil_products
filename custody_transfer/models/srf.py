from odoo import api, fields, models
from odoo.exceptions import UserError



class Srf(models.Model):
    _inherit = "lerm.civil.srf"
    
    document_origin = fields.Selection([
        ('self', 'Self Created'),
        ('custody_transfer', 'Custody Transfer')
    ], string='Document Origin', default='self')
    
    collection_order = fields.Many2one("custody.transfer",string="Collection Order")