from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class Tile(models.Model):
    _name = "mechanical.tile"
    _inherit = "lerm.eln"
    _description = 'mechanical.tile'
    _rec_name = "name"

    name = fields.Char("Name",default="TILE")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id


    def get_all_fields(self):
        record = self.env['mechanical.tile'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



    product_id = fields.Many2one('product.template', string="Product", compute="_compute_product_id",store=True)



    @api.depends('eln_ref')
    def _compute_product_id(self):
        if self.eln_ref:
            self.product_id = self.eln_ref.material.id

  
    

    size = fields.Many2one('lerm.size.line',string="Type of group",store=True,domain="[('product_id', '=', product_id)]")

    tile_type = fields.Char(string="Type Of Tile")

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    # Water Absorption
    water_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")   
    
    water_absorption_line_ids = fields.One2many(
        'tile.water.absorption.line',
        'parent_id',
        string='Water Absorption Lines'
    )

    average_water_absorption = fields.Float(
        string='Average Water Absorption (%)',
        compute='_compute_average_absorption',
        store=True
    )

    @api.depends('water_absorption_line_ids.water_absorption')
    def _compute_average_absorption(self):
        for rec in self:
            values = rec.water_absorption_line_ids.mapped('water_absorption')
            rec.average_water_absorption = (
                sum(values) / len(values)
            ) if values else 0.0


    average_water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_average_water_absorption_confirmity")
    
    @api.depends('average_water_absorption','eln_ref','grade')
    def _compute_average_water_absorption_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_water_absorption_confirmity = 'na'
                continue
            record.average_water_absorption_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d81b405-ed58-4374-bda7-2825e12f307c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d81b405-ed58-4374-bda7-2825e12f307c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_water_absorption - record.average_water_absorption*mu_value
                    upper = record.average_water_absorption + record.average_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_water_absorption_confirmity = 'pass'
                        break
                    else:
                        record.average_water_absorption_confirmity = 'fail'

    average_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_average_water_absorption_nabl",store=True)

    @api.depends('average_water_absorption','eln_ref','grade')
    def _compute_average_water_absorption_nabl(self):
        
        for record in self:
            record.average_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d81b405-ed58-4374-bda7-2825e12f307c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d81b405-ed58-4374-bda7-2825e12f307c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption - record.average_water_absorption*mu_value
                    upper = record.average_water_absorption + record.average_water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_water_absorption_nabl = 'pass'
                        break
                    else:
                        record.average_water_absorption_nabl = 'fail'


    # Straightness

    straightness_name = fields.Char("Name",default="Straightness")
    straightness_visible = fields.Boolean("Straightness Visible",compute="_compute_visible") 

    straightness_length = fields.Float(
        string='Length',
    )

    straightness_width = fields.Float(
        string='Width',
    )

    straightness_line_ids = fields.One2many(
        'mechanical.straightness.tile.line',
        'parent_id',
        string='Straightness Lines'
    )

    straightness_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    straightness_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_straightness_nabl",
    store=True
)

    @api.depends('straightness_report_type')
    def _compute_straightness_nabl(self):
     for rec in self:
        rec.straightness_nabl = 'pass' if rec.straightness_report_type == 'nabl' else 'fail'


    # straightness_max_gap = fields.Float(
    #     string='Maximum Gap Observed (mm)',
    #     compute='_compute_straightness_max_gap',
    #     store=True
    # )

    # @api.depends('straightness_line_ids.average')
    # def _compute_straightness_max_gap(self):
    #     for rec in self:
    #         gaps = rec.straightness_line_ids.mapped('average')
    #         rec.straightness_max_gap = max(gaps) if gaps else 0.0


    # straightness_max_gap_confirmity = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_straightness_max_gap_confirmity")
    
    # @api.depends('straightness_max_gap','eln_ref','grade')
    # def _compute_straightness_max_gap_confirmity(self):
    #     for record in self:
    #         if not record.eln_ref or not record.eln_ref.conformity:
    #             record.straightness_max_gap_confirmity = 'na'
    #             continue
    #         record.straightness_max_gap_confirmity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
    #                 lower = record.straightness_max_gap - record.straightness_max_gap*mu_value
    #                 upper = record.straightness_max_gap + record.straightness_max_gap*mu_value
    #                 if lower >= req_min and upper <= req_max :
    #                     record.straightness_max_gap_confirmity = 'pass'
    #                     break
    #                 else:
    #                     record.straightness_max_gap_confirmity = 'fail'

    # straightness_max_gap_nabl = fields.Selection([
    #     ('pass', 'NABL'),
    #     ('fail', 'Non-NABL')], string='NABL', compute="_compute_straightness_max_gap_nabl",store=True)

    # @api.depends('straightness_max_gap','eln_ref','grade')
    # def _compute_straightness_max_gap_nabl(self):
        
    #     for record in self:
    #         record.straightness_max_gap_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.straightness_max_gap - record.straightness_max_gap*mu_value
    #                 upper = record.straightness_max_gap + record.straightness_max_gap*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.straightness_max_gap_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.straightness_max_gap_nabl = 'fail'


    # Rectangularity
    rectangularity_name = fields.Char("Name",default="Rectangularity")
    rectangularity_visible = fields.Boolean("Rectangularity Visible",compute="_compute_visible")   
    
    rectangularity_line_ids = fields.One2many(
        'mechanical.rectangularity.tile.line',
        'parent_id',
        string='Rectangularity Lines')


    rectangularity_length = fields.Float(
        string='Length',
    )


    rectangularity_width = fields.Float(
        string='Width',
    )


    rectangularity_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    rectangularity_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_rectangularity_nabl",
    store=True
)

    @api.depends('rectangularity_report_type')
    def _compute_rectangularity_nabl(self):
     for rec in self:
        rec.rectangularity_nabl = 'pass' if rec.rectangularity_report_type == 'nabl' else 'fail'


    # Dimension of Tiles (Measurement of Length & Width) 						
    deviation_name = fields.Char("Name",default="Dimension of Tiles (Measurement of Length & Width) ")
    deviation_visible = fields.Boolean("Dimension of Tiles (Measurement of Length & Width)  Visible",compute="_compute_visible")  

    deviation_line_ids = fields.One2many(
        'tile.length.width.line',
        'parent_id',
        string='Dimension of Tiles (Measurement of Length & Width) Lines') 

    work_length = fields.Float(
        string='Nominal Length',
    )

    work_width = fields.Float(
        string='Width',
    )
    
    deviation_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    deviation_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_deviation_nabl",
    store=True
)

    @api.depends('deviation_report_type')
    def _compute_deviation_nabl(self):
     for rec in self:
        rec.deviation_nabl = 'pass' if rec.deviation_report_type == 'nabl' else 'fail'


    # Deviation in Thickness %

    thickness_name = fields.Char("Name",default="Nominal Thickness of Tiles")
    thickness_visible = fields.Boolean("Nominal Thickness of Tiles Visible",compute="_compute_visible") 

    
    thickness_child_lines = fields.One2many('tile.thickness.line','parent_id',string="Parameter")

    nominal_thickness = fields.Float(
        string='Nominal Thickness',
    )

    thickness_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    thickness_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_thickness_nabl",
    store=True
)

    @api.depends('thickness_report_type')
    def _compute_thickness_nabl(self):
     for rec in self:
        rec.thickness_nabl = 'pass' if rec.thickness_report_type == 'nabl' else 'fail'


    # Center Curvature

    center_curvature_name = fields.Char("Name",default="Center Curvature")
    center_curvature_visible = fields.Boolean("Center Curvature Visible",compute="_compute_visible") 

    
    center_curvature_child_lines = fields.One2many('tile.center.curvature.line','parent_id',string="Parameter")

    center_curvature_length = fields.Float(
        string='Length',
    )

    center_curvature_width = fields.Float(
        string='Width',
    )


    center_curvature_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    center_curvature_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_center_curvature_nabl",
    store=True
)

    @api.depends('center_curvature_report_type')
    def _compute_center_curvature_nabl(self):
     for rec in self:
        rec.center_curvature_nabl = 'pass' if rec.center_curvature_report_type == 'nabl' else 'fail'


    # Edge Curvature

    edge_curvature_name = fields.Char("Name",default="Edge Curvature")
    edge_curvature_visible = fields.Boolean("Edge Curvature Visible",compute="_compute_visible") 

    
    edge_curvature_child_lines = fields.One2many('tile.edge.curvature.line','parent_id',string="Parameter")

    edge_curvature_length = fields.Float(
        string='Length',
    )

    edge_curvature_width = fields.Float(
        string='Width',
    )

    edge_curvature_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='non_nabl',
        required=True,
    )

    edge_curvature_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_edge_curvature_nabl",
    store=True
)

    @api.depends('edge_curvature_report_type')
    def _compute_edge_curvature_nabl(self):
     for rec in self:
        rec.edge_curvature_nabl = 'pass' if rec.edge_curvature_report_type == 'nabl' else 'fail'


    # Warpage

    warpage_name = fields.Char("Name",default="Warpage")
    warpage_visible = fields.Boolean("Warpage Visible",compute="_compute_visible") 

    
    warpage_child_lines = fields.One2many('tile.warpage.line','parent_id',string="Parameter")

    warpage_length = fields.Float(
        string='Length',
    )

    warpage_width = fields.Float(
        string='Width',
    )


    warpage_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    warpage_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_warpage_nabl",
    store=True
)

    @api.depends('warpage_report_type')
    def _compute_warpage_nabl(self):
     for rec in self:
        rec.warpage_nabl = 'pass' if rec.warpage_report_type == 'nabl' else 'fail'

    # MOHS Hardness

    mohs_hardness_name = fields.Char("Name",default="MOHS Hardness")
    mohs_hardness_visible = fields.Boolean("MOHS Hardness Visible",compute="_compute_visible") 

    
    mohs_hardness_child_lines = fields.One2many('tile.mohs.hardness.line','parent_id',string="Parameter")

    mohs_hardness_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    mohs_hardness_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_mohs_hardness_nabl",
    store=True
)

    @api.depends('mohs_hardness_report_type')
    def _compute_mohs_hardness_nabl(self):
     for rec in self:
        rec.mohs_hardness_nabl = 'pass' if rec.mohs_hardness_report_type == 'nabl' else 'fail'

    


   ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.water_absorption_visible = False
            record.straightness_visible = False
            record.rectangularity_visible = False
            record.deviation_visible = False
            record.thickness_visible = False
            record.center_curvature_visible = False
            record.edge_curvature_visible = False
            record.warpage_visible = False
            record.mohs_hardness_visible = False
            
           
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "5d81b405-ed58-4374-bda7-2825e12f307c":
                    record.water_absorption_visible = True

                if sample.internal_id == "19999f82-79c0-44a8-9379-f40dd33235aa":
                    record.straightness_visible = True

                if sample.internal_id == "4e209b70-f6b9-49b9-bab6-f38292f64b1c":
                    record.rectangularity_visible = True

                if sample.internal_id == "35777f82-79c0-44a8-9379-f40dd33235uyt":
                    record.deviation_visible = True

                if sample.internal_id == "1db41e6d-550e-4c5d-a923-7510a616beb5":
                    record.thickness_visible = True

                if sample.internal_id == "873e02d1-db08-43d8-a88f-f6de09d41955":
                    record.center_curvature_visible = True

                if sample.internal_id == "2c4efee6-d22a-4eec-afbb-5435f3041f3f":
                    record.edge_curvature_visible = True

                if sample.internal_id == "91fc2258-6bd7-40d4-82d8-404af0928ae9":
                    record.warpage_visible = True

                if sample.internal_id == "ecfb0b0b-0774-4296-af7b-6151fbf4f968":
                    record.mohs_hardness_visible = True

               


                

                

                

                

                






    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
             

            # Water Absorption
            if result.parameter.internal_id == '5d81b405-ed58-4374-bda7-2825e12f307c':
                result.calculated = True
                result.result_char = round(self.average_water_absorption,2)
                if self.average_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            # Straightness
            if result.parameter.internal_id == '19999f82-79c0-44a8-9379-f40dd33235aa':
                result.calculated = True
                if self.straightness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Rectangularity
            if result.parameter.internal_id == '4e209b70-f6b9-49b9-bab6-f38292f64b1c':
                result.calculated = True
                if self.rectangularity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



            # Measurement of Length & Width ( in mm) 	
            if result.parameter.internal_id == '35777f82-79c0-44a8-9379-f40dd33235uyt':
                result.calculated = True
                if self.deviation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Thickness
            if result.parameter.internal_id == '1db41e6d-550e-4c5d-a923-7510a616beb5':
                result.calculated = True
                if self.thickness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Center Curvature
            if result.parameter.internal_id == '873e02d1-db08-43d8-a88f-f6de09d41955':
                result.calculated = True
                if self.center_curvature_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Edge Curvature
            if result.parameter.internal_id == '2c4efee6-d22a-4eec-afbb-5435f3041f3f':
                result.calculated = True
                if self.edge_curvature_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Warpage
            if result.parameter.internal_id == '91fc2258-6bd7-40d4-82d8-404af0928ae9':
                result.calculated = True
                if self.warpage_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Warpage
            if result.parameter.internal_id == 'ecfb0b0b-0774-4296-af7b-6151fbf4f968':
                result.calculated = True
                if self.mohs_hardness_nabl == 'pass':
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
        record = super(Tile, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

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
        record = self.env['mechanical.tile'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    notes_id = fields.One2many('mechanical.tile.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'Attention is drawn to the limitations of liability, indemnification, and jurisdiction provisions applicable to this report. The information contained herein reflects the findings of Geonyms India Private Limited at the time of testing and only within the scope of work and instructions received from the Client, where applicable',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'The Companys responsibility is limited to the Client for whom this report has been issued. This report does not relieve any party from exercising its rights and fulfilling its obligations under any contract, agreement, or applicable statutory requirements. Unless otherwise stated, the results reported herein relate only to the sample(s) tested and do not necessarily indicate the quality of the entire lot, batch, or material from which the sample(s) were drawn. ',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'The sample(s) tested shall be retained for a period of ninety (90) days from the date of issue of this report unless otherwise agreed with the Client. This report shall not be reproduced, except in full, without the prior written approval of Geonyms India Private Limited. ',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'Partial reproduction, unauthorized alteration, forgery, falsification, or misuse of this report is prohibited and may result in legal action.',
            }),
            (0, 0, {
                'sr_no': 'v',
                'notes': ' Any complaint concerning this report shall be submitted in writing within fifteen (15) days from the date of issue of the report. The use of this report or extracts thereof in advertisements, promotional material, media publications, or any public disclosure requires prior written approval from Geonyms India Private Limited',
            }),
        ]


