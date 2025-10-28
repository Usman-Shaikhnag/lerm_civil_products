from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
from statistics import mean


class CementNormalConsistency(models.Model):
    _name = "cement.opc"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Cement")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id
    start_date = fields.Date(string="Start Date", compute="_compute_start_date", store=True)

    @api.depends('eln_ref.start_date')
    def _compute_start_date(self):
        for rec in self:
            rec.start_date = rec.eln_ref.start_date


  
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


   

        ## Density of Cement (Le-Chatlier Flask)

    density_cement_name = fields.Char("Name",default="Density of Cement (Le-Chatlier Flask)")
    density_cement_visible = fields.Boolean("Density of Cement (Le-Chatlier Flask) Visible",compute="_compute_visible")

    temp_specific = fields.Float("Temp.°C")
    humidity_specific= fields.Float("Humidity %")

    temp_water1 = fields.Float("Temperature of Water Bath  when Flask kept in bath – 0C")
    temp_water2 = fields.Float("Temperature of Water Bath  when Flask kept in bath – 0C")

    temp_water_after1 = fields.Float("Temperature of Water Bath  after One Hour when Flask kept in bath – 0C  ")
    temp_water_after2 = fields.Float("Temperature of Water Bath  after One Hour when Flask kept in bath – 0C  )")

    initial_kerosene1 = fields.Float("Initial Level of Kerosene after one hour kept in Water Bath(A) – ml")
    initial_kerosene2 = fields.Float("Initial Level of Kerosene after one hour kept in Water Bath(A) – ml")

    mass1 = fields.Float("Mass of Cement Sample Added in Flask (M) – gms")
    mass2 = fields.Float("Mass of Cement Sample Added in Flask (M) – gms")

    temp_water_flask1 = fields.Float("Temperature of water bath  when Flask kept in bath after Adding Cement – 0C")
    temp_water_flask2 = fields.Float("Temperature of water bath  when Flask kept in bath after Adding Cement – 0C")

    temp_water_one1 = fields.Float("Temperature of water bath  after one hour when Flask kept in bath after Adding Cement – 0C")
    temp_water_one2 = fields.Float("Temperature of water bath  after one hour when Flask kept in bath after Adding Cement – 0C")


    final_kerosene1 = fields.Float("Final Level of Kerosene after one hour kept in water bath(B) – ml")
    final_kerosene2 = fields.Float("Final Level of Kerosene after one hour kept in water bath(B) – ml")

    displaced1 = fields.Float("Displaced Volume after Adding Cement (V) = (B – A) – cm3", store=True, digits=(12, 2))
    displaced2 = fields.Float("Displaced Volume after Adding Cement (V) = (B – A) – cm3", store=True, digits=(12, 2))

    density1 = fields.Float("Density of Cement Sample (    ) – gms/ cm3", store=True, digits=(12, 2),compute="_compute_values")
    density2 = fields.Float("Density of Cement Sample (    ) – gms/ cm3", store=True, digits=(12, 2),compute="_compute_values")


    avg_density = fields.Float(string="Average Density of Cement Sample – gms/ cm3",compute="_compute_avg_density",store=True)

    @api.depends(
        'initial_kerosene1', 'final_kerosene1',
        'initial_kerosene2', 'final_kerosene2',
        'mass1', 'mass2'
    )
    def _compute_values(self):
        for rec in self:
            # --- Displaced volume calculations ---
            rec.displaced1 = (rec.final_kerosene1 or 0.0) - (rec.initial_kerosene1 or 0.0)
            rec.displaced2 = (rec.final_kerosene2 or 0.0) - (rec.initial_kerosene2 or 0.0)

            # --- Density calculations ---
            rec.density1 = (rec.mass1 / rec.displaced1) if rec.displaced1 else 0.0
            rec.density2 = (rec.mass2 / rec.displaced2) if rec.displaced2 else 0.0

    @api.depends('density1', 'density2')
    def _compute_avg_density(self):
        for rec in self:
            # ensure no division by zero
            d1 = rec.density1 or 0.0
            d2 = rec.density2 or 0.0

            # compute average only if at least one density exists
            if d1 and d2:
                rec.avg_density = (d1 + d2) / 2
            else:
                rec.avg_density = 0.0

    # specific_gravity = fields.Float(string="Specific Gravity of Cement",compute="_compute_cement_specific")

    avg_density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_density_conformity")

    avg_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_density_nabl")


    @api.depends('avg_density','eln_ref','grade')
    def _compute_avg_density_conformity(self):
        for record in self:
            record.avg_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254gt2547-372f-4775-9bcb-e9dd70e3587g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254gt2547-372f-4775-9bcb-e9dd70e3587g')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_density - record.avg_density*mu_value
                    upper = record.avg_density + record.avg_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_density_conformity = 'pass'
                        break
                    else:
                        record.avg_density_conformity = 'fail'

    @api.depends('avg_density','eln_ref','grade')
    def _compute_avg_density_nabl(self):
        
        for record in self:
            record.avg_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254gt2547-372f-4775-9bcb-e9dd70e3587g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254gt2547-372f-4775-9bcb-e9dd70e3587g')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_density - record.avg_density*mu_value
            upper = record.avg_density + record.avg_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_density_nabl = 'pass'
                break
            else:
                record.avg_density_nabl = 'fail'

  


  
        ## Consistency of cement

    consistency_cement_name = fields.Char("Name",default="Consistency of cement")
    consistency_cement_visible = fields.Boolean("Consistency of cement Visible",compute="_compute_visible")

    consistency_cement_lines = fields.One2many('consistensy.cement.line','parent_id',string="Consistency")

   


     ### setting Time,Final Setting Time	


    intial_time_lines = fields.One2many('initial.time.line','parent_id',string="Initial Time")


    initial_setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")
    initial_setting_time_name = fields.Char("Name",default="Setting Time")

    


   

                ## Cement Compressive Strength

    # compressive_name = fields.Char("Name",default="Cement Compressive Strength")
    # compressive_visible = fields.Boolean("Cement Compressive Strength Visible",compute="_compute_visible")


   
      

            
    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.density_cement_visible = False
            record.consistency_cement_visible = False
            record.initial_setting_time_visible = False
         
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '254gt2547-372f-4775-9bcb-e9dd70e3587g':
                    record.density_cement_visible = True

                

               
                if sample.internal_id == '3214578nbhgt2-372f-4775-9bcb-e9dd723547htui':
                    record.consistency_cement_visible = True


                if sample.internal_id == '40ce7425-30fe-4043-b518-015f5c60d916':
                    record.initial_setting_time_visible = True

               

             
             

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
         
            if result.parameter.internal_id == '254gt2547-372f-4775-9bcb-e9dd70e3587g':
                result.result_char = round(self.avg_density,2)
                if self.avg_density_nabl == 'pass':
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
        record = super(CementNormalConsistency, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    # @api.model 
    # def write(self, values):
    #     # Perform additional actions or validations before update
    #     result = super(CementNormalConsistency, self).write(values)
    #     # Perform additional actions or validations after update
    #     return result
    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['cement.opc'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value
        return field_values








class ConsistencyCementLine(models.Model):
    _name = "consistensy.cement.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

    serial_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    lab_id = fields.Char(string="Lab ID ")

    trial_no = fields.Integer(string="Trial No.")

   
    
    mass_of_cement = fields.Float(string="Mass of Cement Taken gms.")
    water_added = fields.Float(string="Water Added ml")
    water_mix = fields.Float(string="% Water",compute="_compute_water_mix",store=True)
    needle_penitration = fields.Float(string="Penetration from Bottom of Mould mm")

    @api.depends('mass_of_cement', 'water_added')
    def _compute_water_mix(self):
        for rec in self:
            if rec.mass_of_cement:
                rec.water_mix = (rec.water_added / rec.mass_of_cement) * 100
            else:
                rec.water_mix = 0.0


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsistencyCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

# class SettingTimetLine(models.Model):
#     _name = "setting.time.ssl.line"
#     parent_id = fields.Many2one('cement.opc',string="Parent Id")

#     serial_no = fields.Char(string="Test NO")

   
    
#     wt_of_cements1 = fields.Float(string="Wt of cement in gms")
#     wt_of_water1 = fields.Float(string="wt of water in ml" ,compute="_compute_wt_of_water1")
#     water_mix1 = fields.Char(string="% of water mix")
#     needle_penitration1 = fields.Char(string="Needle penetration in mm")
#     duration1 = fields.Float(string="Duration of time in minutes")

   

#     @api.depends('wt_of_cements1', 'parent_id.consitency_of_cement')
#     def _compute_wt_of_water1(self):
#         for rec in self:
#             if rec.wt_of_cements1 and rec.parent_id.consitency_of_cement:
#                 rec.wt_of_water1 = rec.wt_of_cements1 * 0.85 * rec.parent_id.consitency_of_cement / 100
#             else:
#                 rec.wt_of_water1 = 0.0





class InitialTimeLine(models.Model):
    _name = "initial.time.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)

    lab_id = fields.Char(string="LAB ID")

   
    
    time_water_t1 = fields.Datetime(string="Time at which water is first added to cement, t1, mins")
    time_needle_t2 = fields.Datetime(string="Time when needle fails to penetrate 5 +/-0.5 mm from bottom of the mould, t2 ,mins")
    time_needle_t3 = fields.Datetime(string="Time when the needle makes an impression but the attachment fails to do so, t3, mins")
    initial = fields.Float(string="Initial setting time, min (t2-t1)",compute="_compute_setting_times",store=True)
    final = fields.Float(string="Final setting time, min (t3-t1)",compute="_compute_setting_times",store=True)


    @api.depends('time_water_t1', 'time_needle_t2', 'time_needle_t3')
    def _compute_setting_times(self):
        for rec in self:
            rec.initial = 0.0
            rec.final = 0.0
            if rec.time_water_t1 and rec.time_needle_t2:
                t1 = rec.time_water_t1
                t2 = rec.time_needle_t2
                # Handle midnight crossover
                if t1 > t2:
                    t2 = t2.replace(day=t2.day + 1)
                rec.initial = (t2 - t1).total_seconds() / 60  # Convert seconds to minutes

            if rec.time_water_t1 and rec.time_needle_t3:
                t1 = rec.time_water_t1
                t3 = rec.time_needle_t3
                # Handle midnight crossover
                if t1 > t3:
                    t3 = t3.replace(day=t3.day + 1)
                rec.final = (t3 - t1).total_seconds() / 60

    


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(InitialTimeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1










  