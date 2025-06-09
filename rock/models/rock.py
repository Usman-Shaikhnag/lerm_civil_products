from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalRock(models.Model):
    _name = "mechanical.rock1"
    _inherit = "lerm.eln"
    _description = 'mechanical.rock1'
    _rec_name = "name"

    name = fields.Char("Name",default="Specific Gravity, Water Absorption, Porosity & Dry Density")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")



    child_lines = fields.One2many('mechanical.rock1.line','parent_id',string="Parameter")
    
    avg_porosity = fields.Float("Average porosity",compute="_compute_avg_porosity")
    avg_water_absorption = fields.Float("Average Water Absorption",compute="_compute_water_absorption")
    avg_dry_density = fields.Float("Dry Density",compute="_compute_avg_dry_density")
    avg_saturated_spc_gravity = fields.Float("Saturated Specific Gravity",compute="_compute_saturated_spc_gravity")


    

    @api.depends('child_lines.porosity')
    def _compute_avg_porosity(self):
        for record in self:
            porosity_values = [line.porosity for line in record.child_lines]
            if porosity_values:
                record.avg_porosity = sum(porosity_values) / len(porosity_values)
            else:
                record.avg_porosity = 0.0


    @api.depends('child_lines.water_absorption')
    def _compute_water_absorption(self):
        for record in self:
            water_absorption_values = [line.water_absorption for line in record.child_lines]
            if water_absorption_values:
                record.avg_water_absorption = sum(water_absorption_values) / len(water_absorption_values)
            else:
                record.avg_water_absorption = 0.0


    @api.depends('child_lines.dry_density')
    def _compute_avg_dry_density(self):
        for record in self:
            dry_density_values = [line.dry_density for line in record.child_lines]
            if dry_density_values:
                record.avg_dry_density = sum(dry_density_values) / len(dry_density_values)
            else:
                record.avg_dry_density = 0.0

    @api.depends('child_lines.saturated_spc_gravity')
    def _compute_saturated_spc_gravity(self):
        for record in self:
            saturated_spc_gravity_values = [line.saturated_spc_gravity for line in record.child_lines]
            if saturated_spc_gravity_values:
                record.avg_saturated_spc_gravity = sum(saturated_spc_gravity_values) / len(saturated_spc_gravity_values)
            else:
                record.avg_saturated_spc_gravity = 0.0


    
    #usc
    # parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    usc_name = fields.Char("Name",default="UCS")
    usc_visible = fields.Boolean("USC Visible",compute="_compute_visible")
    child_lines1 = fields.One2many('mechanical.usc.line1','parent_id',string="Parameter")
    
    avg_usc = fields.Float("Average USC",compute="_compute_avg_usc")


    @api.depends('child_lines1.usc')
    def _compute_avg_usc(self):
        for record in self:
            usc_values = record.child_lines1.mapped('usc')
            if usc_values:
                record.avg_usc = sum(usc_values) / len(usc_values)
            else:
                record.avg_usc = 0

    porosity_visible = fields.Boolean("Porosity Visible",compute="_compute_visible")
    specific_gravity_visible = fields.Boolean("Saturated Specific Gravity Visible",compute="_compute_visible")
    dry_density_visible = fields.Boolean("Dry Density Visible",compute="_compute_visible")
    water_absorption_visible = fields.Boolean("USC Visible",compute="_compute_visible")



    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.usc_visible = False
            record.porosity_visible = False
            record.specific_gravity_visible = False
            record.dry_density_visible = False
            record.water_absorption_visible = False

          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "2547ljye-0bc7-41a6-a2bb-0fe9d898008d":
                    record.usc_visible = True
                if sample.internal_id == "2347lier-9d64-48cd-8277-ad734e0edd84":
                    record.porosity_visible = True
                if sample.internal_id == "5687pirt-9a52-4242-9a36-2e40e5fc8247":
                    record.specific_gravity_visible = True
                if sample.internal_id == "897lyuteg-11eb-45ef-addf-e183edabd6dd":
                    record.dry_density_visible = True
                if sample.internal_id == "pytrgbe1-b9a9-41cb-86a5-89d87312f3d6":
                    record.water_absorption_visible = True

               

                
    
   
            
           

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
        record = super(MechanicalRock, self).create(vals)
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
        record = self.env['mechanical.rock1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class MechanicalRockLine(models.Model):
    _name = "mechanical.rock1.line"
    parent_id = fields.Many2one('mechanical.rock1',string="Parent Id")
   
    sr_no = fields.Integer(string="Specimen NO.", readonly=True, copy=False, default=1)
    location = fields.Char(string="Location")
    sample_no = fields.Char(string="Sample Number")
    depth = fields.Char(string="Depth in (mtr)", size=100) 
    ssd_weight = fields.Float(string="SSD weight of sample in kg, Msat",digits=(16, 3))
    wt_sample_water = fields.Float(string="Weight of sample in water in kg, Msub",digits=(16, 3))
    oven_dry_wt = fields.Float(string="Oven dry weight of sample in kg, Ms",digits=(16, 3))
    porosity = fields.Float(string="Porosity",compute="_compute_porosity")
    water_absorption = fields.Float(string="Water Absorption",compute="_compute_water_absorption")
    dry_density = fields.Float(string="Dry Density",compute="_compute_dry_density",digits=(16, 2))
    saturated_spc_gravity = fields.Float(string="Saturated Specific Gravity",compute="_compute_saturated_spc_gravity",digits=(16, 2))

    @api.depends('ssd_weight', 'wt_sample_water', 'oven_dry_wt')
    def _compute_porosity(self):
        for record in self:
            # if record.ssd_weight and record.wt_sample_water and (record.ssd_weight - record.wt_sample_water) != 0:
            if record.ssd_weight and record.wt_sample_water != record.ssd_weight:
                record.porosity = (record.ssd_weight - record.oven_dry_wt) / (record.ssd_weight - record.wt_sample_water) * 100
            else:
                record.porosity = 0.0
        print("<<<<<<<<<<<<<")
    
    @api.depends('ssd_weight', 'oven_dry_wt')
    def _compute_water_absorption(self):
        for record in self:
            if record.oven_dry_wt and record.ssd_weight:
                record.water_absorption = ((record.ssd_weight - record.oven_dry_wt) / record.oven_dry_wt) * 100
            else:
                record.water_absorption = 0.0

    # @api.depends('wt_sample_water', 'wt_sample_water', 'oven_dry_wt')
    # def _compute_dry_density(self):
    #     for record in self:
    #         if record.ssd_weight and record.wt_sample_water and record.oven_dry_wt:
    #             record.dry_density = record.oven_dry_wt / record.ssd_weight - record.wt_sample_water
    #         else:
    #             record.dry_density = 0.0
                
    @api.depends('ssd_weight', 'wt_sample_water', 'oven_dry_wt')
    def _compute_saturated_spc_gravity(self):
        for record in self:
            if record.ssd_weight and record.wt_sample_water and record.oven_dry_wt:
                record.saturated_spc_gravity = record.oven_dry_wt / (record.ssd_weight - record.wt_sample_water)
            else:
                record.saturated_spc_gravity = 0.0

    # @api.depends('oven_dry_wt','dry_density')
    # def _compute_saturated_spc_gravity(self):
    #     for record in self:
    #         if record.dry_density != 0:
    #             record.saturated_spc_gravity = record.oven_dry_wt/record.dry_density
    #         else:
    #             record.saturated_spc_gravity = 0.0
                
    @api.depends('ssd_weight', 'wt_sample_water', 'oven_dry_wt')
    def _compute_dry_density(self):
        for record in self:
            if record.ssd_weight and record.wt_sample_water and record.oven_dry_wt:
                record.dry_density = record.oven_dry_wt / (record.ssd_weight - record.wt_sample_water)
            else:
                record.dry_density = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalRockLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class MechanicalUSCLine(models.Model):
    _name = "mechanical.usc.line1"
    parent_id = fields.Many2one('mechanical.rock1',string="Parent Id")
   
    
    location = fields.Char(string="Location")
    sr_no = fields.Integer(string="Sample NO.", readonly=True, copy=False, default=1)
    depth = fields.Char(string="Depth in (mtr)")
    diameter = fields.Float(string="Dia. in mm")
    length = fields.Float(string="Length in mm")
    ld_ratio = fields.Float(string="L/D ratio",compute="_compute_ld_ratio")
    area = fields.Float(string="Area in mm2",compute="_compute_area",digits=(16,2))
    load = fields.Float(string="Load in KN",digits=(16,2))
    usc = fields.Float(string="UCS in N/mm2",compute="_compute_usc")


    @api.depends('length', 'diameter')
    def _compute_ld_ratio(self):
        for record in self:
            if record.diameter != 0:
                record.ld_ratio = record.length / record.diameter
            else:
                record.ld_ratio = 0


    # @api.depends('length')
    # def _compute_area(self):
    #     for record in self:
    #         record.area = (3.143 )* (record.length * record.length) / 4
                
    @api.depends('diameter')
    def _compute_area(self):
        for record in self:
            record.area = (3.14 * record.diameter * record.diameter) / 4  # Round the result to 2 decimal places
    
    @api.depends('load', 'area')
    def _compute_usc(self):
        for record in self:
            if record.area != 0:
                record.usc = round((record.load / record.area) * 1000, 2)  # Round the result to 2 decimal places
            else:
                record.usc = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalUSCLine, self).create(vals)

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

class RockDatasheet(models.AbstractModel):
        _name = 'report.rock.rock_datasheet1'
        _description = 'Rock DataSheet 1'
    
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



class RockReport1(models.AbstractModel):
    _name = 'report.rock.rock_report1'
    _description = 'Rock Report 1'
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        elif 'active_id' in data['context']:
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


