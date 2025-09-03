from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class LermErtParent(models.Model):
    _name = "lerm.ert.parent"
    _rec_name = "name"

    name = fields.Char("Name")
    ert_lines = fields.One2many('ert.lines','parent_id',"ERT Lines")

    def create_ert(self):
        
        # import wdb; wdb.set_trace()
        # self.ert_lines.sudo().create({
        #     'parent_id':self.id,
        #     # 'soil_resistivity_id':self.id
        # })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ert.soil.resistivity',   # must match the target model's _name
            'target': 'current',
            'context': {
                'default_ert_parent_id':self.id
            }
        }
    
    

class LermErtLines(models.Model):
    _name = "ert.lines"  

    parent_id = fields.Many2one('lerm.ert.parent') 
    soil_resistivity_id = fields.Many2one('ert.soil.resistivity')
        

class ERTDashboard(models.TransientModel):
    _name = "lerm.ert.dashboard"
    _description = "ERT Dashboard"

    def search(self, args, offset=0, limit=None, order=None, count=False):
    # always show 1 record
        res = super(ERTDashboard, self).search(args, offset=offset, limit=limit, order=order, count=count)
        if not res and not count:
            return self.create({})
        return res
    
