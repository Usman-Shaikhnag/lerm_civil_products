from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

import base64
import io
import matplotlib.pyplot as plt
import re

class CoarseAggregateMechanical(models.Model):
    _name = "mechanical.coarse.aggregate"
    _inherit = "lerm.eln"
    _description = 'mechanical.coarse.aggregate'
    _rec_name = "name"

    name = fields.Char("Name",default="Coarse Aggregate")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)

    temprature = fields.Integer("Temperature (°C)", digits=(10,2))
    humidity = fields.Integer("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")



    


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
            # rec.average_impact_value_unit = rec._get_unit("2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2")
            rec.avg_compacted_unit     = rec._get_unit("357f579d-a310-4015-bc11-28a85c53ac83")
            # rec.avg_bulk_density_unit   = rec._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02")
            # rec.aggregate_elongation_unit   = rec._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667")
            # rec.aggregate_flakiness_unit   = rec._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f")
            # rec.avg_specific_gravity_unit   = rec._get_unit("3114db41-cfa7-49ad-9324-fcdbc9661038")
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
            # 'avg_specific_gravity_unit':   self._get_unit("3114db41-cfa7-49ad-9324-fcdbc9661038"),
            # 'avg_water_absorption_unit':   self._get_unit("22ee804f-41a3-4fd1-a301-a8d9180fba10"),
        })
        return res


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

        
    def get_all_fields(self):
        record = self.env['mechanical.coarse.aggregate'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    notes_id = fields.One2many('coarse.notes1', 'parent_id', string="Notes")
    
    # @api.model
    # def default_get(self, fields):
    #     res = super(CoarseAggregateMechanical, self).default_get(fields)

    #     default_notes = [
    #         (0, 0, {
    #             'sr_no': 'a',
    #             'notes': 'The report shall not be reproduced in fullor partially without written approval of the laboratory HOD/CEO/Maganement.',
    #         }),
    #         (0, 0, {
    #             'sr_no': 'b',
    #             'notes': 'ampling is not done by us unless mentioned otherwide.',
    #         }),
    #         (0, 0, {
    #             'sr_no': 'c',
    #             'notes': 'without a QR Code and hologram this report is considered invalid.',
    #         }),
    #         (0, 0, {
    #             'sr_no': 'd',
    #             'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
    #         }),

    #         (0, 0, {
    #             'sr_no': 'e',
    #             'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
    #         }),
    #          (0, 0, {
    #             'sr_no': 'f',
    #             'notes': 'Alldisputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
    #         }),

    #          (0, 0, {
    #             'sr_no': 'g',
    #             'notes': 'Sample willbe destroyed after 30-days from the date of test report unless otherwise Specified.',
    #         }),
    #     ]

    #     res['notes_id'] = default_notes
    #     return res


    


    


     # Sieve Analysis 
    weight_of_sample = fields.Float(string="Weight of Sample in gms")
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")
    sieve_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )

    sieve_analysis_child_lines = fields.One2many('mechanical.coarse.aggregate.sieve.analysis.line','parent_id',string="Parameter")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")


    # def default_get(self, fields):
    #     print("From Default Value")
    #     res = super(CoarseAggregateMechanical, self).default_get(fields)
    #     default_sieve_sizes = []
        
    #     # Safely get eln_ref with default None if not exists
    #     eln_ref = res.get('eln_ref') 
        
    #     if eln_ref:
    #         eln = self.env['lerm.eln'].sudo().browse(eln_ref)
    #         if not eln.exists():
    #             return res
                
    #         size_str = eln.size_id.size or ''
    #         grade_str = (eln.grade_id.grade or '').lower()
            
    #         # Define mappings
    #         if grade_str == 'single sized aggregate':
    #             sieve_mapping = {
    #                 63: ['80 mm', '63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
    #                 40: ['63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
    #                 20: ['40 mm', '20 mm', '10 mm', '4.75 mm', 'pan'],
    #                 16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
    #                 12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
    #                 10: ['12.5 mm', '10 mm', '4.75 mm', '2.36 mm', 'pan'],
    #             }
    #             specific_limits_mapping = {
    #                 63: ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
    #                 40: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
    #                 20: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
    #                 16: ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
    #                 12: ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
    #                 10: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
    #             }
    #         elif grade_str == 'graded aggregate':
    #             sieve_mapping = {
    #                 40: ['80 mm', '40 mm', '20 mm', '10 mm','4.75 mm','pan'],
    #                 20: ['40 mm', '20 mm', '10 mm', '4.75 mm','pan'],
    #                 16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
    #                 12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
    #             }
    #             specific_limits_mapping = {
    #                 40: ['100', '95 - 100', '30 - 70', '10 - 35','0 - 5', '0'],
    #                 20: ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
    #                 16: ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
    #                 12: ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
    #             }
    #         else:
    #             return res

    #         # Extract numeric part
    #         match = re.search(r'\d+', size_str)
    #         if match:
    #             number = int(match.group())
    #             sieve_list = sieve_mapping.get(number, [])
    #             specific_limits = specific_limits_mapping.get(number, [])
                
    #             # Check if lists have same length
    #             # if len(sieve_list) != len(specific_limits):
    #             #     _logger.warning(f"Mismatch in sieve sizes and limits for size {number}")
    #             #     return res
                    
    #             # Create sieve analysis lines
    #             for sieve_size, specific_limit in zip(sieve_list, specific_limits):
    #                 size = {
    #                     'sieve_size': sieve_size,
    #                     'specific_limits': specific_limit,
    #                 }
    #                 default_sieve_sizes.append((0, 0, size))
                
    #             res['sieve_analysis_child_lines'] = default_sieve_sizes

    #     return res


    @api.model
    def default_get(self, fields):
        print("From Default Value")

        res = super(CoarseAggregateMechanical, self).default_get(fields)

        # ------------------ NOTES ------------------
        if 'notes_id' in fields:
            default_notes = [
                (0, 0, {'sr_no': 'a', 'notes': 'The report shall not be reproduced in full or partially without written approval of the laboratory HOD/CEO/Management.'}),
                (0, 0, {'sr_no': 'b', 'notes': 'Sampling is not done by us unless mentioned otherwise.'}),
                (0, 0, {'sr_no': 'c', 'notes': 'Without a QR Code and hologram this report is considered invalid.'}),
                (0, 0, {'sr_no': 'd', 'notes': 'The results listed refer only to tested samples & applicable parameters. Endorsement of product is neither intended nor implied.'}),
                (0, 0, {'sr_no': 'e', 'notes': 'The use of report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.'}),
                (0, 0, {'sr_no': 'f', 'notes': 'All disputes are subject to Raipur jurisdiction. Corrections after 7 days invalidate this report.'}),
                (0, 0, {'sr_no': 'g', 'notes': 'Sample will be destroyed after 30 days from the date of test report unless otherwise specified.'}),
            ]
            res['notes_id'] = default_notes

        # ------------------ SIEVE LOGIC ------------------
        if 'sieve_analysis_child_lines' in fields:
            default_sieve_sizes = []

            eln_ref = res.get('eln_ref')
            if eln_ref:
                eln = self.env['lerm.eln'].sudo().browse(eln_ref)
                if eln.exists():

                    size_str = eln.size_id.size or ''
                    grade_str = (eln.grade_id.grade or '').lower()

                    if grade_str == 'single sized aggregate':
                        sieve_mapping = {
                            63: ['80 mm', '63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
                            40: ['63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
                            20: ['40 mm', '20 mm', '10 mm', '4.75 mm', 'pan'],
                            16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                            12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                            10: ['12.5 mm', '10 mm', '4.75 mm', '2.36 mm', 'pan'],
                        }
                        specific_limits_mapping = {
                            63: ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
                            40: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                            20: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                            16: ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
                            12: ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
                            10: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                        }

                    elif grade_str == 'graded aggregate':
                        sieve_mapping = {
                            40: ['80 mm', '40 mm', '20 mm', '10 mm', '4.75 mm', 'pan'],
                            20: ['40 mm', '20 mm', '10 mm', '4.75 mm', 'pan'],
                            16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                            12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                        }
                        specific_limits_mapping = {
                            40: ['100', '95 - 100', '30 - 70', '10 - 35', '0 - 5', '0'],
                            20: ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                            16: ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                            12: ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
                        }
                    else:
                        return res

                    match = re.search(r'\d+', size_str)
                    if match:
                        number = int(match.group())

                        sieve_list = sieve_mapping.get(number, [])
                        specific_limits = specific_limits_mapping.get(number, [])

                        for sieve_size, specific_limit in zip(sieve_list, specific_limits):
                            default_sieve_sizes.append((0, 0, {
                                'sieve_size': sieve_size,
                                'specific_limits': specific_limit,
                            }))

                        res['sieve_analysis_child_lines'] = default_sieve_sizes

        return res
        
    def populate_sieve_analysis_lines(self):
        self.ensure_one()

        eln = self.eln_ref
        if not eln:
            return

        size_str = eln.size_id.size or ''
        grade_str = (eln.grade_id.grade or '').lower()

        if grade_str == 'single sized aggregate':
            specific_limits_mapping = {
                63: ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
                40: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                20: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                16: ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
                12: ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
                10: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
            }
        elif grade_str == 'graded aggregate':
            specific_limits_mapping = {
                40: ['100', '95 - 100', '30 - 70', '10 - 35', '0 - 5', '0'],
                20: ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                16: ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                12: ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
            }
        else:
            return

        match = re.search(r'\d+', size_str)
        if match:
            number = int(match.group())
            specific_limits = specific_limits_mapping.get(number, [])

            # Only update specific_limits of existing lines
            for line, specific_limit in zip(self.sieve_analysis_child_lines, specific_limits):
                line.specific_limits = specific_limit


    graph_image_slive = fields.Binary(
            "Sieve Graph",
            compute="_compute_graph_image_slive",
            store=True
        )

    @api.depends('sieve_analysis_child_lines.passing_percent',
             'sieve_analysis_child_lines.sieve_size')
    def _compute_graph_image_slive(self):
        for record in self:
            x_vals = []
            y_vals = []

            for line in record.sieve_analysis_child_lines:
                if line.sieve_size and line.passing_percent is not None:
                    
                    # Extract numeric value from sieve_size
                    match = re.search(r'\d+\.?\d*', line.sieve_size)
                    if match:
                        x_vals.append(float(match.group()))
                        y_vals.append(line.passing_percent)

            if not x_vals:
                record.graph_image_slive = False
                continue

            # Sort values (important for graph)
            combined = sorted(zip(x_vals, y_vals), reverse=True)
            x_vals, y_vals = zip(*combined)

            # ---- Plot Graph ----
            plt.figure()
            plt.plot(x_vals, y_vals, marker='o')
            plt.xlabel("Sieve Size (mm)")
            plt.ylabel("Passing Percentage (%)")
            plt.title("Sieve Analysis Graph")
            plt.grid()

            # Save image to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)

            record.graph_image_slive = base64.b64encode(buf.read())




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
                    previous_line_record = self.env['mechanical.coarse.aggregate.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
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


    
    # Crushing Value
    crushing_value_name = fields.Char("Name",default="Crushing Value")
    crushing_visible = fields.Boolean("Crushing Visible",compute="_compute_visible")
   
    crushing_value_child_lines = fields.One2many('crushing.value.coarse.aggregate.line','parent_id',string="Parameter")

    average_crushing_value = fields.Float(string="Average Aggregate Crushing Value (%)", compute="_compute_average_crushing_value")


    @api.depends('crushing_value_child_lines.acv')
    def _compute_average_crushing_value(self):
        for rec in self:
            values = rec.crushing_value_child_lines.mapped('acv')
            rec.average_crushing_value = sum(values) / len(values) if values else 0.0

    
    average_crushing_value_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_average_crushing_value_conformity",store=True)

    average_crushing_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_crushing_value_nabl")


    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_crushing_value_conformity = 'na'
                continue

            record.average_crushing_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_crushing_value - record.average_crushing_value*mu_value
                    upper = record.average_crushing_value + record.average_crushing_value*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_crushing_value_conformity = 'pass'
                        break
                    else:
                        record.average_crushing_value_conformity = 'fail'


   


    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_nabl(self):
        
        for record in self:
            record.average_crushing_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_crushing_value - record.average_crushing_value*mu_value
            upper = record.average_crushing_value + record.average_crushing_value*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_crushing_value_nabl = 'pass'
                break
            else:
                record.average_crushing_value_nabl = 'fail'


    # Flakiness and Elongation 
    elongation_fl_name = fields.Char(default="FLAKINESS AND ELONGATION INDEX COARSE AGGREGATE")
    elongation_fl_visible = fields.Boolean("FLAKINESS AND ELONGATION INDEX",compute="_compute_visible")


    elongation_fl_table = fields.One2many('mechanical.elongation.flakiness.line','parent_id',string="Elongation Flakiness Index",default=lambda self: self.elongation_fl_table_sizes())


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


   

    total_total_weight = fields.Float("Total (Total Weight)", compute="_compute_totals", store=True)
    total_wt_passing_flakiness = fields.Float("Total (Passing Flakiness)", compute="_compute_totals", store=True)
    total_wt_retained_flakiness = fields.Float("Total (Retained Flakiness)", compute="_compute_totals", store=True)
    total_wt_retained_elongation = fields.Float("Total (Retained Elongation)", compute="_compute_totals", store=True)

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
        string="Flakiness Index (%)",
        compute="_compute_indexes",
        store=True
    )

    elongation_index = fields.Float(
        string="Elongation Index (%)",
        compute="_compute_indexes",
        store=True
    )

    combined_index = fields.Float(
        string="Combined FI + EI (%)",
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
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_elongation_index_conformity",store=True)

    elongation_index_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_elongation_index_nabl")


    @api.depends('elongation_index','eln_ref','grade')
    def _compute_elongation_index_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_index_conformity = 'na'
                continue

            record.elongation_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.elongation_index - record.elongation_index*mu_value
                    upper = record.elongation_index + record.elongation_index*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.elongation_index_conformity = 'pass'
                        break
                    else:
                        record.elongation_index_conformity = 'fail'


   


    @api.depends('elongation_index','eln_ref','grade')
    def _compute_elongation_index_nabl(self):
        
        for record in self:
            record.elongation_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')]).parameter_table
            
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
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_flakiness_index_conformity",store=True)

    flakiness_index_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_flakiness_index_nabl")


    @api.depends('flakiness_index','eln_ref','grade')
    def _compute_flakiness_index_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.flakiness_index_conformity = 'na'
                continue

            record.flakiness_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be7a60bc-bb2c-410d-b91a-4f8730a4ac6f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be7a60bc-bb2c-410d-b91a-4f8730a4ac6f')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.flakiness_index - record.flakiness_index*mu_value
                    upper = record.flakiness_index + record.flakiness_index*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.flakiness_index_conformity = 'pass'
                        break
                    else:
                        record.flakiness_index_conformity = 'fail'


   


    @api.depends('flakiness_index','eln_ref','grade')
    def _compute_flakiness_index_nabl(self):
        
        for record in self:
            record.flakiness_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be7a60bc-bb2c-410d-b91a-4f8730a4ac6f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be7a60bc-bb2c-410d-b91a-4f8730a4ac6f')]).parameter_table
            
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

    impact_value_child_lines = fields.One2many('mechanical.impact.value.coarse.aggregate.line','parent_id',string="Parameter")

    average_impact_value = fields.Float(string="Average Aggregate Impact Value (%)", compute="_compute_average_impact_value")


    @api.depends('impact_value_child_lines.aiv')
    def _compute_average_impact_value(self):
        for rec in self:
            values = rec.impact_value_child_lines.mapped('aiv')
            rec.average_impact_value = sum(values) / len(values) if values else 0.0


    average_impact_value_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_average_impact_value_conformity",store=True)

    average_impact_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_impact_value_nabl")


    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_impact_value_conformity = 'na'
                continue

            record.average_impact_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_impact_value - record.average_impact_value*mu_value
                    upper = record.average_impact_value + record.average_impact_value*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_impact_value_conformity = 'pass'
                        break
                    else:
                        record.average_impact_value_conformity = 'fail'


   


    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_nabl(self):
        
        for record in self:
            record.average_impact_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_impact_value - record.average_impact_value*mu_value
            upper = record.average_impact_value + record.average_impact_value*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_impact_value_nabl = 'pass'
                break
            else:
                record.average_impact_value_nabl = 'fail'

    # Specific Gravety 
    specific_gravity_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    specific_water_line_ids = fields.One2many('specific.gravity.water.absorption.line', 'parent_id', string="Observations")

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
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_specific_gravity_conformity",store=True)

    avg_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_specific_gravity_nabl")


    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue

            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_conformity = 'fail'


   


    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')]).parameter_table
            
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
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_water_absorption_conformity",store=True)

    avg_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_water_absorption_nabl")


    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue

            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','22ee804f-41a3-4fd1-a301-a8d9180fba10')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','22ee804f-41a3-4fd1-a301-a8d9180fba10')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.avg_water_absorption_conformity = 'fail'


   


    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','22ee804f-41a3-4fd1-a301-a8d9180fba10')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','22ee804f-41a3-4fd1-a301-a8d9180fba10')]).parameter_table
            
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


    # DELETERIOUS MATERIAL (COAL & LIGNITE)

    deleterious_coal_lignite_name = fields.Char("Name",default="DELETERIOUS MATERIAL (COAL & LIGNITE)")
    deleterious_coal_lignite_visible = fields.Boolean("DELETERIOUS MATERIAL (COAL & LIGNITE) Visible",compute="_compute_visible")

    deleterious_coal_lignite_line_ids = fields.One2many('deleterious.material.coal.lignite.line', 'parent_id', string="Observations")

    avg_deleterious_coal_lignite = fields.Float(
        "Average Percentage of Deleterious Material (%)",
        compute="_compute_avg_deleterious_coal_lignite",
        store=True
    )

    @api.depends('deleterious_coal_lignite_line_ids.deleterious_percent')
    def _compute_avg_deleterious_coal_lignite(self):
        for rec in self:
            lines = rec.deleterious_coal_lignite_line_ids

            if lines:
                values = lines.mapped('deleterious_percent')
                rec.avg_deleterious_coal_lignite = sum(values) / len(values)
            else:
                rec.avg_deleterious_coal_lignite = 0.0


    avg_deleterious_coal_lignite_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_deleterious_coal_lignite_conformity",store=True)

    avg_deleterious_coal_lignite_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_deleterious_coal_lignite_nabl")


    @api.depends('avg_deleterious_coal_lignite','eln_ref','grade')
    def _compute_avg_deleterious_coal_lignite_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_deleterious_coal_lignite_conformity = 'na'
                continue

            record.avg_deleterious_coal_lignite_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7cc6b68-2550-4e1e-a28e-8526295e733f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7cc6b68-2550-4e1e-a28e-8526295e733f')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_deleterious_coal_lignite - record.avg_deleterious_coal_lignite*mu_value
                    upper = record.avg_deleterious_coal_lignite + record.avg_deleterious_coal_lignite*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_deleterious_coal_lignite_conformity = 'pass'
                        break
                    else:
                        record.avg_deleterious_coal_lignite_conformity = 'fail'


   


    @api.depends('avg_deleterious_coal_lignite','eln_ref','grade')
    def _compute_avg_deleterious_coal_lignite_nabl(self):
        
        for record in self:
            record.avg_deleterious_coal_lignite_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7cc6b68-2550-4e1e-a28e-8526295e733f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7cc6b68-2550-4e1e-a28e-8526295e733f')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_deleterious_coal_lignite - record.avg_deleterious_coal_lignite*mu_value
            upper = record.avg_deleterious_coal_lignite + record.avg_deleterious_coal_lignite*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_deleterious_coal_lignite_nabl = 'pass'
                break
            else:
                record.avg_deleterious_coal_lignite_nabl = 'fail'

  


    # Abrasion Value
    abrasion_value_name = fields.Char("Name",default="Los Angeles Abrasion Value")
    abrasion_visible = fields.Boolean("Abrasion Visible",compute="_compute_visible")

    abrasion_value_line_ids = fields.One2many('la.abrasion.line', 'parent_id', string="Observations")

    avg_abrasion_value = fields.Float(
        "Average Value of L.A. Abrasion Value (%)",
        compute="_compute_avg_abrasion_value",
        store=True
    )

    @api.depends('abrasion_value_line_ids.la_value')
    def _compute_avg_abrasion_value(self):
        for rec in self:
            lines = rec.abrasion_value_line_ids

            if lines:
                values = lines.mapped('la_value')
                rec.avg_abrasion_value = sum(values) / len(values)
            else:
                rec.avg_abrasion_value = 0.0 

    avg_abrasion_value_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_abrasion_value_conformity",store=True)

    avg_abrasion_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_abrasion_value_nabl")


    @api.depends('avg_abrasion_value','eln_ref','grade')
    def _compute_avg_abrasion_value_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_abrasion_value_conformity = 'na'
                continue

            record.avg_abrasion_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_abrasion_value - record.avg_abrasion_value*mu_value
                    upper = record.avg_abrasion_value + record.avg_abrasion_value*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_abrasion_value_conformity = 'pass'
                        break
                    else:
                        record.avg_abrasion_value_conformity = 'fail'


   


    @api.depends('avg_abrasion_value','eln_ref','grade')
    def _compute_avg_abrasion_value_nabl(self):
        
        for record in self:
            record.avg_abrasion_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_abrasion_value - record.avg_abrasion_value*mu_value
            upper = record.avg_abrasion_value + record.avg_abrasion_value*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_abrasion_value_nabl = 'pass'
                break
            else:
                record.avg_abrasion_value_nabl = 'fail'


    
    # Material Finer than 75 Micron

    finer75_name = fields.Char("Name",default="Material Finer than 75 Micron")					
    finer75_visible = fields.Boolean("Material Finer than 75 Micron Visible",compute="_compute_visible")

    finer75_line_ids = fields.One2many('material.finer.75.line', 'parent_id', string="Observations")

    avg_finer_percent = fields.Float(
        "Average Value of % Material Finer than 75 micron",
        compute="_compute_avg_finer_percent",
        store=True
    )

    @api.depends('finer75_line_ids.finer_percent')
    def _compute_avg_finer_percent(self):
        for rec in self:
            lines = rec.finer75_line_ids

            if lines:
                values = lines.mapped('finer_percent')
                rec.avg_finer_percent = sum(values) / len(values)
            else:
                rec.avg_finer_percent = 0.0

    avg_finer_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_finer_percent_conformity", store=True)

    @api.depends('avg_finer_percent','eln_ref','grade')
    def _compute_avg_finer_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_finer_percent_conformity = 'na'
                continue
            record.avg_finer_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_finer_percent - record.avg_finer_percent*mu_value
                    upper = record.avg_finer_percent + record.avg_finer_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_finer_percent_conformity = 'pass'
                        break
                    else:
                        record.avg_finer_percent_conformity = 'fail'

    avg_finer_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_finer_percent_nabl", store=True)

    @api.depends('avg_finer_percent','eln_ref','grade')
    def _compute_avg_finer_percent_nabl(self):
        
        for record in self:
            record.avg_finer_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_finer_percent - record.avg_finer_percent*mu_value
            upper = record.avg_finer_percent + record.avg_finer_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_finer_percent_nabl = 'pass'
                break
            else:
                record.avg_finer_percent_nabl = 'fail'

    
    # TEN PERCENT FINES VALUE (10% FINE VALUE) OF COARSE AGGREGATE			

    name_10fine = fields.Char(default="10% Fine Value")
    fine10_visible = fields.Boolean("10% Fine Visible",compute="_compute_visible")		

    fine10_line_ids = fields.One2many('tfv.line', 'parent_id', string="Observations")

    load_10percent_fine_values = fields.Float(
        "Average Value of 10% Fines Value (kN)",
        compute="_compute_avged",
        store=True
    )

    @api.depends('fine10_line_ids.tfv')
    def _compute_avged(self):
        for rec in self:
            lines = rec.fine10_line_ids

            if lines:
                values = lines.mapped('tfv')
                rec.load_10percent_fine_values = sum(values) / len(values)
            else:
                rec.load_10percent_fine_values = 0.0	


    load_10percent_fine_values_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_load_10percent_fine_values_conformity", store=True)



    @api.depends('load_10percent_fine_values','eln_ref','grade')
    def _compute_load_10percent_fine_values_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.load_10percent_fine_values_conformity = 'na'
                continue
            record.load_10percent_fine_values_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.load_10percent_fine_values - record.load_10percent_fine_values*mu_value
                    upper = record.load_10percent_fine_values + record.load_10percent_fine_values*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.load_10percent_fine_values_conformity = 'pass'
                        break
                    else:
                        record.load_10percent_fine_values_conformity = 'fail'

    load_10percent_fine_values_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_load_10percent_fine_values_nabl", store=True)

    @api.depends('load_10percent_fine_values','eln_ref','grade')
    def _compute_load_10percent_fine_values_nabl(self):
        
        for record in self:
            record.load_10percent_fine_values_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.load_10percent_fine_values - record.load_10percent_fine_values*mu_value
            upper = record.load_10percent_fine_values + record.load_10percent_fine_values*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.load_10percent_fine_values_nabl = 'pass'
                break
            else:
                record.load_10percent_fine_values_nabl = 'fail'


    # DELETERIOUS MATERIAL (CLAY & LUMPS)
    
    name_clay_lumps = fields.Char("Name",default="DELETERIOUS MATERIAL (CLAY & LUMPS)")
    clay_lump_visible = fields.Boolean("DELETERIOUS MATERIAL (CLAY & LUMPS) Visible",compute="_compute_visible")

    clay_lumps_percent_line_ids = fields.One2many('deleterious.clay.line', 'parent_id', string="Trials")

    clay_lumps_percent = fields.Float(
        "Average Deleterious Material (%)",
        compute="_compute_clay_lumps_percent",
        store=True
    )

    @api.depends('clay_lumps_percent_line_ids.percent')
    def _compute_clay_lumps_percent(self):
        for rec in self:
            lines = rec.clay_lumps_percent_line_ids

            if lines:
                values = lines.mapped('percent')
                rec.clay_lumps_percent = sum(values) / len(values)
            else:
                rec.clay_lumps_percent = 0.0


    clay_lumps_percent_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_clay_lumps_percent_conformity",store=True)

    clay_lumps_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_clay_lumps_percent_nabl")


    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.clay_lumps_percent_conformity = 'na'
                continue

            record.clay_lumps_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d7e389bc-21ad-41eb-a602-f448f996eb2f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d7e389bc-21ad-41eb-a602-f448f996eb2f')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.clay_lumps_percent - record.clay_lumps_percent*mu_value
                    upper = record.clay_lumps_percent + record.clay_lumps_percent*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.clay_lumps_percent_conformity = 'pass'
                        break
                    else:
                        record.clay_lumps_percent_conformity = 'fail'


   


    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_nabl(self):
        
        for record in self:
            record.clay_lumps_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d7e389bc-21ad-41eb-a602-f448f996eb2f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d7e389bc-21ad-41eb-a602-f448f996eb2f')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.clay_lumps_percent - record.clay_lumps_percent*mu_value
            upper = record.clay_lumps_percent + record.clay_lumps_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.clay_lumps_percent_nabl = 'pass'
                break
            else:
                record.clay_lumps_percent_nabl = 'fail'


    # Stripping Value

    stripping_value_name = fields.Char("Name", default="Stripping Value")
    stripping_value_visible = fields.Boolean("Stripping Value",compute="_compute_visible")

    stripping_value_line_ids = fields.One2many(
        'stripping.value.line',
        'parent_id',
        string="Trials"
    )

    avg_stripping = fields.Float(
        "Average Percentage of Stripping Value",
        compute="_compute_avg_stripping",
        store=True
    )

    @api.depends('stripping_value_line_ids.stripping_percent')
    def _compute_avg_stripping(self):
        for rec in self:
            lines = rec.stripping_value_line_ids

            if lines:
                values = lines.mapped('stripping_percent')
                rec.avg_stripping = sum(values) / len(values)
            else:
                rec.avg_stripping = 0.0

    avg_stripping_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_stripping_conformity", store=True)

    @api.depends('avg_stripping','eln_ref','grade')
    def _compute_avg_stripping_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_stripping_conformity = 'na'
                continue
            record.avg_stripping_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d8b6942a-6349-482a-be8b-fbc3433bedf1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d8b6942a-6349-482a-be8b-fbc3433bedf1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_stripping - record.avg_stripping*mu_value
                    upper = record.avg_stripping + record.avg_stripping*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_stripping_conformity = 'pass'
                        break
                    else:
                        record.avg_stripping_conformity = 'fail'

    avg_stripping_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_stripping_nabl", store=True)

    @api.depends('avg_stripping','eln_ref','grade')
    def _compute_avg_stripping_nabl(self):
        
        for record in self:
            record.avg_stripping_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d8b6942a-6349-482a-be8b-fbc3433bedf1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d8b6942a-6349-482a-be8b-fbc3433bedf1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_stripping - record.avg_stripping*mu_value
                    upper = record.avg_stripping + record.avg_stripping*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_stripping_nabl = 'pass'
                        break
                    else:
                        record.avg_stripping_nabl = 'fail'



    # Wet Impact Value

    wet_impact_name = fields.Char("Name", default="Wet Impact Value")
    wet_impact_visible = fields.Boolean("Wet Impact Value",compute="_compute_visible")


    wet_impact_line_ids = fields.One2many(
        'wet.impact.value.line',
        'parent_id',
        string="Trials"
    )

    avg_impact = fields.Float(
        "Average Wet Impact Value (%)",
        compute="_compute_avg_impact",
        store=True
    )


    @api.depends('wet_impact_line_ids.impact_value')
    def _compute_avg_impact(self):
        for rec in self:
            lines = rec.wet_impact_line_ids

            if lines:
                values = lines.mapped('impact_value')
                rec.avg_impact = sum(values) / len(values)
            else:
                rec.avg_impact = 0.0


    avg_impact_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_impact_conformity", store=True)

    @api.depends('avg_impact','eln_ref','grade')
    def _compute_avg_impact_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_impact_conformity = 'na'
                continue
            record.avg_impact_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a14bc765-e75a-45f8-b8bb-c7c1bf5644ab')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a14bc765-e75a-45f8-b8bb-c7c1bf5644ab')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_impact - record.avg_impact*mu_value
                    upper = record.avg_impact + record.avg_impact*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_impact_conformity = 'pass'
                        break
                    else:
                        record.avg_impact_conformity = 'fail'

    avg_impact_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_impact_nabl", store=True)

    @api.depends('avg_impact','eln_ref','grade')
    def _compute_avg_impact_nabl(self):
        
        for record in self:
            record.avg_impact_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a14bc765-e75a-45f8-b8bb-c7c1bf5644ab')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a14bc765-e75a-45f8-b8bb-c7c1bf5644ab')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_impact - record.avg_impact*mu_value
                    upper = record.avg_impact + record.avg_impact*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_impact_nabl = 'pass'
                        break
                    else:
                        record.avg_impact_nabl = 'fail'



    # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="SOUNDNESS (SODIUM SULPHATE TEST)")
    soundness_na2so4_visible = fields.Boolean("SOUNDNESS OF COARSE AGGREGATE (SODIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_sod_line_ids = fields.One2many(
        'sodium.sulphate.line',
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
    


    total_grading = fields.Float("Total Grading %", compute="_compute_totaled")
    total_weight_before = fields.Float("Total Weight Before", compute="_compute_totaled")
    total_weight_after = fields.Float("Total Weight After", compute="_compute_totaled")
    total_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totaled")
    total_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totaled")

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
        'sodium.sulphate.two.line',
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
    
    total1_grading = fields.Float("Total Grading %", compute="_compute_totally")
    total1_weight_before = fields.Float("Total Weight Before", compute="_compute_totally")
    total1_weight_after = fields.Float("Total Weight After", compute="_compute_totally")
    total1_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totally")
    total1_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totally")

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
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_total_weighted_avg_conformity",store=True)

    total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_total_weighted_avg_nabl")


    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.total_weighted_avg_conformity = 'na'
                continue

            record.total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','153f3c8b-6ccb-4db0-b89d-02db61f61e81')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','153f3c8b-6ccb-4db0-b89d-02db61f61e81')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.total_weighted_avg - record.total_weighted_avg*mu_value
                    upper = record.total_weighted_avg + record.total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.total_weighted_avg_conformity = 'fail'


   


    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_nabl(self):
        
        for record in self:
            record.total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','153f3c8b-6ccb-4db0-b89d-02db61f61e81')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','153f3c8b-6ccb-4db0-b89d-02db61f61e81')]).parameter_table
            
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
        'magnesium.sulphate.line',
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
    


    mag_total_grading = fields.Float("Total Grading %", compute="_compute_totalled")
    mag_total_weight_before = fields.Float("Total Weight Before", compute="_compute_totalled")
    mag_total_weight_after = fields.Float("Total Weight After", compute="_compute_totalled")
    mag_total_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totalled")
    mag_total_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totalled")

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
        'magnesium.sulphate.two.line',
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
    
    mag_total1_grading = fields.Float("Total Grading %", compute="_compute_totallly")
    mag_total1_weight_before = fields.Float("Total Weight Before", compute="_compute_totallly")
    mag_total1_weight_after = fields.Float("Total Weight After", compute="_compute_totallly")
    mag_total1_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totallly")
    mag_total1_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totallly")

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
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_mag_total_weighted_avg_conformity",store=True)

    mag_total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_mag_total_weighted_avg_nabl")


    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.mag_total_weighted_avg_conformity = 'na'
                continue

            record.mag_total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89650e58-11a6-42af-8eb7-187467443a79')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89650e58-11a6-42af-8eb7-187467443a79')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.mag_total_weighted_avg - record.mag_total_weighted_avg*mu_value
                    upper = record.mag_total_weighted_avg + record.mag_total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.mag_total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.mag_total_weighted_avg_conformity = 'fail'


   


    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_nabl(self):
        
        for record in self:
            record.mag_total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89650e58-11a6-42af-8eb7-187467443a79')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89650e58-11a6-42af-8eb7-187467443a79')]).parameter_table
            
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

    # Bulk Density
    loose_bulk_density_name = fields.Char("Name",default="Bulk Density")
    loose_bulk_visible = fields.Boolean("Loose Bulk Density Visible",compute="_compute_visible")

    volume_of_bucket_loose = fields.Float(string="Volume of Bucket, V")
    weight_empty_bucket_loose = fields.Float(string="Weight of Empty Bucket,M1 in g")

    sample_weight_loose = fields.Float(string="Sample Weight in kg",compute="_compute_sample_weight_loose")
    loose_bulk_density = fields.Float(string="Loose Bulk Density",compute="_compute_loose_bulk_density")

    sample_plus_bucket_loose = fields.Float(string="Bucket + Loose Aggregate")
    sample_plus_bucket_rodded = fields.Float(string="Bucket + Compacted Aggregate")
    
    sample_weight_rodded = fields.Float(string="Sample Weight in kg",compute="_compute_sample_weight_rodded")
    rodded_bulk_density = fields.Float(string="Rodded Bulk Density",compute="_compute_loose_bulk_density")



    @api.depends('volume_of_bucket_loose', 'weight_empty_bucket_loose')
    def _compute_sample_weight_loose(self):
        for record in self:
            record.sample_weight_loose = record.sample_plus_bucket_loose - record.weight_empty_bucket_loose
            record.sample_weight_rodded = record.sample_plus_bucket_rodded - record.weight_empty_bucket_rodded
    
    @api.depends('volume_of_bucket_loose', 'sample_plus_bucket_loose')
    def _compute_loose_bulk_density(self):
        for record in self:
            if record.volume_of_bucket_loose:
                record.loose_bulk_density = round((record.sample_plus_bucket_loose-record.weight_empty_bucket_loose)/record.volume_of_bucket_loose,2)
                record.rodded_bulk_density = round((record.sample_plus_bucket_rodded - record.weight_empty_bucket_loose)/record.volume_of_bucket_loose,2)
            else:
                record.loose_bulk_density = 0.0
                record.rodded_bulk_density = 0.0


    loose_bulk_density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_loose_bulk_density_conformity",store=True)

    loose_bulk_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_loose_bulk_density_nabl")


    @api.depends('loose_bulk_density','eln_ref','grade')
    def _compute_loose_bulk_density_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.loose_bulk_density_conformity = 'na'
                continue

            record.loose_bulk_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.loose_bulk_density - record.loose_bulk_density*mu_value
                    upper = record.loose_bulk_density + record.loose_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.loose_bulk_density_conformity = 'pass'
                        break
                    else:
                        record.loose_bulk_density_conformity = 'fail'


   


    @api.depends('loose_bulk_density','eln_ref','grade')
    def _compute_loose_bulk_density_nabl(self):
        
        for record in self:
            record.loose_bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.loose_bulk_density - record.loose_bulk_density*mu_value
            upper = record.loose_bulk_density + record.loose_bulk_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.loose_bulk_density_nabl = 'pass'
                break
            else:
                record.loose_bulk_density_nabl = 'fail'



        

    rodded_bulk_density_name = fields.Char("Name",default="Rodded Bulk Density (RBD)")
    rodded_bulk_visible = fields.Boolean("Rodded Bulk Density Visible",compute="_compute_visible")



    rodded_bulk_density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_rodded_bulk_density_conformity",store=True)

    rodded_bulk_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_rodded_bulk_density_nabl")


    @api.depends('rodded_bulk_density','eln_ref','grade')
    def _compute_rodded_bulk_density_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.rodded_bulk_density_conformity = 'na'
                continue

            record.rodded_bulk_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','155935d1-24d9-4276-9e4f-453803342e8c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','155935d1-24d9-4276-9e4f-453803342e8c')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.rodded_bulk_density - record.rodded_bulk_density*mu_value
                    upper = record.rodded_bulk_density + record.rodded_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.rodded_bulk_density_conformity = 'pass'
                        break
                    else:
                        record.rodded_bulk_density_conformity = 'fail'


   


    @api.depends('rodded_bulk_density','eln_ref','grade')
    def _compute_rodded_bulk_density_nabl(self):
        
        for record in self:
            record.rodded_bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','155935d1-24d9-4276-9e4f-453803342e8c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','155935d1-24d9-4276-9e4f-453803342e8c')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.rodded_bulk_density - record.rodded_bulk_density*mu_value
            upper = record.rodded_bulk_density + record.rodded_bulk_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.rodded_bulk_density_nabl = 'pass'
                break
            else:
                record.rodded_bulk_density_nabl = 'fail'




    # Bulk Density
    compacted_density_name1 = fields.Char("Name",default="Compacted Density ")
    compacted_density_visible = fields.Boolean("compacted density  Visible",compute="_compute_visible")

    wt_of_compact = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    weight_empty_cylender = fields.Float(string="Wt of empty measuring cylinder (A) (Kg)")
    volume_of_cylender = fields.Float(string="Volume of measuring cylinder (v) (lit)")
    compact_bulk = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk",digits=(12,3))
    volume_of_cylender1 = fields.Float(string="Volume of measuring cylinder (v) (lit)")
    weight_empty_cylender1 = fields.Float(string="Wt of empty measuring cylinder (A) (Kg)")

    # avg_bulk_density = fields.Float(string="Avg bulk density ",compute="_compute_avg_bulk_density",digits=(12,3))

    @api.depends('wt_of_compact', 'weight_empty_bucket_loose', 'volume_of_bucket_loose')
    def _compute_compact_bulk(self):
        for rec in self:
            if rec.volume_of_bucket_loose and rec.wt_of_compact and rec.weight_empty_bucket_loose:
                rec.compact_bulk = (rec.wt_of_compact - rec.weight_empty_bucket_loose) / rec.volume_of_bucket_loose
            else:
                rec.compact_bulk = 0.0

    

    wt_of_compact1 = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    compact_bulk1 = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk1",digits=(12,3))

    @api.depends('wt_of_compact1', 'weight_empty_bucket_loose', 'volume_of_bucket_loose')
    def _compute_compact_bulk1(self):
        for rec in self:
            if rec.volume_of_bucket_loose and rec.wt_of_compact1 and rec.weight_empty_bucket_loose:
                rec.compact_bulk1 = (rec.wt_of_compact1 - rec.weight_empty_bucket_loose) / rec.volume_of_bucket_loose
            else:
                rec.compact_bulk1 = 0.0

    avg_compacted = fields.Float(string="Avg Compacted Density",compute="_compute_avg_compacted",digits=(12,3))

    # Average
    @api.depends('compact_bulk', 'compact_bulk1')
    def _compute_avg_compacted(self):
        for rec in self:
            if rec.compact_bulk and rec.compact_bulk1:
                rec.avg_compacted = (rec.compact_bulk + rec.compact_bulk1) / 2
            else:
                rec.avg_compacted = 0.0


       

   
    avg_compacted_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_compacted_conformity",store=True)

    avg_compacted_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_compacted_nabl")


    @api.depends('avg_compacted','eln_ref','grade')
    def _compute_avg_compacted_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_compacted_conformity = 'na'
                continue

            record.avg_compacted_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_compacted - record.avg_compacted*mu_value
                    upper = record.avg_compacted + record.avg_compacted*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_compacted_conformity = 'pass'
                        break
                    else:
                        record.avg_compacted_conformity = 'fail'


   


    @api.depends('avg_compacted','eln_ref','grade')
    def _compute_avg_compacted_nabl(self):
        
        for record in self:
            record.avg_compacted_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_compacted - record.avg_compacted*mu_value
            upper = record.avg_compacted + record.avg_compacted*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_compacted_nabl = 'pass'
                break
            else:
                record.avg_compacted_nabl = 'fail'

      # Deleterious Material - Organic Impurities

    organic_impurities_name = fields.Char( "Name", default="Deleterious Material - Organic Impurities")
    organic_impurities_visible = fields.Boolean( "Deleterious Material - Organic Impurities",compute="_compute_visible")

    sample_color = fields.Selection([
    ('lighter', 'Lighter than Standard'),
    ('same', 'Same as Standard'),
    ('darker', 'Darker than Standard')
      ], string="Sample Color")


    organic_impurities_result = fields.Selection([
    ('pass', 'Pass'),
    ('fail', 'Fail')
        ], string="Organic Impurities Result",
   compute="_compute_organic_impurities",
   store=True
         )


    @api.depends('sample_color')
    def _compute_organic_impurities(self):
      for rec in self:
        if rec.sample_color in ['lighter', 'same']:
            rec.organic_impurities_result = 'pass'
        elif rec.sample_color == 'darker':
            rec.organic_impurities_result = 'fail'
        else:
            rec.organic_impurities_result = False


    






    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            record.sieve_visible = False
            record.loose_bulk_visible = False
            record.rodded_bulk_visible = False
            record.crushing_visible = False
            record.elongation_fl_visible = False
            record.impact_visible = False
            record.specific_gravity_visible = False
            record.deleterious_coal_lignite_visible = False
            record.abrasion_visible = False
            record.finer75_visible = False
            record.fine10_visible = False
            record.clay_lump_visible = False
            record.stripping_value_visible = False
            record.wet_impact_visible = False
            record.soundness_na2so4_visible = False
            record.soundness_mgso4_visible = False
            record.compacted_density_visible = False
            record.organic_impurities_visible = False
           
            
            




            for sample in record.sample_parameters:

                if sample.internal_id == 'c2168fff-e47c-4155-99ff-9d7dc223e768':
                    record.sieve_visible = True

                if sample.internal_id == '65a41d1f-d557-438e-8fd1-2c619a334d02':
                    record.loose_bulk_visible = True

                if sample.internal_id == '155935d1-24d9-4276-9e4f-453803342e8c':
                    record.rodded_bulk_visible = True

                if sample.internal_id == 'ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71':
                    record.crushing_visible = True

                if sample.internal_id == '9effe915-e5a3-45a7-aaeb-10caababd667':
                    record.elongation_fl_visible = True

                if sample.internal_id == '2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2':
                    record.impact_visible = True

                if sample.internal_id == '3114db41-cfa7-49ad-9324-fcdbc9661038':
                    record.specific_gravity_visible = True
                
                if sample.internal_id == 'e7cc6b68-2550-4e1e-a28e-8526295e733f':
                    record.deleterious_coal_lignite_visible = True
                
                if sample.internal_id == '37f2161e-5cc0-413f-b76c-10478c65baf9':
                    record.abrasion_visible = True

                if sample.internal_id == '988f5bf6-c865-453c-9cd6-993a5a59ad95':
                    record.finer75_visible = True

                if sample.internal_id == '5f506c08-4369-491d-93a6-030514c29661':
                    record.fine10_visible = True

                if sample.internal_id == 'd7e389bc-21ad-41eb-a602-f448f996eb2f':
                    record.clay_lump_visible = True

                if sample.internal_id == 'd8b6942a-6349-482a-be8b-fbc3433bedf1':
                    record.stripping_value_visible = True

                if sample.internal_id == 'a14bc765-e75a-45f8-b8bb-c7c1bf5644ab':
                    record.wet_impact_visible = True
              
                
                if sample.internal_id == '153f3c8b-6ccb-4db0-b89d-02db61f61e81':
                    record.soundness_na2so4_visible = True
                if sample.internal_id == '89650e58-11a6-42af-8eb7-187467443a79':
                    record.soundness_mgso4_visible = True

                if sample.internal_id == '357f579d-a310-4015-bc11-28a85c53ac83':
                    record.compacted_density_visible = True

                if sample.internal_id == '9998tyu5-a3f2-440a-b634-76f469d220c7':
                    record.organic_impurities_visible = True
             

                
                   
                
                
                
                
               

                




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
            if result.parameter.internal_id == 'c2168fff-e47c-4155-99ff-9d7dc223e768':
                result.calculated = True


             # Bulk Density
            if result.parameter.internal_id == '8b439d0e-2967-488a-9214-87d68599571a':
                result.calculated = True

             # Loose bulk Density
            if result.parameter.internal_id == '65a41d1f-d557-438e-8fd1-2c619a334d02':
                result.result_char = round(self.loose_bulk_density,2)
                result.calculated = True
                if self.loose_bulk_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Rodded bulk Density
            if result.parameter.internal_id == '155935d1-24d9-4276-9e4f-453803342e8c':
                result.calculated = True
                result.result_char = round(self.rodded_bulk_density,2)
                if self.rodded_bulk_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # crushing value 
            if result.parameter.internal_id == 'ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71':
                result.calculated = True
                result.result_char = round(self.average_crushing_value,2)
                if self.average_crushing_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Elongation
            if result.parameter.internal_id == '9effe915-e5a3-45a7-aaeb-10caababd667':
                result.result_char = round(self.elongation_index,2)
                result.calculated = True
                if self.elongation_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            
            # Flakiness
            if result.parameter.internal_id == 'be7a60bc-bb2c-410d-b91a-4f8730a4ac6f':
                result.result_char = round(self.flakiness_index,2)
                result.calculated = True
                if self.flakiness_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # impact value 
            if result.parameter.internal_id == '2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2':
                result.calculated = True
                result.result_char = round(self.average_impact_value,2)
                if self.average_impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # specific gravity 
            if result.parameter.internal_id == '3114db41-cfa7-49ad-9324-fcdbc9661038':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '22ee804f-41a3-4fd1-a301-a8d9180fba10':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            # Deleterious Material - Lightweight Pieces (Coal & Lignite)
            if result.parameter.internal_id == 'e7cc6b68-2550-4e1e-a28e-8526295e733f':
                result.calculated = True
                result.result_char = round(self.avg_deleterious_coal_lignite,2)
                if self.avg_deleterious_coal_lignite_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Los Angeles Abrasion Value
            if result.parameter.internal_id == '37f2161e-5cc0-413f-b76c-10478c65baf9':
                result.calculated = True
                result.result_char = round(self.avg_abrasion_value,2)
                if self.avg_abrasion_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Material finer than 75 micron
            if result.parameter.internal_id == '988f5bf6-c865-453c-9cd6-993a5a59ad95':
                result.calculated = True
                result.result_char = round(self.avg_finer_percent,2)
                if self.avg_finer_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 10 % Fine Value
            if result.parameter.internal_id == '5f506c08-4369-491d-93a6-030514c29661':
                result.calculated = True
                result.result_char = round(self.load_10percent_fine_values,2)
                if self.load_10percent_fine_values_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # DELETERIOUS MATERIAL (CLAY & LUMPS)
            if result.parameter.internal_id == 'd7e389bc-21ad-41eb-a602-f448f996eb2f':
                result.calculated = True
                result.result_char = round(self.clay_lumps_percent,2)
                if self.clay_lumps_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Stripping Value
            if result.parameter.internal_id == 'd8b6942a-6349-482a-be8b-fbc3433bedf1':
                result.calculated = True
                result.result_char = round(self.avg_stripping,2)
                if self.avg_stripping_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Wet Impact Value
            if result.parameter.internal_id == 'a14bc765-e75a-45f8-b8bb-c7c1bf5644ab':
                result.calculated = True
                result.result_char = round(self.avg_impact,2)
                if self.avg_impact_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Soundness - Na2SO4
            if result.parameter.internal_id == '153f3c8b-6ccb-4db0-b89d-02db61f61e81':
                result.calculated = True
                result.result_char = round(self.total_weighted_avg,2)
                if self.total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Soundness - MgSO4
            if result.parameter.internal_id == '89650e58-11a6-42af-8eb7-187467443a79':
                result.calculated = True
                result.result_char = round(self.mag_total_weighted_avg,2)
                if self.mag_total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '357f579d-a310-4015-bc11-28a85c53ac83':
                result.calculated = True
                result.result_char = round(self.avg_compacted,2)
                if self.avg_compacted_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            #  Deleterious Material - Organic Impurities
            if result.parameter.internal_id == '9998tyu5-a3f2-440a-b634-76f469d220c7':
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
        record = super(CoarseAggregateMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(CoarseAggregateMechanical, self).read(fields=fields, load=load)

   
    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        # parameter_based_assignment
        current_user = self.env.user
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # filter parameter results by current user
            user_param_results = record.eln_ref.parameters_result.filtered(
                lambda r: r.technician and r.technician.id == current_user.id
            )

            # map to parameter master IDs
            parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]



    def get_all_fields(self):
        record = self.env['mechanical.coarse.aggregate'].browse(self.ids[0])
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
    _name = "mechanical.coarse.aggregate.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
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

    # @api.depends('wt_retained', 'parent_id.weight_of_sample')
    # def _compute_percent_retained(self):
    #     for record in self:
    #         try:
    #             record.percent_retained = (record.wt_retained / self.parent_id.weight_of_sample) * 100
    #         except ZeroDivisionError:
    #             record.percent_retained = 0

    @api.depends('parent_id.weight_of_sample', 'wt_retained')
    def _compute_percent_retained(self):
        for rec in self:
            if rec.parent_id.weight_of_sample:
                rec.percent_retained = (rec.wt_retained / rec.parent_id.weight_of_sample) * 100
            else:
                rec.percent_retained = 0


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        

    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)



