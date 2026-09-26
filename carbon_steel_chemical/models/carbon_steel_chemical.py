from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class CarbonSteelChemical(models.Model):
    _name = "chemical.carbon.steel"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name1 = fields.Char("Name",default="Metals & Alloys-Structural Steel")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
    
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")

    def prefill_data(self):
        wizard_action = self.env.ref('concrete_cube.action_cube_prefill_data_wizard')
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'mech.tmt.bar.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    
    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    temprature_section = fields.Float("Temperature (°C)", digits=(10,2))
    humidity_section = fields.Float("Humidity (%)", digits=(10,2))

    temprature_chemical = fields.Float("Temperature (°C)", digits=(10,2))
    humidity_chemical = fields.Float("Humidity (%)", digits=(10,2))

    garde = fields.Char("Grade")
    size = fields.Char("Size")

    sample_submitted = fields.Char("Sample Submitted By")

    sample_status = fields.Char("Sample Status")

    No_of_sample = fields.Integer("Number Of Samples")
    product_name = fields.Char(string="Product",compute="_compute_product_name")

    @api.depends('eln_ref', 'eln_ref.sub_product_id')
    def _compute_product_name(self):
        for record in self:
            if record.eln_ref and record.eln_ref.sub_product_id:
                record.product_name = record.eln_ref.sub_product_id.sub_product
            else:
                record.product_name = False
    
   
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    mechanical_test_visible = fields.Boolean("Stainless Steel Visible",compute="_compute_visible")
    mechanical_test_name = fields.Char("Name",default="Mechanical Test")

    section_weight_visible = fields.Boolean("Stainless Steel Visible",compute="_compute_visible")
    section_weight_name = fields.Char("Name",default="Section Weight")

    section_weight_lines = fields.One2many('mech.carbon.steel.section.line','parent_id',string="Parameter")



    chemical_test_visible = fields.Boolean("Stainless Steel Visible",compute="_compute_visible")
    chemical_test_name1 = fields.Char("Name",default="Chemical Test")

    chemical_test_lines = fields.One2many('chemical.carbon.steel.test.line','parent_id',string="Parameter")


   

    notes_id = fields.One2many('chemical.carbon.steel.notes', 'parent_id', string="Notes")

    child_lines = fields.One2many('chemical.carbon.steel.line','parent_id',string="Parameter")



    @api.model
    def default_get(self, fields):
        res = super(CarbonSteelChemical, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in full or partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sampling is not done by us unless mentioned otherwide.',
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
                'notes': 'All disputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample will be destroyed after 30-days from the date of test report unless otherwise Specified.',
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

            if result.parameter.internal_id == '65587529-c0b6-4054-8b2d-7efc9bfe2c85':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
                # if self.avg_compaction_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'f48158e5-04b1-46d8-98f1-3cca5620cb50':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue


            if result.parameter.internal_id == 'fd78c2d4-57bf-4bfb-a8c1-4c647f099dd4':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '23bacb20-7b4a-481c-aee5-b652d7e912a1':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue
            
            if result.parameter.internal_id == '0888ce50-7e57-4d08-b550-c3206bee2584':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue
            
            if result.parameter.internal_id == 'd9cab869-9e87-4d0e-ae87-a956774da64b':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '501eaf84-c8d5-4002-bf1d-61869799a5cd':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == 'a53e0aab-a7c0-4beb-afc1-704a5917e051':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '99a0d77f-6237-4dc9-898f-6f3be67bcb12':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '11ab83fd-ed54-467e-b4dd-15857fc1c8bc':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            # chemical

            if result.parameter.internal_id == '87a325d9-a353-467d-a142-6ebd1078d438':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '7a4d9b23-9bed-4f12-a633-9d563c3902ad':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '149d84a2-fec0-4b6e-9184-7d9c8da927d4':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == 'f04e75bf-8414-4953-98ce-cb82354e6a3e':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '40897334-a79c-4e54-a639-bd8ed9489131':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '6687d3a3-987f-4dc3-94d5-d453400331db':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

            if result.parameter.internal_id == '0d5b2f12-f87e-462c-9ef3-d464aeb08830':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

            if result.parameter.internal_id == 'fda58929-a85c-4ff0-b0ea-672d3566369b':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

            if result.parameter.internal_id == '21fd335d-5a97-46a0-9ec3-cce85e5cb297':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

            
            if result.parameter.internal_id == '2eed5f1e-9cc3-4779-afde-741f18e7c2df':
                # result.result_char = round(self.average_mpa,2)
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
        record = super(CarbonSteelChemical, self).create(vals)
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
        record = self.env['chemical.carbon.steel'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
   

   

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.mechanical_test_visible = False
            record.section_weight_visible = False
            record.chemical_test_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '65587529-c0b6-4054-8b2d-7efc9bfe2c85':
                    record.mechanical_test_visible = True

                if sample.internal_id == '99a0d77f-6237-4dc9-898f-6f3be67bcb12':
                    record.section_weight_visible = True

                if sample.internal_id == '11ab83fd-ed54-467e-b4dd-15857fc1c8bc':
                    record.chemical_test_visible = True

                


class CarbonSteelChemicalLine(models.Model):
    _name = "chemical.carbon.steel.line"
    parent_id = fields.Many2one('chemical.carbon.steel',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identity = fields.Char(string="Sample  Identity")
   
    # f10 = fields.Integer(string="10")
    uts = fields.Float(string="UTS (MPa)")

    proof_stress = fields.Float(string="0.2 % Proof Stress N/mm2")
    elongation = fields.Float(string="% Elongation On 5.65 √Area")
    total_elongation = fields.Float(string="% Total Elongation")
    ratio_uts_ys = fields.Float(string="Ratio of UTS/YS")

    
    bend = fields.Selection(
        [
            ('ok_3', 'OK (3Ø)'),
            ('ok_4', 'OK (4Ø)'),
            ('ok_5', 'OK (5Ø)'),
            ('ok_6', 'OK (6Ø)'),
            ('not_ok', 'NOT OK')
        ],
        string="Bend Test 180° 2t"
    )

    re_bend = fields.Selection(
        [
            ('ok_3', 'OK (3Ø)'),
            ('ok_4', 'OK (4Ø)'),
            ('ok_5', 'OK (5Ø)'),
            ('ok_6', 'OK (6Ø)'),
            ('not_ok', 'NOT OK')
        ],
        string="Re-Bend Test"
    )

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            self.sample_identity = self.parent_id.product_name
        else:
            self.sample_identity = False


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CarbonSteelChemicalLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class SectionWeightLine(models.Model):
    _name = "mech.carbon.steel.section.line"
    parent_id = fields.Many2one('chemical.carbon.steel',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identity = fields.Char(string="Sample  Identity")
   
    # f10 = fields.Integer(string="10")
    weight = fields.Float(string="Weight (Kg)")

    lenght = fields.Float(string="Length(mm)")
    unit_weight = fields.Float(string="Unit Weight Kg/meter")
    standard_weight = fields.Float(string="Standard Weight  as per IS 1786-2008")
    tolerance = fields.Char(string="Tolerance on the Nominal Mass, Percent Batch")

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            self.sample_identity = self.parent_id.product_name
        else:
            self.sample_identity = False

    
  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SectionWeightLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class ChemicalLine(models.Model):
    _name = "chemical.carbon.steel.test.line"
    parent_id = fields.Many2one('chemical.carbon.steel',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identity = fields.Char(string="Sample  Identity")
   
    # f10 = fields.Integer(string="10")
    c = fields.Float(string="C%",digits=(12,3))

    p = fields.Float(string="P%",digits=(12,3))
    s = fields.Float(string="S%",digits=(12,3))
    si = fields.Float(string="Si%",digits=(12,3))
    cr = fields.Float(string="Cr%",digits=(12,3))
    cu = fields.Float(string="Cu%",digits=(12,3))
    mo = fields.Float(string="Mo%",digits=(12,3))
    ni = fields.Float(string="Ni%",digits=(12,3))
    mn = fields.Float(string="Mn%",digits=(12,3))


    p_s = fields.Float(string="P + S", compute="_compute_p_s", store=True,digits=(12,3))

    @api.depends('p', 's')
    def _compute_p_s(self):
        for rec in self:
            rec.p_s = (rec.p or 0.0) + (rec.s or 0.0)

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            self.sample_identity = self.parent_id.product_name
        else:
            self.sample_identity = False

    
  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ChemicalLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
   
   
                


class CarbonSteelChemicalNotes(models.Model):
    _name = "chemical.carbon.steel.notes"

    parent_id = fields.Many2one('chemical.carbon.steel',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")