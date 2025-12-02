from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from math import pi


class MechanicalRock(models.Model):
    _name = "mechanical.rock"
    _inherit = "lerm.eln"
    _rec_name = "name_rock"

    name_rock = fields.Char("Name",default="ROCK")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    notes_id = fields.One2many('rock.notes','parent_id',string="Notes")

    @api.model
    def default_get(self, fields):
        res = super(MechanicalRock, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an #  received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Genstru.',
            }),
              (0, 0, {
                'sr_no': 'e',
                'notes': '^ represents unsoaked test',
            }),
              (0, 0, {
                'sr_no': 'd',
                'notes': '$ represents crumbled in water',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'rock.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }



    rock_child_lines = fields.One2many('mechanical.rock.line','parent_id',string="Parameter")
    usc_visible = fields.Boolean("USC Visible",compute="_compute_visible")

    point_load_constant = fields.Float(string="Point Load  Constant")
    compressive_strength_constant = fields.Float(string="Compressive Strength  Constant")
    compressive_strength_constant_hd = fields.Float(string="Compressive Strength HD  Constant",digits=(12,4))
    


   
    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.usc_visible = False


          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d":
                    record.usc_visible = True

              
               

                
    
   
            
           

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
        record = self.env['mechanical.rock'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values




class MechanicalRockLine(models.Model):
    _name = "mechanical.rock.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    # blue_input = fields.Boolean(default=True,invisible=True)
   
    sr_no = fields.Integer(string="Specimen NO.", readonly=True, copy=False, default=1)
    date_received = fields.Date(string="Date of Received")
    date_testing = fields.Date(string="Date of Testing")
    lab_id = fields.Char(string="Lab ID") 
    bh_no = fields.Char(string="BH No./Location",digits=(16, 3))
    depth = fields.Char(string="Depth")
    piece_no = fields.Char(string="Piece No")
    lithological = fields.Char(string="Lithological Description of rock")
    room_temp = fields.Float(string="Room Temperature")
    relative_humidity = fields.Float(string="Relative humidity",digits=(16, 2))
    water_temperature = fields.Float(string="Water temperature",digits=(16, 2))
    dia_rock1 = fields.Float(string="Diameter of Rock Sample 1",digits=(16, 2))
    dia_rock2 = fields.Float(string="Diameter of Rock Sample 2",digits=(16, 2))
    dia_rock3 = fields.Float(string="Diameter of Rock Sample 3",digits=(16, 2))
    avg_dia = fields.Float(string="Average Diameter (D)",digits=(16, 2),store=True,compute="_compute_avg_dia")
    height_rock1 = fields.Float(string="Height of Rock Sample 1",digits=(16, 2))
    height_rock2 = fields.Float(string="Height of Rock Sample 2",digits=(16, 2))
    height_rock3 = fields.Float(string="Height of Rock Sample 3",digits=(16, 2))
    avg_height = fields.Float(string="Average Height (H)",digits=(16, 2),store=True,compute="_compute_avg_height")
    hd = fields.Float(string="H/D",digits=(16, 2),store=True,compute="_compute_hd")
    volume_of_sample = fields.Float(string="Volume of Sample(Wsat-Wsub)",digits=(16, 2),store=True,compute="_compute_volume_of_sample")
    volume_of_sample1 = fields.Float(string="Volume of Sample",digits=(16, 2))
    initial_wt = fields.Float(string="Initial Wt of sample",digits=(16, 2))
    dry_wet = fields.Float(string="Dry Wt of sample",digits=(16, 2))
    saturated_wet = fields.Float(string="Saturated Wt of sample",digits=(16, 2))
    volume_of_void = fields.Float(string="Volume of Voids",digits=(16, 2),store=True,compute="_compute_volume_of_void")
    wt_of_sample = fields.Float(string="Wt of sample in Water",digits=(16, 2))
    sp_gravity = fields.Float(string="Sp. Gravity",digits=(16, 2),store=True,compute="_compute_sp_gravity")
    bulk_density = fields.Float(string="Bulk Density",digits=(16, 2),store=True,compute="_compute_bulk_density")
    sat_density = fields.Float(string="Sat Density",digits=(16, 4),store=True,compute="_compute_sat_density")
    dry_density = fields.Float(string="Dry Density",digits=(16, 4),store=True,compute="_compute_dry_density")
    water_absorption = fields.Float(string="Water Absorption",digits=(16, 2),store=True,compute="_compute_water_absorption")
    porosity = fields.Float(string="Porosity",digits=(16, 2),store=True,compute="_compute_porosity")
    load_ucs = fields.Float(string="Load (UCS)",digits=(16, 2))
    load = fields.Float(string="Load",digits=(16, 2),store=True,compute="_compute_load")
    comp_strength1 = fields.Float(string="Compressive Strength qc ",digits=(16, 2),store=True,compute="_compute_comp_strength1")
    comp_strength2 = fields.Float(string="Compressive Strength  qc at H/D=2",digits=(16, 2),store=True,compute="_compute_comp_strength2")
    point_load = fields.Float(string="Point Load",digits=(16, 2))
    point_load_strength = fields.Float(string="Point load strength index-Core",digits=(16, 3),store=True,compute="_compute_point_load_strength")
    point_load_index = fields.Float(string="Point load strength index-Lump",digits=(16, 3),store=True,compute="_compute_point_load_index")
    comp_strength4 = fields.Float(string="Compressive strength , qc from pt load",digits=(16, 2),store=True,compute="_compute_comp_strength4")
    comp_strength5 = fields.Float(string="Compressive strength , qc (H/D >1)",digits=(16, 2),store=True,compute="_compute_comp_strength5")
    duration_of_test = fields.Float(string="Duration of the test (Sec)",digits=(16, 2))
    mode_of_failure = fields.Char(string="Mode of failure",digits=(16, 2))
    comp_rock = fields.Float(string="Compressive Strength  qc ",digits=(16, 2),store=True,compute="_compute_comp_rock")
    comp_rock1 = fields.Float(string="Compressive Strength  qc at H/D=2",digits=(16, 2),store=True,compute="_compute_comp_rock1")
    stress_rate = fields.Float(string="Stress Rate",digits=(16, 2),store=True,compute="_compute_stress_rate")
    moisture_content = fields.Float(string="Moisture Content %",digits=(16, 2),store=True,compute="_compute_moisture_content")


    @api.depends('dia_rock1', 'dia_rock2', 'dia_rock3')
    def _compute_avg_dia(self):
        for rec in self:
            values = [rec.dia_rock1, rec.dia_rock2, rec.dia_rock3]
            valid_values = [v for v in values if v]  
            rec.avg_dia = sum(valid_values) / len(valid_values) if valid_values else 0.0

    @api.depends('height_rock1', 'height_rock2', 'height_rock3')
    def _compute_avg_height(self):
        for rec in self:
            valuess = [rec.height_rock1, rec.height_rock2, rec.height_rock3]
            valid_valuess = [v for v in valuess if v]  
            rec.avg_height = sum(valid_valuess) / len(valid_valuess) if valid_valuess else 0.0

    @api.depends('avg_height', 'avg_dia')
    def _compute_hd(self):
        for rec in self:
            if rec.avg_dia:
                rec.hd = rec.avg_height / rec.avg_dia
            else:
                rec.hd = 0.0

    # ---- Compute method ----
    @api.depends('saturated_wet', 'wt_of_sample')
    def _compute_volume_of_sample(self):
        for rec in self:
            rec.volume_of_sample = rec.saturated_wet - rec.wt_of_sample if rec.saturated_wet and rec.wt_of_sample else 0.0


      # ---- Compute method ----
    @api.depends('saturated_wet', 'dry_wet')
    def _compute_volume_of_void(self):
        for rec in self:
            rec.volume_of_void = rec.saturated_wet - rec.dry_wet if rec.saturated_wet and rec.dry_wet else 0.0

    @api.depends('dry_wet', 'saturated_wet', 'wt_of_sample', 'volume_of_void')
    def _compute_sp_gravity(self):
        for rec in self:
            denominator = (rec.saturated_wet - rec.wt_of_sample) - rec.volume_of_void
            if denominator and denominator != 0:
                rec.sp_gravity = rec.dry_wet / denominator
            else:
                rec.sp_gravity = 0.0

    @api.depends('initial_wt', 'volume_of_sample1')
    def _compute_bulk_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.bulk_density = rec.initial_wt / rec.volume_of_sample1
            else:
                rec.bulk_density = 0.0

    @api.depends('saturated_wet', 'volume_of_sample1')
    def _compute_sat_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.sat_density = rec.saturated_wet / rec.volume_of_sample1
            else:
                rec.sat_density = 0.0

    @api.depends('dry_wet', 'volume_of_sample1')
    def _compute_dry_density(self):
        for rec in self:
            if rec.volume_of_sample1 and rec.volume_of_sample1 != 0:
                rec.dry_density = rec.dry_wet / rec.volume_of_sample1
            else:
                rec.dry_density = 0.0

    # @api.depends('sat_density', 'dry_density')
    # def _compute_water_absorption(self):
    #     for rec in self:
    #         if rec.dry_density and rec.dry_density != 0:
    #             rec.water_absorption = ((rec.sat_density - rec.dry_density) / rec.dry_density) * 100
    #         else:
    #             rec.water_absorption = 0.0

    @api.depends('sat_density', 'dry_density')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.dry_density and rec.dry_density != 0:
                # चार दशांश पर्यंत calculation साठी precision control
                sat = float(f"{rec.sat_density:.4f}")
                dry = float(f"{rec.dry_density:.4f}")

                rec.water_absorption = ((sat - dry) / dry) * 100
            else:
                rec.water_absorption = 0.0

    @api.depends('sat_density', 'dry_density')
    def _compute_porosity(self):
        for rec in self:
                rec.porosity = (rec.sat_density - rec.dry_density) * 100

    @api.depends('load_ucs')
    def _compute_load(self):
        for rec in self:
            rec.load = rec.load_ucs / 10 if rec.load_ucs else 0.0

    @api.depends('load', 'avg_dia')
    def _compute_comp_strength1(self):
        for rec in self:
            if rec.load and rec.avg_dia:
                rec.comp_strength1 = (rec.load * 1000) / ((math.pi / 4) * (rec.avg_dia ** 2) / 100)
            else:
                rec.comp_strength1 = 0.0

    @api.depends('comp_strength1', 'hd')
    def _compute_comp_strength2(self):
        for rec in self:
            if rec.hd and rec.comp_strength1:
                rec.comp_strength2 = 0.889 * rec.comp_strength1 / (0.778 + (0.222 / rec.hd))
            else:
                rec.comp_strength2 = 0.0

    # @api.depends('point_load', 'avg_dia','parent_id.point_load_constant')
    # def _compute_point_load_strength(self):
    #     for rec in self:
    #         if rec.point_load and rec.avg_dia and rec.avg_dia > 0:
    #             rec.point_load_strength = (1000 * rec.point_load) / (math.sqrt(rec.parent_id.point_load_constant) * (rec.avg_dia ** 1.5))
    #         else:
    #             rec.point_load_strength = 0.0
    @api.depends('point_load', 'avg_dia', 'parent_id.point_load_constant')
    def _compute_point_load_strength(self):
        for rec in self:
            if (
                rec.point_load
                and rec.avg_dia
                and rec.avg_dia > 0
                and rec.parent_id.point_load_constant
                and rec.parent_id.point_load_constant > 0
            ):
                rec.point_load_strength = (
                    (1000 * rec.point_load)
                    / (
                        math.sqrt(rec.parent_id.point_load_constant)
                        * (rec.avg_dia ** 1.5)
                    )
                )
            else:
                rec.point_load_strength = 0.0


    # @api.depends('point_load', 'avg_dia', 'avg_height','parent_id.point_load_constant')
    # def _compute_point_load_index(self):
    #     for rec in self:
    #         if rec.point_load and rec.avg_dia and rec.avg_height and rec.avg_dia*rec.avg_height > 0:
    #             rec.point_load_index = (1000 * rec.point_load) / (math.sqrt(rec.parent_id.point_load_constant) * ((rec.avg_dia * rec.avg_height) ** 0.75))
    #         else:
    #             rec.point_load_index = 0.0

    @api.depends('point_load', 'avg_dia', 'avg_height', 'parent_id.point_load_constant')
    def _compute_point_load_index(self):
        for rec in self:
            if (
                rec.point_load 
                and rec.avg_dia 
                and rec.avg_height 
                and rec.avg_dia * rec.avg_height > 0 
                and rec.parent_id.point_load_constant 
                and rec.parent_id.point_load_constant > 0
            ):
                rec.point_load_index = (
                    (1000 * rec.point_load)
                    / (
                        math.sqrt(rec.parent_id.point_load_constant)
                        * ((rec.avg_dia * rec.avg_height) ** 0.75)
                    )
                )
            else:
                rec.point_load_index = 0.0

    @api.depends('point_load_strength','parent_id.compressive_strength_constant')
    def _compute_comp_strength4(self):
        for rec in self:
            rec.comp_strength4 = rec.parent_id.compressive_strength_constant * rec.point_load_strength if rec.point_load_strength else 0.0

    @api.depends('point_load_index','parent_id.compressive_strength_constant')
    def _compute_comp_strength5(self):
        for rec in self:
            rec.comp_strength5 = rec.parent_id.compressive_strength_constant * rec.point_load_index if rec.point_load_index else 0.0


    @api.depends('comp_strength1','parent_id.compressive_strength_constant_hd')
    def _compute_comp_rock(self):
        for rec in self:
            rec.comp_rock = rec.parent_id.compressive_strength_constant_hd * rec.comp_strength1 if rec.comp_strength1 else 0.0

    @api.depends('comp_strength2','parent_id.compressive_strength_constant_hd')
    def _compute_comp_rock1(self):
        for rec in self:
            rec.comp_rock1 = rec.parent_id.compressive_strength_constant_hd * rec.comp_strength2 if rec.comp_strength2 else 0.0

    @api.depends('comp_rock1', 'duration_of_test')
    def _compute_stress_rate(self):
        for rec in self:
            if rec.duration_of_test:
                rec.stress_rate = rec.comp_rock1 / rec.duration_of_test
            else:
                rec.stress_rate = 0.0

    @api.depends('initial_wt', 'dry_wet')
    def _compute_moisture_content(self):
        for rec in self:
            if rec.dry_wet:
                rec.moisture_content = ((rec.initial_wt - rec.dry_wet) / rec.dry_wet) * 100
            else:
                rec.moisture_content = 0.0



          





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


class RockNotes(models.Model):
    _name = "rock.notes"

    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



