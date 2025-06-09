from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class ChequeredCementTile(models.Model):
    _name = "mechanical.cement.chequered.tile1"
    _inherit = "lerm.eln"
    _description = 'mechanical.cement.chequered.tile1'
    _rec_name = "name"

    name = fields.Char("Name",default="Cement Concrete flooring Tiles")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


     # Dimension

    chequered_tiles_cement_cement_name1 = fields.Char("Name",default=" Chequered Tiles")
    chequered_tiles_cement_visible = fields.Boolean("Chequered Visible",compute="_compute_visible")   

    cement_sample_size = fields.Float(string="Sample Size MM",digits=(16,2))

    # name = fields.Char("Name",default="DIMENSION")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    chequered_tiles_cement_lines = fields.One2many('mechanical.cement.chequered.tile1.line','parent_id',string="Parameter")
    average_cememt_flatness = fields.Float(string="Average Flatness (mm)", compute="_compute_average_cememt_flatness",digits=(16,2))

    

    average_cememt_flatness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Flatness Conformity", compute="_compute_average_cememt_flatness_conformity", store=True)



    @api.depends('average_cememt_flatness','eln_ref','grade')
    def _compute_average_cememt_flatness_conformity(self):
        
        for record in self:
            record.average_cememt_flatness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2568fgt4-9cbe-4f6b-a53f-7aa6de46c884')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2568fgt4-9cbe-4f6b-a53f-7aa6de46c884')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_cememt_flatness - record.average_cememt_flatness*mu_value
                    upper = record.average_cememt_flatness + record.average_cememt_flatness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_cememt_flatness_conformity = 'pass'
                        break
                    else:
                        record.average_cememt_flatness_conformity = 'fail'

    average_cememt_flatness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Flatness NABL", compute="_compute_average_cememt_flatness_nabl", store=True)

    @api.depends('average_cememt_flatness','eln_ref','grade')
    def _compute_average_cememt_flatness_nabl(self):
        
        for record in self:
            record.average_cememt_flatness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2568fgt4-9cbe-4f6b-a53f-7aa6de46c884')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2568fgt4-9cbe-4f6b-a53f-7aa6de46c884')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_cememt_flatness - record.average_cememt_flatness*mu_value
                    upper = record.average_cememt_flatness + record.average_cememt_flatness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_cememt_flatness_nabl = 'pass'
                        break
                    else:
                        record.average_cememt_flatness_nabl = 'fail'


    average_cement_perpendicularity = fields.Float(string="Average Perpendicularity (%)", compute="_compute_average_cement_perpendicularity",digits=(16,2))

    average_cement_perpendicularity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Perpendicularity Conformity", compute="_compute_average_cement_perpendicularity_conformity", store=True)



    @api.depends('average_cement_perpendicularity','eln_ref','grade')
    def _compute_average_cement_perpendicularity_conformity(self):
        
        for record in self:
            record.average_cement_perpendicularity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','256opy-7664-4997-b116-6bb1ad2d43d0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','256opy-7664-4997-b116-6bb1ad2d43d0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_cement_perpendicularity - record.average_cement_perpendicularity*mu_value
                    upper = record.average_cement_perpendicularity + record.average_cement_perpendicularity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_cement_perpendicularity_conformity = 'pass'
                        break
                    else:
                        record.average_cement_perpendicularity_conformity = 'fail'

    average_cement_perpendicularity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Perpendicularity NABL", compute="_compute_average_cement_perpendicularity_nabl", store=True)

    @api.depends('average_cement_perpendicularity','eln_ref','grade')
    def _compute_average_cement_perpendicularity_nabl(self):
        
        for record in self:
            record.average_cement_perpendicularity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','256opy-7664-4997-b116-6bb1ad2d43d0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','256opy-7664-4997-b116-6bb1ad2d43d0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_cement_perpendicularity - record.average_cement_perpendicularity*mu_value
                    upper = record.average_cement_perpendicularity + record.average_cement_perpendicularity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_cement_perpendicularity_nabl = 'pass'
                        break
                    else:
                        record.average_cement_perpendicularity_nabl = 'fail'


    average_cement_straightness = fields.Float(string="Average Straightness (%)", compute="_compute_average_cement_straightness",digits=(16,2))


    average_cement_straightness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Straightness Conformity", compute="_compute_average_cement_straightness_conformity", store=True)



    @api.depends('average_cement_straightness','eln_ref','grade')
    def _compute_average_cement_straightness_conformity(self):
        
        for record in self:
            record.average_cement_straightness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254opyt1-0a6a-4a00-ab70-04908d78524c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254opyt1-0a6a-4a00-ab70-04908d78524c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_cement_straightness - record.average_cement_straightness*mu_value
                    upper = record.average_cement_straightness + record.average_cement_straightness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_cement_straightness_conformity = 'pass'
                        break
                    else:
                        record.average_cement_straightness_conformity = 'fail'

    average_cement_straightness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Straightness NABL", compute="_compute_average_cement_straightness_nabl", store=True)

    @api.depends('average_cement_straightness','eln_ref','grade')
    def _compute_average_cement_straightness_nabl(self):
        
        for record in self:
            record.average_cement_straightness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254opyt1-0a6a-4a00-ab70-04908d78524c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254opyt1-0a6a-4a00-ab70-04908d78524c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_cement_straightness - record.average_cement_straightness*mu_value
                    upper = record.average_cement_straightness + record.average_cement_straightness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_cement_straightness_nabl = 'pass'
                        break
                    else:
                        record.average_cement_straightness_nabl = 'fail'


    deviation_cement_flatness = fields.Float(string="Flatness,mm",digits=(16,2))
    deviation_cement_perpendicularity = fields.Float(string="Perpendicularity,%",digits=(16,2))
    deviation_cement_straightness = fields.Float(string="Straightness,%",digits=(16,2))


    @api.depends('chequered_tiles_cement_lines.flatness1', 'chequered_tiles_cement_lines.flatness2', 'chequered_tiles_cement_lines.flatness3', 'chequered_tiles_cement_lines.flatness4')
    def _compute_average_cememt_flatness(self):
        for record in self:
            if record.chequered_tiles_cement_lines:
                # Calculate the average length per child line
                total = sum((line.flatness1 + line.flatness2 + line.flatness3 + line.flatness4) / 4 for line in record.chequered_tiles_cement_lines)
                record.average_cememt_flatness = total / len(record.chequered_tiles_cement_lines)  # Average across all child lines
            else:
                record.average_cememt_flatness = 0.0

    @api.depends('chequered_tiles_cement_lines.perpendicularity1', 'chequered_tiles_cement_lines.perpendicularity2', 'chequered_tiles_cement_lines.perpendicularity3', 'chequered_tiles_cement_lines.perpendicularity4')
    def _compute_average_cement_perpendicularity(self):
        for record in self:
            if record.chequered_tiles_cement_lines:
                # Calculate the average length per child line
                total = sum((line.perpendicularity1 + line.perpendicularity2 + line.perpendicularity3 + line.perpendicularity4) / 4 for line in record.chequered_tiles_cement_lines)
                record.average_cement_perpendicularity = total / len(record.chequered_tiles_cement_lines)  # Average across all child lines
            else:
                record.average_cement_perpendicularity = 0.0

    @api.depends('chequered_tiles_cement_lines.straightness1', 'chequered_tiles_cement_lines.straightness2', 'chequered_tiles_cement_lines.straightness3', 'chequered_tiles_cement_lines.straightness4')
    def _compute_average_cement_straightness(self):
        for record in self:
            if record.chequered_tiles_cement_lines:
                # Calculate the average length per child line
                total = sum((line.straightness1 + line.straightness2 + line.straightness3 + line.straightness4) / 4 for line in record.chequered_tiles_cement_lines)
                record.average_cement_straightness = total / len(record.chequered_tiles_cement_lines)  # Average across all child lines
            else:
                record.average_cement_straightness = 0.0


       # Water Absorption

    chequered_cement_water_absorption_visible_name1 = fields.Char("Name",default="Water Absorption")
    chequered_cement_water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")   

    # name = fields.Char("Name",default="DIMENSION")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    chequered_cement_water_absorption_lines = fields.One2many('mechanical.cement.chequered.water.absorption.line1','parent_id',string="Parameter")
    average_water_cement_absorption = fields.Float(string="Average Water Absorption %",compute="_compute_average_water_cement_absorption",digits=(12,2))

    average_water_cement_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_water_cement_absorption_conformity", store=True)



    @api.depends('average_water_cement_absorption','eln_ref','grade')
    def _compute_average_water_cement_absorption_conformity(self):
        
        for record in self:
            record.average_water_cement_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','258opk1-5406-4010-a81f-88e591d4197e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','258opk1-5406-4010-a81f-88e591d4197e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_water_cement_absorption - record.average_water_cement_absorption*mu_value
                    upper = record.average_water_cement_absorption + record.average_water_cement_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_water_cement_absorption_conformity = 'pass'
                        break
                    else:
                        record.average_water_cement_absorption_conformity = 'fail'

    average_water_cement_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_water_cement_absorption_nabl", store=True)

    @api.depends('average_water_cement_absorption','eln_ref','grade')
    def _compute_average_water_cement_absorption_nabl(self):
        
        for record in self:
            record.average_water_cement_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','258opk1-5406-4010-a81f-88e591d4197e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','258opk1-5406-4010-a81f-88e591d4197e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_water_cement_absorption - record.average_water_cement_absorption*mu_value
                    upper = record.average_water_cement_absorption + record.average_water_cement_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_water_cement_absorption_nabl = 'pass'
                        break
                    else:
                        record.average_water_cement_absorption_nabl = 'fail'

  

    @api.depends('chequered_cement_water_absorption_lines.water_absorption')
    def _compute_average_water_cement_absorption(self):
        for record in self:
            lines = record.chequered_cement_water_absorption_lines
            if lines:
                record.average_water_cement_absorption = sum(lines.mapped('water_absorption')) / len(lines)
            else:
                record.average_water_cement_absorption = 0





      # WET TRANSVERSE STRENGTH TEST (IS 13801 ANNEX F)


    chequeredwet_cement_transver_name1 = fields.Char("Name",default="WET TRANSVERSE STRENGTH TEST")
    chequeredwet_cement_transver_visible = fields.Boolean("WET TRANSVERSE STRENGTH TEST  Visible",compute="_compute_visible")   

    # name = fields.Char("Name",default="DIMENSION")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    chequeredwet_cement_transver_lines = fields.One2many('mechanical.cement.chequered.wet.transverse.line1','parent_id',string="Parameter")
    average_cement_wet_transver = fields.Float(string="Average Wet Transveres %",compute="_compute_average_cement_wet_transver",digits=(12,2))

    average_cement_wet_transver_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_cement_wet_transver_conformity", store=True)



    @api.depends('average_cement_wet_transver','eln_ref','grade')
    def _compute_average_cement_wet_transver_conformity(self):
        
        for record in self:
            record.average_cement_wet_transver_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2658piy-34eb-4442-bccb-3b13f9d05ea2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2658piy-34eb-4442-bccb-3b13f9d05ea2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_cement_wet_transver - record.average_cement_wet_transver*mu_value
                    upper = record.average_cement_wet_transver + record.average_cement_wet_transver*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_cement_wet_transver_conformity = 'pass'
                        break
                    else:
                        record.average_cement_wet_transver_conformity = 'fail'

    average_cement_wet_transver_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_cement_wet_transver_nabl", store=True)

    @api.depends('average_cement_wet_transver','eln_ref','grade')
    def _compute_average_cement_wet_transver_nabl(self):
        
        for record in self:
            record.average_cement_wet_transver_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2658piy-34eb-4442-bccb-3b13f9d05ea2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2658piy-34eb-4442-bccb-3b13f9d05ea2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_cement_wet_transver - record.average_cement_wet_transver*mu_value
                    upper = record.average_cement_wet_transver + record.average_cement_wet_transver*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_cement_wet_transver_nabl = 'pass'
                        break
                    else:
                        record.average_cement_wet_transver_nabl = 'fail'

    @api.depends('chequeredwet_cement_transver_lines.wet_transver')
    def _compute_average_cement_wet_transver(self):
        for record in self:
            lines = record.chequeredwet_cement_transver_lines
            if lines:
                record.average_cement_wet_transver = sum(lines.mapped('wet_transver')) / len(lines)
            else:
                record.average_cement_wet_transver = 0




     
      ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.chequered_tiles_cement_visible = False
            record.chequered_cement_water_absorption_visible = False
            record.chequeredwet_cement_transver_visible = False
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "12578dfgr-a3df-4990-93d1-9904984644a3":
                    record.chequered_tiles_cement_visible = True

                if sample.internal_id == "258opk1-5406-4010-a81f-88e591d4197e":
                    record.chequered_cement_water_absorption_visible = True

                if sample.internal_id == "2658piy-34eb-4442-bccb-3b13f9d05ea2":
                    record.chequeredwet_cement_transver_visible = True

               





    def open_eln_page(self):
        # import wdb; wdb.set_trace()

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
        record = super(ChequeredCementTile, self).create(vals)
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
        record = self.env['mechanical.cement.chequered.tile1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class ChequeredCementTileLine(models.Model):
    _name = "mechanical.cement.chequered.tile1.line"
    parent_id = fields.Many2one('mechanical.cement.chequered.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    flatness1 = fields.Float(string="Flatness (mm) 1")
    flatness2 = fields.Float(string="Flatness (mm)2")
    flatness3 = fields.Float(string="Flatness (mm) 3")
    flatness4 = fields.Float(string="Flatness (mm) 4")

    perpendicularity1 = fields.Float(string="Perpendicularity (%) 1")
    perpendicularity2  = fields.Float(string="Perpendicularity (%) 2")
    perpendicularity3 = fields.Float(string="Perpendicularity (%) 3")
    perpendicularity4 = fields.Float(string="Perpendicularity (%) 4")

    straightness1 = fields.Float(string="Straightness (%) 1")
    straightness2 = fields.Float(string="Straightness (%) 2")
    straightness3 = fields.Float(string="Straightness (%) 3")
    straightness4 = fields.Float(string="Straightness (%) 4")
    
  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ChequeredCementTileLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in chequered_tiles_cement_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ChequeredCementWaterAbsorptionLine(models.Model):
    _name = "mechanical.cement.chequered.water.absorption.line1"
    parent_id = fields.Many2one('mechanical.cement.chequered.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    mass_of_saturated = fields.Float(string="Mass of saturated Specimen in gm-M1")
    mass_of_oven = fields.Float(string="Mass of oven dried Specimen in gm-M2")
    water_absorption = fields.Float(string="Water Absorption (%)=(M1-M2)/M2",compute="_compute_water_absorption",digits=(12,2))


    @api.depends('mass_of_saturated', 'mass_of_oven')
    def _compute_water_absorption(self):
        for record in self:
            if record.mass_of_oven:  # Avoid division by zero
                record.water_absorption = ((record.mass_of_saturated - record.mass_of_oven) / record.mass_of_oven) * 100
            else:
                record.water_absorption = 0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ChequeredCementWaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in chequered_tiles_cement_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class ChequeredCementWetTransverLine(models.Model):
    _name = "mechanical.cement.chequered.wet.transverse.line1"
    parent_id = fields.Many2one('mechanical.cement.chequered.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    width_b = fields.Float(string="Width -b in mm")
    span_between = fields.Float(string="Span Between support-l in mm")
    fracture_thicness = fields.Float(string="Fracture thickness -t  in mm")
    breaking_load = fields.Float(string="Breaking Load-P in (N)")
    wet_transver = fields.Float(string="WET TRANSVERSE STRENGTH",compute="_compute_wet_transver",digits=(12,2))


    @api.depends('breaking_load', 'span_between', 'width_b', 'fracture_thicness')
    def _compute_wet_transver(self):
        for record in self:
            if record.width_b and record.fracture_thicness:
                record.wet_transver = (3 * record.breaking_load * record.span_between) / (2 * record.width_b * record.fracture_thicness ** 2)
            else:
                record.wet_transver = 0  # Avoid division by zero

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ChequeredCementWetTransverLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in chequered_tiles_cement_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1