from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class BituminousMechanical(models.Model):
    _name = "ssl.bituminous"
    _inherit = "lerm.eln"
    _description = 'SSL Bituminous'
    _rec_name = "name"

    name = fields.Char("Name",default="Bituminous")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id


    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(BituminousMechanical, self).create(vals)
        record.eln_ref.write({'model_id':record.id})
        return record
    

    def default_get(self, fields):
        print("From Default Value")
        res = super(BituminousMechanical, self).default_get(fields)

        sieve_mapping = {
            63: ['80 mm', '63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
            40: ['63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
            20: ['40 mm', '20 mm', '10 mm', '4.75 mm', 'pan'],
            16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
            12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
            10: ['12.5 mm', '10 mm', '4.75 mm', '2.36 mm', 'pan'],
        }

        default_sieve_sizes = []
        eln_ref = res['eln_ref']

        if eln_ref:
            eln = self.env['lerm.eln'].sudo().browse(eln_ref)
            size_str = eln.size_id.size or ''
            print("Size:", size_str)

            # Extract numeric part
            match = re.search(r'\d+', size_str)
            if match:
                number = int(match.group())
                print("Number:", number)

                # Find matching sieve list by size
                sieve_list = sieve_mapping.get(number)
                if sieve_list:
                    for sieve_size in sieve_list:
                        size = {
                            'sieve_size': sieve_size
                        }
                        default_sieve_sizes.append((0, 0, size))
                    res['sieve_analysis_child_lines'] = default_sieve_sizes

        return res


    

    # Combined Gradation 
    weight_of_sample = fields.Float(string="Weight of Sample in kg")
    combined_gradation_name = fields.Char("Name",default="Combined Gradation ")
    combined_gradation_visible = fields.Boolean("Combined Gradation Visible",compute="_compute_visible")

    combined_gradation_child_lines = fields.One2many('ssl.bituminous.combined.gradation.line','parent_id',string="Parameter")
    total_combined_gradation = fields.Float(string="Total",compute="_compute_total_combined_gradation")
			
    bitumen_content_name = fields.Char("Name",default="Bitumen Content")
    bitumen_content_visible = fields.Boolean("Bitumen Content Visible",compute="_compute_visible")


    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            record.combined_gradation_visible = False

            for sample in record.sample_parameters:
                if sample.internal_id == '1afda8c1-5045-494a-aec3-29bd5f2ddade':
                    record.combined_gradation_visible = True
                if sample.internal_id == '661bebd2-0149-40f9-93ea-615408b61835':
                    record.bitumen_content_visible = True

    def calculate_combined_gradation(self): 
        for record in self:
            for line in record.combined_gradation_child_lines:
                # print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    if line.percent_retained == 0:
                        # print("Percent retained 0",line.percent_retained)
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2)})
                        line.write({'passing_percent': 100 })
                    else:
                        # print("Percent retained else",line.percent_retained)
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2)})
                        line.write({'passing_percent': round(100 -line.percent_retained - line.percent_retained,2)})
                else:
                    previous_line_record = self.env['ssl.bituminous.combined.gradation.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained})
                    line.write({'passing_percent': round(100-(previous_line_record + line.percent_retained),2)})
                    print("Previous Cumulative",previous_line_record)
                    
    @api.depends('combined_gradation_child_lines.wt_retained')
    def _compute_total_combined_gradation(self):
        for record in self:
            print("recordd",record)
            record.total_combined_gradation = sum(record.combined_gradation_child_lines.mapped('wt_retained'))


    # Bitumen Content
    wt_of_sample = fields.Float(string="Weight of the sample (W1) grams.") 
    init_wt_filter_paper = fields.Float(string="Initial weight of the filter paper (F1) grams")
    wt_agg_extraction = fields.Float(string="Weight of aggregate after extraction (W2) grams")
    wt_filter_paper_after_extraction = fields.Float(string="Weight of filter paper after extraction with fine materials (F2) grams")
    increase_in_wt_filter_paper = fields.Float(string="Increased weight of filter W3 = (F2-F1) grams",compute="_compute_increase_in_wt_filter_paper",digits=(16,1))

    @api.depends('wt_filter_paper_after_extraction','init_wt_filter_paper')
    def _compute_increase_in_wt_filter_paper(self):
        for record in self:
            record.increase_in_wt_filter_paper = record.wt_filter_paper_after_extraction - record.init_wt_filter_paper

    binder_content = fields.Float(string="Binder Content %",digits=(16,2),compute="_compute_binder_content")

    @api.depends('wt_agg_extraction','wt_of_sample','increase_in_wt_filter_paper')
    def _compute_binder_content(self):
        for record in self:
            if record.wt_of_sample > 0:
                try:
                    record.binder_content = ((record.wt_of_sample - (record.wt_agg_extraction + record.increase_in_wt_filter_paper)) / record.wt_of_sample ) * 100
                except ZeroDivisionError:
                    record.binder_content = 0
            else:
                record.binder_content = 0




class CombinedGradationLine(models.Model):
    _name = "ssl.bituminous.combined.gradation.line"
    parent_id = fields.Many2one('ssl.bituminous', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Weight Retained (gms)")
    # cumm_wt_retained = fields.Float(string="Cumm. Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    cumulative_retained = fields.Float(string="Cum. Retained %", store=True)
    passing_percent = fields.Float(string="Passing %",digits=(16,2))
    # cumm_wt_retained_per = fields.Float(string="Cumm. % Wt. Retained",compute="_compute_cumm_wt_retained_per",digits=(16,2))

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CombinedGradationLine, self).create(vals)

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
                    record.cumm_wt_retained_per = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(CombinedGradationLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(CombinedGradationLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(CombinedGradationLine, self).unlink()

        if parent_id:
            parent_id.combined_gradation_child_lines._reorder_serial_numbers()

        return res

    @api.depends('wt_retained', 'parent_id.weight_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / record.parent_id.weight_of_sample) * 100
            except ZeroDivisionError:
                record.percent_retained = 0






    @api.depends('wt_retained', 'parent_id.total_combined_gradation')
    def _compute_cumm_wt_retained_per(self):
        for record in self:
            try:
                record.cumm_wt_retained_per = record.parent_id.total_combined_gradation / record.wt_retained * 100
            except ZeroDivisionError:
                record.cumm_wt_retained_per = 0


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained = 0
        

    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.combined_gradation_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")
