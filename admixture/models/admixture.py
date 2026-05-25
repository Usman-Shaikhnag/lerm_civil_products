from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalAdmixture(models.Model):
    _name = 'mechanical.admixture'
    _inherit = "lerm.eln"
    _rec_name = "name"


    name_admixture = fields.Char("Name",default="Admixture")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    notes_id = fields.One2many('mechanical.admixture.notes', 'parent_id',string="Notes",
    default=lambda self: self._default_notes_lines()
)
    
    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'This report is invalid without the official paper seal of Make Infracon.',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'The # points mentioned in the report which information is given by Client/Customer.',
            }),

            (0, 0, {
                'sr_no': 'v',
                'notes': 'Any disputes shall be subject to jurisdiction of Nashik courts only.',
            }),
        ]
    



    room_temp = fields.Char(string="Room Temp")
    room_rh = fields.Char(string="Room RH")

    # Admixture
    admixture_visible = fields.Boolean("Admixture Visible",compute="_compute_visible")
    admixture_name = fields.Char("Name",default="Admixture")

    child_lines = fields.One2many('mechanical.admixture.line', 'parent_id', string="Parameter", default=lambda self: self._default_sieve_analysis_child_lines())

    @api.model
    def _default_sieve_analysis_child_lines(self):
        default_lines = [
            (0, 0, {'water_content_max1': 'Water Content % of control sample,Max'}),
            (0, 0, {'water_content_max1': 'Slump'}),

            # 
            (0, 0, {'water_content_max1': 'Loss of workability'}),
            (0, 0, {'water_content_max1': 'Flow of Concrete of High Workability'}),

            (0, 0, {'water_content_max1': 'Time of setting allowable deviation from control sample hours Initial'}),
            (0, 0, {'water_content_max1': 'Time of setting allowable deviation from control sample hours Final'}),
            (0, 0, {'water_content_max1': 'Compressive Strength (N/mm2)'}),
            (0, 0, {'water_content_max1': 'a) 1 Day'}),
            (0, 0, {'water_content_max1': 'b) 3 Days'}),
            (0, 0, {'water_content_max1': 'c) 7 Days'}),
            (0, 0, {'water_content_max1': 'd)  28 Days'}),
            (0, 0, {'water_content_max1': 'Flexural strength % of control sample,Min'}),
            (0, 0, {'water_content_max1': 'a) 3 Days'}),
            (0, 0, {'water_content_max1': 'b) 7 Days'}),
            (0, 0, {'water_content_max1': 'c) 28 Days'}),
            (0, 0, {'water_content_max1': 'Bleeding (%) over control'}),
            (0, 0, {'water_content_max1': 'Air Content (%) over control Max'}),
        ]
        return default_lines
    

    # =========================
    # LOSS OF WORKABILITY
    # =========================

    # loss_workability = fields.Float(string="Loss of Workability %",compute="_compute_loss_workability",store=True)

    # @api.depends('child_lines.water_content_max1','child_lines.water_content_max2','child_lines.water_content_max3')
    # def _compute_loss_workability(self):

    #  for rec in self:

    #     initial_slump = 0
    #     final_slump = 0

    #     for line in rec.child_lines:

    #         # Control slump
    #         if line.water_content_max1 == 'Slump':
    #             initial_slump = float(line.water_content_max2 or 0)

    #         # Admixture slump after time
    #         if line.water_content_max1 == 'Loss of workability':
    #             final_slump = float(line.water_content_max3 or 0)

    #     if initial_slump:

    #         rec.loss_workability = round(
    #             ((initial_slump - final_slump) / initial_slump) * 100,
    #             2
    #         )

    #     else:
    #         rec.loss_workability = 0

    #     # WRITE VALUE TO TABLE ROW
    #     for line in rec.child_lines:
    #         if line.water_content_max1 == 'Loss of workability':
    #             line.water_content_max2 = str(rec.loss_workability)

    # =========================
    # FLOW OF HIGH WORKABILITY
    # =========================

    # flow_d1 = fields.Float("Flow D1")
    # flow_d2 = fields.Float("Flow D2")

    # flow_high_workability = fields.Float(string="Flow of Concrete of High Workability",compute="_compute_flow_workability",store=True)

    # @api.depends('flow_d1', 'flow_d2')
    # def _compute_flow_workability(self):

    #   for rec in self:

    #     rec.flow_high_workability = round(
    #         (rec.flow_d1 + rec.flow_d2) / 2,
    #         2
    #     )

    #     # WRITE VALUE TO TABLE ROW
    #     for line in rec.child_lines:
    #         if line.water_content_max1 == 'Flow of Concrete of High Workability':
    #             line.water_content_max2 = str(rec.flow_high_workability)


    
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.admixture_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "5f722fd9-5698-452d-90c1-a36e837d7805":
                    record.admixture_visible = True

                


     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Compressive Strength 
            if result.parameter.internal_id == '5f722fd9-5698-452d-90c1-a36e837d7805':
                result.calculated = True
                # result.result_char = round(self.avrg_compressive_strength,2)
                # if self.comp_strength_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            
            

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
        record = super(MechanicalAdmixture, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

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
        record = self.env['mechanical.bricks'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()

        return super(MechanicalAdmixture, self).read(fields=fields, load=load)
    
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



class MechanicalAdmixtureLine(models.Model):
    _name = "mechanical.admixture.line"
    parent_id = fields.Many2one('mechanical.admixture',string="Parent Id")


    water_content_max1 = fields.Char(string='Test Parameter')
    water_content_max2 = fields.Char(string='Control')
    water_content_max3 = fields.Char(string='Admixture')
    water_content_max4 = fields.Char(string='Accelerating admixture')
    water_content_max5 = fields.Char(string='Retarding Admixture')
    water_content_max6 = fields.Char(string='Water Reducing admixture')
    water_content_max7 = fields.Char(string='Air Entering Admixture')
    water_content_max8 = fields.Char(string='Normal')
    water_content_max9 = fields.Char(string='Retarding Type')

    # slump = fields.Char(string='Slump')

    # time_of_setting_initial = fields.Char(string='Time of Setting - Initial')
    # time_of_setting_final = fields.Char(string='Time of Setting - Final')

    # compressive_strength_1_day = fields.Char(string='Compressive Strength (1 Day)')
    # compressive_strength_3_days = fields.Char(string='Compressive Strength (3 Days)')
    # compressive_strength_7_days = fields.Char(string='Compressive Strength (7 Days)')
    # compressive_strength_28_days = fields.Char(string='Compressive Strength (28 Days)')

    # flexural_strength_3_days = fields.Char(string='Flexural Strength (3 Days)')
    # flexural_strength_7_days = fields.Char(string='Flexural Strength (7 Days)')
    # flexural_strength_28_days = fields.Char(string='Flexural Strength (28 Days)')

    # bleeding = fields.Char(string='Bleeding (%) over control')
    # air_content = fields.Char(string='Air Content (%) over control')



class MechanicalAdmixtureNotes(models.Model):
    _name = "mechanical.admixture.notes"

    parent_id = fields.Many2one('mechanical.admixture',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


    