class CrushingValueLine(models.Model):
    _name = "crushing.value.coarse.aggregate.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)


    w1 = fields.Float("Weight of Mould + Aggregate (W1)")
    w2 = fields.Float("Weight of Empty Mould (W2)")
    w3 = fields.Float("Weight Passing 2.36 mm Sieve (W3)")

    acv = fields.Float(
        string="Aggregate Crushing Value (A.C.V) = W3/(W1-W2)x 100",
        compute="_compute_acv",
        store=True
    )

    @api.depends('w1', 'w2', 'w3')
    def _compute_acv(self):
        for rec in self:
            if (rec.w1 - rec.w2) != 0:
                rec.acv = (rec.w3 / (rec.w1 - rec.w2)) * 100
            else:
                rec.acv = 0.0


    @api.depends('total_wt_aggregate', 'wt_of_aggregate_retained')
    def _compute_wt_of_aggregate_retained(self):
        for rec in self:
            rec.wt_of_aggregate_passing = rec.total_wt_aggregate - rec.wt_of_aggregate_retained


    @api.depends('wt_of_aggregate_passing', 'total_wt_aggregate')
    def _compute_crushing_value(self):
        for rec in self:
            if rec.total_wt_aggregate != 0:
                rec.crushing_value = (rec.wt_of_aggregate_passing / rec.total_wt_aggregate) * 100
            else:
                rec.crushing_value = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(CrushingValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class ElongationFlakinessLine(models.Model):
    _name = "mechanical.elongation.flakiness.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")


    passing_sieve = fields.Float("Passing IS Sieve (mm)")
    retained_sieve = fields.Float("Retained IS Sieve (mm)")

    total_weight = fields.Float("Total Wt of Aggregate Retained (gm)")
    wt_passing_flakiness = fields.Float("Wt Passing Flakiness Gauge (gm)")
    wt_retained_flakiness = fields.Float("Wt Retained Flakiness Gauge (gm)")
    wt_retained_elongation = fields.Float("Wt Retained Elongation Gauge (gm)")



