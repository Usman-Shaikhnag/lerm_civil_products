from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math

import logging
_logger = logging.getLogger(__name__)



class PaverBlock(models.Model):
    _name = "mechanical.paver.block"
    _inherit = "lerm.eln"
    _rec_name = "name_paver"


    name_paver = fields.Char("Name",default="Paver Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    notes_id = fields.One2many('paver.block.notes','parent_id',string="Notes")


    calc_mode = fields.Boolean(default=True)     
    submit_mode = fields.Boolean(default=False)

    lab_id = fields.Char(
            string="Lab ID",
            compute="_compute_lab_id",
            store=True
        )


    @api.depends('eln_ref')
    def _compute_lab_id(self):
        for rec in self:
            if rec.eln_ref:
                rec.lab_id = rec.eln_ref.lab_id
            else:
                rec.lab_id = False

    lab_paver_ids = fields.One2many(
        'paver.lab.line', 
        'parent_id', 
        string="Generated Options"
    )

     # --- Button Function ---
    def action_generate_options_paver(self):
        for record in self:
            # Step 1: Check if lab_id exists and has hyphen
            if record.lab_id and '-' in record.lab_id:
                try:
                    # Step 2: Clear old lines first
                    lines_command = [(5, 0, 0)]
                    
                    # Step 3: String Parsing
                    parts = record.lab_id.split(' - ')
                    
                    if len(parts) >= 2:
                        start_part = parts[0].strip() # Example: "S-25-001"
                        end_part = parts[-1].strip()  # Example: "S-25-006"

                        prefix = start_part.rsplit('-', 1)[0]
                        
                        # --- CHANGE START ---
                        # Number cha string part vegla kara length check karnya sathi
                        start_num_str = start_part.split('-')[-1] # "001" milnar
                        end_num_str = end_part.split('-')[-1]     # "006" milnar
                        
                        # Length calculate kara (Example: "001" chi length 3 ahe)
                        padding_length = len(start_num_str)

                        start_num = int(start_num_str) # Integer madhe convert: 1
                        end_num = int(end_num_str)     # Integer madhe convert: 6
                        # --- CHANGE END ---

                        # Step 4: Loop ani Create Lines
                        for num in range(start_num, end_num + 1):
                            # zfill use karun zero add kara
                            # Jar num=1 ahe ani padding_length=3 ahe, tar "001" banel
                            formatted_num = str(num).zfill(padding_length)
                            
                            val = f"{prefix}-{formatted_num}"
                            lines_command.append((0, 0, {'lab': val}))

                        # Step 5: Assign to One2many field
                        record.lab_paver_ids = lines_command
                        
                except Exception as e:
                    pass
            else:
                if record.lab_id:
                    record.lab_paver_ids = [(5, 0, 0), (0, 0, {'lab': record.lab_id})]


    @api.model
    def default_get(self, fields):
        res = super(PaverBlock, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an # received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Genstru.',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'paver.block.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    # tests = fields.Many2many("mechanical.pever.block.test",string="Tests")


    # Dimension Test
    dimension_name = fields.Char("Name",default="Dimension Test")
    dimension_visible = fields.Boolean("Dimension Test",compute="_compute_visible")

    selected_dimension = fields.Many2one(
        'paver.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_paver_ids)]"
    )

    is_dimension = fields.Boolean(
        string="Lab Fine Selected",
        
    )

    @api.onchange('selected_dimension')
    def _onchange_selected_dimension(self):
        for rec in self:
            if rec.selected_dimension:
                rec.is_dimension = True
            else:
                rec.is_dimension = False

    length_name = fields.Char("Name",default="Length")
    length_visible = fields.Boolean("Length",compute="_compute_visible")

    width_name = fields.Char("Name",default="Width")
    width_visible = fields.Boolean("Width",compute="_compute_visible")

    thickness_name = fields.Char("Name",default="Thickness")
    thickness_visible = fields.Boolean("Thickness",compute="_compute_visible")

    temp_dimension = fields.Char("Temp °c" )
    humidity_dimension = fields.Char("Humidity %" )

    dimension_child_lines = fields.One2many('paver.dimension.line','parent_id',string="Dimension Test")

    average_length = fields.Float(string="Average Length ",compute="_compute_average")
    average_width = fields.Float(string="Average Width ",compute="_compute_average")
    average_thickness = fields.Float(string="Average Thickness ",compute="_compute_average")

    @api.depends('dimension_child_lines.avg_length','dimension_child_lines.avg_width','dimension_child_lines.avg_thickness')
    def _compute_average(self):
        for record in self:
            if record.dimension_child_lines:
              record.average_length = sum(record.dimension_child_lines.mapped('avg_length'))/ len(record.dimension_child_lines)
              record.average_width = sum(record.dimension_child_lines.mapped('avg_width'))/ len(record.dimension_child_lines)
              record.average_thickness = sum(record.dimension_child_lines.mapped('avg_thickness'))/ len(record.dimension_child_lines)
            else:
                record.average_length = 0.0
                record.average_width = 0.0
                record.average_thickness = 0.0

    average_length_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_average_length_conformity", store=True)

    @api.depends('average_length','eln_ref','grade')
    def _compute_average_length_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_length_conformity = 'na'
                continue
            record.average_length_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4609c439-2ee4-4e3e-b40c-334e95b2bbda')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4609c439-2ee4-4e3e-b40c-334e95b2bbda')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_length - record.average_length*mu_value
                    upper = record.average_length + record.average_length*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_length_conformity = 'pass'
                        break
                    else:
                        record.average_length_conformity = 'fail'

    average_length_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_length_nabl", store=True)

    @api.depends('average_length','eln_ref','grade')
    def _compute_average_length_nabl(self):
        
        for record in self:
            record.average_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4609c439-2ee4-4e3e-b40c-334e95b2bbda')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4609c439-2ee4-4e3e-b40c-334e95b2bbda')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_length - record.average_length*mu_value
                    upper = record.average_length + record.average_length*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_length_nabl = 'pass'
                        break
                    else:
                        record.average_length_nabl = 'fail'

    average_width_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_average_width_conformity", store=True)

    @api.depends('average_width','eln_ref','grade')
    def _compute_average_width_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_width_conformity = 'na'
                continue
            record.average_width_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f079957b-608f-40c0-aebd-0db011ab0f2c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f079957b-608f-40c0-aebd-0db011ab0f2c')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_width - record.average_width*mu_value
                    upper = record.average_width + record.average_width*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_width_conformity = 'pass'
                        break
                    else:
                        record.average_length_conformity = 'fail'

    average_width_nabl1 = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_width_nabl1", store=True)

    @api.depends('average_width','eln_ref','grade')
    def _compute_average_width_nabl1(self):
        
        for record in self:
            record.average_width_nabl1 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','549532ef-08e1-46f7-9565-bf034ce334f4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','549532ef-08e1-46f7-9565-bf034ce334f4')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_width - record.average_width*mu_value
                    upper = record.average_width + record.average_width*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_width_nabl1 = 'pass'
                        break
                    else:
                        record.average_width_nabl1 = 'fail'



    average_thickness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_average_thickness_conformity", store=True)

    @api.depends('average_thickness','eln_ref','grade')
    def _compute_average_thickness_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_thickness_conformity = 'na'
                continue
            record.average_thickness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','549532ef-08e1-46f7-9565-bf034ce334f4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','549532ef-08e1-46f7-9565-bf034ce334f4')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_thickness - record.average_thickness*mu_value
                    upper = record.average_thickness + record.average_thickness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_thickness_conformity = 'pass'
                        break
                    else:
                        record.average_thickness_conformity = 'fail'

    average_thickness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_thickness_nabl", store=True)

    @api.depends('average_thickness','eln_ref','grade')
    def _compute_average_thickness_nabl(self):
        
        for record in self:
            record.average_thickness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','549532ef-08e1-46f7-9565-bf034ce334f4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','549532ef-08e1-46f7-9565-bf034ce334f4')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_thickness - record.average_thickness*mu_value
                    upper = record.average_thickness + record.average_thickness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_thickness_nabl = 'pass'
                        break
                    else:
                        record.average_thickness_nabl = 'fail'



    # Water Absorption

    water_absorption_name = fields.Char("Name",default=" Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption",compute="_compute_visible")

    selected_water_absorption = fields.Many2one(
        'paver.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_paver_ids)]"
    )

    is_water_absorption = fields.Boolean(
        string="Lab Fine Selected",
        
    )

    @api.onchange('selected_water_absorption')
    def _onchange_selected_water_absorption(self):
        for rec in self:
            if rec.selected_water_absorption:
                rec.is_water_absorption = True
            else:
                rec.is_water_absorption = False

    temp_water_absorption = fields.Char("Temp °c" )
    humidity_water_absorption = fields.Char("Humidity %" )

    water_absorption_child_lines = fields.One2many('paver.water.absorption.line','parent_id',string="Water Absorption Test")

    avg_water_absorption = fields.Float(string="Average Water Absorption ",compute="_compute_avg_water_absorption")


    @api.depends('water_absorption_child_lines.water_absorption')
    def _compute_avg_water_absorption(self):
        for record in self:
            if record.water_absorption_child_lines:
              record.avg_water_absorption = sum(record.water_absorption_child_lines.mapped('water_absorption'))/ len(record.water_absorption_child_lines)
            else:
                record.avg_water_absorption = 0.0

    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.avg_water_absorption_conformity = 'fail'

    avg_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_water_absorption_nabl = 'pass'
                        break
                    else:
                        record.avg_water_absorption_nabl = 'fail'


    # Compressive Strength
    compressive_strength_name = fields.Char("Name",default=" Compressive Strength")
    compressive_strength_visible = fields.Boolean("Compressive Strength",compute="_compute_visible")

    temp_compressive_strength = fields.Char("Temp °c" )
    humidity_compressive_strength = fields.Char("Humidity %" )

    selected_compressive_strength = fields.Many2one(
        'paver.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_paver_ids)]"
    )

    is_compressive_strength = fields.Boolean(
        string="Lab Fine Selected",
        
    )

    @api.onchange('selected_compressive_strength')
    def _onchange_selected_compressive_strength(self):
        for rec in self:
            if rec.selected_compressive_strength:
                rec.is_compressive_strength = True
            else:
                rec.is_compressive_strength = False

    # correction_factore = fields.Float(string=" Correction Factor")

    thickness2 = fields.Float(string="Thickness of Paver Block:",compute="_compute_thickness2")
    @api.depends('size_id')
    def _compute_thickness2(self):
        for rec in self:
            rec.thickness2 = rec.size_id.size if rec.size_id and rec.size_id.size else 0.0

    block_type = fields.Selection(
        [('plain', 'Plain'), ('arrised', 'Arrised')],
        string="Block Type",
        required=True
    )
    plain_factor = fields.Float("Plain Correction Factor")
    arrised_factor = fields.Float("Arrised Correction Factor")
    correction_factore = fields.Float(string=" Correction Factor", compute='_compute_correction_factor')

    @api.depends('block_type', 'plain_factor', 'arrised_factor')
    def _compute_correction_factor(self):
        for rec in self:
            if rec.block_type == 'plain':
                rec.correction_factore = rec.plain_factor
            elif rec.block_type == 'arrised':
                rec.correction_factore = rec.arrised_factor
            else:
                rec.correction_factore = 0.0

    @api.depends('size_id')
    def _compute_thickness2(self):
        for rec in self:
            rec.thickness2 = rec.size_id.size if rec.size_id and rec.size_id.size else 0.0

    

    compressive_strength_child_lines = fields.One2many('paver.compressive.line','parent_id',string="Compressive Strength Test" )


    


    
    avg_compressive_strength = fields.Float(string="Average Compressive Strength ",compute="_compute_avg_compressive_strength")

    @api.depends('compressive_strength_child_lines.compressive_strength')
    def _compute_avg_compressive_strength(self):
        for record in self:
            if record.compressive_strength_child_lines:
              record.avg_compressive_strength = sum(record.compressive_strength_child_lines.mapped('compressive_strength'))/ len(record.compressive_strength_child_lines)
            else:
                record.avg_compressive_strength = 0.0

    avg_compressive_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_compressive_strength_conformity", store=True)

    @api.depends('avg_compressive_strength','eln_ref','grade')
    def _compute_avg_compressive_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_compressive_strength_conformity = 'na'
                continue
            record.avg_compressive_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_compressive_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_compressive_strength_conformity = 'fail'

    avg_compressive_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_compressive_strength_nabl", store=True)

    @api.depends('avg_compressive_strength','eln_ref','grade')
    def _compute_avg_compressive_strength_nabl(self):
        
        for record in self:
            record.avg_compressive_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_compressive_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_compressive_strength_nabl = 'fail'





	


















 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.dimension_visible = False
            record.length_visible = False
            record.width_visible = False
            record.thickness_visible = False
            record.water_absorption_visible = False
            record.compressive_strength_visible = False
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "23547trew-199c-497a-b3a7-45023c604673":
                    record.dimension_visible = True
                    record.length_visible = True
                    record.width_visible = True
                    record.thickness_visible = True

                if sample.internal_id == "2147fgrr-eba3-4f15-b33d-679b39f7372e":
                    record.water_absorption_visible = True




                if sample.internal_id == "1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11":
                    record.compressive_strength_visible = True
                
                

               



    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }           

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:
            # Dimension Test 
            if result.parameter.internal_id == '23547trew-199c-497a-b3a7-45023c604673':
                result.calculated = True

            if result.parameter.internal_id == '4609c439-2ee4-4e3e-b40c-334e95b2bbda':
                result.result_char = round(self.average_length,2)
                result.calculated = True
                if self.average_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'f079957b-608f-40c0-aebd-0db011ab0f2c':
                result.result_char = round(self.average_width,2)
                result.calculated = True
                if self.average_width_nabl1 == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '549532ef-08e1-46f7-9565-bf034ce334f4':
                result.result_char = round(self.average_thickness,2)
                result.calculated = True
                if self.average_thickness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Water Absorption
            if result.parameter.internal_id == '2147fgrr-eba3-4f15-b33d-679b39f7372e':
                result.result_char = round(self.avg_water_absorption,2)
                result.calculated = True
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compressive Strength
            if result.parameter.internal_id == '1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11':
                result.result_char = round(self.avg_compressive_strength,2)
                result.calculated = True
                if self.avg_compressive_strength_nabl == 'pass':
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







    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        # parameter_based_assignment
        current_user = self.env.user
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # filter parameter results by current user
            user_param_results = record.eln_ref.parameters_result.filtered(
                lambda r: r.technician and r.technician.id == current_user.id
            )

            # map to parameter master IDs
            parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]



    def get_all_fields(self):
        record = self.env['mechanical.paver.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id






class PaverDimensionLine(models.Model):
    _name = "paver.dimension.line"
    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample = fields.Char(string="Sample Identification")
    length1= fields.Float(string="Length 1")
    length2= fields.Float(string="Length 2")
    avg_length = fields.Float(string="Average Length ",compute="_compute_avg")
    width1= fields.Float(string="Width 1")
    width2= fields.Float(string="Width 2")
    width3= fields.Float(string="Width 3")
    avg_width = fields.Float(string="Average Width ",compute="_compute_avg")

    thickness1= fields.Float(string="Thickness 1")
    thickness2= fields.Float(string="Thickness 2")
    thickness3= fields.Float(string="Thickness 3")
    thickness4= fields.Float(string="Thickness 4")
    avg_thickness = fields.Float(string="Average Thickness ",compute="_compute_avg")
    
    @api.depends('length1','length2','width1','width2','width3','thickness1','thickness2','thickness3','thickness4')
    def _compute_avg(self):
        for rec in self:
            rec.avg_length = (rec.length1 + rec.length2 ) / 2 
            rec.avg_width = (rec.width1 + rec.width2 +  rec.width3) / 3
            rec.avg_thickness = (rec.thickness1 + rec.thickness2 +  rec.thickness3 + rec.thickness4) / 4

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PaverDimensionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class PaverWaterObsorptionLine(models.Model):
    _name = "paver.water.absorption.line"
    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample = fields.Char(string="Sample Identification")
    dry_weight= fields.Float(string="Dry Weight")
    sat_weight= fields.Float(string="Saturated Weight")
    sat_dry_weight = fields.Float(string="Saturated Weight-Dry Weight ",compute="_compute_sat_dry_weight")
    
    water_absorption = fields.Float(string="Saturated Weight-Dry Weight/Dry Weight*100	",compute="_compute_water_absorption")
    
    @api.depends('sat_weight','dry_weight')
    def _compute_sat_dry_weight(self):
        for rec in self:
            rec.sat_dry_weight = (rec.sat_weight - rec.dry_weight )

    @api.depends('sat_dry_weight','dry_weight')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.dry_weight != 0:
                rec.water_absorption = (rec.sat_dry_weight / rec.dry_weight ) *100 
            else:
                rec.water_absorption = 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PaverWaterObsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class PaverCompressiveLine(models.Model):
    _name = "paver.compressive.line"
    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")

   

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample1 = fields.Char(string="Sample Identification")
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    thickness = fields.Float(string="Thickness")
    area = fields.Float(string="Area (mm2)",compute="_compute_area",store=True)
    load = fields.Float(string=" Load at Failure (kN)")
    correction_factor = fields.Float(string="Correction Factor",store=True)
    
    
    compressive_strength = fields.Float(string="Compressive Strength  N/mm2",compute="_compute_compressive_strength",store=True)
    block_type = fields.Selection(related="parent_id.block_type", string="Block Type")  # gets parent's choice

    @api.depends('length','width')
    def _compute_area(self):
        for rec in self:
            rec.area = (rec.length * rec.width )

    @api.depends('load','area','correction_factor')
    def _compute_compressive_strength(self):
        for rec in self:
            if rec.area != 0:
                rec.compressive_strength = ((rec.load * 1000) / rec.area ) * rec.correction_factor 
            else:
                rec.compressive_strength = 0.0



    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            self.correction_factor = self.parent_id.correction_factore            


               





    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PaverCompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1






class PaverBlockNotes(models.Model):
    _name = "paver.block.notes"

    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")




class LabOptionLine(models.Model):
    _name = 'paver.lab.line'
    _description = 'Lab Options'
    _rec_name = 'lab'  # Dropdown मध्ये हे नाव दिसेल

    lab = fields.Char(string="Lab ID")
    parent_id = fields.Many2one('mechanical.paver.block', string="Parent")