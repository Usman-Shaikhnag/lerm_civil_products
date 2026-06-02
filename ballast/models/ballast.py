from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class BallastMechanical(models.Model):
    _name = "mechanical.ballast"
    _inherit = "lerm.eln"
    _description = 'mechanical.ballast'
    _rec_name = "name"

    name = fields.Char("Name",default="Ballast")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)
    temperature = fields.Char("Temperature",store=True)


    notes_id = fields.One2many('ballast.notes', 'parent_id',string="Notes",
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
            'res_model': 'ballast.prefill.data',
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
            # rec.average_impact_value_unit = rec._get_unit("c19a25e1-5ba8-41a9-83c4-d6276c5e7c4a")
            rec.avg_compacted_unit     = rec._get_unit("357f579d-a310-4015-bc11-28a85c53ac83")
            # rec.avg_bulk_density_unit   = rec._get_unit("385d8630-abef-410d-b70a-0dc702cc38b0")
            # rec.aggregate_elongation_unit   = rec._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667")
            # rec.aggregate_flakiness_unit   = rec._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f")
            # rec.avg_specific_gravity_unit   = rec._get_unit("3c968fb8-a40a-4035-a027-2f8ce099b522")
            # rec.avg_water_absorption_unit   = rec._get_unit("7535007b-0629-4ab7-9b8e-b972f85d618d")

    # ---- default values (create mode मध्ये दिसण्यासाठी)
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            # 'average_crushing_value_unit':   self._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71"),
            # 'average_impact_value_unit': self._get_unit("c19a25e1-5ba8-41a9-83c4-d6276c5e7c4a"),
            'avg_compacted_unit':     self._get_unit("357f579d-a310-4015-bc11-28a85c53ac83"),
            # 'avg_bulk_density_unit':   self._get_unit("385d8630-abef-410d-b70a-0dc702cc38b0"),
            # 'aggregate_elongation_unit':   self._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667"),
            # 'aggregate_flakiness_unit':   self._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f"),
            # 'avg_specific_gravity_unit':   self._get_unit("3c968fb8-a40a-4035-a027-2f8ce099b522"),
            # 'avg_water_absorption_unit':   self._get_unit("7535007b-0629-4ab7-9b8e-b972f85d618d"),
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
        record = self.env['mechanical.ballast'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


     # Sieve Analysis 
    weight_of_sample = fields.Float(string="Weight of Sample in gms")
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.ballast.sieve.analysis.line','parent_id',string="Parameter",default=lambda self: self._default_sieve_analysis_child_liness())
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")


    @api.model
    def _default_sieve_analysis_child_liness(self):
        default_lines = [
            (0, 0, {'sieve_size': '80mm'}),
            (0, 0, {'sieve_size': '63mm'}),
            (0, 0, {'sieve_size': '50mm'}),
            (0, 0, {'sieve_size': '40mm'}),
            (0, 0, {'sieve_size': '31.5mm'}),
            (0, 0, {'sieve_size': '25mm'}),
            (0, 0, {'sieve_size': '20mm'}),
            (0, 0, {'sieve_size': '16mm'}),
            (0, 0, {'sieve_size': '12.5mm'}),
            (0, 0, {'sieve_size': '10mm'}),
            (0, 0, {'sieve_size': '6.3mm'}),
            (0, 0, {'sieve_size': '4.75mm'}),
              (0, 0, {'sieve_size': 'Pan'})
            
        ]
        return default_lines


    def default_get(self, fields):
        print("From Default Value")
        res = super(BallastMechanical, self).default_get(fields)
        default_sieve_sizes = []
        
        # Safely get eln_ref with default None if not exists
        eln_ref = res.get('eln_ref') 
        
        if eln_ref:
            eln = self.env['lerm.eln'].sudo().browse(eln_ref)
            if not eln.exists():
                return res
                
            size_str = eln.size_id.size or ''
            grade_str = (eln.grade_id.grade or '').lower()
            
            # Define mappings
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
                    40: ['80 mm', '40 mm', '20 mm', '10 mm','4.75 mm','pan'],
                    20: ['40 mm', '20 mm', '10 mm', '4.75 mm','pan'],
                    16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                    12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                }
                specific_limits_mapping = {
                    40: ['100', '95 - 100', '30 - 70', '10 - 35','0 - 5', '0'],
                    20: ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                    16: ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                    12: ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
                }
            else:
                return res

            # Extract numeric part
            match = re.search(r'\d+', size_str)
            if match:
                number = int(match.group())
                sieve_list = sieve_mapping.get(number, [])
                specific_limits = specific_limits_mapping.get(number, [])
                
                # Check if lists have same length
                # if len(sieve_list) != len(specific_limits):
                #     _logger.warning(f"Mismatch in sieve sizes and limits for size {number}")
                #     return res
                    
                # Create sieve analysis lines
                for sieve_size, specific_limit in zip(sieve_list, specific_limits):
                    size = {
                        'sieve_size': sieve_size,
                        'specific_limits': specific_limit,
                    }
                    default_sieve_sizes.append((0, 0, size))
                
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
                    previous_line_record = self.env['mechanical.ballast.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
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


    # Loose Bulk Density
    loose_bulk_density_name = fields.Char("Name",default="Loose Bulk Density")
    loose_bulk_density_visible = fields.Boolean("Loose Bulk Density Visible",compute="_compute_visible")

    loose_line_ids = fields.One2many(
        'ballast.loose.bulk.density.line',
        'parent_id',
        string="Loose Bulk Density Trials"
    )

    loose_avg = fields.Float(
        string="Average Loose Bulk Density",
        compute="_compute_loose_avg",
        store=True
    )

    @api.depends('loose_line_ids.loose_bulk_density')
    def _compute_loose_avg(self):
        for rec in self:
            values = rec.loose_line_ids.mapped('loose_bulk_density')
            rec.loose_avg = sum(values) / len(values) if values else 0.0


    loose_avg_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_loose_avg_confirmity")
    
    @api.depends('loose_avg','eln_ref','grade')
    def _compute_loose_avg_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.loose_avg_confirmity = 'na'
                continue
            record.loose_avg_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','385d8630-abef-410d-b70a-0dc702cc38b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','385d8630-abef-410d-b70a-0dc702cc38b0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.loose_avg - record.loose_avg*mu_value
                    upper = record.loose_avg + record.loose_avg*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.loose_avg_confirmity = 'pass'
                        break
                    else:
                        record.loose_avg_confirmity = 'fail'

    loose_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_loose_avg_nabl",store=True)

    @api.depends('loose_avg','eln_ref','grade')
    def _compute_loose_avg_nabl(self):
        
        for record in self:
            record.loose_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','385d8630-abef-410d-b70a-0dc702cc38b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','385d8630-abef-410d-b70a-0dc702cc38b0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.loose_avg - record.loose_avg*mu_value
                    upper = record.loose_avg + record.loose_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.loose_avg_nabl = 'pass'
                        break
                    else:
                        record.loose_avg_nabl = 'fail'



    # Rodded Bulk Density
    rodded_bulk_density_name = fields.Char("Name",default="Rodded Bulk Density")
    rodded_bulk_density_visible = fields.Boolean("Rodded Bulk Density Visible",compute="_compute_visible")

    rodded_line_ids = fields.One2many(
        'ballast.rodded.bulk.density.line',
        'parent_id',
        string="Rodded Bulk Density Trials"
    )

    rodded_avg = fields.Float(
        string="Average Rodded Bulk Density",
        compute="_compute_rodded_avg",
        store=True
    )

    @api.depends('rodded_line_ids.rodded_bulk_density')
    def _compute_rodded_avg(self):
        for rec in self:
            values = rec.rodded_line_ids.mapped('rodded_bulk_density')
            rec.rodded_avg = sum(values) / len(values) if values else 0.0

    
    rodded_avg_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity', compute="_compute_rodded_avg_confirmity")
    
    @api.depends('rodded_avg','eln_ref','grade')
    def _compute_rodded_avg_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.rodded_avg_confirmity = 'na'
                continue
            record.rodded_avg_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24b6604a-960c-4c3b-a21a-57faf1cfb687')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24b6604a-960c-4c3b-a21a-57faf1cfb687')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.rodded_avg - record.rodded_avg*mu_value
                    upper = record.rodded_avg + record.rodded_avg*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.rodded_avg_confirmity = 'pass'
                        break
                    else:
                        record.rodded_avg_confirmity = 'fail'

    rodded_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_rodded_avg_nabl" ,store=True)

    @api.depends('rodded_avg','eln_ref','grade')
    def _compute_rodded_avg_nabl(self):
        
        for record in self:
            record.rodded_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24b6604a-960c-4c3b-a21a-57faf1cfb687')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24b6604a-960c-4c3b-a21a-57faf1cfb687')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.rodded_avg - record.rodded_avg*mu_value
                    upper = record.rodded_avg + record.rodded_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.rodded_avg_nabl = 'pass'
                        break
                    else:
                        record.rodded_avg_nabl = 'fail'




    # Aggregate Impact Value

    impact_value_name = fields.Char("Name",default="Aggregate Impact Value")
    impact_visible = fields.Boolean("Impact Visible",compute="_compute_visible")

    impact_value_child_lines = fields.One2many('mechanical.impact.value.ballast.line','parent_id',string="Parameter")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c19a25e1-5ba8-41a9-83c4-d6276c5e7c4a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c19a25e1-5ba8-41a9-83c4-d6276c5e7c4a')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
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

    specific_water_line_ids = fields.One2many('ballast.specific.gravity.water.absorption.line', 'parent_id', string="Observations")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3c968fb8-a40a-4035-a027-2f8ce099b522')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3c968fb8-a40a-4035-a027-2f8ce099b522')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3c968fb8-a40a-4035-a027-2f8ce099b522')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3c968fb8-a40a-4035-a027-2f8ce099b522')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7535007b-0629-4ab7-9b8e-b972f85d618d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7535007b-0629-4ab7-9b8e-b972f85d618d')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7535007b-0629-4ab7-9b8e-b972f85d618d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7535007b-0629-4ab7-9b8e-b972f85d618d')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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



  


    # Abrasion Value
    abrasion_value_name = fields.Char("Name",default="Los Angeles Abrasion Value")
    abrasion_visible = fields.Boolean("Abrasion Visible",compute="_compute_visible")

    abrasion_value_line_ids = fields.One2many('ballast.la.abrasion.line', 'parent_id', string="Observations")

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
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_abrasion_value_conformity", store=True)

    @api.depends('avg_abrasion_value','eln_ref','grade')
    def _compute_avg_abrasion_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_abrasion_value_conformity = 'na'
                continue
            record.avg_abrasion_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8c7ae324-86e4-424a-816f-cd315f75550e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8c7ae324-86e4-424a-816f-cd315f75550e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_abrasion_value - record.avg_abrasion_value*mu_value
                    upper = record.avg_abrasion_value + record.avg_abrasion_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_abrasion_value_conformity = 'pass'
                        break
                    else:
                        record.avg_abrasion_value_conformity = 'fail'

    avg_abrasion_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_abrasion_value_nabl", store=True)

    @api.depends('avg_abrasion_value','eln_ref','grade')
    def _compute_avg_abrasion_value_nabl(self):
        
        for record in self:
            record.avg_abrasion_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8c7ae324-86e4-424a-816f-cd315f75550e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8c7ae324-86e4-424a-816f-cd315f75550e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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








    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            record.sieve_visible = False
            record.loose_bulk_density_visible = False
            record.rodded_bulk_density_visible = False
            record.impact_visible = False
            record.specific_gravity_visible = False
            record.abrasion_visible = False
           
            
            




            for sample in record.sample_parameters:

                if sample.internal_id == '5117f10c-b22d-4b62-b061-2a7a14f0dd8e':
                    record.sieve_visible = True

                if sample.internal_id == '385d8630-abef-410d-b70a-0dc702cc38b0':
                    record.loose_bulk_density_visible = True

                if sample.internal_id == '24b6604a-960c-4c3b-a21a-57faf1cfb687':
                    record.rodded_bulk_density_visible = True

                if sample.internal_id == 'c19a25e1-5ba8-41a9-83c4-d6276c5e7c4a':
                    record.impact_visible = True

                if sample.internal_id == '3c968fb8-a40a-4035-a027-2f8ce099b522':
                    record.specific_gravity_visible = True
                
                if sample.internal_id == '8c7ae324-86e4-424a-816f-cd315f75550e':
                    record.abrasion_visible = True

              
              
                
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

            # Sieve Analysis
            if result.parameter.internal_id == '5117f10c-b22d-4b62-b061-2a7a14f0dd8e':
                result.calculated = True


             # Bulk Density
            if result.parameter.internal_id == '13b0b476-9876-40d2-9e51-5ea75bb6ec25':
                result.calculated = True

             # Loose bulk Density
            if result.parameter.internal_id == '385d8630-abef-410d-b70a-0dc702cc38b0':
                result.result_char = round(self.loose_avg,2)
                result.calculated = True
                if self.loose_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Rodded bulk Density
            if result.parameter.internal_id == '24b6604a-960c-4c3b-a21a-57faf1cfb687':
                result.calculated = True
                result.result_char = round(self.rodded_avg,2)
                if self.rodded_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # impact value 
            if result.parameter.internal_id == 'c19a25e1-5ba8-41a9-83c4-d6276c5e7c4a':
                result.calculated = True
                result.result_char = round(self.average_impact_value,2)
                if self.impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # specific gravity 
            if result.parameter.internal_id == '3c968fb8-a40a-4035-a027-2f8ce099b522':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '7535007b-0629-4ab7-9b8e-b972f85d618d':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 



            # Los Angeles Abrasion Value
            if result.parameter.internal_id == '8c7ae324-86e4-424a-816f-cd315f75550e':
                result.calculated = True
                result.result_char = round(self.avg_abrasion_value,2)
                if self.avg_abrasion_value_nabl == 'pass':
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
        record = super(BallastMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(BallastMechanical, self).read(fields=fields, load=load)

   
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
        record = self.env['mechanical.ballast'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



class BallastSieveAnalysisLine(models.Model):
    _name = "mechanical.ballast.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.ballast', string="Parent Id")
    
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

        return super(BallastSieveAnalysisLine, self).create(vals)

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

            new_self = super(BallastSieveAnalysisLine, self).write(vals)
            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass
            return new_self
        return super(BallastSieveAnalysisLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id
        res = super(BallastSieveAnalysisLine, self).unlink()
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


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        

    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)


class BallastLooseBulkDensityLine(models.Model):
    _name = "ballast.loose.bulk.density.line"
    parent_id = fields.Many2one('mechanical.ballast',string="Parent Id")
   
    serial_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)

    # empty_container_weight = fields.Float("Empty Container Weight (Kg)")
    container_with_material = fields.Float("Weight of Material in Container after pouring, W  (Kg)")

    # # AUTO CALCULATED W
    # loose_weight = fields.Float(
    #     "Weight of Material (W)",
    #     compute="_compute_weight",
    #     store=True
    # )
    volume_of_cont = fields.Float(string="Volume of calibrating container ,V (Lit)")
    loose_bulk_density = fields.Float(string="Loose Bulk Density of Material,W/V (Kg/Lit)",compute="_compute_loose_bulk_density")

    # @api.depends('empty_container_weight', 'container_with_material')
    # def _compute_weight(self):
    #     for rec in self:
    #         rec.loose_weight = rec.container_with_material - rec.empty_container_weight

    @api.depends('container_with_material', 'volume_of_cont')
    def _compute_loose_bulk_density(self):
        for record in self:
            if record.volume_of_cont:
                record.loose_bulk_density = record.container_with_material / record.volume_of_cont
            else:
                record.loose_bulk_density = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(BallastLooseBulkDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class BallastRoddedBulkDensityLine(models.Model):
    _name = "ballast.rodded.bulk.density.line"
    parent_id = fields.Many2one('mechanical.ballast',string="Parent Id")
   
    serial_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)

    # empty_container_weight = fields.Float("Empty Container Weight (Kg)")
    container_with_material = fields.Float("Weight of Material in Container after pouring, W  (Kg)")

    # AUTO CALCULATED W
    # rodded_weight = fields.Float(
    #     "Weight of Material (W)",
    #     compute="_compute_weight",
    #     store=True
    # )
    volume_of_cont = fields.Float(string="Volume of calibrating container ,V (Lit)")
    rodded_bulk_density = fields.Float(string="Rodded Bulk Density of Material,W/V (Kg/Lit)",compute="_compute_rodded_bulk_density")

    # @api.depends('empty_container_weight', 'container_with_material')
    # def _compute_weight(self):
    #     for rec in self:
    #         rec.rodded_weight = rec.container_with_material - rec.empty_container_weight


    @api.depends('container_with_material', 'volume_of_cont')
    def _compute_rodded_bulk_density(self):
        for record in self:
            if record.volume_of_cont:
                record.rodded_bulk_density = record.container_with_material / record.volume_of_cont
            else:
                record.rodded_bulk_density = 0.0

   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(BallastRoddedBulkDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class BallastImpactValueLine(models.Model):
    _name = "mechanical.impact.value.ballast.line"
    parent_id = fields.Many2one('mechanical.ballast',string="Parent Id")

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

        return super(BallastImpactValueLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class BallastSpecificGravityWaterAbsorptionLine(models.Model):
    _name = "ballast.specific.gravity.water.absorption.line"
    _description = "Specific Gravity And Water Absorption Test"

    parent_id = fields.Many2one('mechanical.ballast',string="Parent Id")

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

        return super(BallastSpecificGravityWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1





class BallastLAAbrasionLine(models.Model):
    _name = "ballast.la.abrasion.line"
    parent_id = fields.Many2one('mechanical.ballast',string="Parent Id")

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

        return super(BallastLAAbrasionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

    





class BallastNotes(models.Model):
    _name = "ballast.notes"

    parent_id = fields.Many2one('mechanical.ballast',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")





