from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
from decimal import Decimal, ROUND_UP

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


    notes_id = fields.One2many('stone.notes','parent_id',string="Notes")
    

    @api.model
    def create(self, vals):
        record = super(Stones, self).create(vals)

        if not record.notes_id:
            default_notes = [
                {'sr_no': 'a', 'notes': 'The information marked with an # received from customer'},
                {'sr_no': 'b', 'notes': 'The results listed refer only to tested parameter and sample as received'},
                {'sr_no': 'c', 'notes': 'Samples will be discarded after 15 days unless otherwise specified.'},
                {'sr_no': 'd', 'notes': 'This document shall not be reproduced without approval.'},
            ]

            for note in default_notes:
                self.env['coarse.aggregate.notes'].create({
                    'parent_id': record.id,
                    'sr_no': note['sr_no'],
                    'notes': note['notes'],
                })

        return record


    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'stone.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }


     
    lab_id1 = fields.Char(string="Lab ID No. ")
    room_temp1 = fields.Float(string="Temperature during test", digits=(12,2) )
    relative_humidity1= fields.Float(string="Relative humidity during test ", digits=(12,2) )
    depth = fields.Char(string="Depth")
    stone_type1 = fields.Char(string="Type of Stone")


    lab_id = fields.Char(
            string="Lab ID",
            compute="_compute_lab_id",
            store=True
        )

    @api.depends('eln_ref')
    def _compute_lab_id(self):
        for rec in self:
            if rec.eln_ref:
                rec.lab_id = rec.eln_ref.lab_id
            else:
                rec.lab_id = False

    lab_stone_ids = fields.One2many(
        'stone.lab.line', 
        'parent_id', 
        string="Generated Options"
    )



    def action_generate_options_stone(self):
        for record in self:
            # Step 1: Check if lab_id exists and has hyphen
            if record.lab_id and '-' in record.lab_id:
                try:
                    # Step 2: Clear old lines first
                    lines_command = [(5, 0, 0)]
                    
                    # Step 3: String Parsing
                    parts = record.lab_id.split(' - ')
                    
                    if len(parts) >= 2:
                        start_part = parts[0].strip() # Example: "S-25-001"
                        end_part = parts[-1].strip()  # Example: "S-25-006"

                        prefix = start_part.rsplit('-', 1)[0]
                        
                        # --- CHANGE START ---
                        # Number cha string part vegla kara length check karnya sathi
                        start_num_str = start_part.split('-')[-1] # "001" milnar
                        end_num_str = end_part.split('-')[-1]     # "006" milnar
                        
                        # Length calculate kara (Example: "001" chi length 3 ahe)
                        padding_length = len(start_num_str)

                        start_num = int(start_num_str) # Integer madhe convert: 1
                        end_num = int(end_num_str)     # Integer madhe convert: 6
                        # --- CHANGE END ---

                        # Step 4: Loop ani Create Lines
                        for num in range(start_num, end_num + 1):
                            # zfill use karun zero add kara
                            # Jar num=1 ahe ani padding_length=3 ahe, tar "001" banel
                            formatted_num = str(num).zfill(padding_length)
                            
                            val = f"{prefix}-{formatted_num}"
                            lines_command.append((0, 0, {'lab': val}))

                        # Step 5: Assign to One2many field
                        record.lab_stone_ids = lines_command
                        
                except Exception as e:
                    pass
            else:
                if record.lab_id:
                    record.lab_stone_ids = [(5, 0, 0), (0, 0, {'lab': record.lab_id})]



   
