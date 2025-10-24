from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math

# import logging
# _logger = logging.getLogger(__name__)



class Stones(models.Model):
    _name = "mechanical.stones"
    _inherit = "lerm.eln"
    _rec_name = "name_stones"


    name_stones = fields.Char("Name",default="Stones")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id


     
    lab_id1 = fields.Char(string="Lab ID No. ")
    room_temp1 = fields.Float(string="Temperature during test", digits=(12,2))
    relative_humidity1= fields.Float(string="Relative humidity during test ", digits=(12,2))
    depth = fields.Char(string="Depth")
    stone_type1 = fields.Char(string="Type of Stone")



   
#  Scratch hardness According to Moh's Scale

   


    
    scratch_hardness_name = fields.Char("Name",default="Scratch hardness According to Moh's Scale")
    scratch_hardness_visible = fields.Boolean("Surface Quality",compute="_compute_visible") 

    observations1 = fields.Float(string="Observations")
    observations2 = fields.Float(string="Observations")
    observations3 = fields.Float(string="Observations")
    observations4 = fields.Float(string="Observations")
    observations5 = fields.Float(string="Observations")

    scratch_hardness_avg = fields.Float(string="Scratch hardness According to Moh's Scale",compute="_compute_scratch_hardness_avg")

   
    @api.depends('observations1', 'observations2', 'observations3', 'observations4', 'observations5')
    def _compute_scratch_hardness_avg(self):
        for record in self:
            values = [record.observations1, record.observations2, record.observations3, record.observations4, record.observations5]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.scratch_hardness_avg = total / count if count > 0 else 0


     # Compressive Strength in dry condition

    compressive_dry_name = fields.Char("Name",default="Compressive Strength in dry condition  ")
    compressive_dry_visible = fields.Boolean("Compressive Strength in dry condition   Visible",compute="_compute_visible")

    compressive_dry_ids = fields.One2many("mechanical.compressive.dry.line", "parent_id", string="Test Readings")

    compressive_perpendiculer_avg = fields.Float(
        string="Average Compressive Strength Perpendicular Dry (N/mm²)",
        compute="_compute_average_strengths",
        store=True,
        digits=(12, 2)
    )

    compressive_parallel_avg = fields.Float(
        string="Average Compressive Strength Parallel Dry (N/mm²)",
        compute="_compute_average_strengths",
        store=True,
        digits=(12, 2)
    )

    @api.depends('compressive_dry_ids.compressive_perpendiculer', 'compressive_dry_ids.compressive_parallel')
    def _compute_average_strengths(self):
        for record in self:
            perpend_vals = record.compressive_dry_ids.mapped('compressive_perpendiculer')
            parallel_vals = record.compressive_dry_ids.mapped('compressive_parallel')

            record.compressive_perpendiculer_avg = (
                sum(perpend_vals) / len(perpend_vals)
                if perpend_vals else 0.0
            )
            record.compressive_parallel_avg = (
                sum(parallel_vals) / len(parallel_vals)
                if parallel_vals else 0.0
            )

    # Compressive Strength in Satuarted Condition
    compressive_wet_name = fields.Char("Name",default=" Compressive Strength in Satuarted Condition")
    compressive_wet_visible = fields.Boolean(" Compressive Strength in Satuarted Condition Visible",compute="_compute_visible")

    compressive_wet_ids = fields.One2many("mechanical.compressive.wet.line", "parent_id", string="Test Readings")

    compressive_perpendiculer_wet_avg = fields.Float(
        string="Average Compressive Strength Perpendicular Wet (N/mm²)",
        compute="_compute_average_strengths_wet",
        store=True,
        digits=(12, 2)
    )

    compressive_parallel_wet_avg = fields.Float(
        string="Average Compressive Strength Parallel Wet (N/mm²)",
        compute="_compute_average_strengths_wet",
        store=True,
        digits=(12, 2)
    )

    @api.depends('compressive_wet_ids.compressive_perpendiculer', 'compressive_wet_ids.compressive_parallel')
    def _compute_average_strengths_wet(self):
        for record in self:
            perpend_vals = record.compressive_wet_ids.mapped('compressive_perpendiculer')
            parallel_vals = record.compressive_wet_ids.mapped('compressive_parallel')

            record.compressive_perpendiculer_wet_avg = (
                sum(perpend_vals) / len(perpend_vals)
                if perpend_vals else 0.0
            )
            record.compressive_parallel_wet_avg = (
                sum(parallel_vals) / len(parallel_vals)
                if parallel_vals else 0.0
            )

    porosity_name = fields.Char("Name",default=" Porosity,Water Absorption,App. Specific gravity,True Specific gravity")
    porosity_visible = fields.Boolean(" Porosity,Water Absorption,App. Specific gravity,True Specific gravity",compute="_compute_visible")
    water_absorption_visible = fields.Boolean(" Porosity,Water Absorption,App. Specific gravity,True Specific gravity",compute="_compute_visible")
    app_specific_visible = fields.Boolean(" Porosity,Water Absorption,App. Specific gravity,True Specific gravity",compute="_compute_visible")
    true_specific_visible = fields.Boolean(" Porosity,Water Absorption,App. Specific gravity,True Specific gravity",compute="_compute_visible")

    #    App. Porosity
    weight_oven_dried = fields.Float(
        string="Weight of Oven Dried Test Piece (gm)",
        digits=(12, 2)
    )
    weight_saturated_surface_dry = fields.Float(
        string="Weight of Saturated Surface Dry Test Piece (gm)",
        digits=(12, 2)
    )
    water_added = fields.Float(
        string="Quantity of Water Added in 1000 ml Jar Containing Test Piece (gm)",
        digits=(12, 2)
    )

    app_porosity = fields.Float(
        string="Apparent Porosity (%)",
        compute="_compute_app_porosity",
        store=True,
        digits=(12, 2)
    )

    @api.depends('weight_oven_dried', 'weight_saturated_surface_dry', 'water_added')
    def _compute_app_porosity(self):
        for record in self:
            w1 = record.weight_oven_dried or 0.0
            w2 = record.weight_saturated_surface_dry or 0.0
            w3 = record.water_added or 0.0

            denominator = (1000 - w3)
            if denominator != 0:
                record.app_porosity = ((w2 - w1) / denominator) * 100
            else:
                record.app_porosity = 0.0

    # Water Absorption

    wet_of_oven_water = fields.Float(string="Weight of oven dried test piece in gm) ", digits=(12,2),compute="_compute_wet_values",store=True)
    wet_of_satureted_water = fields.Float(string="Weight of saturated surface dry test piece gm", digits=(12,2),compute="_compute_wet_values",store=True)
    water_absorption = fields.Float(string="Water Absorption", digits=(12,2),compute="_compute_water_absorption",store=True)

    @api.depends('weight_oven_dried', 'weight_saturated_surface_dry')
    def _compute_wet_values(self):
        for rec in self:
            rec.wet_of_oven_water = rec.weight_oven_dried
            rec.wet_of_satureted_water = rec.weight_saturated_surface_dry

    @api.depends('wet_of_oven_water', 'wet_of_satureted_water')
    def _compute_water_absorption(self):
        for rec in self:
            wet_oven = rec.wet_of_oven_water or 0.0
            wet_sat = rec.wet_of_satureted_water or 0.0
            if wet_sat != 0:
                rec.water_absorption = ((wet_sat - wet_oven) / wet_sat) * 100
            else:
                rec.water_absorption = 0.0

     # App. Specific gravity

    wet_of_oven_specific = fields.Float(string="Weight of oven dried test piece in gm ", digits=(12,2),compute="_compute_specific_values",store=True)
    water_addes_specifc = fields.Float(string="Quantity of water added in 1000 ml jar containing tets piece in gm", digits=(12,2),compute="_compute_specific_values",store=True)
    app_specific_gravity = fields.Float(string="App. Specific gravity", compute="_compute_specific_gravity",digits=(12,2),store=True)

    @api.depends('weight_oven_dried', 'water_added')
    def _compute_specific_values(self):
        for rec in self:
            rec.wet_of_oven_specific = rec.weight_oven_dried
            rec.water_addes_specifc = rec.water_added

    @api.depends('wet_of_oven_specific', 'water_addes_specifc')
    def _compute_specific_gravity(self):
        for record in self:
            if record.water_addes_specifc and (1000 - record.water_addes_specifc) != 0:
                record.app_specific_gravity = record.wet_of_oven_specific / (1000 - record.water_addes_specifc)
            else:
                record.app_specific_gravity = 0.0

    # True Specific gravity

    wet_true_specific = fields.Float(string="Weight of empty Sp. Gravity bottle with stopper  in gms ", digits=(12,3))
    wt_stop_true_specifc = fields.Float(string="Wt. of bottle with stopper and powder in gms", digits=(12,3))
    wt_bottle_true_specifc = fields.Float(string="Wt. of bottle with stopper, powder and distilled water at room temp. in gms", digits=(12,3))
    wt_bottle_stope_true_specifc = fields.Float(string="Wt. of bottle with stopper filled with distilled water at room temp. in gms", digits=(12,3))
    true_specific_gravity = fields.Float(string="True Specific gravity",digits=(12,2),compute="_compute_true_specific_gravity",store=True)

    @api.depends('wet_true_specific', 'wt_stop_true_specifc', 'wt_bottle_true_specifc', 'wt_bottle_stope_true_specifc')
    def _compute_true_specific_gravity(self):
        for record in self:
            denominator = ((record.wt_bottle_stope_true_specifc - record.wet_true_specific) -
                           (record.wt_bottle_true_specifc - record.wt_stop_true_specifc))
            if denominator != 0:
                record.true_specific_gravity = (record.wt_stop_true_specifc - record.wet_true_specific) / denominator
            else:
                record.true_specific_gravity = 0.0

    true_porosity = fields.Float(string="True porosity",compute="_compute_true_porosity",digits=(12,2),store=True)

    @api.depends('app_specific_gravity', 'true_specific_gravity')
    def _compute_true_porosity(self):
        for record in self:
            if record.true_specific_gravity and record.true_specific_gravity != 0:
                record.true_porosity = ((record.true_specific_gravity - record.app_specific_gravity) / record.true_specific_gravity) * 100
            else:
                record.true_porosity = 0.0




        

    



 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.scratch_hardness_visible = False
            record.compressive_dry_visible = False
            record.compressive_wet_visible = False
            record.porosity_visible = False
            record.water_absorption_visible = False
            record.app_specific_visible = False
            record.true_specific_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                
                if sample.internal_id == "cecda256-41c5-4cb5-843a-e09590c7c587":
                    record.scratch_hardness_visible = True

                if sample.internal_id == "5478ttr5-41c5-4cb5-843a-e09590c7c5789hh":
                    record.compressive_dry_visible = True

                if sample.internal_id == "547896rg-41c5-4cb5-843a-e09590c7c57878tt":
                    record.compressive_wet_visible = True

                if sample.internal_id == "5787896rg-41c5-4cb5-843a-e09590c7c5578rte":
                    record.porosity_visible = True
                    record.water_absorption_visible = True
                    record.app_specific_visible = True
                    record.true_specific_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c74578trew8":
                    record.water_absorption_visible = True
                    record.porosity_visible = True
                    record.app_specific_visible = True
                    record.true_specific_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c7789rte143q":
                    record.app_specific_visible = True
                    record.water_absorption_visible = True
                    record.porosity_visible = True
                    record.true_specific_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv":
                    record.true_specific_visible = True
                    record.water_absorption_visible = True
                    record.porosity_visible = True
                    record.app_specific_visible = True


                    

               
