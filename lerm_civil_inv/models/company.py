from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    inv_header = fields.Binary("Invoice Header")
    inv_footer = fields.Binary("Invoice Footer")