from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class ManholeCoverFrame(models.Model):
    _name = "manhole.cover.frame"
    _inherit = "lerm.eln"
    _description = 'manhole.cover.frame'
    _rec_name = "name"



    name = fields.Char("Name",default="Manhole Cover Frame")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id


    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

        
    def get_all_fields(self):
        record = self.env['manhole.cover.frame'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



    # LOAD TEST & PERMANENT SET TEST DATA
    load_permanent_set_test_name = fields.Char(default="LOAD TEST & PERMANENT SET TEST DATA")
    load_permanent_set_test_data_visible = fields.Boolean(compute="_compute_visible")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    load_permanent_set_test_lines = fields.One2many('load.permanent.set.test.line','parent_id',string="Parameter")
    
    
    # average_permanent_set = fields.Float('Average Permanent Set',compute="_compute_average_permanent_set")
    load_test_result = fields.Char("Load Test Result")
    # permanent_set_test_result = fields.Char("Permanent Set") 
   
   
    load_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
    ], string='Conformity', default='fail',compute="_compute_load_test_conformity")

    
    


 
    

    @api.depends('load_test_result','eln_ref','grade')
    def _compute_load_test_conformity(self):
        for record in self: 
            record.load_test_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','902f262d-e3c2-4e2d-881b-38f1ca647406')], limit=1)
            if not line:
                continue
            try:
                value = float(record.load_test_result)
            except (TypeError, ValueError):
                continue
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    # import wdb;wdb.set_trace();
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.load_test_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = value - value*mu_value
                    upper = value + value*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.load_test_conformity = 'pass'
                        break
                    else:
                        record.load_test_conformity = 'fail'
    
    load_test_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_load_test_nabl")


    @api.depends('load_test_result','eln_ref','grade')
    def _compute_load_test_nabl(self):

        for record in self:
            record.load_test_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','902f262d-e3c2-4e2d-881b-38f1ca647406')], limit=1)
            if not line:
                continue
            try:
                value = float(record.load_test_result)
            except (TypeError, ValueError):
                continue
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value

                    if not lab_min and not lab_max:
                        record.load_test_nabl = 'pass'
                        break

                    lower = value - value*mu_value
                    upper = value + value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.load_test_nabl = 'pass'
                        break
                    else:
                        record.load_test_nabl = 'fail'


    
    
    average_permanent_set = fields.Float('Average Permanent Set',compute="_compute_average_permanent_set")
    permanent_set_test_result = fields.Char("Permanent Set") 
   
   
    permanent_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
    ], string='Conformity', default='fail',compute="_compute_permanent_conformity")

    
    


 
    

    @api.depends('average_permanent_set','eln_ref','grade')
    def _compute_permanent_conformity(self):
        for record in self: 
            record.permanent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','195616f3-5162-4ee3-a16e-52e6266e1307')], limit=1)
            if not line:
                continue
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    # import wdb;wdb.set_trace();
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.permanent_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_permanent_set - record.average_permanent_set*mu_value
                    upper = record.average_permanent_set + record.average_permanent_set*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.permanent_conformity = 'pass'
                        break
                    else:
                        record.permanent_conformity = 'fail'
    
    permanent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_permanent_nabl")


    @api.depends('average_permanent_set','eln_ref','grade')
    def _compute_permanent_nabl(self):

        for record in self:
            record.permanent_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','195616f3-5162-4ee3-a16e-52e6266e1307')], limit=1)
            if not line:
                continue
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value

                    if not lab_min and not lab_max:
                        record.permanent_nabl = 'pass'
                        break

                    lower = record.average_permanent_set - record.average_permanent_set*mu_value
                    upper = record.average_permanent_set + record.average_permanent_set*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.permanent_nabl = 'pass'
                        break
                    else:
                        record.permanent_nabl = 'fail'
                        
                        
    @api.depends('load_permanent_set_test_lines.permanent_set')
    def _compute_average_permanent_set(self):
        for record in self:
            try:
                record.average_permanent_set = round(sum(record.load_permanent_set_test_lines.mapped('permanent_set')) / len(
                    record.load_permanent_set_test_lines),4)
            except:
                record.average_permanent_set = 0