##########################


    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }   
    # 
    # 
    # #################################        

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '4bad1ffc-1874-4ebc-a9e9-acc9557d2fd2':
                result.result_char = round(self.avg_true_specific_gravity,2)
                if self.avg_true_specific_gravity_nabl == 'pass':
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
        record = super(Stones, self).create(vals)
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
        record = self.env['mechanical.stones'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id






class CompressiveDryLine(models.Model):
    _name = "mechanical.compressive.dry.line"
    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    # sr_no = fields.Integer(string="Test", readonly=True, copy=False, default=1)
    date = fields.Date(string="Date")
    lab_id = fields.Char(string="Lab ID No.) ")
    room_temp = fields.Float(string="Room temperature (deg)", digits=(12,2))
    relative_humidity = fields.Float(string="Relative Humidity (%) ", digits=(12,2))
    functional_check = fields.Char(string="Functional Checks ")
    stone_type = fields.Char(string="Type of stone) ")
    shape_stone = fields.Char(string="Shape of test piece (Cube/Cylinder) ")
    height_shape = fields.Float(string="Height of sample(H), mm ", digits=(12,2))
    width_stone = fields.Float(string="Width/Diameter of sample(D), mm ", digits=(12,2))
    test_conditin = fields.Char(string="Test condition (Dry/Saturated) ")
    load_perpendiculer = fields.Float(string="Load Perpendicular to plane of Anisotropy KN", digits=(12,2))
    load_parallel = fields.Float(string="Load Parallel to plane of Anisotropy KN ", digits=(12,2))
    load_perpendiculer_n = fields.Float(string="Load  Perpendicular to plane of Anisotropy N ", digits=(12,2),compute="_compute_loads_in_newton",store=True)
    load_parallel_n = fields.Float(string="Load  Parallel to plane of Anisotropy N ", digits=(12,2),compute="_compute_loads_in_newton",store=True)
    duration_test = fields.Float(string="Duration of test (sec) ", digits=(12,2))
    appearance_stone = fields.Float(string="Appearance/any unusual features at failure ", digits=(12,2))
    hd_stone = fields.Float(string="H/d ", digits=(12,2),compute="_compute_stone_values",store=True)
    area_stone = fields.Float(string="Area of sample (mm2) ", digits=(12,2),compute="_compute_stone_values",store=True)
    compressive_perpendiculer = fields.Float(string="Compressive Strength Perpendicular to plane of Anisotropy (N/mm2)  ", digits=(12,2), compute="_compute_compressive_strength",store=True)
    compressive_parallel = fields.Float(string="Compressive Parallel to plane of Anisotropy (N/mm2)  ", digits=(12,2),compute="_compute_compressive_strength",store=True)
    stress_perpendiculer = fields.Float(string="Stress rate Perpendicular to plane of Anisotropy(MPa/s)  ",digits=(12,2),compute="_compute_stress_rate",store=True)
    stress_parallel = fields.Float(string="Stress rate Parallel to plane of Anisotropy(MPa/s)   ", digits=(12,2),compute="_compute_stress_rate",store=True)


    @api.depends('load_perpendiculer', 'load_parallel')
    def _compute_loads_in_newton(self):
        for record in self:
            record.load_perpendiculer_n = (record.load_perpendiculer or 0.0) * 1000
            record.load_parallel_n = (record.load_parallel or 0.0) * 1000

    @api.depends('height_shape', 'width_stone')
    def _compute_stone_values(self):
        for record in self:
            if record.width_stone:
                record.hd_stone = record.height_shape / record.width_stone
            else:
                record.hd_stone = 0.0

            record.area_stone = (record.height_shape or 0.0) * (record.width_stone or 0.0)


    @api.depends('load_perpendiculer_n', 'load_parallel_n', 'area_stone')
    def _compute_compressive_strength(self):
        for record in self:
            if record.area_stone:
                record.compressive_perpendiculer = record.load_perpendiculer_n / record.area_stone
                record.compressive_parallel = record.load_parallel_n / record.area_stone
            else:
                record.compressive_perpendiculer = 0.0
                record.compressive_parallel = 0.0

    @api.depends('compressive_perpendiculer', 'compressive_parallel', 'duration_test')
    def _compute_stress_rate(self):
        for record in self:
            if record.duration_test:
                record.stress_perpendiculer = record.compressive_perpendiculer / record.duration_test
                record.stress_parallel = record.compressive_parallel / record.duration_test
            else:
                record.stress_perpendiculer = 0.0
                record.stress_parallel = 0.0

    
    
    


   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveDryLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class CompressiveWetLine(models.Model):
    _name = "mechanical.compressive.wet.line"
    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    # sr_no = fields.Integer(string="Test", readonly=True, copy=False, default=1)
    date = fields.Date(string="Date")
    lab_id = fields.Char(string="Lab ID No.) ")
    room_temp = fields.Float(string="Room temperature (deg)", digits=(12,2))
    relative_humidity = fields.Float(string="Relative Humidity (%) ", digits=(12,2))
    functional_check = fields.Char(string="Functional Checks ")
    stone_type = fields.Char(string="Type of stone) ")
    shape_stone = fields.Char(string="Shape of test piece (Cube/Cylinder) ")
    height_shape = fields.Float(string="Height of sample(H), mm ", digits=(12,2))
    width_stone = fields.Float(string="Width/Diameter of sample(D), mm ", digits=(12,2))
    test_conditin = fields.Char(string="Test condition (Dry/Saturated) ")
    load_perpendiculer = fields.Float(string="Load Perpendicular to plane of Anisotropy KN", digits=(12,2))
    load_parallel = fields.Float(string="Load Parallel to plane of Anisotropy KN ", digits=(12,2))
    load_perpendiculer_n = fields.Float(string="Load  Perpendicular to plane of Anisotropy N ", digits=(12,2),compute="_compute_loads_in_newton",store=True)
    load_parallel_n = fields.Float(string="Load  Parallel to plane of Anisotropy N ", digits=(12,2),compute="_compute_loads_in_newton",store=True)
    duration_test = fields.Float(string="Duration of test (sec) ", digits=(12,2))
    appearance_stone = fields.Float(string="Appearance/any unusual features at failure ", digits=(12,2))
    hd_stone = fields.Float(string="H/d ", digits=(12,2),compute="_compute_stone_values",store=True)
    area_stone = fields.Float(string="Area of sample (mm2) ", digits=(12,2),compute="_compute_stone_values",store=True)
    compressive_perpendiculer = fields.Float(string="Compressive Strength Perpendicular to plane of Anisotropy (N/mm2)  ", digits=(12,2), compute="_compute_compressive_strength",store=True)
    compressive_parallel = fields.Float(string="Compressive Parallel to plane of Anisotropy (N/mm2)  ", digits=(12,2),compute="_compute_compressive_strength",store=True)
    stress_perpendiculer = fields.Float(string="Stress rate Perpendicular to plane of Anisotropy(MPa/s)  ",digits=(12,2),compute="_compute_stress_rate",store=True)
    stress_parallel = fields.Float(string="Stress rate Parallel to plane of Anisotropy(MPa/s)   ", digits=(12,2),compute="_compute_stress_rate",store=True)


    @api.depends('load_perpendiculer', 'load_parallel')
    def _compute_loads_in_newton(self):
        for record in self:
            record.load_perpendiculer_n = (record.load_perpendiculer or 0.0) * 1000
            record.load_parallel_n = (record.load_parallel or 0.0) * 1000

    @api.depends('height_shape', 'width_stone')
    def _compute_stone_values(self):
        for record in self:
            if record.width_stone:
                record.hd_stone = record.height_shape / record.width_stone
            else:
                record.hd_stone = 0.0

            record.area_stone = (record.height_shape or 0.0) * (record.width_stone or 0.0)


    @api.depends('load_perpendiculer_n', 'load_parallel_n', 'area_stone')
    def _compute_compressive_strength(self):
        for record in self:
            if record.area_stone:
                record.compressive_perpendiculer = record.load_perpendiculer_n / record.area_stone
                record.compressive_parallel = record.load_parallel_n / record.area_stone
            else:
                record.compressive_perpendiculer = 0.0
                record.compressive_parallel = 0.0

    @api.depends('compressive_perpendiculer', 'compressive_parallel', 'duration_test')
    def _compute_stress_rate(self):
        for record in self:
            if record.duration_test:
                record.stress_perpendiculer = record.compressive_perpendiculer / record.duration_test
                record.stress_parallel = record.compressive_parallel / record.duration_test
            else:
                record.stress_perpendiculer = 0.0
                record.stress_parallel = 0.0

    
    
    


   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveWetLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1














   

   

  



    


   



   
   

   
