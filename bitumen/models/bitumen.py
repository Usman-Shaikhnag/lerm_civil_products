from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class BitumenMechanical(models.Model):
    _name = "mechanical.bitumen"
    _inherit = "lerm.eln"
    _description = 'mechanical.bitumen'
    _rec_name = "name"

    name = fields.Char("Name",default="Bitumen")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)
    temperature = fields.Char("Temperature",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)


    notes_id = fields.One2many('bitumen.notes', 'parent_id',string="Notes",
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


    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'bitumen.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }


     # ---- helper method
    def _get_unit(self, internal_id):
        param = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', internal_id)
        ], limit=1)
        return param.unit.name if param.unit else ""


        # ---- compute fields (unit बदलल्यावर update)
    def _compute_units(self):
        for rec in self:
            # rec.average_crushing_value_unit = rec._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71")
            # rec.average_impact_value_unit = rec._get_unit("2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2")
            rec.avg_compacted_unit     = rec._get_unit("357f579d-a310-4015-bc11-28a85c53ac83")
            # rec.avg_bulk_density_unit   = rec._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02")
            # rec.aggregate_elongation_unit   = rec._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667")
            # rec.aggregate_flakiness_unit   = rec._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f")
            # rec.avg_specific_gravity_unit   = rec._get_unit("b13d2195-69e0-4a8c-b3d6-309e5ffcacc2")
            # rec.avg_water_absorption_unit   = rec._get_unit("22ee804f-41a3-4fd1-a301-a8d9180fba10")

    # ---- default values (create mode मध्ये दिसण्यासाठी)
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            # 'average_crushing_value_unit':   self._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71"),
            # 'average_impact_value_unit': self._get_unit("2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2"),
            'avg_compacted_unit':     self._get_unit("357f579d-a310-4015-bc11-28a85c53ac83"),
            # 'avg_bulk_density_unit':   self._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02"),
            # 'aggregate_elongation_unit':   self._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667"),
            # 'aggregate_flakiness_unit':   self._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f"),
            # 'avg_specific_gravity_unit':   self._get_unit("b13d2195-69e0-4a8c-b3d6-309e5ffcacc2"),
            # 'avg_water_absorption_unit':   self._get_unit("22ee804f-41a3-4fd1-a301-a8d9180fba10"),
        })
        return res


    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id


    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.bitumen'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


    # Penetration Value Of Bitumen
    penetration_value_name = fields.Char("Name",default="Penetration Value Of Bitumen")
    penetration_value_visible = fields.Boolean("Penetration Value Of Bitumen Visible",compute="_compute_visible")

    penetration_value_line_ids = fields.One2many(
        'penetration.value.test.line',
        'parent_id',
        string='Penetration Value Lines'
    )

    average_penetration = fields.Float(
        string="Average",
        compute="_compute_average_penetration",
        store=True
    )

    @api.depends('penetration_value_line_ids.penetration')
    def _compute_average_penetration(self):
        for rec in self:
            values = rec.penetration_value_line_ids.mapped('penetration')
            rec.average_penetration = round(
                sum(values) / len(values), 2
            ) if values else 0.0


    average_penetration_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_average_penetration_conformity", store=True)

    @api.depends('average_penetration','eln_ref','grade')
    def _compute_average_penetration_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_penetration_conformity = 'na'
                continue
            record.average_penetration_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b5ddbb0a-cdde-43b9-a42f-a7071028add5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b5ddbb0a-cdde-43b9-a42f-a7071028add5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_penetration - record.average_penetration*mu_value
                    upper = record.average_penetration + record.average_penetration*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_penetration_conformity = 'pass'
                        break
                    else:
                        record.average_penetration_conformity = 'fail'

    average_penetration_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_penetration_nabl", store=True)

    @api.depends('average_penetration','eln_ref','grade')
    def _compute_average_penetration_nabl(self):
        
        for record in self:
            record.average_penetration_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b5ddbb0a-cdde-43b9-a42f-a7071028add5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b5ddbb0a-cdde-43b9-a42f-a7071028add5')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_penetration - record.average_penetration*mu_value
                    upper = record.average_penetration + record.average_penetration*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_penetration_nabl = 'pass'
                        break
                    else:
                        record.average_penetration_nabl = 'fail'


    penetration_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    penetration_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_penetration_final_report", store=True)

    @api.depends('average_penetration_nabl', 'penetration_report_type')
    def _compute_penetration_final_report(self):
     for rec in self:

        # Manual override
        if rec.penetration_report_type == 'nabl':
            rec.penetration_final_report = 'nabl'

        elif rec.penetration_report_type == 'non_nabl':
            rec.penetration_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_penetration_nabl == 'pass':
                rec.penetration_final_report = 'nabl'
            else:
                rec.penetration_final_report = 'non_nabl'


    



    # Specific Gravity 
    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    specific_water_line_ids = fields.One2many('bitumen.specific.gravity.line', 'parent_id', string="Observations",default=lambda self: self.specific_water_line_ids_sizes())

    @api.model
    def specific_water_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'sample_no': '1',}),
            (0, 0, {'sample_no': '2',}),
            (0, 0, {'sample_no': '3',}),
            
        ]
        return default_lines 

    avg_specific_gravity = fields.Float("Average Specific Gravity", compute="_compute_avg_specific_water", store=True)

    @api.depends('specific_water_line_ids.specific_gravity')
    def _compute_avg_specific_water(self):
     for rec in self:
        lines = rec.specific_water_line_ids

        if lines:
            sg_list = lines.mapped('specific_gravity')
            rec.avg_specific_gravity = sum(sg_list) / len(sg_list) if sg_list else 0.0
        else:
            rec.avg_specific_gravity = 0.0


    avg_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue
            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b13d2195-69e0-4a8c-b3d6-309e5ffcacc2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b13d2195-69e0-4a8c-b3d6-309e5ffcacc2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_conformity = 'fail'

    avg_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_specific_gravity_nabl", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b13d2195-69e0-4a8c-b3d6-309e5ffcacc2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b13d2195-69e0-4a8c-b3d6-309e5ffcacc2')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_nabl = 'fail'

    specific_gravity_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    specific_gravity_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_specific_gravity_final_report", store=True)

    @api.depends('avg_specific_gravity_nabl', 'specific_gravity_report_type')
    def _compute_specific_gravity_final_report(self):
     for rec in self:

        # Manual override
        if rec.specific_gravity_report_type == 'nabl':
            rec.specific_gravity_final_report = 'nabl'

        elif rec.specific_gravity_report_type == 'non_nabl':
            rec.specific_gravity_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_specific_gravity_nabl == 'pass':
                rec.specific_gravity_final_report = 'nabl'
            else:
                rec.specific_gravity_final_report = 'non_nabl'

    # Determination Of Softening Point
    soft_point_name = fields.Char("Name",default="Determination Of Softening Point")
    soft_point_visible = fields.Boolean("Determination Of Softening Point Visible",compute="_compute_visible")

    soft_point_line_ids = fields.One2many('bitumen.soft.point.line', 'parent_id', string="Observations",default=lambda self: self.soft_point_line_ids_sizes())

    rate_of_heating = fields.Char(string="Rate Of Heating",default=" 5 °C ± 0.5 °C")
    soft_cool_temp = fields.Integer(string="Period of Cooling at Room Tepmerature (min) : ")

   			

				
    @api.model
    def soft_point_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'time_min': '1',}),
            (0, 0, {'time_min': '2',}),
            (0, 0, {'time_min': '3',}),
            (0, 0, {'time_min': '4',}),
            (0, 0, {'time_min': '5',}),
            (0, 0, {'time_min': '6',}),
            (0, 0, {'time_min': '7',}),
            (0, 0, {'time_min': '8',}),
            (0, 0, {'time_min': '8',}),
            (0, 0, {'time_min': '10',}),
            (0, 0, {'time_min': '11',}),
            (0, 0, {'time_min': '12',}),
            
        ]
        return default_lines 
    

     # Result Section
    bill_no_1 = fields.Float(string="Bill No.1 (°C)")

    bill_no_2 = fields.Float(string="Bill No.2 (°C)")

    soft_mean_value = fields.Float(string="Mean Value Of Softening Point",compute="_compute_mean",store=True)

    # description = fields.Text(
    #     string="Description",
    #     default="Temperature at which sample touches the bottom plate °C"
    # )

    @api.depends('bill_no_1', 'bill_no_2')
    def _compute_mean(self):
        for rec in self:
            if rec.bill_no_1 and rec.bill_no_2:
                rec.soft_mean_value = (rec.bill_no_1 + rec.bill_no_2) / 2
            else:
                rec.soft_mean_value = 0.0
 


    soft_mean_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_soft_mean_value_conformity", store=True)

    @api.depends('soft_mean_value','eln_ref','grade')
    def _compute_soft_mean_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.soft_mean_value_conformity = 'na'
                continue
            record.soft_mean_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ffca993-9538-40aa-80e4-dbbc43e2de42')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ffca993-9538-40aa-80e4-dbbc43e2de42')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.soft_mean_value - record.soft_mean_value*mu_value
                    upper = record.soft_mean_value + record.soft_mean_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.soft_mean_value_conformity = 'pass'
                        break
                    else:
                        record.soft_mean_value_conformity = 'fail'

    soft_mean_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_soft_mean_value_nabl", store=True)

    @api.depends('soft_mean_value','eln_ref','grade')
    def _compute_soft_mean_value_nabl(self):
        
        for record in self:
            record.soft_mean_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ffca993-9538-40aa-80e4-dbbc43e2de42')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ffca993-9538-40aa-80e4-dbbc43e2de42')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.soft_mean_value - record.soft_mean_value*mu_value
                    upper = record.soft_mean_value + record.soft_mean_value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.soft_mean_value_nabl = 'pass'
                        break
                    else:
                        record.soft_mean_value_nabl = 'fail'


    soft_mean_value_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    soft_mean_value_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_soft_mean_value_final_report", store=True)

    @api.depends('soft_mean_value_nabl', 'soft_mean_value_report_type')
    def _compute_soft_mean_value_final_report(self):
     for rec in self:

        # Manual override
        if rec.soft_mean_value_report_type == 'nabl':
            rec.soft_mean_value_final_report = 'nabl'

        elif rec.soft_mean_value_report_type == 'non_nabl':
            rec.soft_mean_value_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.soft_mean_value_nabl == 'pass':
                rec.soft_mean_value_final_report = 'nabl'
            else:
                rec.soft_mean_value_final_report = 'non_nabl'


    # Ductility Test 
    ductility_name = fields.Char("Name",default="Ductility Test")
    ductility_visible = fields.Boolean("Ductility Test Visible",compute="_compute_visible")

    room_temperature = fields.Float(string="Room Temperature (°C)")
    pouring_temperature = fields.Float(string="Pouring Temperature (°C)" )
    cooling_atmosphere = fields.Float(string="Cooling In Atmosphere (min)" )
    cooling_before_trim = fields.Float(string="Period of cooling in water bath before trimming (min)")
    cooling_after_trim = fields.Float(string="Period of cooling in water bath after trimming (min)")
    actual_test_temperature = fields.Float(string="Actual Test Temperature (°C)")
    rate_of_pull = fields.Float(string="Rate Of Pull (mm/min)")


    ductility_line_ids = fields.One2many('bitumen.ductility.line','parent_id',string="Briquette Readings",default=lambda self: self.ductility_line_ids_sizes())
				
    @api.model
    def ductility_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'sample_no': '1',}),
            (0, 0, {'sample_no': '2',}),
            (0, 0, {'sample_no': '3',}),
            
        ]
        return default_lines 
    
    average_ductility = fields.Float(
    string="Average Ductility",
    compute="_compute_average_ductility",
    store=True
)

    @api.depends('ductility_line_ids.ductility')
    def _compute_average_ductility(self):
     for rec in self:

        values = rec.ductility_line_ids.mapped('ductility')

        if values:
            rec.average_ductility = sum(values) / len(values)
        else:
            rec.average_ductility = 0.0


    average_ductility_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_average_ductility_conformity", store=True)

    @api.depends('average_ductility','eln_ref','grade')
    def _compute_average_ductility_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_ductility_conformity = 'na'
                continue
            record.average_ductility_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4f04739c-d930-49ee-8962-dbe8796fdf5b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4f04739c-d930-49ee-8962-dbe8796fdf5b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_ductility - record.average_ductility*mu_value
                    upper = record.average_ductility + record.average_ductility*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_ductility_conformity = 'pass'
                        break
                    else:
                        record.average_ductility_conformity = 'fail'

    average_ductility_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_ductility_nabl", store=True)

    @api.depends('average_ductility','eln_ref','grade')
    def _compute_average_ductility_nabl(self):
        
        for record in self:
            record.average_ductility_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4f04739c-d930-49ee-8962-dbe8796fdf5b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4f04739c-d930-49ee-8962-dbe8796fdf5b')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_ductility - record.average_ductility*mu_value
                    upper = record.average_ductility + record.average_ductility*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_ductility_nabl = 'pass'
                        break
                    else:
                        record.average_ductility_nabl = 'fail'


    ductility_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    ductility_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_ductility_final_report", store=True)

    @api.depends('average_ductility_nabl', 'ductility_report_type')
    def _compute_ductility_final_report(self):
     for rec in self:

        # Manual override
        if rec.ductility_report_type == 'nabl':
            rec.ductility_final_report = 'nabl'

        elif rec.ductility_report_type == 'non_nabl':
            rec.ductility_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_ductility_nabl == 'pass':
                rec.ductility_final_report = 'nabl'
            else:
                rec.ductility_final_report = 'non_nabl'

    # ABSOLUTE VISCOSITY
    absolute_vis_name = fields.Char("Name",default="Absolute Viscosity")
    absolute_vis_visible = fields.Boolean("Absolute Viscosity Visible",compute="_compute_visible")

    absolute_line_ids = fields.One2many('bitumen.absolute.line','parent_id',string='Absolute Viscosity Lines')

    avg_absolute_viscosity = fields.Float(
        string='Average Absolute Viscosity',
        compute='_compute_avg_absolute_viscosity',
        store=True
    )

    @api.depends('absolute_line_ids.viscosity_60')
    def _compute_avg_absolute_viscosity(self):
        for rec in self:
            values = rec.absolute_line_ids.mapped('viscosity_60')
            rec.avg_absolute_viscosity = (
                sum(values) / len(values)
            ) if values else 0.0

    avg_absolute_viscosity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_absolute_viscosity_conformity", store=True)

    @api.depends('avg_absolute_viscosity','eln_ref','grade')
    def _compute_avg_absolute_viscosity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_absolute_viscosity_conformity = 'na'
                continue
            record.avg_absolute_viscosity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7ce069a-c150-4c4b-91f7-0898ddfd754c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7ce069a-c150-4c4b-91f7-0898ddfd754c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_absolute_viscosity - record.avg_absolute_viscosity*mu_value
                    upper = record.avg_absolute_viscosity + record.avg_absolute_viscosity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_absolute_viscosity_conformity = 'pass'
                        break
                    else:
                        record.avg_absolute_viscosity_conformity = 'fail'

    avg_absolute_viscosity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_absolute_viscosity_nabl", store=True)

    @api.depends('avg_absolute_viscosity','eln_ref','grade')
    def _compute_avg_absolute_viscosity_nabl(self):
        
        for record in self:
            record.avg_absolute_viscosity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7ce069a-c150-4c4b-91f7-0898ddfd754c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7ce069a-c150-4c4b-91f7-0898ddfd754c')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_absolute_viscosity - record.avg_absolute_viscosity*mu_value
                    upper = record.avg_absolute_viscosity + record.avg_absolute_viscosity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_absolute_viscosity_nabl = 'pass'
                        break
                    else:
                        record.avg_absolute_viscosity_nabl = 'fail'

    absolute_viscosity_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    absolute_viscosity_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_absolute_viscosity_final_report", store=True)

    @api.depends('avg_absolute_viscosity_nabl', 'absolute_viscosity_report_type')
    def _compute_absolute_viscosity_final_report(self):
     for rec in self:

        # Manual override
        if rec.absolute_viscosity_report_type == 'nabl':
            rec.absolute_viscosity_final_report = 'nabl'

        elif rec.absolute_viscosity_report_type == 'non_nabl':
            rec.absolute_viscosity_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_absolute_viscosity_nabl == 'pass':
                rec.absolute_viscosity_final_report = 'nabl'
            else:
                rec.absolute_viscosity_final_report = 'non_nabl'



    # KINEMATIC VISCOSITY
    kinematic_vis_name = fields.Char("Name",default="Kinematic Viscosity")
    kinematic_vis_visible = fields.Boolean("Kinematic Viscosity Visible",compute="_compute_visible")

    avg_kinematic_viscosity = fields.Float(
        string='Average Kinematic Viscosity',
        compute='_compute_avg_kinematic_viscosity',
        store=True
    )

    kinematic_line_ids = fields.One2many('bitumen.kinematic.line','parent_id',string='Kinematic Viscosity Lines')

    @api.depends('kinematic_line_ids.viscosity_135')
    def _compute_avg_kinematic_viscosity(self):
        for rec in self:
            values = rec.kinematic_line_ids.mapped('viscosity_135')
            rec.avg_kinematic_viscosity = (
                sum(values) / len(values)
            ) if values else 0.0

    avg_kinematic_viscosity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_kinematic_viscosity_conformity", store=True)

    @api.depends('avg_kinematic_viscosity','eln_ref','grade')
    def _compute_avg_kinematic_viscosity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_kinematic_viscosity_conformity = 'na'
                continue
            record.avg_kinematic_viscosity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7880694c-561c-4600-ae22-d1a290c65299')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7880694c-561c-4600-ae22-d1a290c65299')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_kinematic_viscosity - record.avg_kinematic_viscosity*mu_value
                    upper = record.avg_kinematic_viscosity + record.avg_kinematic_viscosity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_kinematic_viscosity_conformity = 'pass'
                        break
                    else:
                        record.avg_kinematic_viscosity_conformity = 'fail'

    avg_kinematic_viscosity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_kinematic_viscosity_nabl", store=True)

    @api.depends('avg_kinematic_viscosity','eln_ref','grade')
    def _compute_avg_kinematic_viscosity_nabl(self):
        
        for record in self:
            record.avg_kinematic_viscosity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7880694c-561c-4600-ae22-d1a290c65299')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7880694c-561c-4600-ae22-d1a290c65299')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_kinematic_viscosity - record.avg_kinematic_viscosity*mu_value
                    upper = record.avg_kinematic_viscosity + record.avg_kinematic_viscosity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_kinematic_viscosity_nabl = 'pass'
                        break
                    else:
                        record.avg_kinematic_viscosity_nabl = 'fail'


    kinematic_viscosity_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    kinematic_viscosity_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_kinematic_viscosity_final_report", store=True)

    @api.depends('avg_kinematic_viscosity_nabl', 'kinematic_viscosity_report_type')
    def _compute_kinematic_viscosity_final_report(self):
     for rec in self:

        # Manual override
        if rec.kinematic_viscosity_report_type == 'nabl':
            rec.kinematic_viscosity_final_report = 'nabl'

        elif rec.kinematic_viscosity_report_type == 'non_nabl':
            rec.kinematic_viscosity_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_kinematic_viscosity_nabl == 'pass':
                rec.kinematic_viscosity_final_report = 'nabl'
            else:
                rec.kinematic_viscosity_final_report = 'non_nabl'



    





    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:   
            record.penetration_value_visible = False
            record.specific_gravity_visible = False
            record.soft_point_visible = False
            record.ductility_visible = False
            record.absolute_vis_visible = False
            record.kinematic_vis_visible = False




            for sample in record.sample_parameters:

                if sample.internal_id == 'b5ddbb0a-cdde-43b9-a42f-a7071028add5':
                    record.penetration_value_visible = True
                
                if sample.internal_id == 'b13d2195-69e0-4a8c-b3d6-309e5ffcacc2':
                    record.specific_gravity_visible = True

                if sample.internal_id == '5ffca993-9538-40aa-80e4-dbbc43e2de42':
                    record.soft_point_visible = True
                
                if sample.internal_id == '4f04739c-d930-49ee-8962-dbe8796fdf5b':
                    record.ductility_visible = True

                if sample.internal_id == 'e7ce069a-c150-4c4b-91f7-0898ddfd754c':
                    record.absolute_vis_visible = True

                if sample.internal_id == '7880694c-561c-4600-ae22-d1a290c65299':
                    record.kinematic_vis_visible = True
                
                        # import wdb;wdb.set_trace()

                
               


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()

            # Penetration Value Of Bitumen
            if result.parameter.internal_id == 'b5ddbb0a-cdde-43b9-a42f-a7071028add5':
                result.calculated = True
                result.result_char = round(self.average_penetration,2)
                if self.average_penetration_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Specific Gravity 
            if result.parameter.internal_id == 'b13d2195-69e0-4a8c-b3d6-309e5ffcacc2':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Determination Of Softening Point
            if result.parameter.internal_id == '5ffca993-9538-40aa-80e4-dbbc43e2de42':
                result.calculated = True
                result.result_char = round(self.soft_mean_value,2)
                if self.soft_mean_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Ductility Test
            if result.parameter.internal_id == '4f04739c-d930-49ee-8962-dbe8796fdf5b':
                result.calculated = True
                result.result_char = round(self.average_ductility,2)
                if self.average_ductility_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Absolute Viscosity
            if result.parameter.internal_id == 'e7ce069a-c150-4c4b-91f7-0898ddfd754c':
                result.calculated = True
                result.result_char = round(self.avg_absolute_viscosity,2)
                if self.avg_absolute_viscosity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Kinematic Viscosity
            if result.parameter.internal_id == '7880694c-561c-4600-ae22-d1a290c65299':
                result.calculated = True
                result.result_char = round(self.avg_kinematic_viscosity,2)
                if self.avg_kinematic_viscosity_nabl == 'pass':
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
        record = super(BitumenMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(BitumenMechanical, self).read(fields=fields, load=load)

 
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
        record = self.env['mechanical.bitumen'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


class BitumenPenetrationValueLine(models.Model):
    _name = "penetration.value.test.line"
    _description = "Penetration Value Of Bitumen"

    parent_id = fields.Many2one('mechanical.bitumen',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    test_temperature = fields.Float(
        string="Test Temp (°C)"
    )

    initial_reading = fields.Float(
        string="Initial Dial Reading"
    )

    final_reading = fields.Float(
        string="Final Dial Reading"
    )

    penetration = fields.Float(
        string="Penetration (0.1 mm)",
        compute="_compute_penetration",
        store=True
    )

    remarks = fields.Char(
        string="Remark"
    )

    @api.depends('initial_reading', 'final_reading')
    def _compute_penetration(self):
        for rec in self:
            rec.penetration = rec.final_reading - rec.initial_reading


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BitumenPenetrationValueLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class BitumenSpecificGravityLine(models.Model):
    _name = "bitumen.specific.gravity.line"
    _description = "Specific Gravity "

    parent_id = fields.Many2one('mechanical.bitumen',string="Parent Id")

    sample_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)

    # Input Values
    w1 = fields.Float(string="Weight of Density Bottle (W1) g")
    w2 = fields.Float(string="Weight of Density Bottle + Sample (W2) g")
    w3 = fields.Float(string="Weight of Density Bottle + Sample + Water (W3) g")
    w4 = fields.Float(string="Weight of Density Bottle + Water (W4) g")

    # Calculated Values
    sample_weight = fields.Float(
        string="Weight of Sample (W2-W1) g",
        compute="_compute_values",
        store=True
    )

    specific_gravity = fields.Float(
        string="Specific Gravity of Sample = (W2-W1)/(W4-W1) - (W3-W2)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2', 'w3', 'w4')
    def _compute_values(self):
        for rec in self:
            rec.sample_weight = rec.w2 - rec.w1

            denominator = (rec.w4 - rec.w1) - (rec.w3 - rec.w2)

            if denominator:
                rec.specific_gravity = (rec.w2 - rec.w1) / denominator
            else:
                rec.specific_gravity = 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BitumenSpecificGravityLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

class BitumenSoftPointLine(models.Model):
    _name = "bitumen.soft.point.line"
    _description = "Determination Of Softening Point"

    parent_id = fields.Many2one('mechanical.bitumen',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    time_min = fields.Integer(
        string="Time (min)"
    )

    temperature = fields.Float(
        string="Temperature of Water Bath °C"
    )



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BitumenSoftPointLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class BitumenDuctilityLine(models.Model):
    _name = "bitumen.ductility.line"
    _description = "Ductility Test"

    parent_id = fields.Many2one('mechanical.bitumen',string="Parent Id")

    sample_no = fields.Integer(string="Briquette Mould No.", readonly=True, copy=False, default=1)

    initial_reading = fields.Float(string="Initial Reading")

    final_reading = fields.Float(string="Final Reading")

    ductility = fields.Float(string="Ductility",compute="_compute_ductility",store=True)

    @api.depends('initial_reading', 'final_reading')
    def _compute_ductility(self):
        for rec in self:
            rec.ductility = rec.final_reading - rec.initial_reading


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BitumenDuctilityLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1





class BitumenAbsoluteLine(models.Model):
    _name = 'bitumen.absolute.line'
    _description = 'Absolute Viscosity Line'

    parent_id = fields.Many2one('mechanical.bitumen',string="Parent Id")

    sample_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)

    cooling_period = fields.Char(string="Period of Cooling at 60 °C ±  0.1 °C  in Bath")
    actual_temperature = fields.Float(string="Actual Test Temperature (°C)")

    bulb_b_time = fields.Float(string="Time Taken To Pass Bulb B - (Second ) (B)")
    bulb_b_constant = fields.Float(string="Calibration Constant Bulb B (Poise/Second) (C)")

    bulb_c_time = fields.Float(string="Time Taken To Pass Bulb C - (Second) (D)")
    bulb_c_constant = fields.Float(string="Calibration Constant Bulb C (Poise/Second) (E)")

    viscosity_60 = fields.Float(string="Viscosity at  60 °C,  (F) ((B*C)+(D*E))/2",
        compute='_compute_viscosity_60',
        store=True
    )

    @api.depends(
        'bulb_b_time',
        'bulb_b_constant',
        'bulb_c_time',
        'bulb_c_constant'
    )
    def _compute_viscosity_60(self):
        for rec in self:
            rec.viscosity_60 = (
                (rec.bulb_b_time * rec.bulb_b_constant) +
                (rec.bulb_c_time * rec.bulb_c_constant)
            ) / 2


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BitumenAbsoluteLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class BitumenKinematicLine(models.Model):
    _name = 'bitumen.kinematic.line'
    _description = 'Kinematic Viscosity Line'


    parent_id = fields.Many2one('mechanical.bitumen',string="Parent Id")

    sample_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)

    cooling_period = fields.Char(string="Period of Cooling at  135 °C ±  0.1   °C  in Bath")
    actual_temperature = fields.Float(string="Actual Test Temperature (°C)  (A)")

    flow_time = fields.Float(string="Time Taken To Flow of  Bitumen - (Second) (B)")
    tube_constant = fields.Float(string="Calibration Constant Tube (C.S.) (E) Calibration Constant Bulb B (Poise/Second)  (E)")

    viscosity_135 = fields.Float(string="Viscosity at 135  °C, Cst = (B*E) ",
        compute='_compute_viscosity_135',
        store=True
    )

    @api.depends('flow_time', 'tube_constant')
    def _compute_viscosity_135(self):
        for rec in self:
            rec.viscosity_135 = rec.flow_time * rec.tube_constant

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BitumenKinematicLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class BitumenNotes(models.Model):
    _name = "bitumen.notes"

    parent_id = fields.Many2one('mechanical.bitumen',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")






 