#DEFECTS & WORKMANSHIP TEST DATA					
    
    defects_workmanship_test_name = fields.Char(default="DEFECTS & WORKMANSHIP TEST DATA")
    defects_workmanship_test_data_visible = fields.Boolean(compute="_compute_visible")
    defects_workmanship_test_data_line = fields.One2many('defects.workmanship.test.line','parent_id',string="Parameter")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    defects_workmanship_test_result = fields.Char(" DEFECTS & WORKMANSHIP") 


    # defect_test_conformity = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),
    #     ('--', '--')
    # ], string='Conformity', default='fail',compute="_compute_defect_test_conformity")
    # defect_nabl = fields.Selection([
    #     ('pass', 'NABL'),
    #     ('fail', 'NON NABL'),
    # ], string='NABL', default='fail',compute="_compute_defect_nabl")

    # @api.depends('average_permanent_set','eln_ref','grade')
    # def _compute_defect_test_conformity(self):
    #     for record in self: 
    #         record.defect_test_conformity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fefc06a7-a312-44d8-b0c1-70166720935d')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fefc06a7-a312-44d8-b0c1-70166720935d')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 # import wdb;wdb.set_trace();
    #                 if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
    #                     record.defect_test_conformity = '--'
    #                     break
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
    #                 lower = record.average_permanent_set - record.average_permanent_set*mu_value
    #                 upper = record.average_permanent_set + record.average_permanent_set*mu_value
    #                 if lower >= req_min and upper <= req_max :
    #                     record.load_permanent_test_conformity = 'pass'
    #                     break
    #                 else:
    #                     record.load_permanent_test_conformity = 'fail'

    # @api.depends('average_permanent_set','eln_ref','grade')
    # def _compute_load_permanent_set_nabl(self):

    #     for record in self:
    #         record.load_permanent_set_nabl = 'pass'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','902f262d-e3c2-4e2d-881b-38f1ca647406')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','902f262d-e3c2-4e2d-881b-38f1ca647406')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value

    #                 if not lab_min and not lab_max:
    #                     record.load_permanent_set_nabl = 'pass'
    #                     break

    #                 lower = record.average_permanent_set - record.average_permanent_set*mu_value
    #                 upper = record.average_permanent_set + record.average_permanent_set*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.load_permanent_set_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.load_permanent_set_nabl = 'fail'

    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            record.load_permanent_set_test_data_visible = False
            record.defects_workmanship_test_data_visible = False

            for sample in record.sample_parameters:
                if sample.internal_id == '902f262d-e3c2-4e2d-881b-38f1ca647406':
                    record.load_permanent_set_test_data_visible = True
                if sample.internal_id =='fefc06a7-a312-44d8-b0c1-70166720935d':
                    record.defects_workmanship_test_data_visible = True

    def open_eln_page(self):
            # import wdb; wdb.set_trace()
            self.eln_ref.write({'invisible_fetch_inputs': True})
            for result in self.eln_ref.parameters_result:
                # load test
                if result.parameter.internal_id == '902f262d-e3c2-4e2d-881b-38f1ca647406':
                    try:
                        result.result_char = str(round(float(self.load_test_result), 3))
                    except (TypeError, ValueError):
                        result.result_char = self.load_test_result
                    result.calculated = True

                    if self.load_test_nabl == 'pass':
                        result.nabl_status = 'nabl'
                    else:
                        result.nabl_status = 'non-nabl'
                    continue

                            # # defects 
                if result.parameter.internal_id == '195616f3-5162-4ee3-a16e-52e6266e1307':
                    result.result_char = round(self.average_permanent_set,3)
                    result.calculated = True


                    if self.permanent_nabl == 'pass':
                        result.nabl_status = 'nabl'
                    else:
                        result.nabl_status = 'non-nabl'

            # defects 
                if result.parameter.internal_id == 'fefc06a7-a312-44d8-b0c1-70166720935d':
                    # result.result_char = round(self.average_permanent_set,3)
                    result.calculated = True

            # # defects 
            #     if result.parameter.internal_id == 'fefc06a7-a312-44d8-b0c1-70166720935d':
            #         # result.result_char = round(self.average_permanent_set,3)
            #         result.calculated = True


                    # if self.average_permanent_set_nabl == 'pass':
                    #     result.nabl_status = 'nabl'
                    # else:
                    #     result.nabl_status = 'non-nabl'
                    continue

            return {
                    'view_mode': 'form',
                    'res_model': "lerm.eln",
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'res_id': self.eln_ref.id,
            }


    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(ManholeCoverFrame, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()

        return super(ManholeCoverFrame, self).read(fields=fields, load=load)

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['manhole.cover.frame'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


class ManholeCoverFrameLine(models.Model):
    _name = "load.permanent.set.test.line"
    parent_id = fields.Many2one('manhole.cover.frame', string="Parent Id")
    load_permanent_set_test_name = fields.Char(default="LOAD TEST & PERMANENT SET TEST DATA")
    initial_gauge = fields.Float("Initial Gauge Reading (mm)")
    final_gauge = fields.Float("Final Gauge Reading After Load (mm)")
    permanent_set = fields.Float("Permanent Set = (Final - Initial) (mm)", compute="_compute_permanent_set", store=True, digits=(10, 4))
    specified_load = fields.Float("Specified Load (KN)")
    load_holding_time = fields.Float("Load Hold Time (sec)")
    load_test_result = fields.Char("Load Test Result")
   

    @api.depends('final_gauge','initial_gauge')
    def _compute_permanent_set(self):
        for record in self:
            if record.final_gauge:
                record.permanent_set = round(record.final_gauge - record.initial_gauge, 4)
            else:
                record.permanent_set = 0.0

class DefectsWorkmanshipTestLine(models.Model):
    _name = "defects.workmanship.test.line"
    _description = "Defects and Workmanship Test Line"

    parent_id = fields.Many2one('manhole.cover.frame',string="Parent Id")
    specimen_no = fields.Integer("Specimen No.",default=1)
    defects_workmanship_test_name = fields.Char("DEFECTS & WORKMANSHIP TEST DATA")
    visual_inspection_parameter = fields.Char("Visual Inspection Parameter")
    defects_workmanship_test_result = fields.Char(" DEFECTS & WORKMANSHIP") 
    
    specified_requirements = fields.Selection([
        ('defect_free', 'Should be completely free from defects'),
        ('clean_edges', 'Edges must be clean, true, and square'),
        ('no_cracks', 'No structural cracks wider than 0.2 mm'),
    ], string="Specified Requirements (IS 12592)")

    observed_conditions = fields.Selection([
        ('dense_concrete', 'Dense concrete, smooth surfaces found'),
        ('clean_molded_edges', 'Edges are clean and properly molded'),
        ('no_hair_cracks', 'No hair cracks observed'),
    ], string="Observed Conditions")

    con = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string="Conformity")


def get_selection_label(self, field_name, value):
    field = self._fields.get(field_name)

    if not field or not value:
        return ''

    selection = field._description_selection(self.env)
    return dict(selection).get(value, value)

class ManholeCoverNotes(models.Model):
    _name = "manhole.cover.notes"

    parent_id = fields.Many2one('manhole.cover.frame',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



