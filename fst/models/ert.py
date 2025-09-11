from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class LermErtParent(models.Model):
    _name = "lerm.ert.parent"
    _rec_name = "name"

    name = fields.Char("Project Name")
    ert_lines = fields.One2many('ert.lines','parent_id',"ERT Lines")
    rec_date  = fields.Date("Date")

    def create_ert(self):
        
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ert.soil.resistivity',   # must match the target model's _name
            'target': 'current',
            'context': {
                'default_ert_parent_id':self.id
            }
        }

    def print_report(self):
        # import wdb; wdb.set_trace()
        soil_resistivity_records = self.mapped("ert_lines.soil_resistivity_id")
        if not soil_resistivity_records:
            return
        for records in soil_resistivity_records:
            records.action_print_soil_resistivity_report() 


class LermErtLines(models.Model):
    _name = "ert.lines"  

    parent_id = fields.Many2one('lerm.ert.parent') 
    soil_resistivity_id = fields.Many2one('ert.soil.resistivity')
        

class ERTDashboard(models.Model):
    _name = "lerm.ert.dashboard"
    _description = "ERT Dashboard"

    def search(self, args, offset=0, limit=None, order=None, count=False):
    # always show 1 record
        res = super(ERTDashboard, self).search(args, offset=offset, limit=limit, order=order, count=count)
        if not res and not count:
            return self.create({})
        return res
    