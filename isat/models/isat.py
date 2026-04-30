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
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)


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

            

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(IsatMechanical, self).create(vals)
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
        record = self.env['mech.isat'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value
        return field_values

    def open_eln_page(self):
        # import wdb; wdb.set_trace()

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
            }


    notes_id = fields.One2many('mech.isat.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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


#     # Fields for the main model
#     name = fields.Char("Name", default="ISAT")

#     # One2many field to link to child lines
#     child_lines = fields.One2many('mech.isat.line', 'parent_id')

#     # Method to open the elapsed time wizard
#     def action_open_elapsed_time_wizard(self):
#         return {
#             'name': "Create Elapsed Time Lines",
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'mech.elapsed.time.wizard',
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#         }

# # Define the child line model
# class IsatChildLine(models.Model):
#     _name = 'mech.isat.line'

#     # Field to link to the parent (main model)
#     parent_id = fields.Many2one('mech.isat', string='Parent Id')

#     # Field for selecting elapsed time
    # elapsed_time = fields.Selection([
    #     (0, '0 Minutes'),
    #     (10, '10 Minutes'),
    #     (30, '30 Minutes'),
    #     (60, '60 Minutes'),
    # ], string='Elapsed Time', required=True, default=0)

#     # Additional field for the child line
#     other_field = fields.Char(string='Other Field')

# # Define the wizard model
# class ElapsedTimeWizard(models.TransientModel):
#     _name = 'mech.elapsed.time.wizard'

#     # Method to create the elapsed time lines
#     def create_lines(self):
#         # Get the active main model ID from the context
#         main_model_id = self.env.context.get('active_id')
#         main_model = self.env['mech.isat'].browse(main_model_id)

#         # List of elapsed times to create
#         elapsed_times = [0, 10, 30, 60]

#         # Create child lines with specified elapsed times
#         for elapsed_time in elapsed_times:
#             self.env['mech.isat.line'].create({
#                 'parent_id': main_model.id,
#                 'elapsed_time': elapsed_time,
#             })

#         # Close the wizard
#         return {'type': 'ir.actions.act_window_close'}


#     def add_sample_line(self):
#         parent_id = self.env.context.get('active_id')

#         # List of elapsed times to create
#         elapsed_times = [0, 10, 30, 60]
        
#         sample_line_data = {
#             'product_id': parent_id.id,
#             'ir_model': self.ir_model.id,
#         }
#         parent_id.write({'child_lines': [(0, 0, sample_line_data)]})
#         return {'type': 'ir.actions.act_window_close'}
class IsatMechanicalNotes(models.Model):
    _name = "mech.isat.notes"

    parent_id = fields.Many2one('mech.isat', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
