# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lerm_civil_sale_pricelist_validation = fields.Boolean(
        string='Pricelist Validation',
        config_parameter='lerm_civil_sale.pricelist_validation',
        default=False,
        help='When enabled, the pricelist validations in the LERM Civil Sale '
             'module are enforced (a pricelist must be attached to the customer '
             'and the default pricelist cannot be updated). Disabled by default.',
    )
