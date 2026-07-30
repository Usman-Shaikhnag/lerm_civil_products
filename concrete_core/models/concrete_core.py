from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class ConcreteCore(models.Model):
    _name = "mechanical.concrete.core"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Concrete Core")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    sample_id = fields.Many2one('lerm.srf.sample',string='Sample')

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)


    

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'concrete.core.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    

    notes_id = fields.One2many('mechanical.concrete.core.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {'sr_no': 'i', 'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.'}),
            (0, 0, {'sr_no': 'ii', 'notes': 'This report is invalid without the official paper seal of Make Infracon.'}),
            (0, 0, {'sr_no': 'iii', 'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.'}),
            (0, 0, {'sr_no': 'iv', 'notes': 'Any discrepancies or complaints regarding this report must be communicated in writing within 7 days from the date of issue.'}),
            (0, 0, {'sr_no': 'v', 'notes': 'This report shall not be reproduced, except in full, without the prior written approval of Make Infracon.'}),
            (0, 0, {'sr_no': 'vi', 'notes': 'The laboratory assumes no responsibility for the purpose for which the test results are used or for any subsequent actions taken based on these results.'}),
        ]

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    def get_all_fields(self):
        record = self.env['mechanical.concrete.core'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing",compute="_compute_date_testing")

    @api.depends('eln_ref')
    def _compute_date_testing(self):
        if self.eln_ref:
            self.date_of_testing = self.eln_ref.date_testing

    
    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None



    # Water Permeability 					

    water_permeability_name = fields.Char(default="Water Permeability")
    water_permeability_visible = fields.Boolean(compute="_compute_visible")

    water_permeability_table = fields.One2many('core.water.penetration','parent_id',string="Water Permeability")


    average_depth = fields.Float(
        string="Average Depth of Penetration (mm)",
        compute="_compute_average",
        store=True,
    )

    @api.depends("water_permeability_table.average_depth")
    def _compute_average(self):
        for rec in self:
            if rec.water_permeability_table:
                rec.average_depth = sum(
                    rec.water_permeability_table.mapped("average_depth")
                ) / len(rec.water_permeability_table)
            else:
                rec.average_depth = 0.0


    average_depth_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_average_depth_confirmity")

    average_depth_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_average_depth_nabl",store=True)


    @api.depends('average_depth','eln_ref')
    def _compute_average_depth_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_depth_confirmity = 'na'
                continue
            record.average_depth_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','02145jj-eba3-4f15-b33d-679b39f73301')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','02145jj-eba3-4f15-b33d-679b39f73301')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_depth - record.average_depth*mu_value
                    upper = record.average_depth + record.average_depth*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_depth_confirmity = 'pass'
                        break
                    else:
                        record.average_depth_confirmity = 'fail'

    @api.depends('average_depth','eln_ref')
    def _compute_average_depth_nabl(self):
        
        for record in self:
            record.average_depth_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','02145jj-eba3-4f15-b33d-679b39f73301')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','02145jj-eba3-4f15-b33d-679b39f73301')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.average_depth - record.average_depth*mu_value
                  upper = record.average_depth + record.average_depth*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.average_depth_nabl = 'pass'
                      break
                  else:
                      record.average_depth_nabl = 'fail'


    water_permeability_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    water_permeability_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_water_permeability_final_report", store=True)

    @api.depends('average_depth_nabl', 'water_permeability_report_type')
    def _compute_water_permeability_final_report(self):
     for rec in self:

        # Manual override
        if rec.water_permeability_report_type == 'nabl':
            rec.water_permeability_final_report = 'nabl'

        elif rec.water_permeability_report_type == 'non_nabl':
            rec.water_permeability_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_depth_nabl == 'pass':
                rec.water_permeability_final_report = 'nabl'
            else:
                rec.water_permeability_final_report = 'non_nabl'



    # Compressive Strength
    compressive_strength_name = fields.Char(default="Compressive Strength")
    compressive_strength_visible = fields.Boolean(compute="_compute_visible")

    compressive_strength_table = fields.One2many('core.compressive.line','parent_id', string="Compressive Strength")

    avg_compressive_strength = fields.Float(string="Average Strength",compute="_compute_average_strength",store=True)

    @api.depends('compressive_strength_table.compressive_strength')
    def _compute_average_strength(self):
     for rec in self:
        values = rec.compressive_strength_table.mapped('compressive_strength')
        rec.avg_compressive_strength = (
            sum(values) / len(values) if values else 0.0
        )


    

    avg_compressive_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avg_compressive_strength_confirmity")

    avg_compressive_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avg_compressive_strength_nabl",store=True)


    @api.depends('avg_compressive_strength','eln_ref')
    def _compute_avg_compressive_strength_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_compressive_strength_confirmity = 'na'
                continue
            record.avg_compressive_strength_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254187-47c9-4662-9298-3095ac900ffc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254187-47c9-4662-9298-3095ac900ffc')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_compressive_strength_confirmity = 'pass'
                        break
                    else:
                        record.avg_compressive_strength_confirmity = 'fail'

    @api.depends('avg_compressive_strength','eln_ref')
    def _compute_avg_compressive_strength_nabl(self):
        
        for record in self:
            record.avg_compressive_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254187-47c9-4662-9298-3095ac900ffc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254187-47c9-4662-9298-3095ac900ffc')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                  upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avg_compressive_strength_nabl = 'pass'
                      break
                  else:
                      record.avg_compressive_strength_nabl = 'fail'


    compressive_strength_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    compressive_strength_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_compressive_strength_final_report", store=True)

    @api.depends('avg_compressive_strength_nabl', 'compressive_strength_report_type')
    def _compute_compressive_strength_final_report(self):
     for rec in self:

        # Manual override
        if rec.compressive_strength_report_type == 'nabl':
            rec.compressive_strength_final_report = 'nabl'

        elif rec.compressive_strength_report_type == 'non_nabl':
            rec.compressive_strength_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_compressive_strength_nabl == 'pass':
                rec.compressive_strength_final_report = 'nabl'
            else:
                rec.compressive_strength_final_report = 'non_nabl'



    
     

            ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.water_permeability_visible = False
            record.compressive_strength_visible = False
          
            
            for sample in record.sample_parameters:

                if sample.internal_id == "02145jj-eba3-4f15-b33d-679b39f73301":
                    record.water_permeability_visible = True


                if sample.internal_id == '254187-47c9-4662-9298-3095ac900ffc':
                    record.compressive_strength_visible = True
                
             

               
               



    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
        
            
            # Water Permeability
            if result.parameter.internal_id == '02145jj-eba3-4f15-b33d-679b39f73301':
                result.result_char = round(self.average_depth,2)
                result.calculated = True
                if self.average_depth_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compressive Strength
            if result.parameter.internal_id == '254187-47c9-4662-9298-3095ac900ffc':
                result.result_char = round(self.avg_compressive_strength,2)
                result.calculated = True
                if self.avg_compressive_strength_nabl == 'pass':
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
        record = super(ConcreteCore, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record
    

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()

        return super(ConcreteCore, self).read(fields=fields, load=load)







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
     
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)


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
        record = self.env['mechanical.concrete.core'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    



class CoreWaterPenetration(models.Model):
    _name = "core.water.penetration"
    _description = "Water Penetration Trial"

    parent_id = fields.Many2one('mechanical.concrete.core', string="Parent Id")

    serial_no = fields.Integer(string="Trial.No", readonly=True, copy=False, default=1)



    pressure = fields.Float(
        string="Water Pressure Applied (bar/kg/cm²)"
    )

    duration = fields.Float(
        string="Duration of Test (hrs)"
    )

    maximum_depth = fields.Float(
        string="Maximum Depth of Water Penetration (mm)"
    )

    average_depth = fields.Float(
        string="Average Depth of Penetration (mm)"
    )


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CoreWaterPenetration, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class CoreCompressiveLine(models.Model):
    _name = "core.compressive.line"
    parent_id = fields.Many2one('mechanical.concrete.core', string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)


    age = fields.Char(string="Age of Specimen")

    height = fields.Float("Height (mm)")
    diameter = fields.Float("Dia (mm)")

    hd_ratio = fields.Float(string="H/D Ratio (n)",compute="_compute_values",store=True)

    correction_factor = fields.Float(string="Correction factor f =0.11n+0.78 Where,  f= Correction factor,n= height to diameter ratio" , compute="_compute_values",store=True,digits=(12,3))

    area = fields.Float(string="Area (mm²) π r² ",compute="_compute_values",store=True,digits=(16,3))

    volume = fields.Float(string="Volume (cc) πr²h",compute="_compute_values",store=True)

    weight = fields.Float("Weight (gm)")

    density = fields.Float(
        string="Density (gm/cc)",
        compute="_compute_values",
        store=True,digits=(16,3)
    )

    load = fields.Float("Load (kN)")

    compressive_strength = fields.Float(
        string="Compressive Strength (N/mm²)",
        compute="_compute_values",
        store=True
    )

    corrected_compressive_strength = fields.Float(
        string="Corrected Compressive Strength (N/mm²)",
        compute="_compute_values",
        store=True
    )

    equivalent_cube_strength = fields.Float(
        string="Equivalent Cube strength (N/mm²)",
        compute="_compute_values",
        store=True
    )

    @api.depends(
        'height',
        'diameter',
        'weight',
        'load'
    )
    def _compute_values(self):

        for rec in self:

            # H/D Ratio
            if rec.diameter:
                rec.hd_ratio = rec.height / rec.diameter
            else:
                rec.hd_ratio = 0

            # Correction Factor
            # Use the formula if required
            rec.correction_factor = (
                (0.11 * rec.hd_ratio) + 0.78
                
            )

            # If you want exactly like Excel
            # uncomment below and remove above
            #
            # if rec.hd_ratio <= 2:
            #     rec.correction_factor = 1.00
            # else:
            #     rec.correction_factor = 1.01

            # Area
            if rec.diameter:
                rec.area = 3.14 * rec.diameter * rec.diameter / 4
            else:
                rec.area = 0

            # Volume
            rec.volume = (rec.area * rec.height) 

            # Density
            if rec.volume:
                rec.density = (rec.weight / rec.volume) * 1000
            else:
                rec.density = 0

            # Compressive Strength
            if rec.area:
                rec.compressive_strength = (
                    rec.load  / rec.area) * 1000
            else:
                rec.compressive_strength = 0

            # Corrected Compressive Strength
            if rec.correction_factor:
                rec.corrected_compressive_strength = (
                    rec.compressive_strength  * rec.correction_factor)
            else:
                rec.corrected_compressive_strength = 0


            # Equivalent Cube Strength
            if rec.corrected_compressive_strength:
                rec.equivalent_cube_strength = (
                    rec.corrected_compressive_strength)  * (5/4)
            else:
                rec.equivalent_cube_strength = 0

    
   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CoreCompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
   



   
class ConcreteCoreNotes(models.Model):
    _name = "mechanical.concrete.core.notes"

    parent_id = fields.Many2one('mechanical.concrete.core', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
