from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math

import logging
_logger = logging.getLogger(__name__)



class PaverBlock(models.Model):
    _name = "mechanical.paver.nbml.block"
    _inherit = "lerm.eln"
    _rec_name = "name_paver"



    name_paver = fields.Char("Name",default="Paver Block")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'mechanical.paver.nbml.block.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }


    

    block_type = fields.Selection(
    [
        ('plain', 'Plain Block'),
        ('arrised', 'Arrised/Chamfered Block'),
    ],
    string="Block Type",
    required=True
        )

    correction_factor = fields.Float(
        string="Correction Factor",
            )


    notes_id = fields.One2many('paverblock.nbml.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(PaverBlock, self).default_get(fields)

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



    commpressive_name = fields.Char("Name",default="Compressive Strength")
    commpressive_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    commpressive_child_lines = fields.One2many('paver.compressive.nbml.line','parent_id',string="Compressive Line")

    avg_commpressive = fields.Float(
        string="Average Corrected Compressive Strength  ",compute="_compute_avg_commpressive")

    @api.depends('commpressive_child_lines.compressive_strenght')
    def _compute_avg_commpressive(self):
        for rec in self:
            lines = rec.commpressive_child_lines
            if lines:
                total = sum(line.compressive_strenght for line in lines)
                rec.avg_commpressive = round(total / len(lines), 2)
            else:
                rec.avg_commpressive = 0.0

    avg_commpressive_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_commpressive_conformity")

    avg_commpressive_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_commpressive_nabl")


    @api.depends('avg_commpressive','eln_ref','grade')
    def _compute_avg_commpressive_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_commpressive_conformity = 'na'
                continue
            record.avg_commpressive_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1477800rtt-5dc9-4a2a-8bf0-1281d1112354')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1477800rtt-5dc9-4a2a-8bf0-1281d1112354')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_commpressive - record.avg_commpressive*mu_value
                    upper = record.avg_commpressive + record.avg_commpressive*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_commpressive_conformity = 'pass'
                        break
                    else:
                        record.avg_commpressive_conformity = 'fail'

    @api.depends('avg_commpressive','eln_ref','grade')
    def _compute_avg_commpressive_nabl(self):
        
        for record in self:
            
            record.avg_commpressive_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1477800rtt-5dc9-4a2a-8bf0-1281d1112354')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1477800rtt-5dc9-4a2a-8bf0-1281d1112354')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_commpressive - record.avg_commpressive*mu_value
            upper = record.avg_commpressive + record.avg_commpressive*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_commpressive_nabl = 'pass'
                break
            else:
                record.avg_commpressive_nabl = 'fail'

    abrasion_name = fields.Char("Name",default="Abrasion Test")
    abrasion_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    abrasion_child_lines = fields.One2many('abrasion.test.line','parent_id',string="Compressive Line")

    avg_abrasion = fields.Float(
        string="Average Abrasion mm³  ",compute="_compute_avg_abrasion")

    @api.depends('abrasion_child_lines.abrasion')
    def _compute_avg_abrasion(self):
        for rec in self:
            lines = rec.abrasion_child_lines
            if lines:
                total = sum(line.abrasion for line in lines)
                rec.avg_abrasion = round(total / len(lines), 2)
            else:
                rec.avg_abrasion = 0.0

    avg_abrasion_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_abrasion_conformity")

    avg_abrasion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_abrasion_nabl")


    @api.depends('avg_abrasion','eln_ref','grade')
    def _compute_avg_abrasion_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_abrasion_conformity = 'na'
                continue
            record.avg_abrasion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214500rtt-5dc9-4a2a-8bf0-1283214567810')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214500rtt-5dc9-4a2a-8bf0-1283214567810')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_abrasion - record.avg_abrasion*mu_value
                    upper = record.avg_abrasion + record.avg_abrasion*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_abrasion_conformity = 'pass'
                        break
                    else:
                        record.avg_abrasion_conformity = 'fail'

    @api.depends('avg_abrasion','eln_ref','grade')
    def _compute_avg_abrasion_nabl(self):
        
        for record in self:
            
            record.avg_abrasion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214500rtt-5dc9-4a2a-8bf0-1283214567810')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214500rtt-5dc9-4a2a-8bf0-1283214567810')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_abrasion - record.avg_abrasion*mu_value
            upper = record.avg_abrasion + record.avg_abrasion*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_abrasion_nabl = 'pass'
                break
            else:
                record.avg_abrasion_nabl = 'fail'


    flexural_name = fields.Char("Name",default="Flexural Strength")
    flexural_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    correction_factor_flexural = fields.Float(
        string="Correction Factor",
            )

    flexural_child_lines = fields.One2many('flexural.strenght.line','parent_id',string="Compressive Line")

    avg_flexural = fields.Float(
        string="Average Flexural Strength N/mm2  ",compute="_compute_avg_flexural")

    @api.depends('flexural_child_lines.corrected_strength')
    def _compute_avg_flexural(self):
        for rec in self:
            lines = rec.flexural_child_lines
            if lines:
                total = sum(line.corrected_strength for line in lines)
                rec.avg_flexural = round(total / len(lines), 2)
            else:
                rec.avg_flexural = 0.0


    avg_flexural_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_flexural_conformity")

    avg_flexural_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_flexural_nabl")


    @api.depends('avg_flexural','eln_ref','grade')
    def _compute_avg_flexural_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_flexural_conformity = 'na'
                continue
            record.avg_flexural_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32104500rtt-5dc9-4a2a-8bf0-1283012457895')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32104500rtt-5dc9-4a2a-8bf0-1283012457895')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_flexural - record.avg_flexural*mu_value
                    upper = record.avg_flexural + record.avg_flexural*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_flexural_conformity = 'pass'
                        break
                    else:
                        record.avg_flexural_conformity = 'fail'

    @api.depends('avg_flexural','eln_ref','grade')
    def _compute_avg_flexural_nabl(self):
        
        for record in self:
            
            record.avg_flexural_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32104500rtt-5dc9-4a2a-8bf0-1283012457895')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32104500rtt-5dc9-4a2a-8bf0-1283012457895')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_flexural - record.avg_flexural*mu_value
            upper = record.avg_flexural + record.avg_flexural*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_flexural_nabl = 'pass'
                break
            else:
                record.avg_flexural_nabl = 'fail'


 




 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.commpressive_visible = False
            record.abrasion_visible = False
            record.flexural_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == '1477800rtt-5dc9-4a2a-8bf0-1281d1112354':
                    record.commpressive_visible = True

                if sample.internal_id == '3214500rtt-5dc9-4a2a-8bf0-1283214567810':
                    record.abrasion_visible = True

                if sample.internal_id == '32104500rtt-5dc9-4a2a-8bf0-1283012457895':
                    record.flexural_visible = True



                

              
              
               



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
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            
            

            if result.parameter.internal_id == '1477800rtt-5dc9-4a2a-8bf0-1281d1112354':
                    result.result_char = round(self.avg_commpressive,2)
                    result.calculated = True
                    if self.avg_commpressive_nabl == 'pass':
                        result.nabl_status = 'nabl'
                    else:
                        result.nabl_status = 'non-nabl'
                    continue

            if result.parameter.internal_id == '3214500rtt-5dc9-4a2a-8bf0-1283214567810':
                    result.result_char = round(self.avg_abrasion,2)
                    result.calculated = True
                    if self.avg_abrasion_nabl == 'pass':
                        result.nabl_status = 'nabl'
                    else:
                        result.nabl_status = 'non-nabl'
                    continue

            if result.parameter.internal_id == '32104500rtt-5dc9-4a2a-8bf0-1283012457895':
                    result.result_char = round(self.avg_flexural,2)
                    result.calculated = True
                    if self.avg_flexural_nabl == 'pass':
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










