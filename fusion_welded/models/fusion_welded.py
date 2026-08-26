from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalFusionWelded(models.Model):
    _name = "mechanical.fusion.welded"
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

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")
    product_name = fields.Char("Product Name")

    description_work = fields.Text("Description Of Work")

    notes_id = fields.One2many('fusion.welded.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalFusionWelded, self).default_get(fields)

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


    yield_strength_visible = fields.Boolean("Yield Strength Visible",compute="_compute_visible")
    yield_strength_name = fields.Char("Name",default="Yield Strength - (ISO 6892-1 : 2019: 2019)")
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98765nhbgt45-107d-4e30-9d3d-2a9009r9078654567')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98765nhbgt45-107d-4e30-9d3d-2a9009r9078654567')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98765nhbgt45-107d-4e30-9d3d-2a9009r9078654567')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98765nhbgt45-107d-4e30-9d3d-2a9009r9078654567')]).parameter_table
            
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



    face_bend_test_visible = fields.Boolean("Face bend test Visible",compute="_compute_visible")
    face_bend_test_name = fields.Char("Name",default="Face bend test - (ASME Sec IX: 2023)")
    face_bend_test = fields.Char(string="Face bend test")
    face_bend_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    root_bend_test_visible = fields.Boolean("Root bend test Visible",compute="_compute_visible")
    root_bend_test_name = fields.Char("Name",default="Root bend test - (ASME Sec IX: 2023)")
    root_bend_test = fields.Char(string="Root bend test")
    root_bend_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    side_bend_test_visible = fields.Boolean("Side bend Test Visible",compute="_compute_visible")
    side_bend_test_name = fields.Char("Name",default="Side bend Test - (ASME Sec IX: 2023)")
    side_bend_test = fields.Char(string="Side bend Test")
    side_bend_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )


    face_bend_test_visible1 = fields.Boolean("Face bend test Visible",compute="_compute_visible")
    face_bend_test_name1 = fields.Char("Name",default="Face bend test - (IS 3600 (Part 6): 1983: 1983)")
    face_bend_test1 = fields.Char(string="Face bend test")
    face_bend_test_type1 = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    root_bend_test_visible1 = fields.Boolean("Root bend test Visible",compute="_compute_visible")
    root_bend_test_name1 = fields.Char("Name",default="Root bend test - (IS 3600 (Part 6): 1983: 1983)")
    root_bend_test1 = fields.Char(string="Root bend test")
    root_bend_test_type1 = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    side_bend_test_visible1 = fields.Boolean("Side bend Test Visible",compute="_compute_visible")
    side_bend_test_name1 = fields.Char("Name",default="Side bend Test - (IS 3600 (Part 6): 1983: 1983)")
    side_bend_test1 = fields.Char(string="Side bend Test")
    side_bend_test_type1 = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )


    transverse_bend_test_visible = fields.Boolean("Transverse Bend Test Visible",compute="_compute_visible")
    transverse_bend_test_name = fields.Char("Name",default="Transverse Bend Test - (ASME Sec IX: 2023)")
    transverse_bend_test = fields.Char(string="Transverse Bend Test")
    transverse_bend_test_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    fillet_weld_visible = fields.Boolean("Fillet - Weld Visible",compute="_compute_visible")
    fillet_weld_name = fields.Char("Name",default="Fillet - Weld - (ASME Sec IX: 2023)")
    fillet_weld = fields.Char(string="Fillet - Weld")
    fillet_weld_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    fillet_weld_visible1 = fields.Boolean("Fillet - Weld Visible",compute="_compute_visible")
    fillet_weld_name1 = fields.Char("Name",default="Fillet - Weld - (IS 3600 (Part 8):2024: 2024)")
    fillet_weld1 = fields.Char(string="Fillet - Weld")
    fillet_weld_type1 = fields.Selection(
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
    
            record.face_bend_test_visible = False
            record.root_bend_test_visible = False
            record.side_bend_test_visible = False

            record.face_bend_test_visible1 = False
            record.root_bend_test_visible1 = False
            record.side_bend_test_visible1 = False

            record.yield_strength_visible = False

            record.transverse_bend_test_visible = False
            record.fillet_weld_visible = False
            record.fillet_weld_visible1 = False
            
            
            

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "98567ut5-107d-4e30-9d3d-2a8975yh5643j":
                    record.face_bend_test_visible = True 
                if sample.internal_id == "0956yhgrt-107d-4e30-9d3d-2a80867453456":
                    record.root_bend_test_visible = True 
                if sample.internal_id == "0oiuy43rfg-107d-4e30-9d3d-2a85678409876":
                    record.side_bend_test_visible = True 

                if sample.internal_id == "jmnhbgyr-107d-4e30-9d3d-2a8975yh09tyrfg":
                    record.face_bend_test_visible1 = True 
                if sample.internal_id == "fhfbubfhui-107d-4e30-9d3d-2a808674kjnmbh":
                    record.root_bend_test_visible1 = True 
                if sample.internal_id == "7889045gh-107d-4e30-9d3d-2a85678586jfnnh":
                    record.side_bend_test_visible1 = True 

                if sample.internal_id == "98765nhbgt45-107d-4e30-9d3d-2a9009r9078654567":
                    record.yield_strength_visible = True 

                if sample.internal_id == "9898555nhgyt-107d-4e30-9d3d-2a9009r09775yhgtb":
                    record.transverse_bend_test_visible = True 
                if sample.internal_id == "io567455nhgyt-107d-4e30-9d3d-2a9009r8967453456":
                    record.fillet_weld_visible = True 
                if sample.internal_id == "kljuytre453rtg-107d-4e30-9d3d-2a9009r9897645324":
                    record.fillet_weld_visible1 = True 
                

               

               
                

                
     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
           

            
            if result.parameter.internal_id == '98567ut5-107d-4e30-9d3d-2a8975yh5643j':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 
            
            if result.parameter.internal_id == 'kljuytre453rtg-107d-4e30-9d3d-2a9009r9897645324':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'io567455nhgyt-107d-4e30-9d3d-2a9009r8967453456':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '9898555nhgyt-107d-4e30-9d3d-2a9009r09775yhgtb':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '0956yhgrt-107d-4e30-9d3d-2a80867453456':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '0oiuy43rfg-107d-4e30-9d3d-2a85678409876':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'jmnhbgyr-107d-4e30-9d3d-2a8975yh09tyrfg':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'fhfbubfhui-107d-4e30-9d3d-2a808674kjnmbh':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '7889045gh-107d-4e30-9d3d-2a85678586jfnnh':
                # result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                # if self.reduction_in_area_percent_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '98765nhbgt45-107d-4e30-9d3d-2a9009r9078654567':
                result.result_char = round(self.yield_strength,2)
                result.calculated = True
                if self.yield_strength_nabl == 'pass':
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
        record = super(MechanicalFusionWelded, self).create(vals)
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
        record = self.env['mechanical.fusion.welded'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class FusionWeldedNotes(models.Model):
    _name = "fusion.welded.notes"

    parent_id = fields.Many2one('mechanical.fusion.welded',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
