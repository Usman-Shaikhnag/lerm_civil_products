from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class GypsumPlaster(models.Model):
    _name = "mechanical.gypsum.plaster1"
    _inherit = "lerm.eln"
    _description = 'mechanical.gypsum.plaster1'
    _rec_name = "name"

    name = fields.Char("Name",default="GYPSUM PLASTER BOARD")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



    #  density

    density_name = fields.Char("Name",default="Density")
    density_visible = fields.Boolean("Density Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_density = fields.One2many('mechanical.gypsum.density.line1','parent_id',string="Parameter")

    average_density = fields.Float(string="Density, g/cm3 ",compute="_compute_average_gypsum_density",digits=(12,3),store=True)
    requirement_density = fields.Char(string="Requirement, Density")

    @api.depends('child_lines_density.density')
    def _compute_average_gypsum_density(self):
        for record in self:
            densities = record.child_lines_density.mapped('density')
            if densities:
                record.average_density = sum(densities) / len(densities)
            else:
                record.average_density = 0.0

   
   
    


    average_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_density_conformity", store=True)



    @api.depends('average_density','eln_ref','grade')
    def _compute_average_density_conformity(self):
        
        for record in self:
            record.average_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3587lpiy-7a9c-4616-bad5-88eb1b260747')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3587lpiy-7a9c-4616-bad5-88eb1b260747')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_density_conformity = 'pass'
                        break
                    else:
                        record.average_density_conformity = 'fail'

    average_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_density_nabl", store=True)

    @api.depends('average_density','eln_ref','grade')
    def _compute_average_density_nabl(self):
        
        for record in self:
            record.average_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3587lpiy-7a9c-4616-bad5-88eb1b260747')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3587lpiy-7a9c-4616-bad5-88eb1b260747')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_density_nabl = 'pass'
                        break
                    else:
                        record.average_density_nabl = 'fail'




     #  Water Absorption

    water_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_water_absorption = fields.One2many('mechanical.gypsum.water.absorption.line1','parent_id',string="Parameter")

    average_water_absorption = fields.Float(string="Water Absorption, %",compute="_compute_average_gypsum_water_absorption",digits=(12,1),store=True)
    requirement_water_absorption = fields.Char(string="Requirement, Water Absorption")

    @api.depends('child_lines_water_absorption.water_absorption')
    def _compute_average_gypsum_water_absorption(self):
        for record in self:
            absorption = record.child_lines_water_absorption.mapped('water_absorption')
            if absorption:
                record.average_water_absorption = sum(absorption) / len(absorption)
            else:
                record.average_water_absorption = 0.0

   
   
    


    average_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_water_absorption_conformity", store=True)



    @api.depends('average_water_absorption','eln_ref','grade')
    def _compute_average_water_absorption_conformity(self):
        
        for record in self:
            record.average_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','34597lpuy-f555-4f7c-beae-9547435d852a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','34597lpuy-f555-4f7c-beae-9547435d852a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption - record.average_water_absorption*mu_value
                    upper = record.average_water_absorption + record.average_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.average_water_absorption_conformity = 'fail'

    average_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_water_absorption_nabl", store=True)

    @api.depends('average_water_absorption','eln_ref','grade')
    def _compute_average_water_absorption_nabl(self):
        
        for record in self:
            record.average_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','34597lpuy-f555-4f7c-beae-9547435d852a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','34597lpuy-f555-4f7c-beae-9547435d852a')]).parameter_table
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



     # Flexural Breaking Load in Tranverse Direction

    flexural_tranverse_name = fields.Char("Name",default="Flexural Breaking Load in Tranverse Direction")
    flexural_tranverse_visible = fields.Boolean("Flexural Breaking Load in Tranverse Direction Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_flexural_tranverse = fields.One2many('mechanical.gypsum.flexural.tranverse.line1','parent_id',string="Parameter")

    average_flexural_tranverse = fields.Float(string="Flexural Breaking Load in Tranverse Direction, N",compute="_compute_average_gypsum_flexural_tranverse",digits=(12,1),store=True)
    requirement_flexural_tranverse = fields.Char(string="Requirement ,Flexural Breaking Load in Tranverse Direction")

    @api.depends('child_lines_flexural_tranverse.flexural_tranverse')
    def _compute_average_gypsum_flexural_tranverse(self):
        for record in self:
            absorption = record.child_lines_flexural_tranverse.mapped('flexural_tranverse')
            if absorption:
                record.average_flexural_tranverse = sum(absorption) / len(absorption)
            else:
                record.average_flexural_tranverse = 0.0

   
   
    


    average_flexural_tranverse_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_flexural_tranverse_conformity", store=True)



    @api.depends('average_flexural_tranverse','eln_ref','grade')
    def _compute_average_flexural_tranverse_conformity(self):
        
        for record in self:
            record.average_flexural_tranverse_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6587plyr2-b6bb-4100-bf91-24e750389f25')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6587plyr2-b6bb-4100-bf91-24e750389f25')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_flexural_tranverse - record.average_flexural_tranverse*mu_value
                    upper = record.average_flexural_tranverse + record.average_flexural_tranverse*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_flexural_tranverse_conformity = 'pass'
                        break
                    else:
                        record.average_flexural_tranverse_conformity = 'fail'

    average_flexural_tranverse_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_flexural_tranverse_nabl", store=True)

    @api.depends('average_flexural_tranverse','eln_ref','grade')
    def _compute_average_flexural_tranverse_nabl(self):
        
        for record in self:
            record.average_flexural_tranverse_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6587plyr2-b6bb-4100-bf91-24e750389f25')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6587plyr2-b6bb-4100-bf91-24e750389f25')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_flexural_tranverse - record.average_flexural_tranverse*mu_value
                    upper = record.average_flexural_tranverse + record.average_flexural_tranverse*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_flexural_tranverse_nabl = 'pass'
                        break
                    else:
                        record.average_flexural_tranverse_nabl = 'fail'



     # Flexural Breaking Load in Longitudinal Direction

    flexural_longitudinal_name = fields.Char("Name",default="Flexural Breaking Load in Longitudinal Direction")
    flexural_longitudinal_visible = fields.Boolean("Flexural Breaking Load in Longitudinal Direction Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_flexural_longitudinal = fields.One2many('mechanical.gypsum.flexural.longitudinal.line1','parent_id',string="Parameter")

    average_flexural_longitudinal = fields.Float(string="Flexural Breaking Load in Longitudinal Direction, N",compute="_compute_average_gypsum_flexural_longitudinal",digits=(12,1),store=True)
    requirement_flexural_longitudinal = fields.Char(string="Requirement ,Flexural Breaking Load in Longitudinal Direction")

    @api.depends('child_lines_flexural_longitudinal.flexural_longitudinal')
    def _compute_average_gypsum_flexural_longitudinal(self):
        for record in self:
            absorption = record.child_lines_flexural_longitudinal.mapped('flexural_longitudinal')
            if absorption:
                record.average_flexural_longitudinal = sum(absorption) / len(absorption)
            else:
                record.average_flexural_longitudinal = 0.0

   
   
    


    average_flexural_longitudinal_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_flexural_longitudinal_conformity", store=True)



    @api.depends('average_flexural_longitudinal','eln_ref','grade')
    def _compute_average_flexural_longitudinal_conformity(self):
        
        for record in self:
            record.average_flexural_longitudinal_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','g1578pu2-cd1c-4fe1-804a-541a8e9ff19d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','g1578pu2-cd1c-4fe1-804a-541a8e9ff19d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_flexural_longitudinal - record.average_flexural_longitudinal*mu_value
                    upper = record.average_flexural_longitudinal + record.average_flexural_longitudinal*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_flexural_longitudinal_conformity = 'pass'
                        break
                    else:
                        record.average_flexural_longitudinal_conformity = 'fail'

    average_flexural_longitudinal_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_flexural_longitudinal_nabl", store=True)

    @api.depends('average_flexural_longitudinal','eln_ref','grade')
    def _compute_average_flexural_longitudinal_nabl(self):
        
        for record in self:
            record.average_flexural_longitudinal_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','g1578pu2-cd1c-4fe1-804a-541a8e9ff19d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','g1578pu2-cd1c-4fe1-804a-541a8e9ff19d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_flexural_longitudinal - record.average_flexural_longitudinal*mu_value
                    upper = record.average_flexural_longitudinal + record.average_flexural_longitudinal*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_flexural_longitudinal_nabl = 'pass'
                        break
                    else:
                        record.average_flexural_longitudinal_nabl = 'fail'












       ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.density_visible = False
            record.water_absorption_visible = False
            record.flexural_tranverse_visible = False
            record.flexural_longitudinal_visible = False
           
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "3587lpiy-7a9c-4616-bad5-88eb1b260747":
                    record.density_visible = True

                if sample.internal_id == "34597lpuy-f555-4f7c-beae-9547435d852a":
                    record.water_absorption_visible = True

                if sample.internal_id == "6587plyr2-b6bb-4100-bf91-24e750389f25":
                    record.flexural_tranverse_visible = True

                if sample.internal_id == "g1578pu2-cd1c-4fe1-804a-541a8e9ff19d":
                    record.flexural_longitudinal_visible = True

               



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
        record = super(GypsumPlaster, self).create(vals)
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
        record = self.env['mechanical.gypsum.plaster1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class DensityLine(models.Model):
    _name = "mechanical.gypsum.density.line1"
    parent_id = fields.Many2one('mechanical.gypsum.plaster1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    lenght = fields.Float(string="Length",digits=(12,2))
    width = fields.Float(string="Width",digits=(12,2))
    thickness = fields.Float(string="Thickness",digits=(12,2))
    initial_weight = fields.Float(string="Initial Weight",digits=(12,3))
    oven_dry_weight = fields.Float(string="Oven Dry Weight",digits=(12,3))
    density = fields.Float(string="Density",compute="_compute_gypsum_density",digits=(12,3))


    @api.depends('oven_dry_weight', 'lenght', 'width', 'thickness')
    def _compute_gypsum_density(self):
        for record in self:
            if record.lenght > 0 and record.width > 0 and record.thickness > 0:
                volume = record.lenght * record.width * record.thickness
                record.density = record.oven_dry_weight / volume * 1000
            else:
                record.density = 0.0
    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class WaterAbsorptionLine(models.Model):
    _name = "mechanical.gypsum.water.absorption.line1"
    parent_id = fields.Many2one('mechanical.gypsum.plaster1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
    initial_weight = fields.Float(string="Initial Weight",digits=(12,3))
    oven_dry_weight = fields.Float(string="Oven Dry Weight",digits=(12,3))
    water_absorption = fields.Float(string="Density",compute="_compute_gypsum_water_absorption",digits=(12,3))

    @api.depends('initial_weight', 'oven_dry_weight')
    def _compute_gypsum_water_absorption(self):
        for record in self:
            if record.oven_dry_weight > 0:  # Avoid division by zero
                record.water_absorption = (
                    (record.initial_weight - record.oven_dry_weight) / record.oven_dry_weight
                ) * 100
            else:
                record.water_absorption = 0.0


    
    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(WaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class FlexuralTranverseLine(models.Model):
    _name = "mechanical.gypsum.flexural.tranverse.line1"
    parent_id = fields.Many2one('mechanical.gypsum.plaster1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
    lenght = fields.Float(string="Length",digits=(12,2))
    width = fields.Float(string="Width",digits=(12,2))
    thickness = fields.Float(string="Thickness",digits=(12,2))
    flexural_tranverse = fields.Float(string="Flexural Breaking Load (N)",digits=(12,1))

   

    
    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(FlexuralTranverseLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class FlexuralLongitudinalLine(models.Model):
    _name = "mechanical.gypsum.flexural.longitudinal.line1"
    parent_id = fields.Many2one('mechanical.gypsum.plaster1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
    lenght = fields.Float(string="Length",digits=(12,2))
    width = fields.Float(string="Width",digits=(12,2))
    thickness = fields.Float(string="Thickness",digits=(12,2))
    flexural_longitudinal = fields.Float(string="Flexural Breaking Load (N)",digits=(12,1))

   

    
    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(FlexuralLongitudinalLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree

class GypsumPlasterDatasheet1(models.AbstractModel):
        _name = 'report.gypsum_plaster_board.gypsum_plaster_board_datasheet1'
        _description = 'Gypsum Plaster Board DataSheet 1'
    
        @api.model
        def _get_report_values(self, docids, data):
            if data['fromsample'] == True:
                 if 'active_id' in data['context']:
                     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
                 else:
                     eln = self.env['lerm.eln'].sudo().browse(docids) 
            else:
                if data['report_wizard'] == True:
                    eln = self.env['lerm.eln'].sudo().search([('id','=',data['eln'])])
                else:
                    eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
            model_id = eln.model_id
            # differnt location for product based
            # model_name = eln.material.product_based_calculation[0].ir_model.name 
            model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
            if model_name:
                general_data = self.env[model_name].sudo().browse(model_id)
            else:
                general_data = self.env['lerm.eln'].sudo().browse(docids)
            return {
                'eln': eln,
                'data' : general_data
            }


class GypsumPlastereport(models.AbstractModel):
    _name = 'report.gypsum_plaster_board.gypsum_plaster_report1'
    _description = 'Gypsum Plaster Board Report 1'
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        if 'active_id' in data['context']:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids) 
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(eln.kes_no)
        qr.make(fit=True)
        qr_image = qr.make_image()

        # Convert the QR code image to base64 string
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Assign the base64 string to a field in the 'srf' object
        qr_code = qr_image_base64
        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'stamp' : inreport_value,
            'nabl' : nabl
        }




