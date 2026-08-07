from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math




class BitumenConcrete(models.Model):
    _name = "mechanical.bitumen.mix"
    _inherit = "lerm.eln"
    _rec_name = "name_bitumen"


    name_bitumen = fields.Char("Name",default="Bituminous Mix")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id


    
    # Sieve Analysis 
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")


    report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    sieve_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_sieve_nabl",
    store=True
)

    @api.depends('report_type')
    def _compute_sieve_nabl(self):
     for rec in self:
        rec.sieve_nabl = 'pass' if rec.report_type == 'nabl' else 'fail'


    sieve_analysis_child_lines = fields.One2many('mechanical.bitumen.mix.sieve.line','parent_id',string="Parameter"
)

    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")

    wt_of_sample = fields.Float(string="Weight of Sample, gms")
    material_type = fields.Selection([
        ('bm', 'BM'),
        ('dbm', 'DBM'),
        ('bc', 'BC')
    ], string="Type of Material")


    @api.onchange('wt_of_aggregate')
    def _onchange_set_sample_weight(self):
        for record in self:
            record.wt_of_sample = record.wt_of_aggregate

    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))



    @api.onchange('grade')
    def _onchange_grade_set_sieve_lines(self):
        for rec in self:
            sieve_lines = []
            grade_name = rec.grade.grade if rec.grade else ""

            if grade_name == "Grade 1":
                sieve_sizes =[
            '45 mm',
            '37.5 mm',
            '26.5 mm',
            '19 mm',
            '13.2 mm',
            '11.2 mm',
            '9.5 mm',
            '6.3 mm',
            '5.6 mm',
            '4.75 mm',
            '3.35 mm',
            '2.80 mm',
            '2.36 mm',
            '1.18 mm',
            '0.600 mm',
            '0.300 mm',
            '0.150 mm',
            '0.090 mm',
            '0.075 mm',
            'Pan',
        ]
            elif grade_name == "Grade 2":
                sieve_sizes = [
            '45 mm',
            '37.5 mm',
            '26.5 mm',
            '19 mm',
            '13.2 mm',
            '11.2 mm',
            '9.5 mm',
            '6.3 mm',
            '5.6 mm',
            '4.75 mm',
            '3.35 mm',
            '2.80 mm',
            '2.36 mm',
            '1.18 mm',
            '0.600 mm',
            '0.300 mm',
            '0.150 mm',
            '0.090 mm',
            '0.075 mm',
            'Pan',
        ]
            
            else:
                sieve_sizes = []

            for i, size in enumerate(sieve_sizes, start=1):
                sieve_lines.append((0, 0, {
                    'serial_no': i,
                    'sieve_size': size,
                    'specific_limt': ''  # blank initially
                }))

            rec.sieve_analysis_child_lines = sieve_lines


   
    @api.onchange('grade', 'material_type')
    def _onchange_set_specific_limits(self):
        for rec in self:
            grade_name = rec.grade.grade if rec.grade else ""
            material_type = rec.material_type if rec.material_type else ""

            limits = []

            if material_type == "bm":
                if grade_name == "Grade 1":
    
                    limits = [
                   '100','90-100','75-100','-','35-61','-','-','-','-','13-22','-','-','4-19','-','-','2-10','-','-','0-8',''
                   ]
                elif grade_name == "Grade 2":
                    limits = [
                    '-','-','100','90-100','56-88','-','-','-','-','16-36','-','-','4-19','-','-','2-10','-','-','0-8',''
                    ]

            elif material_type == "dbm":
                if grade_name == "Grade 1":
                    limits = [
                   '100',      # 45
                   '95-100',   # 37.5
                   '63-93',    # 26.5
                   '-',        # 19
                   '55-75',    # 13.2
                   '-',        # 11.2
                   '-',        # 9.5
                   '-',        # 6.3
                   '-',        # 5.6
                   '38-54',    # 4.75
                   '-',        # 3.35
                   '-',        # 2.80
                   '28-42',    # 2.36
                   '-',        # 1.18
                   '-',        # 0.600
                   '7-21',     # 0.300
                   '-',        # 0.150
                   '-',        # 0.090
                   '2-8',      # 0.075
                   '',         # Pan
                ]
                elif grade_name == "Grade 2":
                    limits = [
                   '-',        # 45
                   '100',      # 37.5
                   '90-100',   # 26.5
                   '71-95',    # 19
                   '56-80',    # 13.2
                   '-',        # 11.2
                   '-',        # 9.5
                   '-',        # 6.3
                   '-',        # 5.6
                   '38-54',    # 4.75
                   '-',        # 3.35
                   '-',        # 2.80
                   '28-42',    # 2.36
                   '-',        # 1.18
                   '-',        # 0.600
                   '7-21',     # 0.300
                   '-',        # 0.150
                   '-',        # 0.090
                   '2-8',      # 0.075
                   '',         # Pan
                   ]

            elif material_type == "bc":
                if grade_name == "Grade 1":
                    limits = [
                    '-',        # 45
                    '-',        # 37.5
                    '100',      # 26.5
                    '90-100',   # 19
                    '59-79',    # 13.2
                    '-',        # 11.2
                    '52-72',    # 9.5
                    '-',        # 6.3
                    '-',        # 5.6
                    '35-55',    # 4.75
                    '-',        # 3.35
                    '-',        # 2.80
                    '28-44',    # 2.36
                    '20-34',    # 1.18
                    '15-27',    # 0.600
                    '10-20',    # 0.300
                    '5-13',     # 0.150
                    '-',        # 0.090
                    '2-8',      # 0.075
                    '',         # Pan
                    ]
                elif grade_name == "Grade 2":
                    limits = [
                    '-',        # 45
                    '-',        # 37.5
                    '-',        # 26.5
                    '100',      # 19
                    '90-100',   # 13.2
                    '-',        # 11.2
                    '70-88',    # 9.5
                    '-',        # 6.3
                    '-',        # 5.6
                    '53-71',    # 4.75
                    '-',        # 3.35
                    '-',        # 2.80
                    '42-58',    # 2.36
                    '34-48',    # 1.18
                    '26-38',    # 0.600
                    '18-28',    # 0.300
                    '12-20',    # 0.150
                    '-',        # 0.090
                    '4-10',     # 0.075
                    '',         # Pan
                    ]

            

            # Assign limits to sieve lines
            for i, line in enumerate(rec.sieve_analysis_child_lines):
                if i < len(limits):
                    line.specific_limt = limits[i]
                else:
                    line.specific_limt = ''


    
 

    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            lines = rec.sieve_analysis_child_lines
            pan_index = -1

            # Find index of 'Pan'
            for i, line in enumerate(lines):
                if line.sieve_size and line.sieve_size.strip().lower() == 'pan':
                    pan_index = i
                    break

            if pan_index != -1:
                pan_line = lines[pan_index]

                # Sum of wt_retained of all lines before pan
                total_above = sum(l.wt_retained or 0.0 for l in lines[:pan_index])

                pan_line.wt_retained = (rec.wt_of_sample or 0.0) - total_above


   

    def calculate_sieve(self): 
        for record in self:
            previous_cumulative = 0.0  
            for line in record.sieve_analysis_child_lines:
                previous_line = line.serial_no - 1

                if previous_line == 0:
                    cumulative_retained = line.percent_retained or 0.0
                else:
                    previous_line_record = self.env['mechanical.bitumen.mix.sieve.line'].sudo().search([
                        ("serial_no", "=", previous_line),
                        ("parent_id", "=", record.id)
                    ], limit=1)

                    if previous_line_record:
                        previous_cumulative = previous_line_record.cumulative_retained or 0.0

                    cumulative_retained = previous_cumulative + (line.percent_retained or 0.0)

                passing_percent = 100.0 - cumulative_retained

                line.write({
                    'cumulative_retained': cumulative_retained,
                    'passing_percent': passing_percent,
                })

                print("Updated Cumulative Retained:", cumulative_retained)
                print("Updated Passing Percent:", passing_percent)

                previous_cumulative = cumulative_retained

            
    


    
    
    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))





    # Flow Value Test
    flow_value_name = fields.Char("Name",default="Flow Value Test")
    flow_value_visible = fields.Boolean("Flow Value Test Visible",compute="_compute_visible")

    flow_value_child_lines = fields.One2many('bitumen.mix.flow.value.line','parent_id',string="Parameter")


    average_flow = fields.Float(
        string="Average Flow Value",
        compute="_compute_average_flow",
        store=True
    )

    @api.depends('flow_value_child_lines.flow_value')
    def _compute_average_flow(self):
        for rec in self:
            values = rec.flow_value_child_lines.mapped('flow_value')
            rec.average_flow = sum(values) / len(values) if values else 0.0


    average_flow_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_average_flow_conformity", store=True)

    @api.depends('average_flow','eln_ref','grade')
    def _compute_average_flow_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_flow_conformity = 'na'
                continue
            record.average_flow_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35789ght-7188-4086-b132-62b50e63f1247ui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35789ght-7188-4086-b132-62b50e63f1247ui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_flow - record.average_flow*mu_value
                    upper = record.average_flow + record.average_flow*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_flow_conformity = 'pass'
                        break
                    else:
                        record.average_flow_conformity = 'fail'

    average_flow_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_flow_nabl", store=True)

    @api.depends('average_flow','eln_ref','grade')
    def _compute_average_flow_nabl(self):
        
        for record in self:
            record.average_flow_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35789ght-7188-4086-b132-62b50e63f1247ui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35789ght-7188-4086-b132-62b50e63f1247ui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_flow - record.average_flow*mu_value
                    upper = record.average_flow + record.average_flow*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_flow_nabl = 'pass'
                        break
                    else:
                        record.average_flow_nabl = 'fail'


    flow_value_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    flow_value_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_flow_value_final_report", store=True)
    
    @api.depends('average_flow_nabl', 'flow_value_report_type')
    def _compute_flow_value_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.flow_value_report_type == 'nabl':
                rec.flow_value_final_report = 'nabl'
    
            elif rec.flow_value_report_type == 'non_nabl':
                rec.flow_value_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.average_flow_nabl == 'pass':
                    rec.flow_value_final_report = 'nabl'
                else:
                    rec.flow_value_final_report = 'non_nabl'



    





         ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
      
            record.sieve_visible = False
            record.flow_value_visible = False
           
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "62578gtre-7188-4086-b132-62b50e63f1247ui":
                    record.sieve_visible = True

                if sample.internal_id == "35789ght-7188-4086-b132-62b50e63f1247ui":
                    record.flow_value_visible = True

                

   

    def open_eln_page(self):

        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        if current_user.has_group('lerm_civil.lerm_discipline_group'):
            technician_results = self.eln_ref.parameters_result
        else:
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:
            internal_id = result.parameter.internal_id


            # Flow Value
            if result.parameter.internal_id == '35789ght-7188-4086-b132-62b50e63f1247ui':
                result.result_char = round(self.average_flow,2)
                result.calculated = True
                if self.average_flow_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


         # Sieve Analysis
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '62578gtre-7188-4086-b132-62b50e63f1247ui':
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
        record = super(BitumenConcrete, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







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
        record = self.env['mechanical.bitumen.mix'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    notes_id = fields.One2many('mechanical.bitumen.mix.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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





class SieveAnalysisLine(models.Model):
    _name = "mechanical.bitumen.mix.sieve.line"
    parent_id = fields.Many2one('mechanical.bitumen.mix', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Weight Retained (gms)")
    percent_retained = fields.Float(string='% of Weight Retained', compute="_compute_percent_retained",digits=(12,2))
    cumulative_retained = fields.Float(string="% of Cumulative Wt.  Retained ", compute="_compute_cum_retained", store=True,digits=(12,2))
    passing_percent = fields.Float(string="% of wt passing",digits=(12,2))
    specific_limt = fields.Char(string="Specified Limits")



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SieveAnalysisLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def write(self, vals):
        # Handle row deletions and adjust serial numbers
        if 'parent_id' in vals or 'wt_retained' in vals:
            for record in self:
                if record.parent_id and record.parent_id == vals.get('parent_id') and 'wt_retained' in vals:
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(SieveAnalysisLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SieveAnalysisLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SieveAnalysisLine, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()

        return res

# wt_of_sample
    # @api.depends('wt_retained', 'parent_id.total_sieve_analysis')
    # def _compute_percent_retained(self):
    #     for record in self:
    #         try:
    #             record.percent_retained = record.wt_retained / self.parent_id.total_sieve_analysis * 100
    #         except ZeroDivisionError:
    #             record.percent_retained = 0 

    @api.depends('wt_retained', 'parent_id.wt_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / record.parent_id.wt_of_sample) * 100 if record.parent_id.wt_of_sample else 0.0
            except ZeroDivisionError:
                record.percent_retained = 0.0



    # @api.depends('cumulative_retained')
    # def _compute_cum_retained(self):
    #     self.cumulative_retained=0

    @api.depends('percent_retained', 'parent_id.sieve_analysis_child_lines.percent_retained')
    def _compute_cum_retained(self):
        for record in self:
            cumulative = 0.0
            found = False

            for line in sorted(record.parent_id.sieve_analysis_child_lines, key=lambda l: l.serial_no):
                cumulative += line.percent_retained or 0.0
                if line.id == record.id:
                    found = True
                    record.cumulative_retained = cumulative
                    break

            if not found:
                record.cumulative_retained = 0.0

        
    


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")


class BitumenMixFlowValueLine(models.Model):
    _name = "bitumen.mix.flow.value.line"
    parent_id = fields.Many2one('mechanical.bitumen.mix', string="Parent Id")
    
    serial_no = fields.Integer(string="Specimen. No", readonly=True, copy=False, default=1)

    diameter = fields.Float(string="Diameter (mm)")

    height = fields.Float(string="Height (mm)")

    maximum_load = fields.Float(string="Maximum Load (kN)")

    flow_reading = fields.Integer(string="Flow Reading (0.25 mm units)")

    flow_value = fields.Float(string="Flow Value (mm)",compute="_compute_flow_value",store=True)


    @api.depends('flow_reading')
    def _compute_flow_value(self):
        for rec in self:
            rec.flow_value = rec.flow_reading * 0.25





    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(BitumenMixFlowValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





class BitumenConcreteNotes(models.Model):
    _name = "mechanical.bitumen.mix.notes"

    parent_id = fields.Many2one('mechanical.bitumen.mix', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