#  Scratch hardness According to Moh's Scale
 
    scratch_hardness_name = fields.Char("Name",default="Scratch hardness According to Moh's Scale")
    scratch_hardness_visible = fields.Boolean("Surface Quality",compute="_compute_visible") 


    temp_scratch_hardness = fields.Char(string="Temp.°C" )
    humidity_scratch_hardness= fields.Char(string="Humidity %" )



    selected_lab_stone1 = fields.Many2one(
        'stone.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_stone_ids)]"
    )

    
    is_scratch_hardness = fields.Boolean(
        string="Compacted Density Selected",
        
    )

    @api.onchange('selected_lab_stone1')
    def _onchange_selected_lab_stone1(self):
        for rec in self:
            if rec.selected_lab_stone1:
                rec.is_scratch_hardness = True
            else:
                rec.is_scratch_hardness= False




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

    compressive_dry_generated = fields.Boolean(string="Compressive Dry Lab Lines ",default=False)
    show_sieve = fields.Boolean(default=False)



    temp_compressive_dry = fields.Char(string="Temp.°C" )
    humidity_compressive_dry= fields.Char(string="Humidity %" )



   

    def action_generate_compressive_dry_lines(self):
        for record in self:
            if record.lab_id and ' - ' in record.lab_id:
                start_str, end_str = record.lab_id.split(' - ')
                prefix = '-'.join(start_str.split('-')[:2])
                start = int(start_str.split('-')[2])
                end = int(end_str.split('-')[2])

                lines = []
                for i in range(start, end + 1):
                    lab_id = f"{prefix}-{str(i).zfill(3)}"
                    lines.append((0, 0, {'lab_id': lab_id}))

                record.compressive_dry_ids = lines
                record.compressive_dry_generated = True

            # 🔹 Set flag to show sieve analysis
            if record.compressive_dry_ids:
                record.show_sieve = True

            # 🔹 Reload the current record in form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'Stone Form',
                'res_model': 'mechanical.stones',
                'res_id': record.id,  # ✅ Use record.id instead of self.id
                'view_mode': 'form',
                'target': 'current',
            }

    
    @api.onchange('compressive_dry_ids')
    def _onchange_limit_lines(self):
        if len(self.compressive_dry_ids) > 5:
            raise ValidationError("You cannot add more than 5 Test Reading lines.")

    factor_a = fields.Float(string="Constant Factor A",  digits=(12, 4))
    factor_b = fields.Float(string="Constant Factor B",  digits=(12, 4))

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

    @api.depends('compressive_dry_ids.compressive_perpendiculer1', 'compressive_dry_ids.compressive_parallel1')
    def _compute_average_strengths(self):
        for record in self:
            perpend_vals = record.compressive_dry_ids.mapped('compressive_perpendiculer1')
            parallel_vals = record.compressive_dry_ids.mapped('compressive_parallel1')

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

    compressive_wet_generated = fields.Boolean(string="Compressive Dry Lab Lines ",default=False)
    show_sieve = fields.Boolean(default=False)

      
    temp_compressive_satuarted = fields.Char(string="Temp.°C" )
    humidity_compressive_satuarted= fields.Char(string="Humidity %" )
    



    def action_generate_compressive_wet_lines(self):
        for record in self:
            if record.lab_id and ' - ' in record.lab_id:
                start_str, end_str = record.lab_id.split(' - ')
                prefix = '-'.join(start_str.split('-')[:2])
                start = int(start_str.split('-')[2])
                end = int(end_str.split('-')[2])

                lines = []
                for i in range(start, end + 1):
                    lab_id = f"{prefix}-{str(i).zfill(3)}"
                    lines.append((0, 0, {'lab_id': lab_id}))

                record.compressive_wet_ids = lines
                record.compressive_wet_generated = True

            # 🔹 Set flag to show sieve analysis
            if record.compressive_wet_ids:
                record.show_sieve = True

            # 🔹 Reload the current record in form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'Stone Form',
                'res_model': 'mechanical.stones',
                'res_id': record.id,  # ✅ Use record.id instead of self.id
                'view_mode': 'form',
                'target': 'current',
            }

    @api.onchange('compressive_wet_ids')
    def _onchange_limits_lines(self):
        if len(self.compressive_wet_ids) > 5:
            raise ValidationError("You cannot add more than 5 Test Reading lines.")

    wet_factor_a = fields.Float(string="Constant Factor A",  digits=(12, 4))
    wet_factor_b = fields.Float(string="Constant Factor B",  digits=(12, 4))

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

    @api.depends('compressive_wet_ids.compressive_perpendiculer1', 'compressive_wet_ids.compressive_parallel1')
    def _compute_average_strengths_wet(self):
        for record in self:
            perpend_vals = record.compressive_wet_ids.mapped('compressive_perpendiculer1')
            parallel_vals = record.compressive_wet_ids.mapped('compressive_parallel1')

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
    true_porosity_visible = fields.Boolean(" Porosity,Water Absorption,App. Specific gravity,True Specific gravity",compute="_compute_visible")


    temp_porosity = fields.Char(string="Temp.°C" )
    humidity_porosity= fields.Char(string="Humidity %" )



    selected_lab_stone2 = fields.Many2one(
        'stone.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_stone_ids)]"
    )


    is_porosity = fields.Boolean(
        string="Compacted Density Selected",
        
    )

    @api.onchange('selected_lab_stone2')
    def _onchange_selected_lab_stone2(self):
        for rec in self:
            if rec.selected_lab_stone2:
                rec.is_porosity = True
            else:
                rec.is_porosity= False





    #    App. Porosity
    weight_oven_dried = fields.Float(
        string="Weight of Oven Dried Test Piece (gm)",
        digits=(12, 1)
    )
    weight_saturated_surface_dry = fields.Float(
        string="Weight of Saturated Surface Dry Test Piece (gm)",
        digits=(12, 1)
    )
    water_added = fields.Float(
        string="Quantity of Water Added in 1000 ml Jar Containing Test Piece (gm)",
        digits=(12, 1)
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


                # record.submit_mode = True

    # Water Absorption

    wet_of_oven_water = fields.Float(string="Weight of oven dried test piece in gm) ", digits=(12,4),compute="_compute_wet_values",store=True)
    wet_of_satureted_water = fields.Float(string="Weight of saturated surface dry test piece gm", digits=(12,4),compute="_compute_wet_values",store=True)
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
                result = ((wet_sat - wet_oven) / wet_sat) * 100
                # Always round UP to 2 decimals
                rec.water_absorption = float(
                    Decimal(str(result)).quantize(Decimal("0.01"), rounding=ROUND_UP)
                )
            else:
                rec.water_absorption = 0.0


                # rec.submit_mode = True



     # App. Specific gravity

    wet_of_oven_specific = fields.Float(string="Weight of oven dried test piece in gm ", digits=(12,4),compute="_compute_specific_values",store=True)
    water_addes_specifc = fields.Float(string="Quantity of water added in 1000 ml jar containing tets piece in gm", digits=(12,4),compute="_compute_specific_values",store=True)
    app_specific_gravity = fields.Float(string="App. Specific gravity", compute="_compute_specific_gravity",digits=(12,5),store=True)

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

    wet_true_specific = fields.Float(string="Weight of empty Sp. Gravity bottle with stopper  in gms ", digits=(12,4))
    wt_stop_true_specifc = fields.Float(string="Wt. of bottle with stopper and powder in gms", digits=(12,4))
    wt_bottle_true_specifc = fields.Float(string="Wt. of bottle with stopper, powder and distilled water at room temp. in gms", digits=(12,4))
    wt_bottle_stope_true_specifc = fields.Float(string="Wt. of bottle with stopper filled with distilled water at room temp. in gms", digits=(12,4))
    true_specific_gravity = fields.Float(string="True Specific gravity",digits=(12,6),compute="_compute_true_specific_gravity",store=True)

    @api.depends('wet_true_specific', 'wt_stop_true_specifc', 'wt_bottle_true_specifc', 'wt_bottle_stope_true_specifc')
    def _compute_true_specific_gravity(self):
        for record in self:
            denominator = ((record.wt_bottle_stope_true_specifc - record.wet_true_specific) -
                           (record.wt_bottle_true_specifc - record.wt_stop_true_specifc))
            if denominator != 0:
                record.true_specific_gravity = (record.wt_stop_true_specifc - record.wet_true_specific) / denominator
            else:
                record.true_specific_gravity = 0.0

    true_porosity = fields.Float(string="True porosity",compute="_compute_true_porosity",digits=(12,4),store=True)

  
    @api.depends('app_specific_gravity', 'true_specific_gravity')
    def _compute_true_porosity(self):
        for record in self:
            if record.true_specific_gravity:
                record.true_porosity = (
                    (record.true_specific_gravity - record.app_specific_gravity)
                    / record.true_specific_gravity
                ) * 100
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
            record.true_porosity_visible = False
            
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
                    record.true_porosity_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c74578trew8":
                    record.water_absorption_visible = True
                    record.porosity_visible = True
                    record.app_specific_visible = True
                    record.true_specific_visible = True
                    record.true_porosity_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c7789rte143q":
                    record.app_specific_visible = True
                    record.water_absorption_visible = True
                    record.porosity_visible = True
                    record.true_specific_visible = True
                    record.true_porosity_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv":
                    record.true_specific_visible = True
                    record.water_absorption_visible = True
                    record.porosity_visible = True
                    record.app_specific_visible = True
                    record.true_porosity_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c7787954nmht2":
                    record.true_porosity_visible = True
                    record.true_specific_visible = True
                    record.water_absorption_visible = True
                    record.porosity_visible = True
                    record.app_specific_visible = True
                    
       

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        if current_user.has_group('lerm_civil.lerm_discipline_group'):
            technician_results = self.eln_ref.parameters_result
        else:
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:
            if result.parameter.internal_id == '4bad1ffc-1874-4ebc-a9e9-acc9557d2fd2':
                result.result_char = round(self.avg_true_specific_gravity,2)
                result.calculated = True
                if self.avg_true_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '5478ttr5-41c5-4cb5-843a-e09590c7c5789hh':
                result.result_char = round(self.compressive_perpendiculer_avg,2)
                result.calculated = True
            
            if result.parameter.internal_id == '547896rg-41c5-4cb5-843a-e09590c7c57878tt':
                result.result_char = round(self.compressive_perpendiculer_wet_avg,2)
                result.calculated = True
            
            if result.parameter.internal_id == '5787896rg-41c5-4cb5-843a-e09590c7c5578rte':
                result.result_char = round(self.true_porosity,2)
                result.calculated = True

            if result.parameter.internal_id == '57r7896rg-41c5-4cb5-843a-e09590c74578trew8':
                result.result_char = round(self.water_absorption,2)
                result.calculated = True

            if result.parameter.internal_id == '57r7896rg-41c5-4cb5-843a-e09590c7789rte143q':
                result.result_char = round(self.app_specific_gravity,2)
                result.calculated = True

            if result.parameter.internal_id == '57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv':
                result.result_char = round(self.true_specific_gravity,2)
                result.calculated = True

            if result.parameter.internal_id == 'cecda256-41c5-4cb5-843a-e09590c7c587':
                result.result_char = round(self.scratch_hardness_avg,2)
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
        record = super(Stones, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            current_user = self.env.user

            # ✅ Discipline group can see all parameters
            if current_user.has_group('lerm_civil.lerm_discipline_group'):
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # 🔒 Only parameters assigned to current technician
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]



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
    blue_input = fields.Boolean(default=True,invisible=True)
    date = fields.Date(string="Date")
    lab_id = fields.Char(string="Lab ID No.) ")
    room_temp = fields.Float(string="Room temperature (deg)", digits=(12,2))
    relative_humidity = fields.Float(string="Relative Humidity (%) ", digits=(12,2))
    functional_check = fields.Char(string="Functional Checks ")
    stone_type = fields.Char(string="Type of stone) ")
    shape_stone = fields.Char(string="Shape of test piece (Cube/Cylinder) ")
    height_shape = fields.Float(string="Height of sample(H), mm ", digits=(12,2))
    width_stone = fields.Float(string="Width/Diameter of sample(D), mm ", digits=(12,2))
    test_conditin = fields.Char(string="Test condition (Dry/Saturated) ",default="Dry")
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

    compressive_perpendiculer1 = fields.Float(string="Compressive Strength Perpendicular to plane of Anisotropy (N/mm2)  ",compute="_compute_corrected_strength", digits=(12,4),store=True)
    compressive_parallel1 = fields.Float(string="Compressive Parallel to plane of Anisotropy (N/mm2)  ",compute="_compute_corrected_strength", digits=(12,4),store=True)

   


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


    @api.depends(
        'compressive_perpendiculer',
        'compressive_parallel',
        'hd_stone',
        'width_stone',
        'height_shape',
        'parent_id.factor_a',
        'parent_id.factor_b'
    )
    def _compute_corrected_strength(self):
        for rec in self:
            # सुरक्षितपणे parent factors घ्या
            a = rec.parent_id.factor_a
            b = rec.parent_id.factor_b

            ratio = (a + b * (rec.width_stone / rec.height_shape)) if rec.height_shape else 1

            if rec.hd_stone == 1:
                rec.compressive_perpendiculer1 = rec.compressive_perpendiculer
                rec.compressive_parallel1 = rec.compressive_parallel
            else:
                rec.compressive_perpendiculer1 = rec.compressive_perpendiculer / ratio if ratio else 0.0
                rec.compressive_parallel1 = rec.compressive_parallel / ratio if ratio else 0.0


    
    
    


   

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
    blue_input = fields.Boolean(default=True,invisible=True)

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
    test_conditin = fields.Char(string="Test condition (Dry/Saturated) ",default="Saturated")
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

    compressive_perpendiculer1 = fields.Float(string="Compressive Strength Perpendicular to plane of Anisotropy (N/mm2)  ",compute="_compute_corrected_strength", digits=(12,4),store=True)
    compressive_parallel1 = fields.Float(string="Compressive Parallel to plane of Anisotropy (N/mm2)  ",compute="_compute_corrected_strength", digits=(12,4),store=True)



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

    @api.depends(
        'compressive_perpendiculer',
        'compressive_parallel',
        'hd_stone',
        'width_stone',
        'height_shape',
        'parent_id.wet_factor_a',
        'parent_id.wet_factor_b'
    )
    def _compute_corrected_strength(self):
        for rec in self:
            # सुरक्षितपणे parent factors घ्या
            a = rec.parent_id.wet_factor_a
            b = rec.parent_id.wet_factor_b

            ratio = (a + b * (rec.width_stone / rec.height_shape)) if rec.height_shape else 1

            if rec.hd_stone == 1:
                rec.compressive_perpendiculer1 = rec.compressive_perpendiculer
                rec.compressive_parallel1 = rec.compressive_parallel
            else:
                rec.compressive_perpendiculer1 = rec.compressive_perpendiculer / ratio if ratio else 0.0
                rec.compressive_parallel1 = rec.compressive_parallel / ratio if ratio else 0.0


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


class StoneNotes(models.Model):
    _name = "stone.notes"

    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


class LabOptionLine(models.Model):
    _name = 'stone.lab.line'
    _description = 'Lab Options'
    _rec_name = 'lab'  # Dropdown मध्ये हे नाव दिसेल

    lab = fields.Char(string="Lab ID")
    parent_id = fields.Many2one('mechanical.stones', string="Parent")














   

   

  



    


   



   
   

   