class CompressiveLine(models.Model):
    _name = "paver.compressive.nbml.line"
    parent_id = fields.Many2one('mechanical.paver.nbml.block',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    lenght = fields.Float(string="Length (mm)")
    width = fields.Float(string="Width (mm)")
    thickness = fields.Float(string="Thickness (mm)")
    area = fields.Float(string="Area (mm2)",compute="_compute_area")
    
    load = fields.Float(string=" Load (kN)")

    apparent_com = fields.Float(string=" Apparent Compressive Strength (N/mm2)",compute="_compute_apparent")

    correction_factor = fields.Float(string="Correction Factor",compute="_compute_correction_factor",store=True)
    compressive_strenght = fields.Float(string=" Corrected Compressive Strength (N/mm2)",compute="_compute_final_strength")

      # =========================
    # COMPUTE METHODS
    # =========================

    @api.depends('lenght', 'width')
    def _compute_area(self):
        for rec in self:
            rec.area = rec.lenght * rec.width if rec.lenght and rec.width else 0.0

    @api.depends('load', 'area')
    def _compute_apparent(self):
        for rec in self:
            if rec.area > 0:
                rec.apparent_com = (rec.load * 1000) / rec.area
            else:
                rec.apparent_com = 0.0

    @api.depends('parent_id', 'parent_id.correction_factor')
    def _compute_correction_factor(self):
        for rec in self:
            rec.correction_factor = rec.parent_id.correction_factor if rec.parent_id else 0.0

    @api.depends('apparent_com', 'correction_factor')
    def _compute_final_strength(self):
        for rec in self:
            rec.compressive_strenght = rec.apparent_com * rec.correction_factor

    

    

   
    

   
   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class AbrasionTestLine(models.Model):
    _name = "abrasion.test.line"

    parent_id = fields.Many2one('mechanical.paver.nbml.block',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_id = fields.Char(string="Sample Identification")

    # -------------------------
    # INPUT FIELDS
    # -------------------------
    initial_wt = fields.Float(string="Initial Wt. (gm)")
    wt_in_water = fields.Float(string="Weight in Water (gm)")
    volume = fields.Float(string="Volume (mm³)",compute="_compute_volume")


    final_wt = fields.Float(string="Final Wt. 16 cycles of testing  (gm)")

    # -------------------------
    # COMPUTED FIELDS
    # -------------------------


    @api.depends('initial_wt', 'wt_in_water')
    def _compute_volume(self):
        for rec in self:
            rec.volume = (rec.initial_wt - rec.wt_in_water) / 0.001 if rec.initial_wt and rec.wt_in_water else 0.0

    # Density = Initial Weight / Volume
    density = fields.Float(
        string="Density (gm/mm³)",
        compute="_compute_density",
        store=True,digits=(12,8)
    )

    # Loss in Mass = Initial - Final
    loss_mass = fields.Float(
        string="Loss in Mass (gm)",
        
    )

    # Loss in Volume = Loss Mass / Density
    loss_volume = fields.Float(
        string="Loss in Volume after 16 cycles (mm³)",
        compute="_compute_loss_volume",
        store=True
    )

    # Abrasion Resistance
    abrasion = fields.Float(
        string="Abrasion Resistance (mm³ per 5000 mm²)",
        compute="_compute_abrasion",
        store=True
    )

    # =========================
    # COMPUTE METHODS
    # =========================


    @api.depends('loss_volume')
    def _compute_abrasion(self):
        for rec in self:
            if rec.loss_volume > 0:
                rec.abrasion = (rec.loss_volume / (71 * 71)) * 5000
            else:
                rec.abrasion = 0.0

    @api.depends('initial_wt', 'volume')
    def _compute_density(self):
        for rec in self:
            if rec.volume > 0:
                rec.density = rec.initial_wt / rec.volume
            else:
                rec.density = 0.0

   

    @api.depends('loss_mass', 'density')
    def _compute_loss_volume(self):
        for rec in self:
            if rec.density > 0:
                rec.loss_volume = rec.loss_mass / rec.density
            else:
                rec.loss_volume = 0.0

    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(AbrasionTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class FlexuralTestLine(models.Model):
    _name = "flexural.strenght.line"

    parent_id = fields.Many2one('mechanical.paver.nbml.block',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

    # -------------------------
    # INPUTS
    # -------------------------
    distance = fields.Float(string="Distance between central lines of supporting rollers, l (mm)")   # L
    width = fields.Float(string="Average width of block, measured from both faces of the specimen, b (mm)")
    area = fields.Float(
        string="Area",
       
    )
    
    load = fields.Float(string="Maximum Load P (N)")

    flexural_strength = fields.Float(
        string="Flexural Strength, Fb (N/mm2)",compute="_compute_flexural"
      
    )

    correction_factor = fields.Float(string="Correction Factor",compute="_compute_correction_factor_flexural")

 

    # Corrected Flexural Strength
    corrected_strength = fields.Float(
        string="Corrected Flexural Strength (N/mm²)",compute="_compute_corrected"
       
    )

    @api.depends('parent_id', 'parent_id.correction_factor_flexural')
    def _compute_correction_factor_flexural(self):
        for rec in self:
            rec.correction_factor = rec.parent_id.correction_factor_flexural if rec.parent_id else 0.0

     # Flexural = load*1000 / area
    @api.depends('load', 'area')
    def _compute_flexural(self):
        for rec in self:
            if rec.area > 0:
                rec.flexural_strength = (rec.load * 1000) / rec.area
            else:
                rec.flexural_strength = 0.0

    @api.depends('flexural_strength', 'correction_factor')
    def _compute_corrected(self):
        for rec in self:
            rec.corrected_strength = rec.flexural_strength * rec.correction_factor

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FlexuralTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1







    
class paverblockNotes(models.Model):
    _name = "paverblock.nbml.notes"

    parent_id = fields.Many2one('mechanical.paver.nbml.block',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