class ImpactValueLine(models.Model):
    _name = "mechanical.impact.value.coarse.aggregate.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of surface dry sample passing 12.5mm and retained on 10mm IS sieves, W1. (gm)")
    w2 = fields.Float("Weight of fraction passing 2.36mm sieve after the test, W2. (gm) ")
    w3 = fields.Float("Weight of fraction retained on 2.36mm sieve after the test, W3. (gm)")

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

        return super(ImpactValueLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class SpecificGravityWaterAbsorptionLine(models.Model):
    _name = "specific.gravity.water.absorption.line"
    _description = "Specific Gravity And Water Absorption Test"

    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

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

        return super(SpecificGravityWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class DeleteriousMaterialCoalLigniteLine(models.Model):
    _name = "deleterious.material.coal.lignite.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample taken (W1)")
    w2 = fields.Float("Weight of coal & lignite particles (W2)")

    deleterious_percent = fields.Float(
        "Deleterious Material (%)",
        compute="_compute_percent",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_percent(self):
        for rec in self:
            if rec.w1:
                rec.deleterious_percent = (rec.w2 / rec.w1) * 100
            else:
                rec.deleterious_percent = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(DeleteriousMaterialCoalLigniteLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class LAAbrasionLine(models.Model):
    _name = "la.abrasion.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of oven dry sample before test (W1)")
    w2 = fields.Float("Weight retained on 1.7 mm sieve after test (W2)")

    w3 = fields.Float(
        "Weight passing 1.7 mm sieve (W1 - W2)",
        compute="_compute_values",
        store=True
    )

    la_value = fields.Float(
        "L.A. Abrasion Value (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            rec.w3 = rec.w1 - rec.w2

            if rec.w1:
                rec.la_value = ((rec.w1 - rec.w2) / rec.w1) * 100
            else:
                rec.la_value = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(LAAbrasionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

    


class MaterialFiner75Line(models.Model):
    _name = "material.finer.75.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of oven dry sample taken (W1)")
    w2 = fields.Float("Weight retained on 75 micron sieve (W2)")

    w3 = fields.Float(
        "Weight passing 75 micron sieve (W1 - W2)",
        compute="_compute_values",
        store=True
    )

    finer_percent = fields.Float(
        "Material Finer than 75 micron (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            rec.w3 = rec.w1 - rec.w2

            if rec.w1:
                rec.finer_percent = ((rec.w1 - rec.w2) / rec.w1) * 100
            else:
                rec.finer_percent = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(MaterialFiner75Line, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class TFVLine(models.Model):
    _name = "tfv.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    # Inputs
    a = fields.Float("Sample Weight (A)")
    retained = fields.Float("Weight retained on 2.36 mm sieve")
    b = fields.Float("Weight passing 2.36 mm sieve (B)")
    x = fields.Float("Maximum Force X (kN)")

    # Computed
    y = fields.Float("% Passing (Y)", compute="_compute_values", store=True)
    tfv = fields.Float("10% Fines Value (kN)", compute="_compute_values", store=True)

    @api.depends('a', 'b', 'x')
    def _compute_values(self):
        for rec in self:
            # % Passing
            rec.y = (rec.b / rec.a) * 100 if rec.a else 0.0

            # TFV
            rec.tfv = (14 * rec.x) / (rec.y + 4) if (rec.y + 4) else 0.0

    @api.constrains('a', 'b', 'retained')
    def _check_weights(self):
        for rec in self:
            if rec.a and (rec.retained + rec.b) != rec.a:
                raise ValidationError(
                    "Retained + Passing must equal Total Sample (A)"
                )
            

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(TFVLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class DeleteriousClayLine(models.Model):
    _name = "deleterious.clay.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample (W1)")
    w2 = fields.Float("Weight of clay & lumps separated (W₂)")

    percent = fields.Float(
        "Deleterious Material (%)",
        compute="_compute_percent",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_percent(self):
        for rec in self:
            rec.percent = (rec.w2 / rec.w1) * 100 if rec.w1 else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(DeleteriousClayLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class StrippingValueLine(models.Model):
    _name = "stripping.value.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of bitumen coated sample (W1)")
    w2 = fields.Float("Weight of stripped aggregate (W2)")

    stripping_percent = fields.Float(
        "Stripping Value (%)",
        compute="_compute_value",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_value(self):
        for rec in self:
            rec.stripping_percent = (rec.w1 / rec.w2) * 100 if rec.w2 else 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(StrippingValueLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class WetImpactValueLine(models.Model):
    _name = "wet.impact.value.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    # Inputs
    w1 = fields.Float("Weight before soaking (W1)")
    w_ssd = fields.Float("Weight after soaking (SSD)")
    w2 = fields.Float("Weight passing 2.36 mm (W2)")

    retained = fields.Float(
        "Weight retained on 2.36 mm",
        compute="_compute_values",
        store=True
    )

    impact_value = fields.Float(
        "Wet Impact Value (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            # Retained (optional calculation)
            rec.retained = rec.w1 - rec.w2

            # Impact Value
            rec.impact_value = (rec.w2 / rec.w1) * 100 if rec.w1 else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WetImpactValueLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class SodiumSulphateLine(models.Model):
    _name = "sodium.sulphate.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after)
                / rec.weight_before
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class SodiumSulphateTwoLine(models.Model):
    _name = "sodium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after)
                / rec.weight_before
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class MagnesiumSulphateLine(models.Model):
    _name = "magnesium.sulphate.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after)
                / rec.weight_before
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class MagnesiumSulphateTwoLine(models.Model):
    _name = "magnesium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after)
                / rec.weight_before
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100






 


# class SoundnessNa2Line(models.Model):
#     _name = "mechanical.soundness.na2so4.line"
#     parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")
    
#     sieve_size_passing = fields.Char(string="Sieve Size Passing")
#     sieve_size_retained = fields.Char(string="Sieve Size Retained")
#     weight_before_test = fields.Float(string="Weight of test fraction before test in gm.")
#     weight_after_test = fields.Float(string="Weight of test feaction Passing Finer Sieve After test")
#     grading_original_sample = fields.Float(string="Grading of Original sample in %", compute="_compute_grading")
#     passing_percent = fields.Float(string="Percentage Passing Finer Sieve After test (Percentage Loss)",compute="_compute_passing_percent")
#     cumulative_loss_percent = fields.Float(string="Commulative percentage Loss",compute="_compute_cumulative_na2so4")
    
#     @api.depends('parent_id.total_na2so4','weight_before_test')
#     def _compute_grading(self):
#         for record in self:
#             try:
#                 record.grading_original_sample = (record.weight_before_test/record.parent_id.total_na2so4)*100
#             except ZeroDivisionError:
#                 record.grading_original_sample = 0

#     @api.depends('weight_before_test','weight_after_test')
#     def _compute_passing_percent(self):
#         for record in self:
#             try:
#                 record.passing_percent = (record.weight_after_test / record.weight_before_test)*100
#             except:
#                 record.passing_percent = 0

#     @api.depends('weight_after_test', 'parent_id.total_na2so4')
#     def _compute_cumulative_na2so4(self):
#         for record in self:
#             try:
#                 record.cumulative_loss_percent = (record.weight_after_test / record.parent_id.total_na2so4) * 100
#             except:
#                 record.cumulative_loss_percent = 0



    

# class SoundnessMgLine(models.Model):
#     _name = "mechanical.soundness.mgso4.line"
#     parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")
    
#     sieve_size_passing = fields.Char(string="Sieve Size Passing")
#     sieve_size_retained = fields.Char(string="Sieve Size Retained")
#     weight_before_test = fields.Float(string="Weight of test fraction before test in gm.")
#     weight_after_test = fields.Float(string="Weight of test feaction Passing Finer Sieve After test")
#     grading_original_sample = fields.Float(string="Grading of Original sample in %", compute="_compute_grading")
#     passing_percent = fields.Float(string="Percentage Passing Finer Sieve After test (Percentage Loss)",compute="_compute_passing_percent")
#     cumulative_loss_percent = fields.Float(string="Commulative percentage Loss",compute="_compute_cumulative_mgso4")
    
#     @api.depends('parent_id.total_mgso4','weight_before_test')
#     def _compute_grading(self):
#         for record in self:
#             try:
#                 record.grading_original_sample = (record.weight_before_test/record.parent_id.total_mgso4)*100
#             except ZeroDivisionError:
#                 record.grading_original_sample = 0

#     @api.depends('weight_before_test','weight_after_test')
#     def _compute_passing_percent(self):
#         for record in self:
#             try:
#                 record.passing_percent = (record.weight_after_test / record.weight_before_test)*100
#             except:
#                 record.passing_percent = 0

#     @api.depends('weight_after_test', 'parent_id.total_mgso4')
#     def _compute_cumulative_mgso4(self):
#         for record in self:
#             try:
#                 record.cumulative_loss_percent = (record.weight_after_test / record.parent_id.total_mgso4) * 100
#             except:
#                 record.cumulative_loss_percent = 0


class CoarseNotes(models.Model):
    _name = "coarse.notes1"

    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



    







