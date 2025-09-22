from odoo import models, fields ,api

class DatasheetMaster(models.Model):
    _name = 'lerm.datasheet.master'
    _rec_name = 'name'
    
    name = fields.Char("Name" , required=True)
    datasheet = fields.One2many('lerm.datasheet.line','datasheet_id',string="Datasheet")

class DatasheetLine(models.Model):
    _name = 'lerm.datasheet.line'
    _rec_name = 'parameter'
    datasheet_id = fields.Many2one('lerm.datasheet.master',string="Datasheet Id")
    parameter = fields.Many2one('lerm.parameter.master',string="Parameter")
    test_method = fields.Many2one('lerm_civil.test_method',string="Test Method")
    calculated = fields.Boolean("Calculated")


    @api.onchange("parameter")
    def onchange_parameter(self):
        for record in self:
            record.test_method = record.parameter.test_method.id
            record.calculated = record.parameter.calculated
