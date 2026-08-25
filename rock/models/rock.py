from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalRock(models.Model):
    _name = "mechanical.rock"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Specific Gravity, Water Absorption, Porosity & Dry Density")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    notes_id = fields.One2many('mechanical.rock.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalRock, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The Test Report(s) is/are valid only to the sample submitted to the laboratory.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sample(s) was/were not drawn by laboratory.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'This Report may not be reproduced in except full/ part without the permission of the Lab Head of the Laboratory.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': '# - Information provided by the customer.',
            }),
        ]

        res['notes_id'] = default_notes
        return res



    child_lines = fields.One2many('mechanical.rock.line','parent_id',string="Parameter")
    
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
    child_lines1 = fields.One2many('mechanical.usc.line','parent_id',string="Parameter")
    
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

                if sample.internal_id == "a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d":
                    record.usc_visible = True
                if sample.internal_id == "a4eb1d5e-9d64-48cd-8277-ad734e0edd84":
                    record.porosity_visible = True
                if sample.internal_id == "bf5d3d97-9a52-4242-9a36-2e40e5fc8247":
                    record.specific_gravity_visible = True
                if sample.internal_id == "87ec776a-11eb-45ef-addf-e183edabd6dd":
                    record.dry_density_visible = True
                if sample.internal_id == "71e24ae1-b9a9-41cb-86a5-89d87312f3d6":
                    record.water_absorption_visible = True

               

                
    
   
            
           

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:



            if result.parameter.internal_id == 'a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d':
                # result.result_char = self.initial_setting_time_minutes_unrounded
                result.calculated = True
                # if self.initial_setting_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'a4eb1d5e-9d64-48cd-8277-ad734e0edd84':
                # result.result_char = self.initial_setting_time_minutes_unrounded
                result.calculated = True
                # if self.initial_setting_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue


           

            if result.parameter.internal_id == 'bf5d3d97-9a52-4242-9a36-2e40e5fc8247':
                # result.result_char = round(self.average_water_absorption_particle,2)
                result.calculated = True
                # if self.average_water_absorption_particle_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '87ec776a-11eb-45ef-addf-e183edabd6dd':
                # result.result_char = round(self.average_length,2)
                result.calculated = True
                # if self.average_length_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '71e24ae1-b9a9-41cb-86a5-89d87312f3d6':
                # result.result_char = round(self.average_width,2)
                result.calculated = True
                # if self.average_width_nabl == 'pass':
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
        record = self.env['mechanical.rock'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class MechanicalRockLine(models.Model):
    _name = "mechanical.rock.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")
   
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
    _name = "mechanical.usc.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")
   
    
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



class RockNotes(models.Model):
    _name = "mechanical.rock.notes"

    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")