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

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id


    # 1. Bitumen Content

    location = fields.Char(string="Location:")

    location_heding = fields.Char(string="Heding")

    @api.onchange('location')
    def _onchange_location_set_heading(self):
        for rec in self:
            rec.location_heding = rec.location


    bitumen_content_name = fields.Char("Name",default="Bitumen Content")
    bitumen_content_visible = fields.Boolean("Bitumen Content",compute="_compute_visible")


    wt_of_samplew1 = fields.Float(string="Weight of the sample (W1)")
    wt_of_intial = fields.Float(string="Initial weight of the filter paper (F1)")
    wt_of_aggregate = fields.Float(string="Weight of aggregate after extraction (W2)")
    wt_of_extraction = fields.Float(string="Weight of filter paper after extraction with fine materials (F2)")
    wt_of_filter = fields.Float(string="Increased weight of filter W3 = (F2-F1)",compute="_compute_wt_of_filter",store=True,digits=(12,1))

    binder_content = fields.Float(string="% Binder content",compute="_compute_binder_content",digits=(12,2),store=True)

    binder_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_binder_content_conformity", store=True)

    @api.depends('binder_content','eln_ref','grade')
    def _compute_binder_content_conformity(self):
        
        for record in self:
            record.binder_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35789ght-7188-4086-b132-62b50e63f1247ui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35789ght-7188-4086-b132-62b50e63f1247ui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.binder_content - record.binder_content*mu_value
                    upper = record.binder_content + record.binder_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.binder_content_conformity = 'pass'
                        break
                    else:
                        record.binder_content_conformity = 'fail'

    binder_content_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_binder_content_nabl", store=True)

    @api.depends('binder_content','eln_ref','grade')
    def _compute_binder_content_nabl(self):
        
        for record in self:
            record.binder_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35789ght-7188-4086-b132-62b50e63f1247ui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35789ght-7188-4086-b132-62b50e63f1247ui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.binder_content - record.binder_content*mu_value
                    upper = record.binder_content + record.binder_content*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.binder_content_nabl = 'pass'
                        break
                    else:
                        record.binder_content_nabl = 'fail'

    @api.depends('wt_of_extraction', 'wt_of_intial')
    def _compute_wt_of_filter(self):
        for rec in self:
            if rec.wt_of_extraction and rec.wt_of_intial:
                rec.wt_of_filter = rec.wt_of_extraction - rec.wt_of_intial
            else:
                rec.wt_of_filter = 0.0

    @api.depends('wt_of_samplew1', 'wt_of_aggregate', 'wt_of_filter')
    def _compute_binder_content(self):
        for rec in self:
            if rec.wt_of_samplew1:
                rec.binder_content = ((rec.wt_of_samplew1 - (rec.wt_of_aggregate + rec.wt_of_filter)) / rec.wt_of_samplew1) * 100
            else:
                rec.binder_content = 0.0


  


    # Sieve Analysis 
    sieve_analysis_name = fields.Char("Name",default="Gradation")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.bitumen.mix.sieve.line','parent_id',string="Parameter")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")
    wt_of_sample = fields.Float(string="Weight of Sample, gms")

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

            if grade_name == "Bituminous Macadam":
                sieve_sizes = ['45 mm', '37.5 mm', '26.5 mm', '19 mm', '13.2 mm',
                            '4.75 mm', '2.36 mm', '300 μm', '75 μm', '0', '0', 'Pan']
            elif grade_name == "Dense Graded Bituminous Macadam":
                sieve_sizes = ['45 mm', '37.5 mm', '26.5 mm', '19 mm', '13.2 mm',
                            '4.75 mm', '2.36 mm', '300 μm', '75 μm', '0', '0', 'Pan']
            elif grade_name == "Semi Dense Bituminous Concrete":
                sieve_sizes = ['19 mm', '13.2 mm', '9.5 mm', '4.75 mm', '2.36 mm',
                            '1.18 mm', '300 μm', '75 μm', '0', '0', '0', 'Pan']
            elif grade_name == "Bituminous Concrete":
                sieve_sizes = ['26.5 mm', '19 mm', '13.2 mm', '9.5 mm', '4.75 mm',
                            '2.36 mm', '1.18 mm', '600 μm', '300 μm', '150 μm', '75 μm', 'Pan']
            elif grade_name == "Mixed Seal Surfacing":
                sieve_sizes = ['13.2 mm', '11.2 mm', '5.6 mm', '2.8 mm', '90 μm',
                            '0', '0', '0', '0', '0', '0', 'Pan']
            elif grade_name == "Open Graded Premix Surfacing":
                sieve_sizes = ['13.2 mm', '11.2 mm', '5.6 mm', '2.8 mm', '90 μm',
                            '0', '0', '0', '0', '0', '0', 'Pan']
            else:
                sieve_sizes = []

            for i, size in enumerate(sieve_sizes, start=1):
                sieve_lines.append((0, 0, {
                    'serial_no': i,
                    'sieve_size': size,
                    'specific_limt': ''  # blank initially
                }))

            rec.sieve_analysis_child_lines = sieve_lines


   
    @api.onchange('grade', 'size_id')
    def _onchange_set_specific_limits(self):
        for rec in self:
            grade_name = rec.grade.grade if rec.grade else ""
            size_value = rec.size_id.size if rec.size_id else ""

            limits = []

            if grade_name == "Bituminous Macadam":
                if size_value == "1":
                    limits = [
                        '100',
                        '90 - 100',
                        '75 - 100',
                        '-',
                        '35 - 61',
                        '13 - 22',
                        '4 - 19',
                        '2 - 10',
                        '0 - 8',
                        '0',
                        '0',
                        '0',
                    ]
                elif size_value == "2":
                    limits = [
                        '-',
                        '-',
                        '100',
                        '90 - 100',
                        '56 - 88',
                        '16 - 36',
                        '4 - 19',
                        '2 - 10',
                        '0 - 8',
                        '0',
                        '0',
                        '0',
                    ]

            elif grade_name == "Dense Graded Bituminous Macadam":
                if size_value == "1":
                    limits = [
                        '100',
                        '90 - 100',
                        '63 - 93',
                        '-',
                        '55 - 75',
                        '38 - 54',
                        '28 - 42',
                        '7 -- 21',
                        '2 -- 8',
                        '0',
                        '0',
                        '0',
                    ]
                elif size_value == "2":
                    limits = [
                        '-',
                        '100',
                        '90 - 100',
                        '71 - 95',
                        '56 - 80',
                        '38 - 54',
                        '28 - 42',
                        '7 -- 21',
                        '2 -- 8',
                        '0',
                        '0',
                        '0',
                    ]

            elif grade_name == "Semi Dense Bituminous Concrete":
                if size_value == "1":
                    limits = [
                        '100',
                        '90 - 100',
                        '70 - 90',
                        '35 - 51',
                        '24 - 39',
                        '15 - 30',
                        '9 -- 19',
                        '3 -- 8',
                        '0',
                        '0',
                        '0',
                        '0',
                    ]
                elif size_value == "2":
                    limits = [
                        '-',
                        '100',
                        '90 - 100',
                        '35 - 51',
                        '24 - 39',
                        '15 - 30',
                        '9 -- 19',
                        '3 -- 8',
                        '0',
                        '0',
                        '0',
                        '0',
                    ]

            elif grade_name == "Bituminous Concrete":
                if size_value == "1":
                    limits = [
                        '100',
                        '90 - 100',
                        '59 - 79',
                        '52 - 72',
                        '35 - 55',
                        '28 - 44',
                        '20 - 34',
                        '15 - 27',
                        '10 -- 20',
                        '5 -- 13',
                        '2 -- 8',
                        '0',
                    ]
                elif size_value == "2":
                    limits = [
                        '-',
                        '100',
                        '90 - 100',
                        '70 - 88',
                        '53 - 71',
                        '42 - 58',
                        '34 - 48',
                        '26 - 38',
                        '18 - 28',
                        '12 -- 20',
                        '4 -- 10',
                        '0',
                    ]

            elif grade_name == "Mixed Seal Surfacing":
                if size_value == "1":
                    limits = [
                        '-',
                        '100',
                        '52 - 88',
                        '14 - 38',
                        '0 - 5',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                    ]
                elif size_value == "2":
                    limits = [
                        '100',
                        '88 - 100',
                        '31 - 52',
                        '5 - 25',
                        '0 - 5',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                    ]

            elif grade_name == "Open Graded Premix Surfacing":
                if size_value == "1":
                    limits = [
                        '--',
                        '100',
                        '52 - 88',
                        '14 - 38',
                        '0 - 5',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                    ]
                elif size_value == "2":
                    limits = [
                        '100',
                        '88 - 100',
                        '31 - 52',
                        '5 - 25',
                        '0 - 5',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
                        '0',
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





         ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
      
            record.sieve_visible = False
            record.bitumen_content_visible = False
           
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "62578gtre-7188-4086-b132-62b50e63f1247ui":
                    record.sieve_visible = True

                if sample.internal_id == "35789ght-7188-4086-b132-62b50e63f1247ui":
                    record.bitumen_content_visible = True

                

            
              
    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '35789ght-7188-4086-b132-62b50e63f1247ui':
                result.result_char = round(self.binder_content,2)
                if self.binder_content_nabl == 'pass':
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
        record = super(BitumenConcrete, self).create(vals)
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