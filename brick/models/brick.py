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
    brick_temperature = fields.Char("Temperature",store=True)
    brick_humidity = fields.Char("Humidity",store="True")

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'bricks.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    

    notes_id = fields.One2many('mechanical.bricks.notes', 'parent_id',string="Notes",
    default=lambda self: self._default_notes_lines()
)
    
    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'This report is invalid without the official paper seal of Make Infracon.',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'The # points mentioned in the report which information is given by Client/Customer.',
            }),

            (0, 0, {
                'sr_no': 'v',
                'notes': 'Any disputes shall be subject to jurisdiction of Nashik courts only.',
            }),
        ]
    

    # Dimension

    length_in_mm = fields.Float(string="Length in mm")
    width_in_mm = fields.Float(string="Width in mm")
    height_in_mm = fields.Float(string="Height in mm")
    


    #  Water Absorption
    water_absorbtion_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    wt_absorption_name = fields.Char("Name",default="Water Absorption")

    water_absorbtion_line_ids = fields.One2many('brick.water.absorption.line', 'parent_id', string="Observations")

    @api.depends('water_absorbtion_line_ids.water_absorption')
    def _compute_avrg_water_absorption(self):
        for rec in self:
            values = rec.water_absorbtion_line_ids.mapped('water_absorption')
            rec.avrg_water_absorption = sum(values) / len(values) if values else 0.0

    avrg_water_absorption = fields.Float(string="Average Water Absorption, %", compute="_compute_avrg_water_absorption", digits=(16, 2))

    water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_water_absorption_confirmity")

    water_absorption_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_water_absorption_nabl",store=True)


    @api.depends('avrg_water_absorption','eln_ref')
    def _compute_water_absorption_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.water_absorption_confirmity = 'na'
                continue
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
            for material in materials:
                if material.grade.id == record.grade.id:
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

  



    #  Compressive Strength

    compressive_strength_visible = fields.Boolean("Compressive Strengt Visible",compute="_compute_visible")
    compressive_strength_name = fields.Char("Name",default="Compressive Strength")

    compressive_strength_line_ids = fields.One2many('brick.compressive.line', 'parent_id', string="Observations")

    @api.depends('compressive_strength_line_ids.compressive_strength')
    def _compute_avrg_compressive_strength(self):
        for rec in self:
            values = rec.compressive_strength_line_ids.mapped('compressive_strength')
            rec.avrg_compressive_strength = sum(values) / len(values) if values else 0.0

    
    avrg_compressive_strength = fields.Float(string="Average Compressive Strength",compute="_compute_avrg_compressive_strength", digits=(16, 2))

    comp_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_comp_strength_conformity")

    comp_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_comp_strength_nabl",store=True)

    @api.depends('avrg_compressive_strength','eln_ref')
    def _compute_comp_strength_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.comp_strength_confirmity = 'na'
                continue
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

    


        #-2----------Efflorescence Visual Observation 
    efflorescence_visible = fields.Boolean("Efflorescence Visible",compute="_compute_visible")
    visual_observation_name_efforescence = fields.Char("Name",default="Efflorescence")

    visual_observation_1 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')


         #-3----------  Dimension As per IS: IS : 1077 -1992 

    dimension_visible = fields.Boolean("Efflorescence Visible",compute="_compute_visible")
    dimension_name1 = fields.Char("Name",default="Dimension (mm)")
    avrg_length = fields.Float(string="Average length")
    avrg_width = fields.Float(string="Average Width")
    avrg_height = fields.Float(string="Average Height")

    

    
    

    confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail')


    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.compressive_strength_visible = False
            record.water_absorbtion_visible = False
            record.efflorescence_visible = False
            record.dimension_visible = False
            record.efflorescence_visible=False
            
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

                if sample.internal_id == "3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac":
                    record.efflorescence_visible = True 
                


     
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

            # Efflorescence
            if result.parameter.internal_id == '3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac':
                result.result_char = self.visual_observation_1
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
        record = self.env['mechanical.bricks'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()

        return super(MechanicalBricks, self).read(fields=fields, load=load)
    
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
    


class BrickWaterAbsorptionLine(models.Model):
    _name = "brick.water.absorption.line"
    _description = "Water Absorption Test"

    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    
    identifi_no = fields.Char("Bricks Identification No.")
    w1 = fields.Float("Weight of Oven Dried Sample (W1)")
    w2 = fields.Float("Weight of Sample After Water Absorption (W2)")

    water_absorption = fields.Float("% Water Aborption (W2-W1/W1)*100", compute="_compute_values", store=True)

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            if rec.w1:
                rec.water_absorption = ((rec.w2 - rec.w1) / rec.w1) * 100
            else:
                rec.water_absorption = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BrickWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

class BrickCompressiveLine(models.Model):
    _name = "brick.compressive.line"
    _description = "Brick Compressive Test"

    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    length = fields.Float("Length in mm")
    width = fields.Float("Width in  mm")
    area = fields.Float("Area in mm2", compute="_compute_area", store=True)
    load_kn = fields.Float("Load in KN")
    compressive_strength = fields.Float("Compressive Strength (N/mm2)", compute="_compute_area", store=True)

    @api.depends('length', 'width','load_kn')
    def _compute_area(self):
        for record in self:
                record.area = record.length * record.width
                if record.area != 0:
                  record.compressive_strength = record.load_kn / record.area * 1000
                else:
                  record.compressive_strength = 0.0

            


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BrickCompressiveLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

class MechanicalBricksNotes(models.Model):
    _name = "mechanical.bricks.notes"

    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")