# -*- coding: utf-8 -*-
from odoo import models, fields

class Equipment(models.Model):
    _name = 'lerm.equipment'
    _description = 'Laboratory Equipment'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    