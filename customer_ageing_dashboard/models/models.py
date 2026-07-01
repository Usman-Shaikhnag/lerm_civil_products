from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    lerm_customer = fields.Boolean(string="Is LERM Customer", default=True)
