from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class StackEmission(models.Model):
    _name = "stack.emission"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Stack Emission")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
   
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
   
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)


    # child_lines = fields.One2many('stack.emission.line','parent_id',string="Parameter")

    stack_details_name = fields.Char("Name",default="Stack Details")
    stack_details_visible = fields.Boolean("Stack Details",compute="_compute_visible")   

    # ================= STACK DETAILS =================
    stack_id = fields.Char("Stack ID")
    thimble_no = fields.Char("Thimble No")
    stack_attached_to = fields.Char("Stack Attached To")
    initial_weight = fields.Float("Initial Weight of Thimble (gm) W1 ")
    final_weight = fields.Float("Final Weight of Thimble (gm) W2 ")
    diff_weight = fields.Float("Differance Weight (gm) ΔW ")
    stack_height = fields.Float("Stack Height")
    stack_duct = fields.Char("Stack/Duct Dia ")
    fuel_type = fields.Char("Type of Fuel Use :")
    cross_area = fields.Float("Cross Sectional Area (m2) ")
    nozzle = fields.Char("Nozzle Dia and Type")


    parameter_details_name = fields.Char("Name",default="Parameter Details")
    parameter_details_visible = fields.Boolean("Parameter Details",compute="_compute_visible")


    # ================= PARAMETERS =================
    ambient_temp = fields.Float("Ambient Temp °C")
    ambient_temp_k = fields.Float("Ambient Temp °K")
    stack_temp = fields.Float("Stack Temp °C")
    stack_temp_k = fields.Float("Stack Temp °K")
    barometric_pressure = fields.Float("Barometric Pressure (mmHg)  (hpa/1.3332) ")
    diff_pressure = fields.Float("Deferential Pressure ΔH mmH2O (Avg.)")
    stack_pressure = fields.Float("Stack Pressure, (mmHg) (Avg.) : (mmH2O/13.6)")
    absolute_pressure = fields.Float("Absolute Static Pressure Ps, mmHg : (BP -SP)")

    coefficient_k = fields.Float("Coefficient  K =  (33.5 X 0.85)/√Abs Stack Presure x 30 ")

    avg_velocity = fields.Float("Avg. Velocity m/s =  coefficient factor x √stack Temp. x diff. pressure")
    flow_rate = fields.Float("Flow rate, Qs (LPM) = Velocity x Nosel dia x 60 x 1000")
    flow_rate_ts = fields.Float("Flow rate Normalization, Q's (LPM) = Qs x TStd. / Ts")
    sampling_time = fields.Float("Sampling time, Minute = 1000/sampling flow rate ")
    total_gas = fields.Float("Total Gas Pass (L)=Q's x Sampling Time ")
    actual_flow = fields.Float("Actual Flow rate Qm , (LPM)= Ps/760 x Qs x (298/Ta) :")
    corrected_flow = fields.Float("Corrected flow = (Qm X Q's X 298)/Pstd×Ts")
    tpm = fields.Float("TPM= (Diff. Weight x 106) / (Q's x sampling time)")
    total_gas_quantity = fields.Float("Total Gas Quantity(Nm3/hr) = Cross Sectional Area (m2) x Velocity x 3600 x 298 / Ts")


    # -------- Differential Pressure --------
    dp1 = fields.Float()
    dp2 = fields.Float()
    dp3 = fields.Float()
    dp4 = fields.Float()
    dp5 = fields.Float()
    dp6 = fields.Float()
    dp7 = fields.Float()
    dp8 = fields.Float()
    dp9 = fields.Float()
    dp10 = fields.Float()
    dp11 = fields.Float()
    dp12 = fields.Float()
    dp_avg = fields.Float(compute="_compute_avg")

    # -------- Static Pressure --------
    sp1 = fields.Float()
    sp2 = fields.Float()
    sp3 = fields.Float()
    sp4 = fields.Float()
    sp5 = fields.Float()
    sp6 = fields.Float()
    sp7 = fields.Float()
    sp8 = fields.Float()
    sp9 = fields.Float()
    sp10 = fields.Float()
    sp11 = fields.Float()
    sp12 = fields.Float()
    sp_avg = fields.Float(compute="_compute_avg")

    # -------- Velocity --------
    v1 = fields.Float()
    v2 = fields.Float()
    v3 = fields.Float()
    v4 = fields.Float()
    v5 = fields.Float()
    v6 = fields.Float()
    v7 = fields.Float()
    v8 = fields.Float()
    v9 = fields.Float()
    v10 = fields.Float()
    v11 = fields.Float()
    v12 = fields.Float()
    v_avg = fields.Float(compute="_compute_avg")

    @api.depends(
        'dp1','dp2','dp3','dp4','dp5','dp6','dp7','dp8','dp9','dp10','dp11','dp12',
        'sp1','sp2','sp3','sp4','sp5','sp6','sp7','sp8','sp9','sp10','sp11','sp12',
        'v1','v2','v3','v4','v5','v6','v7','v8','v9','v10','v11','v12'
    )
    def _compute_avg(self):
        for rec in self:
            # DP
            dp_vals = [rec.dp1,rec.dp2,rec.dp3,rec.dp4,rec.dp5,rec.dp6,
                       rec.dp7,rec.dp8,rec.dp9,rec.dp10,rec.dp11,rec.dp12]
            dp_vals = [v for v in dp_vals if v]
            rec.dp_avg = sum(dp_vals)/len(dp_vals) if dp_vals else 0

            # SP
            sp_vals = [rec.sp1,rec.sp2,rec.sp3,rec.sp4,rec.sp5,rec.sp6,
                       rec.sp7,rec.sp8,rec.sp9,rec.sp10,rec.sp11,rec.sp12]
            sp_vals = [v for v in sp_vals if v]
            rec.sp_avg = sum(sp_vals)/len(sp_vals) if sp_vals else 0

            # Velocity
            v_vals = [rec.v1,rec.v2,rec.v3,rec.v4,rec.v5,rec.v6,
                      rec.v7,rec.v8,rec.v9,rec.v10,rec.v11,rec.v12]
            v_vals = [v for v in v_vals if v]
            rec.v_avg = sum(v_vals)/len(v_vals) if v_vals else 0


    avgg_velocity = fields.Float(string="Avg. Velocity  {V} (m/sec)",compute="_compute_final_avg", store=True)

    @api.depends('dp_avg', 'sp_avg', 'v_avg')
    def _compute_final_avg(self):
        for rec in self:
            rec.avgg_velocity = (rec.dp_avg + rec.sp_avg + rec.v_avg) / 3




    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
   
    

   

    notes_id = fields.One2many('stack.emission.notes', 'parent_id', string="Notes")



    @api.model
    def default_get(self, fields):
        res = super(StackEmission, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in fullor partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'ampling is not done by us unless mentioned otherwide.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'without a QR Code and hologram this report is considered invalid.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
            }),
             (0, 0, {
                'sr_no': 'f',
                'notes': 'Alldisputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample willbe destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


   

 


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

        

            # if result.parameter.internal_id == '124578874gtre-372f-4775-9bcb-e999987hy':
            #     # result.result_char = self.avg_specific_gravity
            #     result.calculated = True

            if result.parameter.internal_id == '87985614-c893-4991-a463-6596321045879':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
                # if self.avg_compaction_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '95647852-c893-4991-a463-6595214789562':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
             
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
        record = super(StackEmission, self).create(vals)
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
        record = self.env['stack.emission'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    # added
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


   

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.stack_details_visible = False
            record.parameter_details_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '87985614-c893-4991-a463-6596321045879':
                    record.stack_details_visible = True

                if sample.internal_id == '95647852-c893-4991-a463-6595214789562':
                    record.parameter_details_visible = True

                


# class StainlessSteelLine(models.Model):
#     _name = "stack.emission.line"
#     parent_id = fields.Many2one('stack.emission',string="Parent Id")

#     serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
#     sample_identity = fields.Char(string="Sample  Identity")
#     blank = fields.Char(string="")
   
#     # f10 = fields.Integer(string="10")
#     uts = fields.Float(string="UTS (MPa)")
#     yield_sterss = fields.Float(string="Yield Stress (MPa)")
#     elongation = fields.Float(string="% Elongation On 5.65 √Area")
#     bend = fields.Selection(
#         [
#             ('ok_3', 'OK (3Ø)'),
#             ('ok_4', 'OK (4Ø)'),
#             ('ok_5', 'OK (5Ø)'),
#             ('ok_6', 'OK (6Ø)'),
#             ('not_ok', 'NOT OK')
#         ],
#         string="Bend Test 180° 2t"
#     )


#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('serial_no'))
#                 vals['serial_no'] = max_serial_no + 1

#         return super(StainlessSteelLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.serial_no = index + 1
   
                


class StackEmissionNotes(models.Model):
    _name = "stack.emission.notes"

    parent_id = fields.Many2one('stack.emission',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")