class TileWaterAbsorptionLine(models.Model):
    _name = "tile.water.absorption.line"
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    dry_mass_w1 = fields.Float(
        string='Dry Mass, W1 (g)'
    )

    saturated_mass_w2 = fields.Float(
        string='Saturated Mass, W2 (g)'
    )


    water_absorption = fields.Float(
        string='Water Absorption (%)',
        compute='_compute_values',
        store=True,
        digits=(16, 2)
    )

    @api.depends('dry_mass_w1', 'saturated_mass_w2')
    def _compute_values(self):
        for rec in self:
            if rec.dry_mass_w1:
                rec.water_absorption = (
                    (rec.saturated_mass_w2 - rec.dry_mass_w1)
                    / rec.dry_mass_w1
                ) * 100
            else:
                rec.water_absorption = 0.0

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileWaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class StraightnessTile(models.Model):
    _name = "mechanical.straightness.tile.line"
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Tile ID",readonly=True, copy=False, default=1)

    side1 = fields.Float(
        string='Side 1',
    )

    side2 = fields.Float(
        string='Side 2',
    )

    side3 = fields.Float(
        string='Side 3',
    )

    side4 = fields.Float(
        string='Side 4',
    )

    deviation_length = fields.Float(
        string='Deviation (Length) (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    deviation_width = fields.Float(
        string='Deviation (Width) (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    average = fields.Float(
        string='Average (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    @api.depends(
        'side1',
        'side2',
        'side3',
        'side4',
        'parent_id.straightness_length',
        'parent_id.straightness_width',
    )
    def _compute_deviation(self):
        for line in self:

            length = line.parent_id.straightness_length
            width = line.parent_id.straightness_width

            if length:
                line.deviation_length = (
                    ((line.side1 - line.side3) / length) * 100
                )
            else:
                line.deviation_length = 0.0

            if width:
                line.deviation_width = (
                    ((line.side2 - line.side4) / width) * 100
                )
            else:
                line.deviation_width = 0.0

            line.average = (
                line.deviation_length + line.deviation_width
            ) / 2


            

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(StraightnessTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class RectangularityTile(models.Model):
    _name = "mechanical.rectangularity.tile.line"
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    
    side1 = fields.Float(
        string='Reading 1',
    )

    side2 = fields.Float(
        string='Reading 2',
    )

    side3 = fields.Float(
        string='Reading 3',
    )

    side4 = fields.Float(
        string='Reading 4',
    )

    deviation_length = fields.Float(
        string='Deviation (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    deviation_width = fields.Float(
        string='Deviation (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    average = fields.Float(
        string='Average (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    @api.depends(
        'side1',
        'side2',
        'side3',
        'side4',
        'parent_id.rectangularity_length',
        'parent_id.rectangularity_width',
    )
    def _compute_deviation(self):
        for line in self:

            length = line.parent_id.rectangularity_length
            width = line.parent_id.rectangularity_width

            if length:
                line.deviation_length = (
                    ((line.side3 - line.side1) / length) * 100
                )
            else:
                line.deviation_length = 0.0

            if width:
                line.deviation_width = (
                    ((line.side2 - line.side4) / width) * 100
                )
            else:
                line.deviation_width = 0.0

            line.average = (
                line.deviation_length + line.deviation_width
            ) / 2



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(RectangularityTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class TileLengthWidthLine(models.Model):
    _name = 'tile.length.width.line'
    _description = 'Dimension of Tiles (Measurement of Length & Width)'

    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    side1 = fields.Float(
        string='Side 1',
    )

    side2 = fields.Float(
        string='Side 2',
    )

    side3 = fields.Float(
        string='Side 3',
    )

    side4 = fields.Float(
        string='Side 4',
    )

    deviation_length = fields.Float(
        string='Deviation (Length) (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    deviation_width = fields.Float(
        string='Deviation (Width) (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    average = fields.Float(
        string='Average (%)',
        digits=(16, 2),
        compute='_compute_deviation',
        store=True,
    )

    @api.depends(
        'side1',
        'side2',
        'side3',
        'side4',
        'parent_id.work_length',
        'parent_id.work_width',
    )
    def _compute_deviation(self):
        for line in self:

            length = line.parent_id.work_length
            width = line.parent_id.work_width

            if length:
                line.deviation_length = (
                    ((line.side1 - line.side3) / length) * 100
                )
            else:
                line.deviation_length = 0.0

            if width:
                line.deviation_width = (
                    ((line.side2 - line.side4) / width) * 100
                )
            else:
                line.deviation_width = 0.0

            line.average = (
                line.deviation_length + line.deviation_width
            ) / 2


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileLengthWidthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class TileThicknessLine(models.Model):
    _name = 'tile.thickness.line'
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    t1 = fields.Float(string='T1 mm')
    t2 = fields.Float(string='T2 mm')
    t3 = fields.Float(string='T3 mm')
    t4 = fields.Float(string='T4 mm')

    average = fields.Float(
        string='Average of Each Tile mm',
        compute='_compute_average',
        store=True,
        digits=(16, 2)
    )

    deviation = fields.Float(
        string='% Deviation',
        compute='_compute_deviation',
        store=True,
        digits=(16, 2)
    )

    @api.depends('t1', 't2', 't3', 't4')
    def _compute_average(self):
        for line in self:
            values = [line.t1, line.t2, line.t3, line.t4]
            line.average = sum(values) / 4

    @api.depends('average', 'parent_id.nominal_thickness')
    def _compute_deviation(self):
        for line in self:
            nominal = line.parent_id.nominal_thickness

            if nominal:
                line.deviation = (
                    (line.average - nominal) / nominal
                ) * 100
            else:
                line.deviation = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileThicknessLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class TileCenterCurvatureLine(models.Model):
    _name = 'tile.center.curvature.line'
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    center1 = fields.Float(
        string='Center 1'
    )

    center2 = fields.Float(
        string='Center 2'
    )

    center3 = fields.Float(
        string='Center 3'
    )

    center4 = fields.Float(
        string='Center 4'
    )

    diagonal = fields.Float(
        string='Diagonal',
        compute='_compute_diagonal',
        store=True,
        digits=(16, 2)
    )

    deviation1 = fields.Float(
        string='% Deviation 1',
        compute='_compute_deviations',
        store=True,
        digits=(16, 2)
    )

    deviation2 = fields.Float(
        string='% Deviation 2',
        compute='_compute_deviations',
        store=True,
        digits=(16, 2)
    )

    average_percent = fields.Float(
        string='Average %',
        compute='_compute_deviations',
        store=True,
        digits=(16, 2)
    )

    @api.depends('parent_id.center_curvature_length', 'parent_id.center_curvature_width')
    def _compute_diagonal(self):
        for line in self:
            length = line.parent_id.center_curvature_length or 0.0
            width = line.parent_id.center_curvature_width or 0.0

            line.diagonal = math.sqrt(
                (length ** 2) + (width ** 2)
            )

    @api.depends(
        'center1',
        'center2',
        'center3',
        'center4','parent_id.center_curvature_length', 'parent_id.center_curvature_width'
    )
    def _compute_deviations(self):
        for line in self:
            length = line.parent_id.center_curvature_length or 0.0
            width = line.parent_id.center_curvature_width or 0.0

            line.diagonal = math.sqrt(
                (length ** 2) + (width ** 2)
            )

            # Center 1 vs Center 3
            if line.diagonal:
                line.deviation1 = (
                    (line.center1 - line.center3)
                    / line.diagonal
                ) * 100
            else:
                line.deviation1 = 0.0

            # Center 2 vs Center 4
            if line.diagonal:
                line.deviation2 = (
                    (line.center2 - line.center4)
                    / line.diagonal
                ) * 100
            else:
                line.deviation2 = 0.0

            # Average of both deviations
            line.average_percent = (
                line.deviation1 + line.deviation2
            ) / 2


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileCenterCurvatureLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class TileEdgeCurvatureLine(models.Model):
    _name = 'tile.edge.curvature.line'
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    edge1 = fields.Float(
        string='Edge 1'
    )

    edge2 = fields.Float(
        string='Edge 2'
    )

    edge3 = fields.Float(
        string='Edge 3'
    )

    edge4 = fields.Float(
        string='Edge 4'
    )

    deviation1 = fields.Float(
        string='% Deviation 1',
        compute='_compute_deviation',
        store=True,
        digits=(16, 2)
    )

    deviation2 = fields.Float(
        string='% Deviation 2',
        compute='_compute_deviation',
        store=True,
        digits=(16, 2)
    )

    average_percent = fields.Float(
        string='Average%',
        compute='_compute_deviation',
        store=True,
        digits=(16, 2)
    )

    @api.depends(
        'edge1',
        'edge2',
        'edge3',
        'edge4','parent_id.center_curvature_length', 'parent_id.center_curvature_width'
    )
    def _compute_deviation(self):
        for line in self:

            length = line.parent_id.center_curvature_length or 0.0
            width = line.parent_id.center_curvature_width or 0.0

            # Edge 2 and Edge 4 deviation
            if length:
                line.deviation1 = (
                    (line.edge2 - line.edge4)
                    / length
                ) * 100
            else:
                line.deviation1 = 0.0

            # Edge 1 and Edge 3 deviation
            if width:
                line.deviation2 = (
                    (line.edge1 - line.edge3)
                    / width
                ) * 100
            else:
                line.deviation2 = 0.0

            # Average of both deviations
            line.average_percent = (
                line.deviation1 + line.deviation2
            ) / 2




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileEdgeCurvatureLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class TileWarpageLine(models.Model):
    _name = 'tile.warpage.line'
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    corner1 = fields.Float(
        string='Corner 1'
    )

    corner2 = fields.Float(
        string='Corner 2'
    )

    corner3 = fields.Float(
        string='Corner 3'
    )

    corner4 = fields.Float(
        string='Corner 4'
    )

    diagonal = fields.Float(
        string='Diagonal',
        compute='_compute_diagonal',
        store=True,
        digits=(16, 2)
    )

    deviation1 = fields.Float(
        string='% Deviation 1',
        compute='_compute_deviation',
        store=True,
        digits=(16, 2)
    )

    deviation2 = fields.Float(
        string='% Deviation 2',
        compute='_compute_deviation',
        store=True,
        digits=(16, 2)
    )

    average_percent = fields.Float(
        string='Average%',
        compute='_compute_deviation',
        store=True,
        digits=(16, 2)
    )

    @api.depends(
        'parent_id.warpage_length',
        'parent_id.warpage_width'
    )
    def _compute_diagonal(self):
        for line in self:
            length = line.parent_id.warpage_length or 0.0
            width = line.parent_id.warpage_width or 0.0

            line.diagonal = math.sqrt(
                (length ** 2) + (width ** 2)
            )

    @api.depends(
        'corner1',
        'corner2',
        'corner3',
        'corner4','parent_id.warpage_length',
        'parent_id.warpage_width'
    )
    def _compute_deviation(self):
        for line in self:

            length = line.parent_id.warpage_length or 0.0
            width = line.parent_id.warpage_width or 0.0

            line.diagonal = math.sqrt(
                (length ** 2) + (width ** 2)
            )

            # Corner 1 vs Corner 3
            if line.diagonal:
                line.deviation1 = (
                    (line.corner1 - line.corner3)
                    / line.diagonal
                ) * 100
            else:
                line.deviation1 = 0.0

            # Corner 2 vs Corner 4
            if line.diagonal:
                line.deviation2 = (
                    (line.corner2 - line.corner4)
                    / line.diagonal
                ) * 100
            else:
                line.deviation2 = 0.0

            # Average of both deviations
            line.average_percent = (
                line.deviation1 + line.deviation2
            ) / 2


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileWarpageLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1









class TileMOHSHardnessLine(models.Model):
    _name = 'tile.mohs.hardness.line'
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    mohs_hardness = fields.Float(
        string='MOHS Hardness'
    )


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileMOHSHardnessLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1





class TileNotes(models.Model):
    _name = "mechanical.tile.notes"

    parent_id = fields.Many2one('mechanical.tile', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
