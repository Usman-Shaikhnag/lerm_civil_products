from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class IsatMechanical(models.Model):
    _name = "mech.isat"
    _inherit = "lerm.eln"  
    _rec_name = "name"


    name = fields.Char(default="ISAT",readonly=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    # grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


    notes_id = fields.One2many('mech.isat.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(IsatMechanical, self).default_get(fields)

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


    # @api.depends('eln_ref')
    # def _compute_grade_id(self):
    #     if self.eln_ref:
    #         self.grade = self.eln_ref.grade_id.id

    isat_name = fields.Char("Name",default="ISAT ")
    isat_visible = fields.Boolean("I SAT  of Concrete   Visible",compute="_compute_visible")


    isat_child_lines = fields.One2many('mech.isat.line', 'parent_id')
    
    average_10min = fields.Float("Average 10 mins",compute="_compute_avg_10mins")

    @api.depends('isat_child_lines')
    def _compute_avg_10mins(self):
        for record in self:
            if record.isat_child_lines:
                isat_10min_values = []
                for line in record.isat_child_lines:
                    isat_10min_values.append(line.child_lines[1].isat_corrected)
                average_10min = sum(isat_10min_values)/len(record.isat_child_lines)
                record.average_10min = round(average_10min,2)       
            else:
                record.average_10min = 0

    ## Isat parameter


    isat_of_concrte_name1 = fields.Char("Name",default="ISAT  of Concrete")
    isat_of_concrte_visible = fields.Boolean("I SAT  of Concrete   Visible",compute="_compute_visible")


    isat_of_concrete_lines = fields.One2many('mechanical.isat.concrete.line', 'parent_id')


    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        

        for record in self:
         
            record.isat_of_concrte_visible = False
            record.isat_visible = False


            
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
               
                if sample.internal_id == '0t071b15-baa4-466f-a6a7-65879tyuer1':
                    record.isat_of_concrte_visible = True
                if sample.internal_id == '13c26e81-4e34-48ae-9568-d0560f4f6e9b':
                    record.isat_visible = True

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            if result.parameter.internal_id == '0t071b15-baa4-466f-a6a7-65879tyuer1':
                # result.result_char = round(self.average_strength,2)
                result.calculated = True
                # if self.nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '13c26e81-4e34-48ae-9568-d0560f4f6e9b':
                # result.result_char = round(self.average_strength,2)
                result.calculated = True
                # if self.nabl == 'pass':
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
        record = super(IsatMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mech.isat'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

   


class IsatChildLine(models.Model):
    _name = 'mech.isat.line'

    # Field to link to the parent (main model)
    parent_id = fields.Many2one('mech.isat', string='Parent Id')

    sample_id = fields.Char("Sample Id")
    age_days = fields.Integer('Age days')
    time_hrs = fields.Integer("Time Hrs")
    child_lines = fields.One2many('mech.isat.nested.line', 'parent_id',string="ISAT Table")
    comments = fields.Char("Comments")


    def default_get(self, fields):
        print("From Default Value")
        res = super(IsatChildLine, self).default_get(fields)

        default_elapsed_times = []
        elapsed_times = ['0','10','30','60']

        for i in range(4): 
            time = {
                'elapsed_time': elapsed_times[i] 
            }
            default_elapsed_times.append((0, 0, time))
        res['child_lines'] = default_elapsed_times
        return res

class IsatNestedChildLine(models.Model):
    _name = 'mech.isat.nested.line'

    # Field to link to the parent (main model)
    parent_id = fields.Many2one('mech.isat.line', string='Parent Id')


    elapsed_time = fields.Char("Elapsed Time min")
    no_of_scale_div_5sec = fields.Integer('No of scale Division in 5 sec')
    period_movement_measured = fields.Char('Period During Movement Measured')
    no_of_div_moved_selected_period = fields.Float('No of Scale division moved during selected period')
    no_of_scale_div_1min = fields.Integer('No of scale Division in 1 min')
    isat_sec = fields.Float('ISAT  ml/m2/sec',compute='_compute_isat_sec')
    correction_factor = fields.Float('Correction Factor')
    isat_corrected = fields.Float('ISAT Corrected to Equ 27°C ml/㎡/sec',compute="_compute_isat_corrected")


    @api.depends('no_of_scale_div_1min')
    def _compute_isat_sec(self):
        for record in self:
            record.isat_sec = record.no_of_scale_div_1min / 100

    @api.depends('correction_factor','isat_sec')
    def _compute_isat_corrected(self):
        for record in self:
            record.isat_corrected = record.correction_factor * record.isat_sec




class MechanicalIsatConcreteLine(models.Model):
    _name = "mechanical.isat.concrete.line"
    parent_id = fields.Many2one('mech.isat',string="Parent Id")

    sr_no = fields.Integer(string="Sample",readonly=True, copy=False, default=1)
    id_mark = fields.Char(string="ID Mark/Location")
    length = fields.Float(string="Length (mm)")
    width = fields.Float(string="Width (mm)")
    intial_surface10 = fields.Float(string="Initial Surface Absorption in ml/m2.sec  at 10 Minute")
    intial_surface_corrected = fields.Float(string="Initial Surface Absorption Corrected to Equivalent 27°C  ml/m2.sec")
    
    intial_surface30 = fields.Float(string="Initial Surface Absorption in ml/m2.sec  at 30 Minute")
    intial_surface60 = fields.Float(string="Initial Surface Absorption in ml/m2.sec  at 60 Minute")

    remark = fields.Char(string="Remark")
   


    # @api.depends('parent_id')
    # def _compute_id_mark(self):
    #     for record in self:
    #         sample_id = record.parent_id.eln_ref.sample_id.client_sample_id
    #         record.id_mark = sample_id


    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for record in self:
            parent = record.parent_id.sudo()
            sample_id = parent.eln_ref.sample_id.client_sample_id
            if sample_id:
                record.id_mark = sample_id
            else:
                record.id_mark = ""

    @api.onchange('id_mark')
    def _onchange_id_mark(self):
        for record in self:
            if record.id_mark and not record.parent_id.eln_ref.sample_id.client_sample_id:
                record.parent_id.eln_ref.sample_id.client_sample_id = record.id_mark





    # @api.depends('length', 'width')
    # def _compute_area(self):
    #     for record in self:
    #         record.area = round((record.length * record.width) , 4)


    # @api.depends('crushing_load', 'area')
    # def _compute_compressive_strength(self):
    #     for record in self:
    #         if record.area != 0:
    #             record.compressive_strength = record.crushing_load / record.area * 1000
    #         else:
    #             record.compressive_strength = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalIsatConcreteLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ISATNotes(models.Model):
    _name = "mech.isat.notes"

    parent_id = fields.Many2one('mech.isat',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")