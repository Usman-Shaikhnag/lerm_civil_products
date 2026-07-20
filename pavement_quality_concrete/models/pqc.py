from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re
from datetime import datetime , timedelta
import re
import logging
_logger = logging.getLogger(__name__)

class PavementQualityConcrete(models.Model):
    _name = "mechanical.pavement.quality.concrete"
    _inherit = "lerm.eln"
    _description = 'mechanical.pavement.quality.concrete'
    _rec_name = "name"

    name = fields.Char("Name",default="Pavment Quality Concrete")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)
    temperature = fields.Char("Temperature",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    notes_id = fields.One2many('pqc.notes', 'parent_id',string="Notes",
    default=lambda self: self._default_notes_lines())
    
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
            'res_model': 'coarse.aggregate.prefill.data',
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
            # rec.average_impact_value_unit = rec._get_unit("5d55143e-9447-47ba-9477-31eabb5fe40f")
            rec.avg_compacted_unit     = rec._get_unit("357f579d-a310-4015-bc11-28a85c53ac83")
            # rec.avg_bulk_density_unit   = rec._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02")
            # rec.aggregate_elongation_unit   = rec._get_unit("df9d9803-d458-4e8f-965c-ecd9f5974f84")
            # rec.aggregate_flakiness_unit   = rec._get_unit("c224881c-bd16-42b5-b502-cb2ed8b85ebb")
            # rec.avg_specific_gravity_unit   = rec._get_unit("15b2b0c7-76d8-46a5-b9ac-11ac817e2f78")
            # rec.avg_water_absorption_unit   = rec._get_unit("8f20b97e-e578-4a24-b885-f11f95874377")

    # ---- default values (create mode मध्ये दिसण्यासाठी)
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            # 'average_crushing_value_unit':   self._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71"),
            # 'average_impact_value_unit': self._get_unit("5d55143e-9447-47ba-9477-31eabb5fe40f"),
            'avg_compacted_unit':     self._get_unit("357f579d-a310-4015-bc11-28a85c53ac83"),
            # 'avg_bulk_density_unit':   self._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02"),
            # 'aggregate_elongation_unit':   self._get_unit("df9d9803-d458-4e8f-965c-ecd9f5974f84"),
            # 'aggregate_flakiness_unit':   self._get_unit("c224881c-bd16-42b5-b502-cb2ed8b85ebb"),
            # 'avg_specific_gravity_unit':   self._get_unit("15b2b0c7-76d8-46a5-b9ac-11ac817e2f78"),
            # 'avg_water_absorption_unit':   self._get_unit("8f20b97e-e578-4a24-b885-f11f95874377"),
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
        record = self.env['mechanical.pavement.quality.concrete'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


     # Sieve Analysis 
    weight_of_sample = fields.Float(string="Weight of Sample in gms")
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.pqc.sieve.analysis.line','parent_id',string="Parameter")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")


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


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        default_lines = []

        eln_ref = res.get("eln_ref")
        if not eln_ref:
            return res

        eln = self.env["lerm.eln"].browse(eln_ref)

        size = (eln.size_id.size or "").strip().lower()

        sieve_sizes = [
        "37.5 mm",
        "31.50 mm",
        "26.50 mm",
        "19.0 mm",
        "9.50 mm",
        "4.75 mm",
        "600 mic",
        "150 mic",
        "75 mic",
    ]

        specific_limits_mapping = {

        "31.5 mm": [
            "100",
            "90 - 100",
            "85 - 95",
            "68 - 88",
            "45 - 65",
            "30 - 55",
            "8 - 30",
            "0 - 10",
            "0 - 5",
        ],

        "26.5 mm": [
            "100",
            "100",
            "90 - 100",
            "75 - 95",
            "50 - 70",
            "30 - 55",
            "8 - 30",
            "0 - 10",
            "0 - 5",
        ],

        "19 mm": [
            "100",
            "100",
            "100",
            "90 - 100",
            "48 - 78",
            "30 - 58",
            "8 - 35",
            "0 - 12",
            "0 - 5",
        ],
    }

        limits = specific_limits_mapping.get(size, [])

        for sieve, limit in zip(sieve_sizes, limits):
            default_lines.append((0, 0, {
            "sieve_size": sieve,
            "specific_limits": limit,
        }))

        res["sieve_analysis_child_lines"] = default_lines

        return res
    


    def populate_sieve_analysis_lines(self):
      self.ensure_one()

      if not self.eln_ref:
        return

      size = (self.eln_ref.size_id.size or "").strip().lower()

      specific_limits_mapping = {

        "31.5 mm": [
            "100",
            "90 - 100",
            "85 - 95",
            "68 - 88",
            "45 - 65",
            "30 - 55",
            "8 - 30",
            "0 - 10",
            "0 - 5",
        ],

        "26.5 mm": [
            "100",
            "100",
            "90 - 100",
            "75 - 95",
            "50 - 70",
            "30 - 55",
            "8 - 30",
            "0 - 10",
            "0 - 5",
        ],

        "19 mm": [
            "100",
            "100",
            "100",
            "90 - 100",
            "48 - 78",
            "30 - 58",
            "8 - 35",
            "0 - 12",
            "0 - 5",
        ],
    }

      limits = specific_limits_mapping.get(size, [])

      for line, limit in zip(self.sieve_analysis_child_lines, limits):
        line.specific_limits = limit


    
    def calculate_sieve(self): 
        for record in self:
            # import wdb; wdb.set_trace()
            record.populate_sieve_analysis_lines()  # replace default_get call
            for line in record.sieve_analysis_child_lines:
                # print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    if line.percent_retained == 0:
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
                                    'passing_percent': 100 ,})
                    else:
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
                                    'passing_percent': round(100 -line.percent_retained - line.percent_retained,2),})
                else:
                    previous_line_record = self.env['mechanical.pqc.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained,
                                'passing_percent': round(100-(previous_line_record + line.percent_retained),2),})
                    
                    # print("Previous Cumulative",previous_line_record)
                    

    
    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))

    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            pan_line = None
            total_retained = 0.0            
            # Find all unique sieve sizes except pan
            all_sieves = set()
            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() != 'pan':
                    all_sieves.add(line.sieve_size.strip())
            
            # Calculate total retained for all non-pan sieves
            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() == 'pan':
                    pan_line = line
                elif line.sieve_size in all_sieves:  # Include all non-pan sieves
                    total_retained += line.wt_retained or 0.0

            # Update pan weight if pan exists and we have a sample weight
            if pan_line and rec.weight_of_sample:
                pan_line.wt_retained = rec.weight_of_sample - total_retained


    # @api.depends('sieve_analysis_child_lines.wt_retained')
    # def _compute_cumulative_sieve(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.cumulative = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))


    


    # Flakiness and Elongation 
    elongation_fl_name = fields.Char(default="FLAKINESS AND ELONGATION INDEX")
    elongation_fl_visible = fields.Boolean("FLAKINESS AND ELONGATION INDEX",compute="_compute_visible")


    elongation_fl_table = fields.One2many('mechanical.pqc.elongation.flakiness.line','parent_id',string="Elongation Flakiness Index",default=lambda self: self.elongation_fl_table_sizes())


    @api.model
    def elongation_fl_table_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '63.0','retained_sieve': '50.0'}),
            (0, 0, {'passing_sieve': '50.0','retained_sieve': '40.0'}),
            (0, 0, {'passing_sieve': '40.0','retained_sieve': '31.5'}),
            (0, 0, {'passing_sieve': '31.5','retained_sieve': '25.0'}),
            (0, 0, {'passing_sieve': '25.0','retained_sieve': '20.0'}),
            (0, 0, {'passing_sieve': '20.0','retained_sieve': '16.0'}),
            (0, 0, {'passing_sieve': '16.0','retained_sieve': '12.5'}),
            (0, 0, {'passing_sieve': '12.5','retained_sieve': '10.0'}),
            (0, 0, {'passing_sieve': '10.0','retained_sieve': '6.3'}),
            
        ]
        return default_lines 


   

    total_total_weight = fields.Float("Total (Total Wt of Aggregate Retained (gm)) (A)", compute="_compute_totals", store=True)
    total_wt_passing_flakiness = fields.Float("Total (Wt Passing Flakiness Gauge (gm)) (B)", compute="_compute_totals", store=True)
    total_wt_retained_flakiness = fields.Float("Total (Wt. Retained on Flakiness gauge (gm) = [(Total Wt of aggregate Retained (gm)) - (Wt. Passing on Flakiness gauge (gm)] (C)", compute="_compute_totals", store=True)
    total_wt_retained_elongation = fields.Float("Total (Wt Retained Elongation Gauge (gm)) (D)", compute="_compute_totals", store=True)

    @api.depends(
        'elongation_fl_table.total_weight',
        'elongation_fl_table.wt_passing_flakiness',
        'elongation_fl_table.wt_retained_flakiness',
        'elongation_fl_table.wt_retained_elongation'
    )
    def _compute_totals(self):
        for rec in self:
            rec.total_total_weight = sum(rec.elongation_fl_table.mapped('total_weight'))
            rec.total_wt_passing_flakiness = sum(rec.elongation_fl_table.mapped('wt_passing_flakiness'))
            rec.total_wt_retained_flakiness = sum(rec.elongation_fl_table.mapped('wt_retained_flakiness'))
            rec.total_wt_retained_elongation = sum(rec.elongation_fl_table.mapped('wt_retained_elongation'))

    flakiness_index = fields.Float(
        string="Flakiness Index (FI=(B/A)*100) (%)",
        compute="_compute_indexes",
        store=True
    ) 

    elongation_index = fields.Float(
        string="Elongation Index (FI=(D/C)*100) (%)",
        compute="_compute_indexes",
        store=True
    )

    combined_index = fields.Float(
        string="Combined Flakiness  & Elongation Index (%)",
        compute="_compute_indexes",
        store=True
    )

    @api.depends('total_total_weight', 'total_wt_passing_flakiness', 'total_wt_retained_flakiness', 'total_wt_retained_elongation')
    def _compute_indexes(self):
        for rec in self:
            # FI = B/A * 100
            if rec.total_total_weight:
                rec.flakiness_index = (rec.total_wt_passing_flakiness / rec.total_total_weight) * 100
            else:
                rec.flakiness_index = 0.0

            # EI = D/C * 100
            if rec.total_wt_retained_flakiness:
                rec.elongation_index = (rec.total_wt_retained_elongation / rec.total_wt_retained_flakiness) * 100
            else:
                rec.elongation_index = 0.0

            # Combined
            rec.combined_index = rec.flakiness_index + rec.elongation_index


    elongation_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Elongation Index Conformity", compute="_compute_elongation_index_conformity", store=True)

    @api.depends('elongation_index','eln_ref','grade')
    def _compute_elongation_index_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_index_conformity = 'na'
                continue
            record.elongation_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','df9d9803-d458-4e8f-965c-ecd9f5974f84')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','df9d9803-d458-4e8f-965c-ecd9f5974f84')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.elongation_index - record.elongation_index*mu_value
                    upper = record.elongation_index + record.elongation_index*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.elongation_index_conformity = 'pass'
                        break
                    else:
                        record.elongation_index_conformity = 'fail'

    elongation_index_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Elongation Index NABL", compute="_compute_elongation_index_nabl", store=True)

    @api.depends('elongation_index','eln_ref','grade')
    def _compute_elongation_index_nabl(self):
        
        for record in self:
            record.elongation_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','df9d9803-d458-4e8f-965c-ecd9f5974f84')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','df9d9803-d458-4e8f-965c-ecd9f5974f84')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.elongation_index - record.elongation_index*mu_value
                    upper = record.elongation_index + record.elongation_index*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.elongation_index_nabl = 'pass'
                        break
                    else:
                        record.elongation_index_nabl = 'fail'

    flakiness_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Flakiness Index Conformity", compute="_compute_flakiness_index_conformity", store=True)

    @api.depends('flakiness_index','eln_ref','grade')
    def _compute_flakiness_index_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.flakiness_index_conformity = 'na'
                continue
            record.flakiness_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c224881c-bd16-42b5-b502-cb2ed8b85ebb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c224881c-bd16-42b5-b502-cb2ed8b85ebb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.flakiness_index - record.flakiness_index*mu_value
                    upper = record.flakiness_index + record.flakiness_index*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.flakiness_index_conformity = 'pass'
                        break
                    else:
                        record.flakiness_index_conformity = 'fail'

    flakiness_index_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_flakiness_index_nabl", store=True)

    @api.depends('flakiness_index','eln_ref','grade')
    def _compute_flakiness_index_nabl(self):
        
        for record in self:
            record.flakiness_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c224881c-bd16-42b5-b502-cb2ed8b85ebb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c224881c-bd16-42b5-b502-cb2ed8b85ebb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.flakiness_index - record.flakiness_index*mu_value
                    upper = record.flakiness_index + record.flakiness_index*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.flakiness_index_nabl = 'pass'
                        break
                    else:
                        record.flakiness_index_nabl = 'fail'


    # Aggregate Impact Value

    impact_value_name = fields.Char("Name",default="Aggregate Impact Value")
    impact_visible = fields.Boolean("Impact Visible",compute="_compute_visible")

    impact_value_child_lines = fields.One2many('mechanical.impact.value.pqc.line','parent_id',string="Parameter")

    average_impact_value = fields.Float(string="Average Aggregate Impact Value (%)", compute="_compute_average_impact_value")


    @api.depends('impact_value_child_lines.aiv')
    def _compute_average_impact_value(self):
        for rec in self:
            values = rec.impact_value_child_lines.mapped('aiv')
            rec.average_impact_value = sum(values) / len(values) if values else 0.0


    average_impact_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_average_impact_value_conformity", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_impact_value_conformity = 'na'
                continue
            record.average_impact_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d55143e-9447-47ba-9477-31eabb5fe40f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d55143e-9447-47ba-9477-31eabb5fe40f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_impact_value - record.average_impact_value*mu_value
                    upper = record.average_impact_value + record.average_impact_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_impact_value_conformity = 'pass'
                        break
                    else:
                        record.average_impact_value_conformity = 'fail'

    impact_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_impact_value_nabl", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_impact_value_nabl(self):
        
        for record in self:
            record.impact_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d55143e-9447-47ba-9477-31eabb5fe40f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d55143e-9447-47ba-9477-31eabb5fe40f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_impact_value - record.average_impact_value*mu_value
                    upper = record.average_impact_value + record.average_impact_value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.impact_value_nabl = 'pass'
                        break
                    else:
                        record.impact_value_nabl = 'fail'

    # Specific Gravety 
    specific_gravity_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    specific_water_line_ids = fields.One2many('pqc.specific.gravity.water.absorption.line', 'parent_id', string="Observations")

    avg_specific_gravity = fields.Float("Average Specific Gravity", compute="_compute_avg_specific_water", store=True)
    avg_water_absorption = fields.Float("Average Water Absorption (%)", compute="_compute_avg_specific_water", store=True)

    @api.depends('specific_water_line_ids.specific_gravity', 'specific_water_line_ids.water_absorption')
    def _compute_avg_specific_water(self):
     for rec in self:
        lines = rec.specific_water_line_ids

        if lines:
            sg_list = lines.mapped('specific_gravity')
            wa_list = lines.mapped('water_absorption')

            rec.avg_specific_gravity = sum(sg_list) / len(sg_list) if sg_list else 0.0
            rec.avg_water_absorption = sum(wa_list) / len(wa_list) if wa_list else 0.0
        else:
            rec.avg_specific_gravity = 0.0
            rec.avg_water_absorption = 0.0


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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15b2b0c7-76d8-46a5-b9ac-11ac817e2f78')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15b2b0c7-76d8-46a5-b9ac-11ac817e2f78')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15b2b0c7-76d8-46a5-b9ac-11ac817e2f78')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15b2b0c7-76d8-46a5-b9ac-11ac817e2f78')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8f20b97e-e578-4a24-b885-f11f95874377')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8f20b97e-e578-4a24-b885-f11f95874377')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.avg_water_absorption_conformity = 'fail'

    avg_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8f20b97e-e578-4a24-b885-f11f95874377')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8f20b97e-e578-4a24-b885-f11f95874377')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_water_absorption_nabl = 'pass'
                        break
                    else:
                        record.avg_water_absorption_nabl = 'fail'


    
    # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="SOUNDNESS (SODIUM SULPHATE TEST)")
    soundness_na2so4_visible = fields.Boolean("SOUNDNESS OF COARSE AGGREGATE (SODIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_sod_line_ids = fields.One2many(
        'pqc.sodium.sulphate.line',
        'parent_id',
        string="Soundness Na2SO4",default=lambda self: self.soundness_sod_line_ids_sizes()
    )

    @api.model
    def soundness_sod_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '60mm','retained_sieve': '40mm'}),
            (0, 0, {'passing_sieve': '40mm','retained_sieve': '20mm'}),
            (0, 0, {'passing_sieve': '20mm','retained_sieve': '10mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
        ]
        return default_lines 
    


    total_grading = fields.Float("Total (Grading of Original Sample (%))", compute="_compute_totaled")
    total_weight_before = fields.Float("Total (Weight of Test Fraction Before Test (gm))", compute="_compute_totaled")
    total_weight_after = fields.Float("Total (Weight of Test Fraction After Test (gm))", compute="_compute_totaled")
    total_percent_loss = fields.Float("Total (Percentage Passing Finer Sieve After Test (Actual Percentage Loss))", compute="_compute_totaled")
    total_weighted_avg = fields.Float("Final Result (Weighted Average  (Corrected Percent Loss))", compute="_compute_totaled")

    @api.depends(
        'soundness_sod_line_ids.grading_percent',
        'soundness_sod_line_ids.weight_before',
        'soundness_sod_line_ids.weight_after',
        'soundness_sod_line_ids.percent_loss',
        'soundness_sod_line_ids.weighted_avg'
    )
    def _compute_totaled(self):
        for rec in self:
            rec.total_grading = sum(rec.soundness_sod_line_ids.mapped('grading_percent'))
            rec.total_weight_before = sum(rec.soundness_sod_line_ids.mapped('weight_before'))
            rec.total_weight_after = sum(rec.soundness_sod_line_ids.mapped('weight_after'))
            rec.total_percent_loss = sum(rec.soundness_sod_line_ids.mapped('percent_loss'))
            rec.total_weighted_avg = sum(rec.soundness_sod_line_ids.mapped('weighted_avg'))

    soundness_sodtwo_line_ids = fields.One2many(
        'pqc.sodium.sulphate.two.line',
        'parent_id',
        string="Soundness Na2SO4",default=lambda self: self.soundness_sodtwo_line_ids_sizes()
    )

    @api.model
    def soundness_sodtwo_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '600mic','retained_sieve': '300mic'}),
            (0, 0, {'passing_sieve': '1.18mm','retained_sieve': '600mic'}),
            (0, 0, {'passing_sieve': '2.36mm','retained_sieve': '1.18mm'}),
            (0, 0, {'passing_sieve': '4.75mm','retained_sieve': '2.36mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
            
        ]
        return default_lines 
    
    total1_grading = fields.Float("Total (Grading of Original Sample (%)", compute="_compute_totally")
    total1_weight_before = fields.Float("Total (Weight of Test Fraction Before Test (gm))", compute="_compute_totally")
    total1_weight_after = fields.Float("Total (Weight of Test Fraction After Test (gm))", compute="_compute_totally")
    total1_percent_loss = fields.Float("Total (Percentage Passing Finer Sieve After Test (Actual Percentage Loss))", compute="_compute_totally")
    total1_weighted_avg = fields.Float("Final Result (Weighted Average  (Corrected Percent Loss))", compute="_compute_totally")

    @api.depends(
        'soundness_sodtwo_line_ids.grading_percent',
        'soundness_sodtwo_line_ids.weight_before',
        'soundness_sodtwo_line_ids.weight_after',
        'soundness_sodtwo_line_ids.percent_loss',
        'soundness_sodtwo_line_ids.weighted_avg'
    )
    def _compute_totally(self):
        for rec in self:
            rec.total1_grading = sum(rec.soundness_sodtwo_line_ids.mapped('grading_percent'))
            rec.total1_weight_before = sum(rec.soundness_sodtwo_line_ids.mapped('weight_before'))
            rec.total1_weight_after = sum(rec.soundness_sodtwo_line_ids.mapped('weight_after'))
            rec.total1_percent_loss = sum(rec.soundness_sodtwo_line_ids.mapped('percent_loss'))
            rec.total1_weighted_avg = sum(rec.soundness_sodtwo_line_ids.mapped('weighted_avg'))

    total_weighted_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_total_weighted_avg_conformity", store=True)

    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.total_weighted_avg_conformity = 'na'
                continue
            record.total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','74165249-323c-4adf-ad2a-2fa1d68536de')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','74165249-323c-4adf-ad2a-2fa1d68536de')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.total_weighted_avg - record.total_weighted_avg*mu_value
                    upper = record.total_weighted_avg + record.total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.total_weighted_avg_conformity = 'fail'

    total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_total_weighted_avg_nabl", store=True)

    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_nabl(self):
        
        for record in self:
            record.total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','74165249-323c-4adf-ad2a-2fa1d68536de')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','74165249-323c-4adf-ad2a-2fa1d68536de')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                 lab_min = line.lab_min_value
                 lab_max = line.lab_max_value
                 mu_value = line.mu_value
            
                 lower = record.total_weighted_avg - record.total_weighted_avg*mu_value
                 upper = record.total_weighted_avg + record.total_weighted_avg*mu_value
                 if lower >= lab_min and upper <= lab_max:
                   record.total_weighted_avg_nabl = 'pass'
                   break
                 else:
                    record.total_weighted_avg_nabl = 'fail'


    # SOUNDNESS (MAGNESIUM SULPHATE TEST)
    soundness_mgso4_name = fields.Char("Name",default="SOUNDNESS (MAGNESIUM SULPHATE TEST)")
    soundness_mgso4_visible = fields.Boolean("SOUNDNESS (MAGNESIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_mag_line_ids = fields.One2many(
        'pqc.magnesium.sulphate.two.line',
        'parent_id',
        string="Soundness MgSO4",default=lambda self: self.soundness_mag_line_ids_sizes()
    )

    @api.model
    def soundness_mag_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '60mm','retained_sieve': '40mm'}),
            (0, 0, {'passing_sieve': '40mm','retained_sieve': '20mm'}),
            (0, 0, {'passing_sieve': '20mm','retained_sieve': '10mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
        ]
        return default_lines 
    


    mag_total_grading = fields.Float("Total (Grading of Original Sample (%))", compute="_compute_totalled")
    mag_total_weight_before = fields.Float("Total (Weight of Test Fraction Before Test (gm))", compute="_compute_totalled")
    mag_total_weight_after = fields.Float("Total (Weight of Test Fraction After Test (gm))", compute="_compute_totalled")
    mag_total_percent_loss = fields.Float("Total (Percentage Passing Finer Sieve After Test (Actual Percentage Loss))", compute="_compute_totalled")
    mag_total_weighted_avg = fields.Float("Final Result (Weighted Average  (Corrected Percent Loss))", compute="_compute_totalled")

    @api.depends(
        'soundness_mag_line_ids.grading_percent',
        'soundness_mag_line_ids.weight_before',
        'soundness_mag_line_ids.weight_after',
        'soundness_mag_line_ids.percent_loss',
        'soundness_mag_line_ids.weighted_avg'
    )
    def _compute_totalled(self):
        for rec in self:
            rec.mag_total_grading = sum(rec.soundness_mag_line_ids.mapped('grading_percent'))
            rec.mag_total_weight_before = sum(rec.soundness_mag_line_ids.mapped('weight_before'))
            rec.mag_total_weight_after = sum(rec.soundness_mag_line_ids.mapped('weight_after'))
            rec.mag_total_percent_loss = sum(rec.soundness_mag_line_ids.mapped('percent_loss'))
            rec.mag_total_weighted_avg = sum(rec.soundness_mag_line_ids.mapped('weighted_avg'))

    soundness_magtwo_line_ids = fields.One2many(
        'pqc.magnesium.sulphate.two.line',
        'parent_id',
        string="Soundness MgSO4",default=lambda self: self.soundness_magtwo_line_ids_sizes()
    )

    @api.model
    def soundness_magtwo_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '600mic','retained_sieve': '300mic'}),
            (0, 0, {'passing_sieve': '1.18mm','retained_sieve': '600mic'}),
            (0, 0, {'passing_sieve': '2.36mm','retained_sieve': '1.18mm'}),
            (0, 0, {'passing_sieve': '4.75mm','retained_sieve': '2.36mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
            
        ]
        return default_lines 
    
    mag_total1_grading = fields.Float("Total (Grading of Original Sample (%))", compute="_compute_totallly")
    mag_total1_weight_before = fields.Float("TTotal (Weight of Test Fraction Before Test (gm))", compute="_compute_totallly")
    mag_total1_weight_after = fields.Float("Total (Weight of Test Fraction After Test (gm))", compute="_compute_totallly")
    mag_total1_percent_loss = fields.Float("otal (Percentage Passing Finer Sieve After Test (Actual Percentage Loss))", compute="_compute_totallly")
    mag_total1_weighted_avg = fields.Float("Final Result (Weighted Average  (Corrected Percent Loss))", compute="_compute_totallly")

    @api.depends(
        'soundness_magtwo_line_ids.grading_percent',
        'soundness_magtwo_line_ids.weight_before',
        'soundness_magtwo_line_ids.weight_after',
        'soundness_magtwo_line_ids.percent_loss',
        'soundness_magtwo_line_ids.weighted_avg'
    )
    def _compute_totallly(self):
        for rec in self:
            rec.mag_total1_grading = sum(rec.soundness_magtwo_line_ids.mapped('grading_percent'))
            rec.mag_total1_weight_before = sum(rec.soundness_magtwo_line_ids.mapped('weight_before'))
            rec.mag_total1_weight_after = sum(rec.soundness_magtwo_line_ids.mapped('weight_after'))
            rec.mag_total1_percent_loss = sum(rec.soundness_magtwo_line_ids.mapped('percent_loss'))
            rec.mag_total1_weighted_avg = sum(rec.soundness_magtwo_line_ids.mapped('weighted_avg'))


    mag_total_weighted_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_mag_total_weighted_avg_conformity", store=True)


    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mag_total_weighted_avg_conformity = 'na'
                continue
            record.mag_total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2823d838-885e-46b2-8b86-c712e821ccf2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2823d838-885e-46b2-8b86-c712e821ccf2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mag_total_weighted_avg - record.mag_total_weighted_avg*mu_value
                    upper = record.mag_total_weighted_avg + record.mag_total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.mag_total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.mag_total_weighted_avg_conformity = 'fail'


    mag_total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_mag_total_weighted_avg_nabl", store=True)

    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_nabl(self):
        
        for record in self:
            record.mag_total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2823d838-885e-46b2-8b86-c712e821ccf2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2823d838-885e-46b2-8b86-c712e821ccf2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mag_total_weighted_avg - record.mag_total_weighted_avg*mu_value
                    upper = record.mag_total_weighted_avg + record.mag_total_weighted_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mag_total_weighted_avg_nabl = 'pass'
                        break
                    else:
                        record.mag_total_weighted_avg_nabl = 'fail'


    # Compressive Strength Of Pavement Quality Concrete (PQC) 
    
    comp_strength_name = fields.Char("Name",default="Compressive Strength Of Pavement Quality Concrete (PQC)")
    comp_strength_visible = fields.Boolean("Compressive Strength Of Pavement Quality Concrete (PQC) Visible",compute="_compute_visible")

    comp_strength_line_ids = fields.One2many(
        'pqc.compressive.strength.line',
        'parent_id',
        string="Compressive Strength Of Pavement Quality Concrete (PQC)"
    )

    comp_size_cube = fields.Selection([
    ('150 x 150 x 150', '150 x 150 x 150'),], string="Size of Cube")

    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing",compute="_compute_date_testing")



    @api.depends('eln_ref')
    def _compute_date_testing(self):
        if self.eln_ref:
            self.date_of_testing = self.eln_ref.date_testing
        else:
            self.date_of_testing = ''
            

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None


    def action_calculate_avg_strength(self):
        for rec in self:
            lines = rec.comp_strength_line_ids.sorted(key=lambda l: l.sr_no)  
            group_size = 3

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strengths = [l.compressive_strength for l in group if l.compressive_strength > 0]
                avg = sum(strengths) / len(strengths) if strengths else 0.0

                if group:
                    group[0].avg_compressive_strength = avg

            for line in lines:
                if line not in [lines[i] for i in range(0, len(lines), group_size)]:
                    line.avg_compressive_strength = 0.0


    avg_7_comp_strength = fields.Float(string="Max 7 Compressive Strength (MPa)",compute="_compute_max_strength",
    store=True,)

    avg_28_comp_strength = fields.Float(string="Max 28 Compressive Strength (MPa)",compute="_compute_max_strength",
    store=True,)

    

    @api.depends('comp_strength_line_ids.avg_compressive_strength',
             'comp_strength_line_ids.days')
    def _compute_max_strength(self):
     for rec in self:
        strength_7 = rec.comp_strength_line_ids.filtered(
            lambda l: l.days == '7'
        ).mapped('avg_compressive_strength')

        strength_28 = rec.comp_strength_line_ids.filtered(
            lambda l: l.days == '28'
        ).mapped('avg_compressive_strength')

        rec.avg_7_comp_strength = max(strength_7) if strength_7 else 0.0
        rec.avg_28_comp_strength = max(strength_28) if strength_28 else 0.0



    avg_7_comp_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_7_comp_strength_conformity", store=True)

    @api.depends('avg_7_comp_strength','eln_ref','grade')
    def _compute_avg_7_comp_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_comp_strength_conformity = 'na'
                continue
            record.avg_7_comp_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afe730f2-e917-40f4-b039-5aefab017e9f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afe730f2-e917-40f4-b039-5aefab017e9f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_comp_strength - record.avg_7_comp_strength*mu_value
                    upper = record.avg_7_comp_strength + record.avg_7_comp_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_7_comp_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_7_comp_strength_conformity = 'fail'

    avg_7_comp_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_7_comp_strength_nabl", store=True)

    @api.depends('avg_7_comp_strength','eln_ref','grade')
    def _compute_avg_7_comp_strength_nabl(self):
        
        for record in self:
            record.avg_7_comp_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afe730f2-e917-40f4-b039-5aefab017e9f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afe730f2-e917-40f4-b039-5aefab017e9f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_comp_strength - record.avg_7_comp_strength*mu_value
                    upper = record.avg_7_comp_strength + record.avg_7_comp_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_7_comp_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_7_comp_strength_nabl = 'fail'


    avg_28_comp_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_28_comp_strength_conformity", store=True)

    @api.depends('avg_28_comp_strength','eln_ref','grade')
    def _compute_avg_28_comp_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_comp_strength_conformity = 'na'
                continue
            record.avg_28_comp_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ea9024b-c9aa-488e-aebe-383bd0b98ba4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ea9024b-c9aa-488e-aebe-383bd0b98ba4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_comp_strength - record.avg_28_comp_strength*mu_value
                    upper = record.avg_28_comp_strength + record.avg_28_comp_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_28_comp_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_28_comp_strength_conformity = 'fail'

    avg_28_comp_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_28_comp_strength_nabl", store=True)

    @api.depends('avg_28_comp_strength','eln_ref','grade')
    def _compute_avg_28_comp_strength_nabl(self):
        
        for record in self:
            record.avg_28_comp_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ea9024b-c9aa-488e-aebe-383bd0b98ba4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ea9024b-c9aa-488e-aebe-383bd0b98ba4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_comp_strength - record.avg_28_comp_strength*mu_value
                    upper = record.avg_28_comp_strength + record.avg_28_comp_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_28_comp_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_28_comp_strength_nabl = 'fail'



    # Flexural Strength Of Pavement Quality Concrete (PQC) 
    
    flexural_strength_name = fields.Char("Name",default="Flexural Strength Of Pavement Quality Concrete (PQC)")
    flexural_strength_visible = fields.Boolean("Flexural Strength Of Pavement Quality Concrete (PQC) Visible",compute="_compute_visible")

    flexural_strength_line_ids = fields.One2many(
        'pqc.flexural.strength.line',
        'parent_id',
        string="Flexural Strength Of Pavement Quality Concrete (PQC)"
    )

    flexural_size_cube = fields.Selection([
    ('700 x 150 x 150', '700 x 150 x 150'),], string="Size of Beam L X B X B in mm")


    def action_calculate_avg_flex_strength(self):
        for rec in self:
            lines = rec.flexural_strength_line_ids.sorted(key=lambda l: l.sr_no)  
            group_size = 3

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strengths = [l.flexural_strength for l in group if l.flexural_strength > 0]
                avg = sum(strengths) / len(strengths) if strengths else 0.0

                if group:
                    group[0].avg_flexural_strength = avg

            for line in lines:
                if line not in [lines[i] for i in range(0, len(lines), group_size)]:
                    line.avg_flexural_strength = 0.0


    avg_7_flex_strength = fields.Float(string="Max 7 Flexural Strength (MPa)",compute="_compute_max_flex_strength",
    store=True,)

    avg_28_flex_strength = fields.Float(string="Max 28 Flexural Strength (MPa)",compute="_compute_max_flex_strength",
    store=True,)

    

    @api.depends('flexural_strength_line_ids.avg_flexural_strength',
             'flexural_strength_line_ids.days')
    def _compute_max_flex_strength(self):
     for rec in self:
        strength_7 = rec.flexural_strength_line_ids.filtered(
            lambda l: l.days == '7'
        ).mapped('avg_flexural_strength')

        strength_28 = rec.flexural_strength_line_ids.filtered(
            lambda l: l.days == '28'
        ).mapped('avg_flexural_strength')

        rec.avg_7_flex_strength = max(strength_7) if strength_7 else 0.0
        rec.avg_28_flex_strength = max(strength_28) if strength_28 else 0.0



    avg_7_flex_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_7_flex_strength_conformity", store=True)

    @api.depends('avg_7_flex_strength','eln_ref','grade')
    def _compute_avg_7_flex_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_flex_strength_conformity = 'na'
                continue
            record.avg_7_flex_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','540252e6-0d76-4abb-b771-3e50cb6d5f8f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','540252e6-0d76-4abb-b771-3e50cb6d5f8f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_flex_strength - record.avg_7_flex_strength*mu_value
                    upper = record.avg_7_flex_strength + record.avg_7_flex_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_7_flex_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_7_flex_strength_conformity = 'fail'

    avg_7_flex_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_7_flex_strength_nabl", store=True)

    @api.depends('avg_7_flex_strength','eln_ref','grade')
    def _compute_avg_7_flex_strength_nabl(self):
        
        for record in self:
            record.avg_7_flex_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','540252e6-0d76-4abb-b771-3e50cb6d5f8f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','540252e6-0d76-4abb-b771-3e50cb6d5f8f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_flex_strength - record.avg_7_flex_strength*mu_value
                    upper = record.avg_7_flex_strength + record.avg_7_flex_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_7_flex_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_7_flex_strength_nabl = 'fail'


    avg_28_flex_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_28_flex_strength_conformity", store=True)

    @api.depends('avg_28_flex_strength','eln_ref','grade')
    def _compute_avg_28_flex_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_flex_strength_conformity = 'na'
                continue
            record.avg_28_flex_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e822841-9a00-4a97-a788-7327c4290273')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e822841-9a00-4a97-a788-7327c4290273')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_flex_strength - record.avg_28_flex_strength*mu_value
                    upper = record.avg_28_flex_strength + record.avg_28_flex_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_28_flex_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_28_flex_strength_conformity = 'fail'

    avg_28_flex_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_28_flex_strength_nabl", store=True)

    @api.depends('avg_28_flex_strength','eln_ref','grade')
    def _compute_avg_28_flex_strength_nabl(self):
        
        for record in self:
            record.avg_28_flex_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e822841-9a00-4a97-a788-7327c4290273')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e822841-9a00-4a97-a788-7327c4290273')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_flex_strength - record.avg_28_flex_strength*mu_value
                    upper = record.avg_28_flex_strength + record.avg_28_flex_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_28_flex_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_28_flex_strength_nabl = 'fail'


    



    


    
    


    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            record.sieve_visible = False
            record.elongation_fl_visible = False
            record.impact_visible = False
            record.specific_gravity_visible = False
            record.soundness_na2so4_visible = False
            record.soundness_mgso4_visible = False
            record.comp_strength_visible = False
            record.flexural_strength_visible = False
           
            
            




            for sample in record.sample_parameters:

                if sample.internal_id == 'bece5e9a-f1c4-406a-9cd7-251e4d7b00f9':
                    record.sieve_visible = True

                if sample.internal_id == 'df9d9803-d458-4e8f-965c-ecd9f5974f84':
                    record.elongation_fl_visible = True

                if sample.internal_id == '5d55143e-9447-47ba-9477-31eabb5fe40f':
                    record.impact_visible = True

                if sample.internal_id == '15b2b0c7-76d8-46a5-b9ac-11ac817e2f78':
                    record.specific_gravity_visible = True
                
                if sample.internal_id == '74165249-323c-4adf-ad2a-2fa1d68536de':
                    record.soundness_na2so4_visible = True

                if sample.internal_id == '2823d838-885e-46b2-8b86-c712e821ccf2':
                    record.soundness_mgso4_visible = True

                if sample.internal_id == '8d8bad46-5632-4a0f-af09-4d433279c709':
                    record.comp_strength_visible = True

                if sample.internal_id == '22671418-c2ed-49c1-ac23-460876e9da65':
                    record.flexural_strength_visible = True


                
                   
                
                
                
                
               

                




    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()

            # Sieve Analysis
            if result.parameter.internal_id == 'bece5e9a-f1c4-406a-9cd7-251e4d7b00f9':
                result.calculated = True


            # Elongation
            if result.parameter.internal_id == 'df9d9803-d458-4e8f-965c-ecd9f5974f84':
                result.result_char = round(self.elongation_index,2)
                result.calculated = True
                if self.elongation_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            
            # Flakiness
            if result.parameter.internal_id == 'c224881c-bd16-42b5-b502-cb2ed8b85ebb':
                result.result_char = round(self.flakiness_index,2)
                result.calculated = True
                if self.flakiness_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # impact value 
            if result.parameter.internal_id == '5d55143e-9447-47ba-9477-31eabb5fe40f':
                result.calculated = True
                result.result_char = round(self.average_impact_value,2)
                if self.impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # specific gravity 
            if result.parameter.internal_id == '15b2b0c7-76d8-46a5-b9ac-11ac817e2f78':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '8f20b97e-e578-4a24-b885-f11f95874377':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            
            # Soundness - Na2SO4
            if result.parameter.internal_id == '74165249-323c-4adf-ad2a-2fa1d68536de':
                result.calculated = True
                result.result_char = round(self.total_weighted_avg,2)
                if self.total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Soundness - MgSO4
            if result.parameter.internal_id == '2823d838-885e-46b2-8b86-c712e821ccf2':
                result.calculated = True
                result.result_char = round(self.mag_total_weighted_avg,2)
                if self.mag_total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Compressive Strength Of Pavement Quality Concrete (PQC)
            if result.parameter.internal_id == '8d8bad46-5632-4a0f-af09-4d433279c709':
                result.calculated = True

            # 7 Days Compressive Strength 
            if result.parameter.internal_id == 'afe730f2-e917-40f4-b039-5aefab017e9f':
                result.calculated = True
                result.result_char = round(self.avg_7_comp_strength,2)
                if self.avg_7_comp_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 28 Days Compressive Strength 
            if result.parameter.internal_id == '5ea9024b-c9aa-488e-aebe-383bd0b98ba4':
                result.calculated = True
                result.result_char = round(self.avg_28_comp_strength,2)
                if self.avg_28_comp_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 


            # Flexural Strength Of Pavement Quality Concrete (PQC)
            if result.parameter.internal_id == '22671418-c2ed-49c1-ac23-460876e9da65':
                result.calculated = True

            # 7 Days Flexural Strength 
            if result.parameter.internal_id == '540252e6-0d76-4abb-b771-3e50cb6d5f8f':
                result.calculated = True
                result.result_char = round(self.avg_7_flex_strength,2)
                if self.avg_7_flex_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 28 Days Flexural Strength 
            if result.parameter.internal_id == '8e822841-9a00-4a97-a788-7327c4290273':
                result.calculated = True
                result.result_char = round(self.avg_28_flex_strength,2)
                if self.avg_28_flex_strength_nabl == 'pass':
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
        record = super(PavementQualityConcrete, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        # self.default_get(fields)

        return super(PavementQualityConcrete, self).read(fields=fields, load=load)

   
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
        record = self.env['mechanical.pavement.quality.concrete'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



class PQCSieveAnalysisLine(models.Model):
    _name = "mechanical.pqc.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    cumulative_percent = fields.Float(string="Cum. Weight Retained (gm)",compute="_compute_cumulative_percent",
    store=True,)
    percent_retained = fields.Float(string='% of Weight Retained', compute="_compute_percent_retained",digits=(16,2))
    cumulative_retained = fields.Float(string="% of Cumulative Wt. Retained ", store=True,digits=(16,2))
    passing_percent = fields.Float(string="% of wt passing",digits=(16,2))
    specific_limits = fields.Char(string="Specified Limits",store=True)



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PQCSieveAnalysisLine, self).create(vals)

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

            new_self = super(PQCSieveAnalysisLine, self).write(vals)
            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass
            return new_self
        return super(PQCSieveAnalysisLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id
        res = super(PQCSieveAnalysisLine, self).unlink()
        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()
        return res

    @api.depends('wt_retained', 'parent_id.weight_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / self.parent_id.weight_of_sample) * 100
            except ZeroDivisionError:
                record.percent_retained = 0

    @api.depends('wt_retained', 'parent_id.sieve_analysis_child_lines.wt_retained')
    def _compute_cumulative_percent(self):
        for parent in self.mapped('parent_id'):
            total = 0
            lines = parent.sieve_analysis_child_lines.sorted('serial_no')

            for line in lines:
                total += line.wt_retained or 0
                line.cumulative_percent = total


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        

    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)



class PQCElongationFlakinessLine(models.Model):
    _name = "mechanical.pqc.elongation.flakiness.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete', string="Parent Id")


    passing_sieve = fields.Float("Passing IS Sieve (mm)" )
    retained_sieve = fields.Float("Retained IS Sieve (mm)" )

    total_weight = fields.Float("Total Wt of Aggregate Retained (gm)")
    wt_passing_flakiness = fields.Float("Wt Passing Flakiness Gauge (gm)")
    wt_retained_flakiness = fields.Float("Wt. Retained on Flakiness gauge (gm) = [(Total Wt of aggregate Retained (gm)) - (Wt. Passing on Flakiness gauge (gm)]",compute="_compute_wt_retained_flakiness",store=True,)
    wt_retained_elongation = fields.Float("Wt Retained Elongation Gauge (gm)")

    @api.depends("total_weight", "wt_passing_flakiness")
    def _compute_wt_retained_flakiness(self):
        for rec in self:
            rec.wt_retained_flakiness = (
                rec.total_weight - rec.wt_passing_flakiness
            )



class PQCImpactValueLine(models.Model):
    _name = "mechanical.impact.value.pqc.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of surface dry sample passing 12.5mm and retained on 10mm IS sieves, W1. (gm)")
    w2 = fields.Float("Weight of fraction passing 2.36mm sieve after the test, W2. (gm) ")
    w3 = fields.Float("Weight of fraction retained on 2.36mm sieve after the test, W3 = [ (Weight of surface dry sample passing 12.5mm and retained on 10mm IS sieves, W1) - ( Weight of fraction passing2.36mm sieve after the test, W2)")

    w4 = fields.Float(
        string="W4 = W1 - (W2 + W3)	(gm)",
        compute="_compute_values",
        store=True
    )

    aiv = fields.Float(
        string="Aggregate Impact Value (A.I.V) = (W2/W1) x 100	 (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2', 'w3')
    def _compute_values(self):
        for rec in self:
            rec.w4 = rec.w1 - (rec.w2 + rec.w3)

            if rec.w1:
                rec.aiv = (rec.w2 / rec.w1) * 100
            else:
                rec.aiv = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(PQCImpactValueLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class PQCSpecificGravityWaterAbsorptionLine(models.Model):
    _name = "pqc.specific.gravity.water.absorption.line"
    _description = "Specific Gravity And Water Absorption Test"

    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    # Input fields
    w1 = fields.Float("Weight of Saturated Aggregates + Basket in Water (W1) (gm)")
    w2 = fields.Float("Weight of Basket in Water (W2) (gm)")
    w3 = fields.Float("Weight of Saturated Surface Dry Aggregates in Air (W3) (gm)")
    w4 = fields.Float("Weight of Oven Dry Aggregates in Air (W4) (gm)")

    # Output fields
    specific_gravity = fields.Float("Specific Gravity", compute="_compute_values", store=True)
    apparent_specific_gravity = fields.Float("Apparent Specific Gravity", compute="_compute_values", store=True)
    water_absorption = fields.Float("Water Absorption (%)", compute="_compute_values", store=True)

    @api.depends('w1', 'w2', 'w3', 'w4')
    def _compute_values(self):
        for rec in self:
            try:
                denominator = rec.w3 - (rec.w1 - rec.w2)
                apparent_denominator = rec.w4 - (rec.w1 - rec.w2)

                # Specific Gravity
                rec.specific_gravity = rec.w4 / denominator if denominator else 0.0

                # Apparent Specific Gravity
                rec.apparent_specific_gravity = rec.w4 / apparent_denominator if apparent_denominator else 0.0

                # Water Absorption %
                rec.water_absorption = ((rec.w3 - rec.w4) / rec.w4) * 100 if rec.w4 else 0.0

            except Exception:
                rec.specific_gravity = 0.0
                rec.apparent_specific_gravity = 0.0
                rec.water_absorption = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(PQCSpecificGravityWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class PQCSodiumSulphateLine(models.Model):
    _name = "pqc.sodium.sulphate.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size" )
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Orignal Sample Percent")

    weight_before = fields.Float("Weight of Test Fraction Before Test (gm)")
    weight_after = fields.Float("Weight of Test Fraction After Test (gm)")

    percent_loss = fields.Float(
        "Percentage Passing Finer Sieve After Test (Actual Percentage Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average  (Corrected Percent Loss)",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before:
            rec.percent_loss = (
                (rec.weight_after / rec.weight_before)
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class PQCSodiumSulphateTwoLine(models.Model):
    _name = "pqc.sodium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size" )
    retained_sieve = fields.Char("Retained Sieve Size" )

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight of Test Fraction Before Test (gm)")
    weight_after = fields.Float("Weight of Test Fraction After Test (gm)")

    percent_loss = fields.Float(
        "Percentage Passing Finer Sieve After Test (Actual Percentage Loss)",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average  (Corrected Percent Loss)",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before:
            rec.percent_loss = (
                (rec.weight_after / rec.weight_before)
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class PQCMagnesiumSulphateLine(models.Model):
    _name = "pqc.magnesium.sulphate.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size" )
    retained_sieve = fields.Char("Retained Sieve Size" )

    grading_percent = fields.Float("Grading of Orignal Sample Percent")

    weight_before = fields.Float("Weight of Test Fraction Before Test (gm)")
    weight_after = fields.Float("Weight of Test Fraction After Test (gm)")

    percent_loss = fields.Float(
        "Percentage Passing Finer Sieve After Test (Actual Percentage Loss",compute="_compute_loss",store=True)

    weighted_avg = fields.Float(
        "Weighted Average  (Corrected Percent Loss)",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before:
            rec.percent_loss = (
               (rec.weight_after / rec.weight_before)
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class PQCMagnesiumSulphateTwoLine(models.Model):
    _name = "pqc.magnesium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size" )
    retained_sieve = fields.Char("Retained Sieve Size" )

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight of Test Fraction Before Test (gm)")
    weight_after = fields.Float("Weight of Test Fraction After Test (gm)")

    percent_loss = fields.Float(
        "Percentage Passing Finer Sieve After Test (Actual Percentage Loss)",compute="_compute_loss",store=True)

    weighted_avg = fields.Float(
        "Weighted Average  (Corrected Percent Loss)",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before:
            rec.percent_loss = (
                (rec.weight_after / rec.weight_before)
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class PQCCompressiveStrengthLine(models.Model):
    _name = "pqc.compressive.strength.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
  
    id_mark = fields.Char(string="Cube Identification No.",store=True)
    wt_sample = fields.Float(string="Weight (gms)",digits=(16,1))

    dt_of_casting = fields.Date(string="Date of casting",compute="_compute_dt_of_casting",store=True)

    # days = fields.Integer(string="No.of Days",compute="_compute_days",store=True)

    days = fields.Selection([
    ('7', '7 DAYS'),
    ('28', '28 DAYS'),], string="Age", required=True)

    dt_of_testing1 = fields.Date(string="Date of Testing",compute="_compute_dt_of_testing",store=True)

    load = fields.Float(string="Load (KN)")
    compressive_strength = fields.Float(string="Compressive Strength (MPa)",compute="_compute_strength",store=True)

    avg_compressive_strength = fields.Float(string="Avg. Compressive Strength (MPa)")

    

    dimension = fields.Char(string="Size of cube (mm)",compute="_compute_dimension",store=True)

    density = fields.Float(string="Density (gms/cc)",compute="_compute_density",store=True,digits=(16,3))



    @api.depends('parent_id.comp_size_cube') 
    def _compute_dimension(self):
        for rec in self:
            rec.dimension = rec.parent_id.comp_size_cube
            
    @api.depends('wt_sample')
    def _compute_density(self):
        for rec in self:
            if rec.wt_sample :
                rec.density = round((rec.wt_sample) / 3375,3)
            else:
                rec.density = 0.0

    

    @api.depends('load')
    def _compute_strength(self):
        for record in self:
            if record.load:
                record.compressive_strength = record.load / 22.5
            else:
                record.compressive_strength = 0.0


    @api.depends('parent_id.date_of_casting')
    def _compute_dt_of_casting(self):
        for record in self:
            record.dt_of_casting = record.parent_id.date_of_casting



    @api.depends('dt_of_casting', 'days')
    def _compute_dt_of_testing(self):
     for rec in self:
        if rec.dt_of_casting and rec.days:
            rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=int(rec.days))
        else:
            rec.dt_of_testing1 = False
   




  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(PQCCompressiveStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class PQCFlexuralStrengthLine(models.Model):
    _name = "pqc.flexural.strength.line"
    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
  
    id_mark = fields.Char(string="Cube Identification No.",store=True)
    wt_sample = fields.Float(string="Weight (gms)",digits=(16,1))

    dt_of_casting = fields.Date(string="Date of casting",compute="_compute_dt_of_casting",store=True)

    # days = fields.Integer(string="No.of Days",compute="_compute_days",store=True)

    days = fields.Selection([
    ('7', '7 DAYS'),
    ('28', '28 DAYS'),], string="Age", required=True)

    dt_of_testing1 = fields.Date(string="Date of Testing",compute="_compute_dt_of_testing",store=True)

    load = fields.Float(string="Max.Load (P) in KN")
    flexural_strength = fields.Float(string="Flexural Strength (MPa)",compute="_compute_strength",store=True)

    avg_flexural_strength = fields.Float(string="Avg. Flexural Strength (MPa)")

    

    dimension = fields.Char(string="Size of Beam L X B X B in mm",compute="_compute_dimension",store=True)

    span_length = fields.Float(string="Span Length (I) in mm")
    pos_fracture_value = fields.Float(string="Position of Fracture Value (a in mm)")
    


    @api.depends('parent_id.flexural_size_cube') 
    def _compute_dimension(self):
        for rec in self:
            rec.dimension = rec.parent_id.flexural_size_cube
          

    @api.depends('load','span_length')
    def _compute_strength(self):
        for record in self:
            if record.load and record.span_length :
                record.flexural_strength = (record.load * record.span_length) /(150*150*150) * 1000
            else:
                record.flexural_strength = 0.0


    @api.depends('parent_id.date_of_casting')
    def _compute_dt_of_casting(self):
        for record in self:
            record.dt_of_casting = record.parent_id.date_of_casting



    @api.depends('dt_of_casting', 'days')
    def _compute_dt_of_testing(self):
     for rec in self:
        if rec.dt_of_casting and rec.days:
            rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=int(rec.days))
        else:
            rec.dt_of_testing1 = False
   




  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(PQCFlexuralStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class PQCNotes(models.Model):
    _name = "pqc.notes"

    parent_id = fields.Many2one('mechanical.pavement.quality.concrete',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")





