from odoo import models, fields

class FTPStorage(models.Model):
    _name = 'ftp.storage'
    _description = 'FTP Storage Configuration'

    name = fields.Char(string='Name', required=True)
    host = fields.Char(string='Host', required=True)
    port = fields.Integer(string='Port', default=21)
    username = fields.Char(string='Username')
    password = fields.Char(string='Password')
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')