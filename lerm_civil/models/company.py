from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError


class LabCompany(models.Model):
    _inherit = "res.company"
    lab_certificate_no = fields.Char("Lab Certificate No .",size=6, size_min=6)
    lab_location = fields.Char("Lab Location ." , size=2, size_min=2)
    # non_nabl = fields.Char("Non-NABL" , size=1, size_min=1)
    # lab_location1 = fields.Char(string="Non Nabl")