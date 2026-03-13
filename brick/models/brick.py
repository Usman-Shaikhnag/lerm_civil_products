from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalBricks(models.Model):
    _name = "mechanical.bricks"
    _inherit = "lerm.eln"
    _description = 'mechanical.bricks'
    _rec_name = "name"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    name = fields.Char("Name",default="Fly Ash Bricks")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    # child_lines = fields.One2many('mechanical.water.absorption.bricks.line','parent_id',string="Parameter")
    # test_start_date = fields.Date("Test Start Date")
    # test_end_date = fields.Date("Test End Date")
   
    length_in_mm = fields.Float(string="Length in mm")
    width_in_mm = fields.Float(string="Width in mm")
    height_in_mm = fields.Float(string="Height in mm")


    # Initial Rate Of Absorption

    ini_rate_absorption_visible = fields.Boolean("Initial Rate Of Absorption",compute="_compute_visible")
    ini_rate_absorption_name = fields.Char("Name",default="Initial Rate Of Absorption")
    
    absorption_line_ids = fields.One2many(
        'brick.initial.rate.absorption.line',
        'parent_id',
        string="IRA Test Lines"
    )

    average_ira = fields.Float(
        string="Average Initial Rate of Absorption (g/min/100 cm²)",
        compute="_compute_average_ira",
        store=True
    )

    @api.depends('absorption_line_ids.initial_rate_absorp')
    def _compute_average_ira(self):
        for rec in self:
            if rec.absorption_line_ids:
                total = sum(rec.absorption_line_ids.mapped('initial_rate_absorp'))
                rec.average_ira = total / len(rec.absorption_line_ids)
            else:
                rec.average_ira = 0

















        #1------------ Compressive Strength

    compressive_strength_visible = fields.Boolean("Compressive Strengt Visible",compute="_compute_visible")
    compressive_strength_name = fields.Char("Name",default="Compressive Strength")
    length = fields.Float(string="Length mm")
    length_2 = fields.Float(string="Length mm")
    length_3 = fields.Float(string="Length mm")
    length_4 = fields.Float(string="Length mm")
    length_5 = fields.Float(string="Length mm")
    width = fields.Float(string="Width mm")
    width_2 = fields.Float(string="Width mm")
    width_3 = fields.Float(string="Width mm")
    width_4 = fields.Float(string="Width mm")
    width_5 = fields.Float(string="Width mm")
    height = fields.Float(string="Height mm")
    height_2 = fields.Float(string="Height mm")
    height_3 = fields.Float(string="Height mm")
    height_4 = fields.Float(string="Height mm")
    height_5 = fields.Float(string="Height mm")
    area = fields.Float(string="Area (mm²)", digits=(12,4),compute="_compute_area")
    area_2 = fields.Float(string="Area (mm²)", digits=(12,4),compute="_compute_area_2")
    area_3 = fields.Float(string="Area (mm²)", digits=(12,4),compute="_compute_area_3")
    area_4 = fields.Float(string="Area (mm²)", digits=(12,4),compute="_compute_area_4")
    area_5 = fields.Float(string="Area (mm²)", digits=(12,4),compute="_compute_area_5")
    load = fields.Float(string=" Load in, Kn", digits=(12,1))
    load_2 = fields.Float(string=" Load in, Kn", digits=(12,1))
    load_3 = fields.Float(string=" Load in, Kn", digits=(12,1))
    load_4 = fields.Float(string=" Load in, Kn", digits=(12,1))
    load_5 = fields.Float(string=" Load in, Kn", digits=(12,1))
    comp_strength_1 = fields.Float(string="Compressive strength MPa",compute="_compute_comp_strength_1")
    comp_strength_2 = fields.Float(string="Compressive strength MPa",compute="_compute_comp_strength_2")
    comp_strength_3 = fields.Float(string="Compressive strength MPa",compute="_compute_comp_strength_3")
    comp_strength_4 = fields.Float(string="Compressive strength MPa",compute="_compute_comp_strength_4")
    comp_strength_5 = fields.Float(string="Compressive strength MPa",compute="_compute_comp_strength_5")
    
    avrg_compressive_strength = fields.Float(string="Average Compressive Strength",compute="_compute_avrg_compressive_strength", digits=(16, 3))

    comp_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_comp_strength_conformity")

    comp_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_comp_strength_nabl",store=True)

    @api.depends('avrg_compressive_strength','eln_ref')
    def _compute_comp_strength_conformity(self):
        for record in self:
            record.comp_strength_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_compressive_strength - record.avrg_compressive_strength*mu_value
                    upper = record.avrg_compressive_strength + record.avrg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.comp_strength_confirmity = 'pass'
                        break
                    else:
                        record.comp_strength_confirmity = 'fail'

    @api.depends('avrg_compressive_strength','eln_ref')
    def _compute_comp_strength_nabl(self):
        
        for record in self:
            record.comp_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avrg_compressive_strength - record.avrg_compressive_strength*mu_value
            upper = record.avrg_compressive_strength + record.avrg_compressive_strength*mu_value
            # import wdb;wdb.set_trace()
            if lower >= lab_min and upper <= lab_max:
                record.comp_strength_nabl = 'pass'
                break
            else:
                record.comp_strength_nabl = 'fail'

    

    

    @api.depends('comp_strength_1', 'comp_strength_2', 'comp_strength_3', 'comp_strength_4', 'comp_strength_5')
    def _compute_avrg_compressive_strength(self):
        for record in self:
            comp_strength_1 = [
                record.comp_strength_1,
                record.comp_strength_2,
                record.comp_strength_3,
                record.comp_strength_4,
                record.comp_strength_5,
            ]
            # Filter out None values and calculate the average
            non_empty_strengths = [strength for strength in comp_strength_1 if strength is not None]
            if non_empty_strengths:
                average_strength = sum(non_empty_strengths) / len(non_empty_strengths)
            else:
                average_strength = 0.0
            record.avrg_compressive_strength = average_strength

      
    @api.depends('length', 'width')
    def _compute_area(self):
        for record in self:
            record.area = record.length * record.width

    @api.depends('length_2', 'width_2')
    def _compute_area_2(self):
        for record in self:
            record.area_2 = record.length_2 * record.width_2

    @api.depends('length_3', 'width_3')
    def _compute_area_3(self):
        for record in self:
            record.area_3 = record.length_3 * record.width_3

    @api.depends('length_4', 'width_4')
    def _compute_area_4(self):
        for record in self:
            record.area_4 = record.length_4 * record.width_4

    @api.depends('length_5', 'width_5')
    def _compute_area_5(self):
        for record in self:
            record.area_5 = record.length_5 * record.width_5

    @api.depends('load', 'area')
    def _compute_comp_strength_1(self):
        for record in self:
            if record.area != 0:
                record.comp_strength_1 = record.load / record.area * 1000
            else:
                record.comp_strength_1 = 0.0
    
    @api.depends('load_2', 'area_2')
    def _compute_comp_strength_2(self):
        for record in self:
            if record.area_2 != 0:
                record.comp_strength_2 = record.load_2 / record.area_2 * 1000
            else:
                record.comp_strength_2 = 0.0

    @api.depends('load_3', 'area_3')
    def _compute_comp_strength_3(self):
        for record in self:
            if record.area_3 != 0:
                record.comp_strength_3 = record.load_3 / record.area_3 * 1000
            else:
                record.comp_strength_3 = 0.0

    @api.depends('load_4', 'area_4')
    def _compute_comp_strength_4(self):
        for record in self:
            if record.area_4 != 0:
                record.comp_strength_4 = record.load_4 / record.area_4 * 1000
            else:
                record.comp_strength_4 = 0.0

    @api.depends('load_5', 'area_5')
    def _compute_comp_strength_5(self):
        for record in self:
            if record.area_5 != 0:
                record.comp_strength_5 = record.load_5 / record.area_5 * 1000
            else:
                record.comp_strength_5 = 0.0

    


        #-2----------Efflorescence Visual Observation 
    efflorescence_visible = fields.Boolean("Efflorescence Visible",compute="_compute_visible")
    visual_observation_name_efflorescence = fields.Char("Name",default="Efflorescence")
    visual_observation_1 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    visual_observation_2 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    visual_observation_3 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    visual_observation_4 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    visual_observation_5 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')


         #-3----------  Dimension As per IS: IS : 1077 -1992 

    dimension_visible = fields.Boolean("Efflorescence Visible",compute="_compute_visible")
    dimension_name1 = fields.Char("Name",default="Dimension (mm)")
    avrg_length = fields.Float(string="Average length")
    avrg_width = fields.Float(string="Average Width")
    avrg_height = fields.Float(string="Average Height")

    

    #-4--------------  Water Absorption

    water_absorbtion_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    wt_absorption_name = fields.Char("Name",default="Water Absorption")
    initial_wt = fields.Float(string="Dry wt (W1)")
    initial_wt_2 = fields.Float(string="Dry wt (W1)")
    initial_wt_3 = fields.Float(string="Dry wt (W1)")
    initial_wt_4 = fields.Float(string="Dry wt (W1)")
    initial_wt_5 = fields.Float(string="Dry wt (W1)")
    final_wt = fields.Float(string="Wet wt (W2)")
    final_wt_2 = fields.Float(string="Wet wt (W2)")
    final_wt_3 = fields.Float(string="Wet wt (W2)")
    final_wt_4 = fields.Float(string="Wet wt (W2)")
    final_wt_5 = fields.Float(string="Wet wt (W2)")
    water_absorption = fields.Float(string="Water Absorption %", compute="_compute_water_absorption")
    water_absorption_2 = fields.Float(string="Water Absorption %", compute="_compute_water_absorption_2")
    water_absorption_3 = fields.Float(string="Water Absorption %", compute="_compute_water_absorption_3")
    water_absorption_4 = fields.Float(string="Water Absorption %", compute="_compute_water_absorption_4")
    water_absorption_5 = fields.Float(string="Water Absorption %", compute="_compute_water_absorption_5")
    avrg_water_absorption = fields.Float(string="Average Water Absorption, %", compute="_compute_avrg_water_absorption", digits=(16, 3))

    water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_water_absorption_confirmity")

    water_absorption_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_water_absorption_nabl",store=True)


    @api.depends('avrg_water_absorption','eln_ref')
    def _compute_water_absorption_confirmity(self):
        for record in self:
            record.water_absorption_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_water_absorption - record.avrg_water_absorption*mu_value
                    upper = record.avrg_water_absorption + record.avrg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.water_absorption_confirmity = 'pass'
                        break
                    else:
                        record.water_absorption_confirmity = 'fail'

    @api.depends('avrg_water_absorption','eln_ref')
    def _compute_water_absorption_nabl(self):
        
        for record in self:
            record.water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avrg_water_absorption - record.avrg_water_absorption*mu_value
            upper = record.avrg_water_absorption + record.avrg_water_absorption*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.water_absorption_nabl = 'pass'
                break
            else:
                record.water_absorption_nabl = 'fail'

    @api.depends('water_absorption', 'water_absorption_2', 'water_absorption_3', 'water_absorption_4', 'water_absorption_5')
    def _compute_avrg_water_absorption(self):
        for record in self:
            total_absorption = (
                record.water_absorption +
                record.water_absorption_2 +
                record.water_absorption_3 +
                record.water_absorption_4 +
                record.water_absorption_5
            )
            num_entries = sum(1 for field in [
                record.water_absorption,
                record.water_absorption_2,
                record.water_absorption_3,
                record.water_absorption_4,
                record.water_absorption_5
            ] if field)
            if num_entries > 0:
                record.avrg_water_absorption = total_absorption / num_entries
            else:
                record.avrg_water_absorption = 0.0

    @api.depends('initial_wt' , 'final_wt')
    def _compute_water_absorption(self):
        for record in self:
            if record.final_wt != 0:
                record.water_absorption = (record.final_wt - record.initial_wt) / record.initial_wt * 100
            else:
                record.water_absorption = 0

    @api.depends('initial_wt_2' , 'final_wt_2')
    def _compute_water_absorption_2(self):
        for record in self:
            if record.final_wt_2 != 0:
                record.water_absorption_2 = (record.final_wt_2 - record.initial_wt_2) / record.initial_wt_2 * 100
            else:
                record.water_absorption_2 = 0

    @api.depends('initial_wt_3' , 'final_wt_3')
    def _compute_water_absorption_3(self):
        for record in self:
            if record.final_wt_3 != 0:
                record.water_absorption_3 = (record.final_wt_3 - record.initial_wt_3) / record.initial_wt_3 * 100
            else:
                record.water_absorption_3 = 0

    @api.depends('initial_wt_4' , 'final_wt_4')
    def _compute_water_absorption_4(self):
        for record in self:
            if record.final_wt_4 != 0:
                record.water_absorption_4 = (record.final_wt_4 - record.initial_wt_4) / record.initial_wt_4 * 100
            else:
                record.water_absorption_4 = 0

    @api.depends('initial_wt_5' , 'final_wt_5')
    def _compute_water_absorption_5(self):
        for record in self:
            if record.final_wt_5 != 0:
                record.water_absorption_5 = (record.final_wt_5 - record.initial_wt_5) / record.initial_wt_5 * 100
            else:
                record.water_absorption_5 = 0

    confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail')


    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.compressive_strength_visible = False
            record.water_absorbtion_visible = False
            record.efflorescence_visible = False
            record.dimension_visible = False
            record.ini_rate_absorption_visible = False

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                if sample.internal_id == "31478fghht-9287-48c7-a607-bf1b64a8115d":
                    record.compressive_strength_visible = True
                if sample.internal_id == "321475gfet1-f3ab-4b19-af25-91a4671baf5f":
                    record.water_absorbtion_visible = True
                if sample.internal_id == "3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac":
                    record.efflorescence_visible = True
                if sample.internal_id == "125478bvf3-8d5d-4f45-8afb-b911f9cafe41":
                    record.dimension_visible = True 
                if sample.internal_id == "bd2bda15-78fa-400d-8643-d9d2b9551bcf":
                    record.ini_rate_absorption_visible = True 


     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Compressive Strength 
            if result.parameter.internal_id == '31478fghht-9287-48c7-a607-bf1b64a8115d':
                result.result_char = round(self.avrg_compressive_strength,2)
                result.calculated = True
                if self.comp_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '321475gfet1-f3ab-4b19-af25-91a4671baf5f':
                result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True
                if self.water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            # Efflorence
            if result.parameter.internal_id == '3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac':
                # result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True

            # Dimension
            if result.parameter.internal_id == '125478bvf3-8d5d-4f45-8afb-b911f9cafe41':
                # result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True
            
            # Rate Of Absorption
            if result.parameter.internal_id == 'bd2bda15-78fa-400d-8643-d9d2b9551bcf':
                # result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True

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
        record = super(MechanicalBricks, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

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
        record = self.env['mechanical.bricks'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


class BrickInitialRateAbsorptionLine(models.Model):
    _name = "brick.initial.rate.absorption.line"
    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

    serial_no = fields.Integer(string="sample", readonly=True, copy=False, default=1)
    iW1 = fields.Float("Weight of dry brick (g) ")
    W2 = fields.Float("Weight of brick after 1 minute immersion (g) ")
    W2_W1 = fields.Float("Water Absorbed (W₂–W₁) g ",compute="_compute_initial_rate_absorp",
        store=True)
    area = fields.Float("Area of immersed surface (cm²) ",compute="_compute_area", store=True)
    initial_rate_absorp = fields.Float("Initial Rate of Absorption (g/min/100 cm²)",compute="_compute_initial_rate_absorp",store=True)

    @api.depends('parent_id.length_in_mm', 'parent_id.width_in_mm')
    def _compute_area(self):
        for rec in self:
            length = rec.parent_id.length_in_mm or 0
            breadth = rec.parent_id.width_in_mm or 0
            rec.area = length * breadth

    @api.depends('iW1', 'W2', 'area')
    def _compute_initial_rate_absorp(self):
        for rec in self:

            # Water absorbed
            rec.W2_W1 = rec.W2 - rec.iW1

            # Initial Rate Absorption
            if rec.area:
                rec.initial_rate_absorp = (rec.W2_W1 * 100) / rec.area
            else:
                rec.initial_rate_absorp = 0

    @api.model
    def create(self, vals):
     vals['serial_no'] = self.search_count([]) + 1
     return super().create(vals)