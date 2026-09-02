from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math



class PaverBlock(models.Model):
    _name = "mechanical.paver.block"
    _inherit = "lerm.eln"
    _rec_name = "name_paver"


    name_paver = fields.Char("Name",default="Paver Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # tests = fields.Many2many("mechanical.pever.block.test",string="Tests")

    notes_id = fields.One2many('mechanical.paver.block.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(PaverBlock, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The Test Report(s) is/are valid only to the sample submitted to the laboratory.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sample(s) was/were not drawn by laboratory.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'This Report may not be reproduced in except full/ part without the permission of the Lab Head of the Laboratory.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': '# - Information provided by the customer.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    

    paver_name = fields.Char("Name",default="Tensile Splitting Strength")
    paver_visible = fields.Boolean("Tensile Splitting Strength Visible",compute="_compute_visible")
    # job_no_soil = fields.Char(string="Job No")
    # material_soil = fields.Char(String="Material")
    # start_date_soil = fields.Date("Start Date")
    # end_date_soil = fields.Date("End Date")
    # soil_table = fields.One2many('mechanical.soils.cbr.line','parent_id',string="CBR")

    mean_of_lenght1 = fields.Float(string="Mean of failure Length in mm (l)")
    mean_of_lenght2 = fields.Float(string="Mean of failure Length in mm (l)")
    mean_of_lenght3 = fields.Float(string="Mean of failure Length in mm (l)")
    mean_of_lenght4 = fields.Float(string="Mean of failure Length in mm (l)")
    mean_of_lenght5 = fields.Float(string="Mean of failure Length in mm (l)")
    mean_of_lenght6 = fields.Float(string="Mean of failure Length in mm (l)")
    mean_of_lenght7 = fields.Float(string="Mean of failure Length in mm (l)")
    mean_of_lenght8 = fields.Float(string="Mean of failure Length in mm (l)")

    mean_thickness1 = fields.Float(string="Mean of failure Thickness in mm (t)")
    mean_thickness2 = fields.Float(string="Mean of failure Thickness in mm (t)")
    mean_thickness3 = fields.Float(string="Mean of failure Thickness in mm (t)")
    mean_thickness4 = fields.Float(string="Mean of failure Thickness in mm (t)")
    mean_thickness5 = fields.Float(string="Mean of failure Thickness in mm (t)")
    mean_thickness6 = fields.Float(string="Mean of failure Thickness in mm (t)")
    mean_thickness7 = fields.Float(string="Mean of failure Thickness in mm (t)")
    mean_thickness8 = fields.Float(string="Mean of failure Thickness in mm (t)")


    area1 = fields.Float(string="Area of Failure = l x t in mm2", compute="_compute_area1")
    area2 = fields.Float(string="Area of Failure = l x t in mm2", compute="_compute_area2")
    area3 = fields.Float(string="Area of Failure = l x t in mm2", compute="_compute_area3")
    area4 = fields.Float(string="Area of Failure = l x t in mm2", compute="_compute_area4")
    area5 = fields.Float(string="Area of Failure = l x t in mm2", compute="_compute_area5")
    area6 = fields.Float(string="Area of Failure = l x t in mm2", compute="_compute_area6")
    area7 = fields.Float(string="Area of Failure = l x t in mm2", compute="_compute_area7")
    area8 = fields.Float(string="Area of Failure = l x t in mm2", compute="_compute_area8")

    failure_load1 = fields.Float(string="Failure Load in N")
    failure_load2 = fields.Float(string="Failure Load in N")
    failure_load3 = fields.Float(string="Failure Load in N")
    failure_load4 = fields.Float(string="Failure Load in N")
    failure_load5 = fields.Float(string="Failure Load in N")
    failure_load6 = fields.Float(string="Failure Load in N")
    failure_load7 = fields.Float(string="Failure Load in N")
    failure_load8 = fields.Float(string="Failure Load in N")

    st_correction_factor1 = fields.Float(string="Correction Factor")
    st_correction_factor2 = fields.Float(string="Correction Factor")
    st_correction_factor3 = fields.Float(string="Correction Factor")
    st_correction_factor4 = fields.Float(string="Correction Factor")
    st_correction_factor5 = fields.Float(string="Correction Factor")
    st_correction_factor6 = fields.Float(string="Correction Factor")
    st_correction_factor7 = fields.Float(string="Correction Factor")
    st_correction_factor8 = fields.Float(string="Correction Factor")

    split_tensile1 = fields.Float(string="Tensile Splitting Strength in N/mm2",compute="_compute_split_tensile1")
    split_tensile2 = fields.Float(string="Tensile Splitting Strength in N/mm2",compute="_compute_split_tensile2")
    split_tensile3 = fields.Float(string="Tensile Splitting Strength in N/mm2",compute="_compute_split_tensile3")
    split_tensile4 = fields.Float(string="Tensile Splitting Strength in N/mm2",compute="_compute_split_tensile4")
    split_tensile5 = fields.Float(string="Tensile Splitting Strength in N/mm2",compute="_compute_split_tensile5")
    split_tensile6 = fields.Float(string="Tensile Splitting Strength in N/mm2",compute="_compute_split_tensile6")
    split_tensile7 = fields.Float(string="Tensile Splitting Strength in N/mm2",compute="_compute_split_tensile7")
    split_tensile8 = fields.Float(string="Tensile Splitting Strength in N/mm2",compute="_compute_split_tensile8")

    average = fields.Float(string="AverageTensile Splitting Strength in N/mm2",compute="_compute_average")

    average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Conformity", compute="_compute_average_conformity", store=True)



    @api.depends('average','eln_ref','grade')
    def _compute_average_conformity(self):
        
        for record in self:
            record.average_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','938992f7-199c-497a-b3a7-45023c604673')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','938992f7-199c-497a-b3a7-45023c604673')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average - record.average*mu_value
                    upper = record.average + record.average*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_conformity = 'pass'
                        break
                    else:
                        record.average_conformity = 'fail'

    average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_nabl", store=True)

    @api.depends('average','eln_ref','grade')
    def _compute_average_nabl(self):
        
        for record in self:
            record.average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','938992f7-199c-497a-b3a7-45023c604673')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','938992f7-199c-497a-b3a7-45023c604673')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average - record.average*mu_value
                    upper = record.average + record.average*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_nabl = 'pass'
                        break
                    else:
                        record.average_nabl = 'fail'



    @api.depends('mean_of_lenght1', 'mean_thickness1')
    def _compute_area1(self):
        for record in self:
            record.area1 = record.mean_of_lenght1 * record.mean_thickness1

    @api.depends('mean_of_lenght2', 'mean_thickness2')
    def _compute_area2(self):
        for record in self:
            record.area2 = record.mean_of_lenght2 * record.mean_thickness2


    @api.depends('mean_of_lenght3', 'mean_thickness3')
    def _compute_area3(self):
        for record in self:
            record.area3 = record.mean_of_lenght3 * record.mean_thickness3


    @api.depends('mean_of_lenght4', 'mean_thickness4')
    def _compute_area4(self):
        for record in self:
            record.area4 = record.mean_of_lenght4 * record.mean_thickness4



    @api.depends('mean_of_lenght5', 'mean_thickness5')
    def _compute_area5(self):
        for record in self:
            record.area5 = record.mean_of_lenght5 * record.mean_thickness5


    @api.depends('mean_of_lenght6', 'mean_thickness6')
    def _compute_area6(self):
        for record in self:
            record.area6 = record.mean_of_lenght6 * record.mean_thickness6


    @api.depends('mean_of_lenght7', 'mean_thickness7')
    def _compute_area7(self):
        for record in self:
            record.area7 = record.mean_of_lenght7 * record.mean_thickness7


    @api.depends('mean_of_lenght8', 'mean_thickness8')
    def _compute_area8(self):
        for record in self:
            record.area8 = record.mean_of_lenght8 * record.mean_thickness8


    @api.depends('failure_load1', 'area1','st_correction_factor1')
    def _compute_split_tensile1(self):
        for record in self:
            if record.area1 != 0:
                record.split_tensile1 = 0.637*record.failure_load1*record.st_correction_factor1 / record.area1
            else:
                record.split_tensile1 = 0.0

    @api.depends('failure_load2', 'area2','st_correction_factor2')
    def _compute_split_tensile2(self):
        for record in self:
            if record.area2 != 0:
                record.split_tensile2 = 0.637*record.failure_load2*record.st_correction_factor2 / record.area2
            else:
                record.split_tensile2 = 0.0

    @api.depends('failure_load3', 'area3','st_correction_factor3')
    def _compute_split_tensile3(self):
        for record in self:
            if record.area3 != 0:
                record.split_tensile3 = 0.637*record.failure_load3*record.st_correction_factor3 / record.area3
            else:
                record.split_tensile3 = 0.0



    @api.depends('failure_load4', 'area4','st_correction_factor4')
    def _compute_split_tensile4(self):
        for record in self:
            if record.area4 != 0:
                record.split_tensile4 = 0.637*record.failure_load4*record.st_correction_factor4 / record.area4
            else:
                record.split_tensile4 = 0.0

    @api.depends('failure_load5', 'area5','st_correction_factor5')
    def _compute_split_tensile5(self):
        for record in self:
            if record.area5 != 0:
                record.split_tensile5 = 0.637*record.failure_load5*record.st_correction_factor5 / record.area5
            else:
                record.split_tensile5 = 0.0


    @api.depends('failure_load6', 'area6','st_correction_factor6')
    def _compute_split_tensile6(self):
        for record in self:
            if record.area6 != 0:
                record.split_tensile6 = 0.637*record.failure_load6*record.st_correction_factor6 / record.area6
            else:
                record.split_tensile6 = 0.0

    @api.depends('failure_load7', 'area7','st_correction_factor7')
    def _compute_split_tensile7(self):
        for record in self:
            if record.area7 != 0:
                record.split_tensile7 = 0.637*record.failure_load7*record.st_correction_factor7 / record.area7
            else:
                record.split_tensile7 = 0.0

    @api.depends('failure_load8', 'area8','st_correction_factor8')
    def _compute_split_tensile8(self):
        for record in self:
            if record.area8 != 0:
                record.split_tensile8 = 0.637*record.failure_load8*record.st_correction_factor8 / record.area8
            else:
                record.split_tensile8 = 0.0


 
    @api.depends('split_tensile1', 'split_tensile2', 'split_tensile3', 'split_tensile4', 'split_tensile5', 'split_tensile6', 'split_tensile7', 'split_tensile8')
    def _compute_average(self):
        for record in self:
            # Calculate the average of split tensile strength values
            split_tensile_values = [
                record.split_tensile1, record.split_tensile2, record.split_tensile3,
                record.split_tensile4, record.split_tensile5, record.split_tensile6,
                record.split_tensile7, record.split_tensile8
            ]

            # Filter out None values (computed fields might be None before computation)
            filtered_values = [val for val in split_tensile_values if val is not None]

            # Calculate the average only if there are valid values
            record.average = sum(filtered_values) / len(filtered_values) if filtered_values else 0



    commpressive_name = fields.Char("Name",default=" Compressive Strength")
    commpressive_visible = fields.Boolean(" Compressive Strength Visible",compute="_compute_visible")      

    areas1 = fields.Float(string="Area of Paver Block, mm2")  
    areas2 = fields.Float(string="Area of Paver Block, mm2") 
    areas3 = fields.Float(string="Area of Paver Block, mm2") 
    areas4 = fields.Float(string="Area of Paver Block, mm2") 
    areas5 = fields.Float(string="Area of Paver Block, mm2") 
    areas6 = fields.Float(string="Area of Paver Block, mm2") 
    areas7 = fields.Float(string="Area of Paver Block, mm2") 
    areas8 = fields.Float(string="Area of Paver Block, mm2") 

    crushing_load1 = fields.Float(string="Crushing Load, KN")
    crushing_load2 = fields.Float(string="Crushing Load, KN")
    crushing_load3 = fields.Float(string="Crushing Load, KN")
    crushing_load4 = fields.Float(string="Crushing Load, KN")
    crushing_load5 = fields.Float(string="Crushing Load, KN")
    crushing_load6 = fields.Float(string="Crushing Load, KN")
    crushing_load7 = fields.Float(string="Crushing Load, KN")
    crushing_load8 = fields.Float(string="Crushing Load, KN")

    compressive1 = fields.Float(string=" Compressive Strength, N/mm²",compute="_compute_compressive1")
    compressive2 = fields.Float(string=" Compressive Strength, N/mm²",compute="_compute_compressive2")
    compressive3 = fields.Float(string=" Compressive Strength, N/mm²",compute="_compute_compressive3")
    compressive4 = fields.Float(string=" Compressive Strength, N/mm²",compute="_compute_compressive4")
    compressive5 = fields.Float(string=" Compressive Strength, N/mm²",compute="_compute_compressive5")
    compressive6 = fields.Float(string=" Compressive Strength, N/mm²",compute="_compute_compressive6")
    compressive7 = fields.Float(string=" Compressive Strength, N/mm²",compute="_compute_compressive7")
    compressive8 = fields.Float(string=" Compressive Strength, N/mm²",compute="_compute_compressive8")

    correction_factor1 = fields.Float(string="Correction Factor")
    correction_factor2 = fields.Float(string="Correction Factor")
    correction_factor3 = fields.Float(string="Correction Factor")
    correction_factor4 = fields.Float(string="Correction Factor")
    correction_factor5 = fields.Float(string="Correction Factor")
    correction_factor6 = fields.Float(string="Correction Factor")
    correction_factor7 = fields.Float(string="Correction Factor")
    correction_factor8 = fields.Float(string="Correction Factor")

    correct_compressive1 = fields.Float(string="Corrected Compressive Strength,  N/mm²",compute="_compute_correct_comp1")
    correct_compressive2 = fields.Float(string="Corrected Compressive Strength,  N/mm²",compute="_compute_correct_comp2")
    correct_compressive3 = fields.Float(string="Corrected Compressive Strength,  N/mm²",compute="_compute_correct_comp3")
    correct_compressive4 = fields.Float(string="Corrected Compressive Strength,  N/mm²",compute="_compute_correct_comp4")
    correct_compressive5 = fields.Float(string="Corrected Compressive Strength,  N/mm²",compute="_compute_correct_comp5")
    correct_compressive6 = fields.Float(string="Corrected Compressive Strength,  N/mm²",compute="_compute_correct_comp6")
    correct_compressive7 = fields.Float(string="Corrected Compressive Strength,  N/mm²",compute="_compute_correct_comp7")
    correct_compressive8 = fields.Float(string="Corrected Compressive Strength,  N/mm²",compute="_compute_correct_comp8")

    average1 = fields.Float(string="Average Compressive Strength N/mm²",compute="_compute_average1")


    average1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Conformity", compute="_compute_average1_conformity", store=True)



    @api.depends('average1','eln_ref','grade')
    def _compute_average1_conformity(self):
        
        for record in self:
            record.average1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d2b88f2-5dc9-4a2a-8bf0-1281d1865a11')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d2b88f2-5dc9-4a2a-8bf0-1281d1865a11')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average1_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average1 - record.average1*mu_value
                    upper = record.average1 + record.average1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average1_conformity = 'pass'
                        break
                    else:
                        record.average1_conformity = 'fail'

    average1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average1_nabl", store=True)

    @api.depends('average1','eln_ref','grade')
    def _compute_average1_nabl(self):
        
        for record in self:
            record.average1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d2b88f2-5dc9-4a2a-8bf0-1281d1865a11')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d2b88f2-5dc9-4a2a-8bf0-1281d1865a11')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average1 - record.average1*mu_value
                    upper = record.average1 + record.average1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average1_nabl = 'pass'
                        break
                    else:
                        record.average1_nabl = 'fail'

    @api.depends('crushing_load1', 'areas1')
    def _compute_compressive1(self):
        for record in self:
            if record.areas1 != 0:
                record.compressive1 = (record.crushing_load1 * 1000) / record.areas1
            else:
                record.compressive1 = 0.0

    @api.depends('crushing_load2', 'areas2')
    def _compute_compressive2(self):
        for record in self:
            if record.areas2 != 0:
                record.compressive2 = (record.crushing_load2 * 1000) / record.areas2
            else:
                record.compressive2 = 0.0


    @api.depends('crushing_load3', 'areas3')
    def _compute_compressive3(self):
        for record in self:
            if record.areas3 != 0:
                record.compressive3 = (record.crushing_load3 * 1000) / record.areas3
            else:
                record.compressive3 = 0.0

    @api.depends('crushing_load4', 'areas4')
    def _compute_compressive4(self):
        for record in self:
            if record.areas4 != 0:
                record.compressive4 = (record.crushing_load4 * 1000) / record.areas4
            else:
                record.compressive4 = 0.0


    @api.depends('crushing_load5', 'areas5')
    def _compute_compressive5(self):
        for record in self:
            if record.areas5 != 0:
                record.compressive5 = (record.crushing_load5 * 1000) / record.areas5
            else:
                record.compressive5 = 0.0


    @api.depends('crushing_load6', 'areas6')
    def _compute_compressive6(self):
        for record in self:
            if record.areas6 != 0:
                record.compressive6 = (record.crushing_load6 * 1000) / record.areas6
            else:
                record.compressive6 = 0.0


    @api.depends('crushing_load7', 'areas7')
    def _compute_compressive7(self):
        for record in self:
            if record.areas7 != 0:
                record.compressive7 = (record.crushing_load7 * 1000) / record.areas7
            else:
                record.compressive7 = 0.0


    @api.depends('crushing_load8', 'areas8')
    def _compute_compressive8(self):
        for record in self:
            if record.areas8 != 0:
                record.compressive8 = (record.crushing_load8 * 1000) / record.areas8
            else:
                record.compressive8 = 0.0



    @api.depends('compressive1', 'correction_factor1')
    def _compute_correct_comp1(self):
        for record in self:
            record.correct_compressive1 = record.compressive1 * record.correction_factor1

    @api.depends('compressive2', 'correction_factor2')
    def _compute_correct_comp2(self):
        for record in self:
            record.correct_compressive2 = record.compressive2 * record.correction_factor2


    @api.depends('compressive3', 'correction_factor3')
    def _compute_correct_comp3(self):
        for record in self:
            record.correct_compressive3 = record.compressive3 * record.correction_factor3

    @api.depends('compressive4', 'correction_factor4')
    def _compute_correct_comp4(self):
        for record in self:
            record.correct_compressive4 = record.compressive4 * record.correction_factor4

   
    @api.depends('compressive5', 'correction_factor5')
    def _compute_correct_comp5(self):
        for record in self:
            record.correct_compressive5 = record.compressive5 * record.correction_factor5


    @api.depends('compressive6', 'correction_factor6')
    def _compute_correct_comp6(self):
        for record in self:
            record.correct_compressive6 = record.compressive6 * record.correction_factor6

    @api.depends('compressive7', 'correction_factor7')
    def _compute_correct_comp7(self):
        for record in self:
            record.correct_compressive7 = record.compressive7 * record.correction_factor7

    @api.depends('compressive8', 'correction_factor8')
    def _compute_correct_comp8(self):
        for record in self:
            record.correct_compressive8 = record.compressive8 * record.correction_factor8


    @api.depends('correct_compressive1', 'correct_compressive2', 'correct_compressive3', 'correct_compressive4', 'correct_compressive5', 'correct_compressive6', 'correct_compressive7', 'correct_compressive8')
    def _compute_average1(self):
        for record in self:
            # Calculate the average of split tensile strength values
            correct_compressive_values = [
                record.correct_compressive1, record.correct_compressive2, record.correct_compressive3,
                record.correct_compressive4, record.correct_compressive5, record.correct_compressive6,
                record.correct_compressive7, record.correct_compressive8
            ]

            # Filter out None values (computed fields might be None before computation)
            filtered_values = [val for val in correct_compressive_values if val is not None]

            # Calculate the average only if there are valid values
            record.average1 = sum(filtered_values) / len(filtered_values) if filtered_values else 0


    water_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")      

    initial_wt1 = fields.Float(string="Initial Weight (wt. after 24 hour emersion in water)")   
    initial_wt2 = fields.Float(string="Initial Weight (wt. after 24 hour emersion in water)") 
    initial_wt3 = fields.Float(string="Initial Weight (wt. after 24 hour emersion in water)")   


    dry_wt1 = fields.Float(string="Dry Weight (after 24 hour in oven)")  
    dry_wt2 = fields.Float(string="Dry Weight (after 24 hour in oven)")
    dry_wt3 = fields.Float(string="Dry Weight (after 24 hour in oven)") 

    water_absorption1 = fields.Float(string="Water Absorption %",compute="_compute_water_absorption1")
    water_absorption2 = fields.Float(string="Water Absorption %",compute="_compute_water_absorption2")
    water_absorption3 = fields.Float(string="Water Absorption %",compute="_compute_water_absorption3")


    average_water = fields.Float(string="Average Water Absorption %",compute="_compute_average_water")

    average_water_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Conformity", compute="_compute_average_water_conformity", store=True)



    @api.depends('average_water','eln_ref','grade')
    def _compute_average_water_conformity(self):
        
        for record in self:
            record.average_water_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','56859103-eba3-4f15-b33d-679b39f7372e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','56859103-eba3-4f15-b33d-679b39f7372e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_water_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_water - record.average_water*mu_value
                    upper = record.average_water + record.average_water*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_water_conformity = 'pass'
                        break
                    else:
                        record.average_water_conformity = 'fail'

    average_water_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_water_nabl", store=True)

    @api.depends('average_water','eln_ref','grade')
    def _compute_average_water_nabl(self):
        
        for record in self:
            record.average_water_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','56859103-eba3-4f15-b33d-679b39f7372e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','56859103-eba3-4f15-b33d-679b39f7372e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_water - record.average_water*mu_value
                    upper = record.average_water + record.average_water*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_water_nabl = 'pass'
                        break
                    else:
                        record.average_water_nabl = 'fail'





    @api.depends('initial_wt1', 'dry_wt1')
    def _compute_water_absorption1(self):
        for record in self:
            print("_compute_water_absorption1 before if ")
            if record.dry_wt1 != 0:
                print("_compute_water_absorption1 in if ")
                record.water_absorption1 = ((record.initial_wt1 - record.dry_wt1) / record.dry_wt1) * 100
            else:
                
                print("_compute_water_absorption1 in else ")
                record.water_absorption1 = 0.0

    @api.depends('initial_wt2', 'dry_wt2')
    def _compute_water_absorption2(self):
        print("_compute_water_absorption2 before if ")
        for record in self:
            if record.dry_wt2 != 0:
                print("_compute_water_absorption2 in if ")        
                record.water_absorption2 = ((record.initial_wt2 - record.dry_wt2) / record.dry_wt2) * 100
            else:
                print("_compute_water_absorption2 in else ")        

                record.water_absorption2 = 0.0

    @api.depends('initial_wt3', 'dry_wt3')
    def _compute_water_absorption3(self):
        for record in self:
            if record.dry_wt3 != 0:
                record.water_absorption3 = ((record.initial_wt3 - record.dry_wt3) / record.dry_wt3) * 100
            else:
                record.water_absorption3 = 0.0


    @api.depends('water_absorption1', 'water_absorption2', 'water_absorption3')
    def _compute_average_water(self):
        for record in self:
            # Calculate the average water absorption percentage
            water_absorption_values = [record.water_absorption1, record.water_absorption2, record.water_absorption3]
            non_zero_values = [value for value in water_absorption_values if value]

            if non_zero_values:
                record.average_water = sum(non_zero_values) / len(non_zero_values)
            else:
                record.average_water = 0.0



   # Dimension

    dimension_name1 = fields.Char("Name",default="Dimension")
    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible")   

    # name = fields.Char("Name",default="DIMENSION")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines = fields.One2many('mechanical.dimension.paver.block.line','parent_id',string="Parameter")
    average_length = fields.Float(string="Average Length", compute="_compute_average_length",digits=(16,1))
    average_hight = fields.Float(string="Average Thickness",compute="_compute_average_hight", digits=(16, 1))
    average_width = fields.Float(string="Average Width", compute="_compute_average_width",digits=(16,1))
    plan_area = fields.Float(string="Plan Area", compute="_compute_plan_area", digits=(16, 1))


    plan_area_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Conformity", compute="_compute_plan_area_conformity", store=True)



    @api.depends('plan_area','eln_ref','grade')
    def _compute_plan_area_conformity(self):
        
        for record in self:
            record.plan_area_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','95fc46f1-ccb9-41c2-9ae2-c8b4610622a1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','95fc46f1-ccb9-41c2-9ae2-c8b4610622a1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.plan_area_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.plan_area - record.plan_area*mu_value
                    upper = record.plan_area + record.plan_area*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.plan_area_conformity = 'pass'
                        break
                    else:
                        record.plan_area_conformity = 'fail'

    plan_area_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_plan_area_nabl", store=True)

    @api.depends('plan_area','eln_ref','grade')
    def _compute_plan_area_nabl(self):
        
        for record in self:
            record.plan_area_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','95fc46f1-ccb9-41c2-9ae2-c8b4610622a1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','95fc46f1-ccb9-41c2-9ae2-c8b4610622a1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.plan_area - record.plan_area*mu_value
                    upper = record.plan_area + record.plan_area*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.plan_area_nabl = 'pass'
                        break
                    else:
                        record.plan_area_nabl = 'fail'



   
   

    @api.depends('child_lines.length')
    def _compute_average_length(self):
        for record in self:
            if record.child_lines:
                lengths = [line.length for line in record.child_lines]
                record.average_length = sum(lengths) / len(lengths)
            else:
                record.average_length = 0.0

                
    @api.depends('child_lines.hight')
    def _compute_average_hight(self):
        for record in self:
            if record.child_lines:
                heights = [line.hight for line in record.child_lines]
                record.average_hight = sum(heights) / len(heights)
            else:
                record.average_hight = 0.0

  
   

    @api.depends('child_lines.width')
    def _compute_average_width(self):
        for record in self:
            if record.child_lines:
                widths = [line.width for line in record.child_lines]
                record.average_width = sum(widths) / len(widths)
            else:
                record.average_width = 0.0

    @api.depends('average_length', 'average_width')
    def _compute_plan_area(self):
        for record in self:
            record.plan_area = record.average_length * record.average_width



    
   






 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.paver_visible = False
            record.commpressive_visible = False
            record.water_absorption_visible = False
            record.dimension_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "938992f7-199c-497a-b3a7-45023c604673":
                    record.paver_visible = True

                if sample.internal_id == "4d2b88f2-5dc9-4a2a-8bf0-1281d1865a11":
                    record.commpressive_visible = True
                
                if sample.internal_id == "56859103-eba3-4f15-b33d-679b39f7372e":
                    record.water_absorption_visible = True

                if sample.internal_id == "95fc46f1-ccb9-41c2-9ae2-c8b4610622a1":
                    record.dimension_visible = True




    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            
            # Length
            if result.parameter.internal_id == '938992f7-199c-497a-b3a7-45023c604673':
                result.result_char = round(self.average,2)
                result.calculated = True
                if self.average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Width
            if result.parameter.internal_id == '4d2b88f2-5dc9-4a2a-8bf0-1281d1865a11':
                result.result_char = round(self.average1,2)
                result.calculated = True
                if self.average1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Thickness
            if result.parameter.internal_id == '56859103-eba3-4f15-b33d-679b39f7372e':
                result.result_char = round(self.average_water,2)
                result.calculated = True
                if self.average_water_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Squareness
            if result.parameter.internal_id == '95fc46f1-ccb9-41c2-9ae2-c8b4610622a1':
                result.result_char = round(self.plan_area,2)
                result.calculated = True
                if self.plan_area_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
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
        record = super(PaverBlock, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)



    def get_all_fields(self):
        record = self.env['mechanical.paver.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values




class PaverBlockTest(models.Model):
    _name = "mechanical.pever.block.test"
    _rec_name = "name"
    name = fields.Char("Name")



class DimensionPaverBlock(models.Model):
    _name = "mechanical.dimension.paver.block.line"
    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)
    length = fields.Float(string="Length in mm")
    hight = fields.Float(string="Thickness in mm")
    width = fields.Float(string="Width in mm")



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DimensionPaverBlock, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class PaverBolckNotes(models.Model):
    _name = "mechanical.paver.block.notes"

    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")