from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalWeldedSteel(models.Model):
    _name = "mechanical.welded.steel"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    name2 = fields.Char("Name",default="Welded Steel")
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

    notes_id = fields.One2many('welded.steel.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalWeldedSteel, self).default_get(fields)

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


    elongation_visible = fields.Boolean("% of Elongation Visible",compute="_compute_visible")
    elongation_name = fields.Char("Name",default="% of Elongation - (ASME Sec IX: 2023)")
    elongation = fields.Float(string="% of Elongation")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pmjnhbgr-7d28-425e-ad2e-cd3645987645t')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pmjnhbgr-7d28-425e-ad2e-cd3645987645t')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pmjnhbgr-7d28-425e-ad2e-cd3645987645t')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pmjnhbgr-7d28-425e-ad2e-cd3645987645t')]).parameter_table
            
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

    



    bend_test_visible = fields.Boolean("Bend Test Visible",compute="_compute_visible")
    bend_test_name = fields.Char("Name",default="Bend Test - (ASME Sec IX: 2023)")
    bend_test = fields.Char(string="Bend Test")
    bend_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    fracture_test_visible = fields.Boolean("Fracture test Visible",compute="_compute_visible")
    fracture_test_name = fields.Char("Name",default="Fracture test - (ASME Sec IX: 2023)")
    fracture_test = fields.Char(string="Fracture test")
    fracture_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    longitudinal_test_visible = fields.Boolean("Longitudinal Tensile testing Visible",compute="_compute_visible")
    longitudinal_test_name = fields.Char("Name",default="Longitudinal Tensile testing - (ASME Sec IX: 2023)")
    longitudinal_test = fields.Char(string="Longitudinal Tensile testing")
    longitudinal_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )



    tensile_strength_visible = fields.Boolean("Tensile strength Visible",compute="_compute_visible")
    tensile_strength_name = fields.Char("Name",default="Tensile Strength - (ASME Sec IX: 2023)")
    tensile_strength = fields.Float(string="Tensile strength")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','mnhyt564-7d28-425e-ad2e-cd39ijuyhgt65')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','mnhyt564-7d28-425e-ad2e-cd39ijuyhgt65')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','mnhyt564-7d28-425e-ad2e-cd39ijuyhgt65')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','mnhyt564-7d28-425e-ad2e-cd39ijuyhgt65')]).parameter_table
            
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


    tensile_strength_uts_visible = fields.Boolean("Tensile Strength (UTS) Visible",compute="_compute_visible")
    tensile_strength_uts_name = fields.Char("Name",default="Tensile Strength (UTS) - (ASME Sec IX: 2023)")
    tensile_strength_uts = fields.Float(string="Tensile Strength (UTS)")

    tensile_strength_uts_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_strength_uts_conformity")

    tensile_strength_uts_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_strength_uts_nabl")


    @api.depends('tensile_strength_uts','eln_ref','grade')
    def _compute_tensile_strength_uts_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_strength_uts_conformity = 'na'
                continue
            record.tensile_strength_uts_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ikmnjhuy6-7d28-425e-ad2e-cd39iu765trgb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ikmnjhuy6-7d28-425e-ad2e-cd39iu765trgb')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_strength_uts - record.tensile_strength_uts*mu_value
                    upper = record.tensile_strength_uts + record.tensile_strength_uts*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_strength_uts_conformity = 'pass'
                        break
                    else:
                        record.tensile_strength_uts_conformity = 'fail'

    @api.depends('tensile_strength_uts','eln_ref','grade')
    def _compute_tensile_strength_uts_nabl(self):
        
        for record in self:
            
            record.tensile_strength_uts_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ikmnjhuy6-7d28-425e-ad2e-cd39iu765trgb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ikmnjhuy6-7d28-425e-ad2e-cd39iu765trgb')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_strength_uts - record.tensile_strength_uts*mu_value
            upper = record.tensile_strength_uts + record.tensile_strength_uts*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_strength_uts_nabl = 'pass'
                break
            else:
                record.tensile_strength_uts_nabl = 'fail'

    transverse_bend_test_visible = fields.Boolean("Transverse side Bend test Visible",compute="_compute_visible")
    transverse_bend_test_name = fields.Char("Name",default="Transverse side Bend test - (ASME Sec IX: 2023)")
    transverse_bend_test = fields.Char(string="Transverse side Bend test")
    transverse_bend_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )


    yield_strength_visible = fields.Boolean("Yield Strength Visible",compute="_compute_visible")
    yield_strength_name = fields.Char("Name",default="Yield Strength - (ASME Sec IX: 2023)")
    yield_strength = fields.Float(string="Yield Strength")

    yield_strength_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_yield_strength_conformity")

    yield_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_yield_strength_nabl")


    @api.depends('yield_strength','eln_ref','grade')
    def _compute_yield_strength_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.yield_strength_conformity = 'na'
                continue
            record.yield_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','yut65rfvg-7d28-425e-ad2e-cd3opmnbghtyr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','yut65rfvg-7d28-425e-ad2e-cd3opmnbghtyr')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.yield_strength - record.yield_strength*mu_value
                    upper = record.yield_strength + record.yield_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.yield_strength_conformity = 'pass'
                        break
                    else:
                        record.yield_strength_conformity = 'fail'

    @api.depends('yield_strength','eln_ref','grade')
    def _compute_yield_strength_nabl(self):
        
        for record in self:
            
            record.yield_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','yut65rfvg-7d28-425e-ad2e-cd3opmnbghtyr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','yut65rfvg-7d28-425e-ad2e-cd3opmnbghtyr')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.yield_strength - record.yield_strength*mu_value
            upper = record.yield_strength + record.yield_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.yield_strength_nabl = 'pass'
                break
            else:
                record.yield_strength_nabl = 'fail'

    transverse_tensile_visible = fields.Boolean("Transverse Tensile test Visible",compute="_compute_visible")
    transverse_tensile_name = fields.Char("Name",default="Transverse Tensile test - (ASME Sec IX: 2023)")
    transverse_tensile = fields.Float(string="Transverse Tensile test")

    transverse_tensile_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_transverse_tensile_conformity")

    transverse_tensile_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_transverse_tensile_nabl")


    @api.depends('transverse_tensile','eln_ref','grade')
    def _compute_transverse_tensile_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.transverse_tensile_conformity = 'na'
                continue
            record.transverse_tensile_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oiu786tygb-7d28-425e-ad2e-cd0omnhjyu56')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oiu786tygb-7d28-425e-ad2e-cd0omnhjyu56')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.transverse_tensile - record.transverse_tensile*mu_value
                    upper = record.transverse_tensile + record.transverse_tensile*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.transverse_tensile_conformity = 'pass'
                        break
                    else:
                        record.transverse_tensile_conformity = 'fail'

    @api.depends('transverse_tensile','eln_ref','grade')
    def _compute_transverse_tensile_nabl(self):
        
        for record in self:
            
            record.transverse_tensile_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oiu786tygb-7d28-425e-ad2e-cd0omnhjyu56')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oiu786tygb-7d28-425e-ad2e-cd0omnhjyu56')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.transverse_tensile - record.transverse_tensile*mu_value
            upper = record.transverse_tensile + record.transverse_tensile*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.transverse_tensile_nabl = 'pass'
                break
            else:
                record.transverse_tensile_nabl = 'fail'


   


    
    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
    
            record.elongation_visible = False
            record.bend_test_visible = False
            record.fracture_test_visible = False
            record.longitudinal_test_visible = False
            record.tensile_strength_visible = False
            record.tensile_strength_uts_visible = False
            record.transverse_bend_test_visible = False
            record.yield_strength_visible = False
            record.transverse_tensile_visible = False
           
            
            

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "pmjnhbgr-7d28-425e-ad2e-cd3645987645t":
                    record.elongation_visible = True 

                if sample.internal_id == "mnbgt543e-7d28-425e-ad2e-cd3oiuytrfg65":
                    record.bend_test_visible = True 

                if sample.internal_id == "plmnbghte-7d28-425e-ad2e-cd3oinhytgfrt":
                    record.fracture_test_visible = True 
                
                if sample.internal_id == "pmnbhgtyr-7d28-425e-ad2e-cd3pomnyhbgt":
                    record.longitudinal_test_visible = True 

                if sample.internal_id == "mnhyt564-7d28-425e-ad2e-cd39ijuyhgt65":
                    record.tensile_strength_visible = True 

                if sample.internal_id == "ikmnjhuy6-7d28-425e-ad2e-cd39iu765trgb":
                    record.tensile_strength_uts_visible = True 

                if sample.internal_id == "mnbgtr453e-7d28-425e-ad2e-cd3mnby65trfg":
                    record.transverse_bend_test_visible = True 

                if sample.internal_id == "yut65rfvg-7d28-425e-ad2e-cd3opmnbghtyr":
                    record.yield_strength_visible = True

                if sample.internal_id == "oiu786tygb-7d28-425e-ad2e-cd0omnhjyu56":
                    record.transverse_tensile_visible = True
                
                
                

                
     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
           

            
            if result.parameter.internal_id == 'pmjnhbgr-7d28-425e-ad2e-cd3645987645t':
                result.result_char = round(self.elongation,2)
                result.calculated = True
                if self.elongation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'mnbgt543e-7d28-425e-ad2e-cd3oiuytrfg65':
                # result.result_char = round(self.elongation,2)
                result.calculated = True
                # if self.elongation_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'plmnbghte-7d28-425e-ad2e-cd3oinhytgfrt':
                # result.result_char = round(self.elongation,2)
                result.calculated = True
                # if self.elongation_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'pmnbhgtyr-7d28-425e-ad2e-cd3pomnyhbgt':
                # result.result_char = round(self.elongation,2)
                result.calculated = True
                # if self.elongation_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'mnhyt564-7d28-425e-ad2e-cd39ijuyhgt65':
                result.result_char = round(self.tensile_strength,2)
                result.calculated = True
                if self.tensile_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'ikmnjhuy6-7d28-425e-ad2e-cd39iu765trgb':
                result.result_char = round(self.tensile_strength_uts,2)
                result.calculated = True
                if self.tensile_strength_uts_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'mnbgtr453e-7d28-425e-ad2e-cd3mnby65trfg':
                # result.result_char = round(self.elongation,2)
                result.calculated = True
                # if self.elongation_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'yut65rfvg-7d28-425e-ad2e-cd3opmnbghtyr':
                result.result_char = round(self.yield_strength,2)
                result.calculated = True
                if self.yield_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            
            if result.parameter.internal_id == 'oiu786tygb-7d28-425e-ad2e-cd0omnhjyu56':
                result.result_char = round(self.transverse_tensile,2)
                result.calculated = True
                if self.transverse_tensile_nabl == 'pass':
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
        record = super(MechanicalWeldedSteel, self).create(vals)
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
        record = self.env['mechanical.welded.steel'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class WeldedSteelNotes(models.Model):
    _name = "welded.steel.notes"

    parent_id = fields.Many2one('mechanical.welded.steel',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
