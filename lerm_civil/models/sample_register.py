from odoo import models, fields ,api

class LabMaster(models.Model):
    _name = 'lerm.sample.register'
    _rec_name = 'sample'

    sample = fields.Many2one('lerm.srf.sample',string="Sample")
    quantity = fields.Integer(string="Quantity")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")  
    quantity_received = fields.Integer(string="Quantity Received")
    quantity_consumed = fields.Integer(string="Quantity Consumed")
    quantity_balance = fields.Integer(string="Quantity Balance")
    resample_id = fields.Many2one('lerm.srf.sample',string="Sample")


    @api.depends('quantity_received', 'quantity_consumed','quantity_balance')
    def discard_quantity(self):
        for rec in self:
            rec.quantity_balance = 0