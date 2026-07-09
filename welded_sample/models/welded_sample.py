from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalWeldedSample(models.Model):
    _name = "mechanical.welded.sample"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    name2 = fields.Char("Name",default="Fusion Welded Ferrous Materials")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    temprature = fields.Integer("Temperature (°C)", digits=(10,2))
    humidity = fields.Integer("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")
    product_name = fields.Char("Product Name")

    description_work = fields.Text("Description Of Work")

    notes_id = fields.One2many('welded.sample.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalWeldedSample, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in full or partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sampling is not done by us unless mentioned otherwide.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'without a QR Code and hologram this report is considered invalid.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
            }),
             (0, 0, {
                'sr_no': 'f',
                'notes': 'All disputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample will be destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    tensile_strength_visible = fields.Boolean("Tensile Strength Visible",compute="_compute_visible")
    tensile_strength_name = fields.Char("Name",default="Tensile Strength - (ASME Sec IX: 2023)")
    tensile_strength = fields.Float(string="Tensile Strength")

    tensile_strength_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_strength_conformity")

    tensile_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_strength_nabl")


    @api.depends('tensile_strength','eln_ref','grade')
    def _compute_tensile_strength_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_strength_conformity = 'na'
                continue
            record.tensile_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d96a5e06-7d28-425e-ad2e-cd425cbfb8d5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d96a5e06-7d28-425e-ad2e-cd425cbfb8d5')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_strength - record.tensile_strength*mu_value
                    upper = record.tensile_strength + record.tensile_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_strength_conformity = 'pass'
                        break
                    else:
                        record.tensile_strength_conformity = 'fail'

    @api.depends('tensile_strength','eln_ref','grade')
    def _compute_tensile_strength_nabl(self):
        
        for record in self:
            
            record.tensile_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d96a5e06-7d28-425e-ad2e-cd425cbfb8d5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d96a5e06-7d28-425e-ad2e-cd425cbfb8d5')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_strength - record.tensile_strength*mu_value
            upper = record.tensile_strength + record.tensile_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_strength_nabl = 'pass'
                break
            else:
                record.tensile_strength_nabl = 'fail'

    elongation_visible = fields.Boolean("Elongation Visible",compute="_compute_visible")
    elongation_name = fields.Char("Name",default="Elongation - (AWS D1.1/ D1.1M : 2020)")
    elongation = fields.Float(string="Elongation")

    elongation_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_elongation_conformity")

    elongation_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_elongation_nabl")


    @api.depends('elongation','eln_ref','grade')
    def _compute_elongation_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_conformity = 'na'
                continue
            record.elongation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d3e787-c3f3-4d98-b2af-8a25cf5fa837')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d3e787-c3f3-4d98-b2af-8a25cf5fa837')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.elongation - record.elongation*mu_value
                    upper = record.elongation + record.elongation*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.elongation_conformity = 'pass'
                        break
                    else:
                        record.elongation_conformity = 'fail'

    @api.depends('elongation','eln_ref','grade')
    def _compute_elongation_nabl(self):
        
        for record in self:
            
            record.elongation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d3e787-c3f3-4d98-b2af-8a25cf5fa837')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d3e787-c3f3-4d98-b2af-8a25cf5fa837')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.elongation - record.elongation*mu_value
            upper = record.elongation + record.elongation*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.elongation_nabl = 'pass'
                break
            else:
                record.elongation_nabl = 'fail'


    tensile_strength_visible1 = fields.Boolean("Tensile Strength Visible",compute="_compute_visible")
    tensile_strength_name1 = fields.Char("Name",default="Tensile Strength - (AWS D1.1/ D1.1M : 2020)")
    tensile_strength1 = fields.Float(string="Tensile Strength")

    tensile_strength1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_strength1_conformity")

    tensile_strength1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_strength1_nabl")


    @api.depends('tensile_strength1','eln_ref','grade')
    def _compute_tensile_strength1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_strength1_conformity = 'na'
                continue
            record.tensile_strength1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9bb2ac9c-5a6e-4e4d-bb2d-07ebb3c42089')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9bb2ac9c-5a6e-4e4d-bb2d-07ebb3c42089')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_strength1 - record.tensile_strength1*mu_value
                    upper = record.tensile_strength1 + record.tensile_strength1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_strength1_conformity = 'pass'
                        break
                    else:
                        record.tensile_strength1_conformity = 'fail'

    @api.depends('tensile_strength1','eln_ref','grade')
    def _compute_tensile_strength1_nabl(self):
        
        for record in self:
            
            record.tensile_strength1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9bb2ac9c-5a6e-4e4d-bb2d-07ebb3c42089')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9bb2ac9c-5a6e-4e4d-bb2d-07ebb3c42089')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_strength1 - record.tensile_strength1*mu_value
            upper = record.tensile_strength1 + record.tensile_strength1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_strength1_nabl = 'pass'
                break
            else:
                record.tensile_strength1_nabl = 'fail'

    tensile_test_visible = fields.Boolean("Tensile test Visible",compute="_compute_visible")
    tensile_test_name = fields.Char("Name",default="Tensile test - (IS 7307 Pt-1 : 1974: 2019)")
    tensile_test = fields.Float(string="Tensile test")

    tensile_test_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_test_conformity")

    tensile_test_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_test_nabl")


    @api.depends('tensile_test','eln_ref','grade')
    def _compute_tensile_test_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_test_conformity = 'na'
                continue
            record.tensile_test_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','dcfe8664-3cf9-4e4b-be3f-2bff8f2397d6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','dcfe8664-3cf9-4e4b-be3f-2bff8f2397d6')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_test - record.tensile_test*mu_value
                    upper = record.tensile_test + record.tensile_test*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_test_conformity = 'pass'
                        break
                    else:
                        record.tensile_test_conformity = 'fail'

    @api.depends('tensile_test','eln_ref','grade')
    def _compute_tensile_test_nabl(self):
        
        for record in self:
            
            record.tensile_test_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','dcfe8664-3cf9-4e4b-be3f-2bff8f2397d6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','dcfe8664-3cf9-4e4b-be3f-2bff8f2397d6')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_test - record.tensile_test*mu_value
            upper = record.tensile_test + record.tensile_test*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_test_nabl = 'pass'
                break
            else:
                record.tensile_test_nabl = 'fail'



    face_bend_visible = fields.Boolean("Face Bend Visible",compute="_compute_visible")
    face_bend_name = fields.Char("Name",default="Face Bend - (IS 3600 Pt 7 : 1985: 2019)")
    face_bend = fields.Char(string="Face Bend")
    face_bend_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    root_bend_visible = fields.Boolean("Root bend Visible",compute="_compute_visible")
    root_bend_name = fields.Char("Name",default="Root bend - (IS 3600 Pt 7 : 1985: 2019)")
    root_bend = fields.Char(string="Root bend")
    root_bend_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    fillet_weld_fracture_visible = fields.Boolean("Fillet weld Fracture test Visible",compute="_compute_visible")
    fillet_weld_fracture_name = fields.Char("Name",default="Fillet weld Fracture test - (IS 3600 Pt-8 : 2024: 2024)")
    fillet_weld_fracture = fields.Char(string="Fillet weld Fracture test")
    fillet_weld_fracture_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )


    fracture_test_visible1 = fields.Boolean("Fracture Test Visible",compute="_compute_visible")
    fracture_test_name1 = fields.Char("Name",default="Fracture Test - (IS 7307 Pt-1 : 1974: 2019)")
    fracture_test1 = fields.Char(string="Fracture Test")
    fracture_test_type1 = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    fracture_visible2 = fields.Boolean("Fracture Test Visible",compute="_compute_visible")
    fracture_name2 = fields.Char("Name",default="Fracture Test - (IS 7310 Pt-1 : 2019: 2019)")
    fracture2 = fields.Char(string="Fracture Test")
    fracture_type2 = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    weld_fracture_test_visible = fields.Boolean("Weld fracture test Visible",compute="_compute_visible")
    weld_fracture_test_name = fields.Char("Name",default="Weld fracture test - (ISO 9606 (Part-1): 2012)")
    weld_fracture_test = fields.Char(string="Weld fracture test")
    weld_fracture_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    fillet_weld_fracture_test_visible = fields.Boolean("Fillet weld Fracture test Visible",compute="_compute_visible")
    fillet_weld_fracture_test_name = fields.Char("Name",default="Fillet weld Fracture test - (AWS D1.1/ D1.1M : 2020: 2020)")
    fillet_weld_fracture_test = fields.Char(string="Fillet weld Fracture test")
    fillet_weld_fracture_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    fracture_test_visible3 = fields.Boolean("Fracture Test Visible",compute="_compute_visible")
    fracture_test_name3 = fields.Char("Name",default="Fracture Test - (ASME Sec IX: 2023)")
    fracture_test3 = fields.Char(string="Fracture Test")
    fracture_test_type3 = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )


    
    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
    
            record.tensile_strength_visible = False
            record.elongation_visible = False
            record.tensile_strength_visible1 = False

            record.tensile_test_visible = False
            record.face_bend_visible = False
            record.root_bend_visible = False

            record.fillet_weld_fracture_visible = False

            record.fracture_test_visible1 = False
            record.fracture_visible2 = False
            record.weld_fracture_test_visible = False
            record.fillet_weld_fracture_test_visible = False
            record.fracture_test_visible3 = False
            
            
            

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "d96a5e06-7d28-425e-ad2e-cd425cbfb8d5":
                    record.tensile_strength_visible = True 
                if sample.internal_id == "03d3e787-c3f3-4d98-b2af-8a25cf5fa837":
                    record.elongation_visible = True 
                if sample.internal_id == "9bb2ac9c-5a6e-4e4d-bb2d-07ebb3c42089":
                    record.tensile_strength_visible1 = True 

                if sample.internal_id == "dcfe8664-3cf9-4e4b-be3f-2bff8f2397d6":
                    record.tensile_test_visible = True 
                if sample.internal_id == "346b9bc7-6e36-4d50-852d-4a8fe4d3d1fa":
                    record.face_bend_visible = True 
                if sample.internal_id == "998eec27-af5c-4eef-97f4-7b48e2fe3e9b":
                    record.root_bend_visible = True 

                if sample.internal_id == "6e6c60db-2e99-45f4-95a1-1eab96544bd5":
                    record.fillet_weld_fracture_visible = True 

                if sample.internal_id == "0247b05a-5fc4-4c7f-82f4-99d10320b5ac":
                    record.fracture_test_visible1 = True 
                if sample.internal_id == "2ba6a0d0-5d39-40b8-ab3f-483eb94c5b5f":
                    record.fracture_visible2 = True 
                if sample.internal_id == "5657ef7f-9583-470f-9048-0a091dcefc38":
                    record.weld_fracture_test_visible = True 
                
                if sample.internal_id == "f2ae5a34-2945-47e5-a2a3-49196e776431":
                    record.fillet_weld_fracture_test_visible = True 

                if sample.internal_id == "5d65cd1a-3964-4c9f-a236-bc19ef817beb":
                    record.fracture_test_visible3 = True 

               

               
                

                
     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
           

            
            if result.parameter.internal_id == 'd96a5e06-7d28-425e-ad2e-cd425cbfb8d5':
                result.result_char = round(self.tensile_strength,2)
                result.calculated = True
                if self.tensile_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            
            if result.parameter.internal_id == '03d3e787-c3f3-4d98-b2af-8a25cf5fa837':
                result.result_char = round(self.elongation,2)
                result.calculated = True
                if self.elongation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '9bb2ac9c-5a6e-4e4d-bb2d-07ebb3c42089':
                result.result_char = round(self.tensile_strength1,2)
                result.calculated = True
                if self.tensile_strength1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'dcfe8664-3cf9-4e4b-be3f-2bff8f2397d6':
                result.result_char = round(self.tensile_test,2)
                result.calculated = True
                if self.tensile_test_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '998eec27-af5c-4eef-97f4-7b48e2fe3e9b':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '0247b05a-5fc4-4c7f-82f4-99d10320b5ac':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '6e6c60db-2e99-45f4-95a1-1eab96544bd5':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '2ba6a0d0-5d39-40b8-ab3f-483eb94c5b5f':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '5657ef7f-9583-470f-9048-0a091dcefc38':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'f2ae5a34-2945-47e5-a2a3-49196e776431':
                # result.result_char = round(self.yield_strength,2)
                result.calculated = True
                # if self.yield_strength_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '5d65cd1a-3964-4c9f-a236-bc19ef817beb':
                # result.result_char = round(self.yield_strength,2)
                result.calculated = True
                # if self.yield_strength_nabl == 'pass':
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
        record = super(MechanicalWeldedSample, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

   

    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        current_user = self.env.user

        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # Check if user is in Lerm Admin group
            if (
                current_user.has_group('lerm_civil.kes_admin_access_group')
                or current_user.has_group('lerm_civil.lerm_sample_verification')
                or current_user.has_group('lerm_civil.lerm_sample_approval')
            ):
                # Admin sees all parameters
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # Other users only see parameters assigned to them
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]

    def get_all_fields(self):
        record = self.env['mechanical.welded.sample'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class WeldedNotes(models.Model):
    _name = "welded.sample.notes"

    parent_id = fields.Many2one('mechanical.welded.sample',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
