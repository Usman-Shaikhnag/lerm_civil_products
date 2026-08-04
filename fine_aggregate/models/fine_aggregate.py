from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math



class FineAggregate(models.Model):
    _name = "mechanical.fine.aggregate"
    _inherit = "lerm.eln"
    _rec_name = "name_aggregate"


    name_aggregate = fields.Char("Name",default="Fine Aggregate")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'fine.aggregate.prefill.data',
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

  


    # Sieve Analysis 
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.fine.agg.sieve.analysis.line','parent_id',string="Parameter",default=lambda self: self._default_sieve_analysis_child_lines())
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")
    # cumulative = fields.Float(string="Cumulative",compute="_compute_cumulative")

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


        
    wt_of_sample = fields.Float(string="Weight of Sample, gms")
    zone_type = fields.Selection(
    selection=[
        ('zone_i', 'Zone I'),
        ('zone_ii', 'Zone II'),
        ('zone_iii', 'Zone III'),
        ('zone_iv', 'Zone IV'),
    ],
    string="Zone",
    required=False  
)


    fineness_modulus = fields.Float(string="Fineness Modulus", compute="_compute_fineness_modulus")
    grading = fields.Char(string="Grading",compute="_compute_zone_display_name")

    @api.depends('zone_type')
    def _compute_zone_display_name(self):
        for record in self:
            if record.zone_type:
                record.grading = dict(self._fields['zone_type'].selection).get(record.zone_type, '')
            else:
                record.grading = ''



    # @api.depends('sieve_analysis_child_lines.cumulative_retained')
    # def _compute_fineness_modulus(self):
    #     for record in self:
    #         fineness_modulus = sum(line.cumulative_retained for line in record.sieve_analysis_child_lines)/100
    #         record.fineness_modulus = fineness_modulus

    @api.depends('sieve_analysis_child_lines.cumulative_retained')
    def _compute_fineness_modulus(self):
        for record in self:
            # Exclude the last line (assumes order is important)
            lines = record.sieve_analysis_child_lines[:-1]  # all except last
            fineness_modulus = sum(line.cumulative_retained for line in lines) / 100
            record.fineness_modulus = fineness_modulus



    @api.model
    def _default_sieve_analysis_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '10 mm'}),
            (0, 0, {'sieve_size': '4.75 mm'}),
            (0, 0, {'sieve_size': '2.36 mm'}),
            (0, 0, {'sieve_size': '1.18 mm'}),
            (0, 0, {'sieve_size': '600 micron'}),
            (0, 0, {'sieve_size': '300 micron'}),
            (0, 0, {'sieve_size': '150 micron'}),
            (0, 0, {'sieve_size': '75 micron'}),
            (0, 0, {'sieve_size': 'Pan'})
            
        ]
        return default_lines

    @api.onchange('zone_type')
    def _onchange_zone_type(self):
        zone_limits = {
            'zone_i': {
                '10 mm': '100',
                '4.75 mm': '90 - 100',
                '2.36 mm': '60 - 95',
                '1.18 mm': '30 - 70',
                '600 micron': '15 - 34',
                '300 micron': '5 - 20',
                '150 micron': '0 - 10',
                '75 micron': '-',
                'Pan': '-',
            },
            'zone_ii': {
                '10 mm': '100',
                '4.75 mm': '90 - 100',
                '2.36 mm': '75 - 100',
                '1.18 mm': '55 - 90',
                '600 micron': '35 - 59',
                '300 micron': '8 - 30',
                '150 micron': '0 - 10',
                '75 micron': '-',
                'Pan': '-',
            },
            'zone_iii': {
                '10 mm': '100',
                '4.75 mm': '90 - 100',
                '2.36 mm': '85 - 100',
                '1.18 mm': '75 - 100',
                '600 micron': '60 - 79',
                '300 micron': '12 - 40',
                '150 micron': '0 - 10',
                '75 micron': '-',
                'Pan': '-',
            },
            'zone_iv': {
                '10 mm': '100',
                '4.75 mm': '95 - 100',
                '2.36 mm': '95 - 100',
                '1.18 mm': '90 - 100',
                '600 micron': '80 - 100',
                '300 micron': '15 - 50',
                '150 micron': '0 - 5',
                '75 micron': '-',
                'Pan': '-',
            }
        }

        limits = zone_limits.get(self.zone_type)
        if limits:
            for line in self.sieve_analysis_child_lines:
                line.specific_limt = limits.get(line.sieve_size, '')




    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            pan_line = None
            total_retained = 0.0
            target_sieves = ['10 mm','4.75 mm','2.36 mm','1.18 mm', '600 micron', '300 micron', '150 micron','75 micron']

            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() == 'pan':
                    pan_line = line
                elif line.sieve_size in target_sieves:
                    total_retained += line.wt_retained or 0.0

            if pan_line:
                pan_line.wt_retained = (rec.wt_of_sample or 0.0) - total_retained


    # corrected(added)
    # def calculate_sieve(self): 
    #     for record in self:
    #         previous_cumulative = 0  
    #         for line in record.sieve_analysis_child_lines:
    #             print("Rows", str(line.percent_retained))
    #             previous_line = line.serial_no - 1
    #             if previous_line == 0:
    #                 cumulative_retained = line.percent_retained
    #             else:
    #                 previous_line_record = self.env['mechanical.fine.agg.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id", "=", record.id)], limit=1)
                    
    #                 if previous_line_record:
    #                     previous_cumulative = previous_line_record.cumulative_retained
    #                 cumulative_retained = previous_cumulative + line.percent_retained

    #             passing_percent = 100 - cumulative_retained

    #             line.write({
    #                 'cumulative_retained': round(cumulative_retained, 2),
    #                 'passing_percent': round(passing_percent, 2),
    #             })
                
    #             print("Updated Cumulative Retained:", cumulative_retained)
    #             print("Updated Passing Percent:", passing_percent)

    #             previous_cumulative = cumulative_retained



    def calculate_sieve(self):
     for record in self:
        cumulative_weight = 0.0

        lines = record.sieve_analysis_child_lines.sorted(
            key=lambda line: line.serial_no
        )

        sample_weight = record.wt_of_sample or 0.0

        for line in lines:
            cumulative_weight += line.wt_retained or 0.0

            if sample_weight > 0:
                cumulative_retained = (
                    cumulative_weight / sample_weight
                ) * 100.0

                passing_percent = 100.0 - cumulative_retained

            else:
                cumulative_retained = 0.0
                passing_percent = 0.0

            line.write({
                'cumulative_percent': round(
                    cumulative_weight, 2
                ),
                'cumulative_retained': round(
                    cumulative_retained, 2
                ),
                'passing_percent': round(
                    passing_percent, 2
                ),
            })

    
    
    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))


    # DELETERIOUS MATERIAL (COAL & LIGNITE)

    deleterious_coal_lignite_name = fields.Char("Name",default="DELETERIOUS MATERIAL (COAL & LIGNITE)")
    deleterious_coal_lignite_visible = fields.Boolean("DELETERIOUS MATERIAL (COAL & LIGNITE) Visible",compute="_compute_visible")

    deleterious_coal_lignite_line_ids = fields.One2many('fine.deleterious.material.coal.lignite.line', 'parent_id', string="Observations")

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
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_deleterious_coal_lignite_conformity", store=True)

    @api.depends('avg_deleterious_coal_lignite','eln_ref','grade')
    def _compute_avg_deleterious_coal_lignite_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_deleterious_coal_lignite_conformity = 'na'
                continue
            record.avg_deleterious_coal_lignite_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','efc370df-e45d-43a8-a4fa-e1139b59b134')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','efc370df-e45d-43a8-a4fa-e1139b59b134')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_deleterious_coal_lignite - record.avg_deleterious_coal_lignite*mu_value
                    upper = record.avg_deleterious_coal_lignite + record.avg_deleterious_coal_lignite*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_deleterious_coal_lignite_conformity = 'pass'
                        break
                    else:
                        record.avg_deleterious_coal_lignite_conformity = 'fail'

    avg_deleterious_coal_lignite_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_deleterious_coal_lignite_nabl", store=True)

    @api.depends('avg_deleterious_coal_lignite','eln_ref','grade')
    def _compute_avg_deleterious_coal_lignite_nabl(self):
        
        for record in self:
            record.avg_deleterious_coal_lignite_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','efc370df-e45d-43a8-a4fa-e1139b59b134')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','efc370df-e45d-43a8-a4fa-e1139b59b134')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    deleterious_coal_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    deleterious_coal_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_deleterious_coal_final_report", store=True)
    
    @api.depends('avg_deleterious_coal_lignite_nabl', 'deleterious_coal_report_type')
    def _compute_deleterious_coal_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.deleterious_coal_report_type == 'nabl':
                rec.deleterious_coal_final_report = 'nabl'
    
            elif rec.deleterious_coal_report_type == 'non_nabl':
                rec.deleterious_coal_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.avg_deleterious_coal_lignite_nabl == 'pass':
                    rec.deleterious_coal_final_report = 'nabl'
                else:
                    rec.deleterious_coal_final_report = 'non_nabl'


    # DELETERIOUS MATERIAL (CLAY & LUMPS)
    
    name_clay_lumps = fields.Char("Name",default="DELETERIOUS MATERIAL (CLAY & LUMPS)")
    clay_lump_visible = fields.Boolean("DELETERIOUS MATERIAL (CLAY & LUMPS) Visible",compute="_compute_visible")

    clay_lumps_percent_line_ids = fields.One2many('fine.deleterious.clay.line', 'parent_id', string="Trials")

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
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_clay_lumps_percent_conformity", store=True)

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.clay_lumps_percent_conformity = 'na'
                continue
            record.clay_lumps_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.clay_lumps_percent - record.clay_lumps_percent*mu_value
                    upper = record.clay_lumps_percent + record.clay_lumps_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.clay_lumps_percent_conformity = 'pass'
                        break
                    else:
                        record.clay_lumps_percent_conformity = 'fail'

    clay_lumps_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_clay_lumps_percent_nabl", store=True)

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_nabl(self):
        
        for record in self:
            record.clay_lumps_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    clay_lumps_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    clay_lumps_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_clay_lumps_final_report", store=True)
    
    @api.depends('clay_lumps_percent_nabl', 'clay_lumps_report_type')
    def _compute_clay_lumps_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.clay_lumps_report_type == 'nabl':
                rec.clay_lumps_final_report = 'nabl'
    
            elif rec.clay_lumps_report_type == 'non_nabl':
                rec.clay_lumps_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.clay_lumps_percent_nabl == 'pass':
                    rec.clay_lumps_final_report = 'nabl'
                else:
                    rec.clay_lumps_final_report = 'non_nabl'


    # Material Finer than 75 Micron

    finer75_name = fields.Char("Name",default="Material Finer than 75 Micron")					
    finer75_visible = fields.Boolean("Material Finer than 75 Micron Visible",compute="_compute_visible")

    finer75_line_ids = fields.One2many('fine.material.finer.75.line', 'parent_id', string="Observations")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d49f6725-5779-42b1-ac6e-44ba24926649')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d49f6725-5779-42b1-ac6e-44ba24926649')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d49f6725-5779-42b1-ac6e-44ba24926649')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d49f6725-5779-42b1-ac6e-44ba24926649')]).parameter_table
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


    finer_percent_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    finer_percent_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_finer_percent_final_report", store=True)
    
    @api.depends('avg_finer_percent_nabl', 'finer_percent_report_type')
    def _compute_finer_percent_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.finer_percent_report_type == 'nabl':
                rec.finer_percent_final_report = 'nabl'
    
            elif rec.finer_percent_report_type == 'non_nabl':
                rec.finer_percent_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.avg_finer_percent_nabl == 'pass':
                    rec.finer_percent_final_report = 'nabl'
                else:
                    rec.finer_percent_final_report = 'non_nabl'

    

    # Deleterious Material (Soft Fragments)
    
    name_soft_fragments = fields.Char("Name",default="Deleterious Material (Soft Fragments)")
    soft_fragments_visible = fields.Boolean("Deleterious Material (Soft Fragments) Visible",compute="_compute_visible")

    soft_fragments_ids = fields.One2many('fine.soft.particles.line', 'parent_id', string="Trials")

    soft_fragments_percent = fields.Float(
        "Average Deleterious Material Soft Fragments (%)",
        compute="_compute_soft_fragments_percent",
        store=True
    )

    @api.depends('soft_fragments_ids.percent')
    def _compute_soft_fragments_percent(self):
        for rec in self:
            lines = rec.soft_fragments_ids

            if lines:
                values = lines.mapped('percent')
                rec.soft_fragments_percent = sum(values) / len(values)
            else:
                rec.soft_fragments_percent = 0.0


    soft_fragments_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_soft_fragments_percent_conformity", store=True)

    @api.depends('soft_fragments_percent','eln_ref','grade')
    def _compute_soft_fragments_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.soft_fragments_percent_conformity = 'na'
                continue
            record.soft_fragments_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d66a05-767f-4e4f-9f09-b1a3af00af76')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d66a05-767f-4e4f-9f09-b1a3af00af76')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.soft_fragments_percent - record.soft_fragments_percent*mu_value
                    upper = record.soft_fragments_percent + record.soft_fragments_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.soft_fragments_percent_conformity = 'pass'
                        break
                    else:
                        record.soft_fragments_percent_conformity = 'fail'

    soft_fragments_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_soft_fragments_percent_nabl", store=True)

    @api.depends('soft_fragments_percent','eln_ref','grade')
    def _compute_soft_fragments_percent_nabl(self):
        
        for record in self:
            record.soft_fragments_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d66a05-767f-4e4f-9f09-b1a3af00af76')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d66a05-767f-4e4f-9f09-b1a3af00af76')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.soft_fragments_percent - record.soft_fragments_percent*mu_value
                    upper = record.soft_fragments_percent + record.soft_fragments_percent*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.soft_fragments_percent_nabl = 'pass'
                        break
                    else:
                        record.soft_fragments_percent_nabl = 'fail'


    soft_fragments_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    soft_fragments_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_soft_fragments_final_report", store=True)
    
    @api.depends('soft_fragments_percent_nabl', 'soft_fragments_report_type')
    def _compute_soft_fragments_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.soft_fragments_report_type == 'nabl':
                rec.soft_fragments_final_report = 'nabl'
    
            elif rec.soft_fragments_report_type == 'non_nabl':
                rec.soft_fragments_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.soft_fragments_percent_nabl == 'pass':
                    rec.soft_fragments_final_report = 'nabl'
                else:
                    rec.soft_fragments_final_report = 'non_nabl'


       # Moisture Content
    moisture_content_name1 = fields.Char("Name",default="Moisture Content")
    moisture_content_visible = fields.Boolean("Silt Content",compute="_compute_visible")

    moisture_content_child_lines = fields.One2many('fine.moisture.content.line','parent_id',string="Parameter",default=lambda self: self._default_moisture_content_lines())

    average_moisture_content = fields.Float(
        string="Average Moisture Content (%)",
        compute="_compute_average_moisture_content",
        store=True,
        digits=(16, 2),
    )

    # DEFAULT 3 TRIALS

    @api.model
    def _default_moisture_content_lines(self):
        default_lines = [
            (0, 0, {"serial_no": 1}),
            (0, 0, {"serial_no": 2}),
            (0, 0, {"serial_no": 3}),
            
        ]
        return default_lines


    # AVERAGE MOISTURE CONTENT

    @api.depends(
        "moisture_content_child_lines.moisture_content",
    )
    def _compute_average_moisture_content(self):
        for record in self:

            valid_lines = record.moisture_content_child_lines.filtered(
                lambda line: (
                    line.w1 > 0
                    and line.w2 > 0
                    and line.w3 > 0
                    and line.w3 != line.w1
                )
            )

            if valid_lines:
                record.average_moisture_content = (
                    sum(valid_lines.mapped("moisture_content"))
                    / len(valid_lines)
                )
            else:
                record.average_moisture_content = 0.0


    average_moisture_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_average_moisture_content_conformity", store=True)

    @api.depends('average_moisture_content','eln_ref','grade')
    def _compute_average_moisture_content_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_moisture_content_conformity = 'na'
                continue
            record.average_moisture_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture_content - record.average_moisture_content*mu_value
                    upper = record.average_moisture_content + record.average_moisture_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_moisture_content_conformity = 'pass'
                        break
                    else:
                        record.average_moisture_content_conformity = 'fail'

    average_moisture_content_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_moisture_content_nabl", store=True)

    @api.depends('average_moisture_content','eln_ref','grade')
    def _compute_average_moisture_content_nabl(self):
        
        for record in self:
            record.average_moisture_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture_content - record.average_moisture_content*mu_value
                    upper = record.average_moisture_content + record.average_moisture_content*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_moisture_content_nabl = 'pass'
                        break
                    else:
                        record.average_moisture_content_nabl = 'fail'

    moisture_content_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    moisture_content_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_moisture_content_final_report", store=True)
        
    @api.depends('average_moisture_content_nabl', 'moisture_content_report_type')
    def _compute_moisture_content_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.moisture_content_report_type == 'nabl':
                    rec.moisture_content_final_report = 'nabl'
        
                elif rec.moisture_content_report_type == 'non_nabl':
                    rec.moisture_content_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.average_moisture_content_nabl == 'pass':
                        rec.moisture_content_final_report = 'nabl'
                    else:
                        rec.moisture_content_final_report = 'non_nabl'


    
    #  Bulking of Sand

    bulking_sand_name = fields.Char("Name",default="Bulking of Sand")
    bulking_sand_visible = fields.Boolean("Bulking of Sand",compute="_compute_visible")

    bulking_sand_child_lines = fields.One2many('fine.bulking.sand.line','parent_id',string="Parameter",default=lambda self: self._default_bulking_lines())

    

    average_bulking = fields.Float(
        string="Average Bulking (%)",
        compute="_compute_average_bulking",
        store=True,
        digits=(16, 2),
    )

    # DEFAULT 3 TRIAL LINES

    @api.model
    def _default_bulking_lines(self):
        default_lines = [
            (0, 0, {"serial_no": 1}),
            (0, 0, {"serial_no": 2}),
            (0, 0, {"serial_no": 3}),
            
        ]
        return default_lines

    # COMPUTE AVERAGE BULKING

    @api.depends(
        "bulking_sand_child_lines.bulking_percent",
        "bulking_sand_child_lines.h1",
        "bulking_sand_child_lines.h2",
    )
    def _compute_average_bulking(self):
        for record in self:

            valid_lines = record.bulking_sand_child_lines.filtered(
                lambda line: line.h1 > 0 and line.h2 > 0
            )

            if valid_lines:
                record.average_bulking = round(
                    sum(valid_lines.mapped("bulking_percent"))
                    / len(valid_lines),
                    2,
                )
            else:
                record.average_bulking = 0.0
   


    average_bulking_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_average_bulking_conformity", store=True)

    @api.depends('average_bulking','eln_ref','grade')
    def _compute_average_bulking_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_bulking_conformity = 'na'
                continue
            record.average_bulking_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45789bhgt25-3fa3-4b83-ae31-9d28176718457')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45789bhgt25-3fa3-4b83-ae31-9d28176718457')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_bulking - record.average_bulking*mu_value
                    upper = record.average_bulking + record.average_bulking*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_bulking_conformity = 'pass'
                        break
                    else:
                        record.average_bulking_conformity = 'fail'

    average_bulking_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_bulking_nabl", store=True)

    @api.depends('average_bulking','eln_ref','grade')
    def _compute_average_bulking_nabl(self):
        
        for record in self:
            record.average_bulking_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45789bhgt25-3fa3-4b83-ae31-9d28176718457')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45789bhgt25-3fa3-4b83-ae31-9d28176718457')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_bulking - record.average_bulking*mu_value
                    upper = record.average_bulking + record.average_bulking*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_bulking_nabl = 'pass'
                        break
                    else:
                        record.average_bulking_nabl = 'fail'



    bulking_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    bulking_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_bulking_final_report", store=True)
    
    @api.depends('average_bulking_nabl', 'bulking_report_type')
    def _compute_bulking_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.bulking_report_type == 'nabl':
                rec.bulking_final_report = 'nabl'
    
            elif rec.bulking_report_type == 'non_nabl':
                rec.bulking_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.average_bulking_nabl == 'pass':
                    rec.bulking_final_report = 'nabl'
                else:
                    rec.bulking_final_report = 'non_nabl'

     



            


      








      # Specific Gravity

    specific_gravity_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    specific_gravity_line_ids = fields.One2many(
        "fine.aggregate.specific.gravity.line",
        "parent_id",
        string="Tests",default=lambda self: self._default_specific_gravity_lines())
    

    average_specific_gravity = fields.Float(
        string="Average Specific Gravity",
        compute="_compute_specific_gravity_averages",
        store=True,
        digits=(16, 3),
    )

    average_apparent_specific_gravity = fields.Float(
        string="Average Apparent Specific Gravity",
        compute="_compute_specific_gravity_averages",
        store=True,
        digits=(16, 3),
    )

    average_water_absorption = fields.Float(
        string="Average Water Absorption (%)",
        compute="_compute_specific_gravity_averages",
        store=True,
        digits=(16, 3),
    )

    
    @api.model
    def _default_specific_gravity_lines(self):
        default_lines = [
            (0, 0, {"serial_no": 1}),
            (0, 0, {"serial_no": 2}),
            (0, 0, {"serial_no": 3}),
            
        ]
        return default_lines

    @api.depends(
        "specific_gravity_line_ids.specific_gravity",
        "specific_gravity_line_ids.apparent_specific_gravity",
        "specific_gravity_line_ids.water_absorption",
        "specific_gravity_line_ids.w1",
        "specific_gravity_line_ids.w2",
        "specific_gravity_line_ids.w3",
        "specific_gravity_line_ids.w4",
    )
    def _compute_specific_gravity_averages(self):
        for record in self:
            # Only include completed/valid test lines.
            valid_lines = record.specific_gravity_line_ids.filtered(
                lambda line: (
                    line.w1 > 0
                    and line.w2 > 0
                    and line.w3 > 0
                    and line.w4 > 0
                    and (line.w1 - (line.w2 - line.w3)) != 0
                    and (line.w4 - (line.w2 - line.w3)) != 0
                )
            )

            if valid_lines:
                record.average_specific_gravity = (
                    sum(valid_lines.mapped("specific_gravity"))
                    / len(valid_lines)
                )

                record.average_apparent_specific_gravity = (
                    sum(valid_lines.mapped("apparent_specific_gravity"))
                    / len(valid_lines)
                )

                record.average_water_absorption = (
                    sum(valid_lines.mapped("water_absorption"))
                    / len(valid_lines)
                )

            else:
                record.average_specific_gravity = 0.0
                record.average_apparent_specific_gravity = 0.0
                record.average_water_absorption = 0.0


  

    average_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_average_specific_gravity_conformity", store=True)

    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_specific_gravity_conformity = 'na'
                continue
            record.average_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.average_specific_gravity_conformity = 'fail'

    average_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_specific_gravity_nabl", store=True)

    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_nabl(self):
        
        for record in self:
            record.average_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.average_specific_gravity_nabl = 'fail'

    specific_gravity_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    specific_gravity_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_specific_gravity_final_report", store=True)
    
    @api.depends('average_specific_gravity_nabl', 'specific_gravity_report_type')
    def _compute_specific_gravity_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.specific_gravity_report_type == 'nabl':
                rec.specific_gravity_final_report = 'nabl'
    
            elif rec.specific_gravity_report_type == 'non_nabl':
                rec.specific_gravity_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.average_specific_gravity_nabl == 'pass':
                    rec.specific_gravity_final_report = 'nabl'
                else:
                    rec.specific_gravity_final_report = 'non_nabl'

    average_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
        
          ], string="Water Absorption Conformity", compute="_compute_average_water_absorption_conformity", store=True)

    @api.depends('average_water_absorption_conformity','eln_ref','grade')
    def _compute_average_water_absorption_conformity(self):
        
        for record in self:

        
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_water_absorption_conformity = 'na'
                continue


            record.average_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4dbde30b-0cdc-4641-abdd-68a574fd7e1f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4dbde30b-0cdc-4641-abdd-68a574fd7e1f')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption - record.average_water_absorption*mu_value
                    upper = record.average_water_absorption + record.average_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.average_water_absorption_conformity = 'fail'

    average_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Water Absorption NABL", compute="_compute_average_water_absorption_nabl", store=True)

    @api.depends('average_water_absorption','eln_ref','grade')
    def _compute_average_water_absorption_nabl(self):
        
        for record in self:
            record.average_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4dbde30b-0cdc-4641-abdd-68a574fd7e1f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4dbde30b-0cdc-4641-abdd-68a574fd7e1f')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption - record.average_water_absorption*mu_value
                    upper = record.average_water_absorption + record.average_water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_water_absorption_nabl = 'pass'
                        break
                    else:
                        record.average_water_absorption_nabl = 'fail'


    water_absorption_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    water_absorption_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_water_absorption_final_report", store=True)
    
    @api.depends('average_water_absorption_nabl', 'water_absorption_report_type')
    def _compute_water_absorption_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.water_absorption_report_type == 'nabl':
                rec.water_absorption_final_report = 'nabl'
    
            elif rec.water_absorption_report_type == 'non_nabl':
                rec.water_absorption_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.average_water_absorption_nabl == 'pass':
                    rec.water_absorption_final_report = 'nabl'
                else:
                    rec.water_absorption_final_report = 'non_nabl'




          
    # Loose Bulk Density
    loose_bulk_density_name = fields.Char("Name",default="Loose Bulk Density")
    loose_bulk_density_visible = fields.Boolean("Loose Bulk Density Visible",compute="_compute_visible")

    loose_line_ids = fields.One2many(
        'fine.loose.bulk.density.line',
        'parent_id',
        string="Loose Bulk Density Trials"
    )

    loose_avg = fields.Float(
        string="Average Loose Bulk Density",
        compute="_compute_loose_avg",
        store=True,digits=(10,3)
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')]).parameter_table
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
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_loose_avg_nabl" ,store=True)

    @api.depends('loose_avg','eln_ref','grade')
    def _compute_loose_avg_nabl(self):
        
        for record in self:
            record.loose_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')]).parameter_table
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

    loose_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    loose_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_loose_final_report", store=True)
    
    @api.depends('loose_avg_nabl', 'loose_report_type')
    def _compute_loose_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.loose_report_type == 'nabl':
                rec.loose_final_report = 'nabl'
    
            elif rec.loose_report_type == 'non_nabl':
                rec.loose_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.loose_avg_nabl == 'pass':
                    rec.loose_final_report = 'nabl'
                else:
                    rec.loose_final_report = 'non_nabl'

    


    # Rodded Bulk Density
    rodded_bulk_density_name = fields.Char("Name",default="Rodded Bulk Density")
    rodded_bulk_density_visible = fields.Boolean("Rodded Bulk Density Visible",compute="_compute_visible")

    rodded_line_ids = fields.One2many(
        'fine.rodded.bulk.density.line',
        'parent_id',
        string="Rodded Bulk Density Trials"
    )

    rodded_avg = fields.Float(
        string="Average Rodded Bulk Density",
        compute="_compute_rodded_avg",
        store=True,digits=(10,3)
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d961c78a-9f5c-4e7f-9f03-86ab65740161')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d961c78a-9f5c-4e7f-9f03-86ab65740161')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d961c78a-9f5c-4e7f-9f03-86ab65740161')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d961c78a-9f5c-4e7f-9f03-86ab65740161')]).parameter_table
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


    rodded_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    rodded_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_rodded_final_report", store=True)
    
    @api.depends('rodded_avg_nabl', 'rodded_report_type')
    def _compute_rodded_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.rodded_report_type == 'nabl':
                rec.rodded_final_report = 'nabl'
    
            elif rec.rodded_report_type == 'non_nabl':
                rec.rodded_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.rodded_avg_nabl == 'pass':
                    rec.rodded_final_report = 'nabl'
                else:
                    rec.rodded_final_report = 'non_nabl'




    # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="SOUNDNESS (SODIUM SULPHATE TEST)")
    soundness_na2so4_visible = fields.Boolean("SOUNDNESS OF COARSE AGGREGATE (SODIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_sod_line_ids = fields.One2many(
        'fine.sodium.sulphate.line',
        'parent_id',
        string="Soundness Na2SO4",default=lambda self: self.soundness_sod_line_ids_sizes()
    )

    @api.model
    def soundness_sod_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '150 µ','retained_sieve': '-'}),
            (0, 0, {'passing_sieve': '300 µ','retained_sieve': '150 µ mm'}),
            (0, 0, {'passing_sieve': '600 µ','retained_sieve': '300 µ'}),
            (0, 0, {'passing_sieve': '1.18 mm','retained_sieve': '600 um'}),
            (0, 0, {'passing_sieve': '2.36 mm','retained_sieve': '1.18 mm'}),
            (0, 0, {'passing_sieve': '4.75 mm','retained_sieve': '2.36 mm'}),
            (0, 0, {'passing_sieve': '10 mm','retained_sieve': '4.75 mm'}),
        ]
        return default_lines 
    


    total_grading = fields.Float("Total (Grading of Orignal Sample Percent (%))", compute="_compute_totaled")
    total_weight_before = fields.Float("Total (Weight of Test Fraction Before Test (gm))", compute="_compute_totaled")
    total_weight_after = fields.Float("Total (Weight of Test Fraction After Test (gm))", compute="_compute_totaled")
    total_percent_loss = fields.Float("Total (Percentage Passing Finer Sieve After Test ( Actual Percentage Loss) (%))", compute="_compute_totaled")
    total_weighted_avg = fields.Float("Final Result (Weighted Average ( Corrected Percent Loss ))", compute="_compute_totaled")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f5796')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f5796')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f5796')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f5796')]).parameter_table
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


    sodium_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    sodium_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_sodium_final_report", store=True)
    
    @api.depends('total_weighted_avg_nabl', 'sodium_report_type')
    def _compute_sodium_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.sodium_report_type == 'nabl':
                rec.sodium_final_report = 'nabl'
    
            elif rec.sodium_report_type == 'non_nabl':
                rec.sodium_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.total_weighted_avg_nabl == 'pass':
                    rec.sodium_final_report = 'nabl'
                else:
                    rec.sodium_final_report = 'non_nabl'


    # SOUNDNESS (MAGNESIUM SULPHATE TEST)
    soundness_mgso4_name = fields.Char("Name",default="SOUNDNESS (MAGNESIUM SULPHATE TEST)")
    soundness_mgso4_visible = fields.Boolean("SOUNDNESS (MAGNESIUM SULPHATE TEST) Visible",compute="_compute_visible")
 
    soundness_mag_line_ids = fields.One2many(
        'fine.magnesium.sulphate.line',
        'parent_id',
        string="Soundness MgSO4",default=lambda self: self.soundness_mag_line_ids_sizes()
    )

    @api.model
    def soundness_mag_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '150 µ','retained_sieve': '-'}),
            (0, 0, {'passing_sieve': '300 µ','retained_sieve': '150 µ mm'}),
            (0, 0, {'passing_sieve': '600 µ','retained_sieve': '300 µ'}),
            (0, 0, {'passing_sieve': '1.18 mm','retained_sieve': '600 um'}),
            (0, 0, {'passing_sieve': '2.36 mm','retained_sieve': '1.18 mm'}),
            (0, 0, {'passing_sieve': '4.75 mm','retained_sieve': '2.36 mm'}),
            (0, 0, {'passing_sieve': '10 mm','retained_sieve': '4.75 mm'}),
        ]
        return default_lines 
    


    mag_total_grading = fields.Float("Total (Grading of Orignal Sample Percent (%))", compute="_compute_totalled")
    mag_total_weight_before = fields.Float("Total (Weight of Test Fraction Before Test (gm))", compute="_compute_totalled")
    mag_total_weight_after = fields.Float("Total (Weight of Test Fraction After Test (gm))", compute="_compute_totalled")
    mag_total_percent_loss = fields.Float("Total (Percentage Passing Finer Sieve After Test ( Actual Percentage Loss) (%))", compute="_compute_totalled")
    mag_total_weighted_avg = fields.Float("Final Result (Weighted Average ( Corrected Percent Loss ))", compute="_compute_totalled")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace97d80-fdf8-45ed-8762-8ec73805ea68')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace97d80-fdf8-45ed-8762-8ec73805ea68')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace97d80-fdf8-45ed-8762-8ec73805ea68')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace97d80-fdf8-45ed-8762-8ec73805ea68')]).parameter_table
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


    magnesium_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    magnesium_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_magnesium_final_report", store=True)
    
    @api.depends('mag_total_weighted_avg_nabl', 'magnesium_report_type')
    def _compute_magnesium_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.magnesium_report_type == 'nabl':
                rec.magnesium_final_report = 'nabl'
    
            elif rec.magnesium_report_type == 'non_nabl':
                rec.magnesium_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.mag_total_weighted_avg_nabl == 'pass':
                    rec.magnesium_final_report = 'nabl'
                else:
                    rec.magnesium_final_report = 'non_nabl'




    
    

    

    # Deleterious Material - Organic Impurities

    organic_impurities_name = fields.Char( "Name", default="Organic Impurities")
    organic_impurities_visible = fields.Boolean( "Organic Impurities",compute="_compute_visible")


    organic_impurities_line_ids = fields.One2many(
        'organic.impurities.line',
        'parent_id',
        string="Organic Impurities Trial"
    )

    avg_clay_percentage = fields.Float(
        string="Average Percentage of Clay (%); (L = (W-R)/(W) x 100",
        compute="_compute_avg_clay_percentage",
        store=True
    )

    @api.depends('organic_impurities_line_ids.clay_percentage')
    def _compute_avg_clay_percentage(self):
        for rec in self:
            percentages = rec.organic_impurities_line_ids.mapped('clay_percentage')
            rec.avg_clay_percentage = (
                sum(percentages) / len(percentages)
                if percentages else 0.0
            )

    
    avg_clay_percentage_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity', compute="_compute_avg_clay_percentage_confirmity")
    
    @api.depends('avg_clay_percentage','eln_ref','grade')
    def _compute_avg_clay_percentage_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_clay_percentage_confirmity = 'na'
                continue
            record.avg_clay_percentage_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0363075f-a3f2-440a-b634-76f469d220c7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0363075f-a3f2-440a-b634-76f469d220c7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_clay_percentage - record.avg_clay_percentage*mu_value
                    upper = record.avg_clay_percentage + record.avg_clay_percentage*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_clay_percentage_confirmity = 'pass'
                        break
                    else:
                        record.avg_clay_percentage_confirmity = 'fail'

    avg_clay_percentage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_clay_percentage_nabl" ,store=True)

    @api.depends('avg_clay_percentage','eln_ref','grade')
    def _compute_avg_clay_percentage_nabl(self):
        
        for record in self:
            record.avg_clay_percentage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0363075f-a3f2-440a-b634-76f469d220c7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0363075f-a3f2-440a-b634-76f469d220c7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_clay_percentage - record.avg_clay_percentage*mu_value
                    upper = record.avg_clay_percentage + record.avg_clay_percentage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_clay_percentage_nabl = 'pass'
                        break
                    else:
                        record.avg_clay_percentage_nabl = 'fail'


    avg_clay_percent_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    avg_clay_percent_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_avg_clay_percent_final_report", store=True)
    
    @api.depends('avg_clay_percentage_nabl', 'avg_clay_percent_report_type')
    def _compute_avg_clay_percent_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.avg_clay_percent_report_type == 'nabl':
                rec.avg_clay_percent_final_report = 'nabl'
    
            elif rec.avg_clay_percent_report_type == 'non_nabl':
                rec.avg_clay_percent_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.avg_clay_percentage_nabl == 'pass':
                    rec.avg_clay_percent_final_report = 'nabl'
                else:
                    rec.avg_clay_percent_final_report = 'non_nabl'

    



    

    






    












     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
      
            record.sieve_visible = False
            record.deleterious_coal_lignite_visible = False
            record.clay_lump_visible = False
            record.finer75_visible = False
            record.soft_fragments_visible = False
            record.moisture_content_visible = False
            record.bulking_sand_visible = False
            record.specific_gravity_visible = False
            record.loose_bulk_density_visible = False
            record.rodded_bulk_density_visible = False


            record.soundness_na2so4_visible = False
            record.soundness_mgso4_visible = False
            
            record.organic_impurities_visible  = False
            






          
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "318d72a1-7188-4086-b132-62b50e63f5d1":
                    record.sieve_visible = True


                if sample.internal_id == 'efc370df-e45d-43a8-a4fa-e1139b59b134':
                    record.deleterious_coal_lignite_visible = True

                if sample.internal_id == 'ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb':
                    record.clay_lump_visible = True


                if sample.internal_id == 'd49f6725-5779-42b1-ac6e-44ba24926649':
                    record.finer75_visible = True

                if sample.internal_id == '03d66a05-767f-4e4f-9f09-b1a3af00af76':
                    record.soft_fragments_visible = True

                if sample.internal_id == "1457htyu1245-3fa3-4b83-ae31-9d281457457hy":
                    record.moisture_content_visible = True


                if sample.internal_id == "45789bhgt25-3fa3-4b83-ae31-9d28176718457":
                    record.bulking_sand_visible = True


                if sample.internal_id == "45875ght-7188-4086-b132-62b50e63f1245gt":
                    record.specific_gravity_visible = True

                if sample.internal_id == "4587tyhloos-3fa3-4b83-ae31-9d281767188c":
                    record.loose_bulk_density_visible = True
                    
                
                if sample.internal_id == 'd961c78a-9f5c-4e7f-9f03-86ab65740161':
                    record.rodded_bulk_density_visible  = True

                

                if sample.internal_id == 'a0e7aaf3-68ff-4e75-830d-91ae04c98f5796':
                    record.soundness_na2so4_visible = True

                if sample.internal_id == 'ace97d80-fdf8-45ed-8762-8ec73805ea68':
                    record.soundness_mgso4_visible = True

                if sample.internal_id == '0363075f-a3f2-440a-b634-76f469d220c7':
                    record.organic_impurities_visible = True

                
               
                

            
   
    

    def open_eln_page(self):

        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        if current_user.has_group('lerm_civil.lerm_discipline_group'):
            technician_results = self.eln_ref.parameters_result
        else:
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:
            internal_id = result.parameter.internal_id

            # Sieve Analysis
            if result.parameter.internal_id == '318d72a1-7188-4086-b132-62b50e63f5d1':
                result.calculated = True


            # Deleterious Material - Lightweight Pieces (Coal & Lignite)
            if result.parameter.internal_id == 'efc370df-e45d-43a8-a4fa-e1139b59b134':
                result.calculated = True
                result.result_char = round(self.avg_deleterious_coal_lignite,2)
                if self.avg_deleterious_coal_lignite_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # DELETERIOUS MATERIAL (CLAY & LUMPS)
            if result.parameter.internal_id == 'ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb':
                result.calculated = True
                result.result_char = round(self.clay_lumps_percent,2)
                if self.clay_lumps_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Material finer than 75 micron
            if result.parameter.internal_id == 'd49f6725-5779-42b1-ac6e-44ba24926649':
                result.calculated = True
                result.result_char = round(self.avg_finer_percent,2)
                if self.avg_finer_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Deleterious Material (Soft Fragments)
            if result.parameter.internal_id == '03d66a05-767f-4e4f-9f09-b1a3af00af76':
                result.calculated = True
                result.result_char = round(self.soft_fragments_percent,2)
                if self.soft_fragments_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Moisture Content
            if result.parameter.internal_id == '1457htyu1245-3fa3-4b83-ae31-9d281457457hy':
                result.result_char = round(self.average_moisture_content,2)
                result.calculated = True
                if self.average_moisture_content_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Bulking Sand
            if result.parameter.internal_id == '45789bhgt25-3fa3-4b83-ae31-9d28176718457':
                result.calculated = True
                result.result_char = round(self.average_bulking,2)
                if self.average_bulking_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



            # Specific Gravity
            if result.parameter.internal_id == '45875ght-7188-4086-b132-62b50e63f1245gt':
                result.result_char = round(self.average_specific_gravity,2)
                result.calculated = True
                if self.average_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Water Absorption
            if result.parameter.internal_id == '4dbde30b-0cdc-4641-abdd-68a574fd7e1f':
                result.result_char = round(self.average_water_absorption,2)
                result.calculated = True
                if self.average_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Bulk Density
            if result.parameter.internal_id == 'f2c6222e-e761-4b65-844a-fb882948c47f':
                result.calculated = True

             # Loose bulk Density
            if result.parameter.internal_id == '4587tyhloos-3fa3-4b83-ae31-9d281767188c':
                result.result_char = round(self.loose_avg,2)
                result.calculated = True
                if self.loose_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Rodded bulk Density
            if result.parameter.internal_id == 'd961c78a-9f5c-4e7f-9f03-86ab65740161':
                result.calculated = True
                result.result_char = round(self.rodded_avg,2)
                if self.rodded_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            
            # Soundness na2so4
            if result.parameter.internal_id == "a0e7aaf3-68ff-4e75-830d-91ae04c98f5796":
                result.result_char = round(self.total_weighted_avg, 2)
                result.calculated = True
                if self.total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Soundness mgso4
            if result.parameter.internal_id == "ace97d80-fdf8-45ed-8762-8ec73805ea68":
                result.result_char = round(self.mag_total_weighted_avg, 2)
                result.calculated = True
                if self.mag_total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            #  Deleterious Material - Organic Impurities
            if result.parameter.internal_id == '0363075f-a3f2-440a-b634-76f469d220c7':
                result.result_char = round(self.avg_clay_percentage, 2)
                result.calculated = True
                if self.avg_clay_percentage_nabl == 'pass':
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
        record = super(FineAggregate, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(FineAggregate, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(FineAggregate, self).read(fields=fields, load=load)

   
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



    notes_id = fields.One2many('mechanical.fine.aggregate.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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






class SieveAnalysisLine(models.Model):
    _name = "mechanical.fine.agg.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms")

    cumulative_percent = fields.Float(string="Cum. Weight Retained (gm)",compute="_compute_cumulative_percent",
    store=True,)

    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained",digits=(12,1))
    cumulative_retained = fields.Float(string="Cum. Retained %", compute="_compute_cum_retained", store=True,digits=(12,2))
    passing_percent = fields.Float(string="Passing %",digits=(12,2))
    specific_limt = fields.Char(string="Specified Limits")



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
    

    @api.depends('wt_retained', 'parent_id.sieve_analysis_child_lines.wt_retained')
    def _compute_cumulative_percent(self):
        for parent in self.mapped('parent_id'):
            total = 0
            lines = parent.sieve_analysis_child_lines.sorted('serial_no')

            for line in lines:
                total += line.wt_retained or 0
                line.cumulative_percent = total


    @api.depends('wt_retained', 'parent_id.wt_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / record.parent_id.wt_of_sample) * 100 if record.parent_id.wt_of_sample else 0.0
            except ZeroDivisionError:
                record.percent_retained = 0.0





    @api.depends('percent_retained', 'parent_id.sieve_analysis_child_lines.percent_retained')
    def _compute_cum_retained(self):
        for record in self:
            cumulative = 0.0
            found = False

            for line in sorted(record.parent_id.sieve_analysis_child_lines, key=lambda l: l.serial_no):
                cumulative += line.percent_retained or 0.0
                if line.id == record.id:
                    found = True
                    record.cumulative_retained = cumulative
                    break

            if not found:
                record.cumulative_retained = 0.0

        
    


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")


class FineDeleteriousMaterialCoalLigniteLine(models.Model):
    _name = "fine.deleterious.material.coal.lignite.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample taken (W₁) gms.")
    w2 = fields.Float("Weight of coal & lignite particles separated (W₂)")

    deleterious_percent = fields.Float(
        "Deleterious Material (%) = (W2/W1) x 100",
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

        return super(FineDeleteriousMaterialCoalLigniteLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class FineDeleteriousClayLine(models.Model):
    _name = "fine.deleterious.clay.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample (W1)")
    w2 = fields.Float("Weight of clay & lumps separated (W₂)")

    percent = fields.Float(
        "3. Deleterious Material (%) = (W2/W1) x 100",
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

        return super(FineDeleteriousClayLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class FineMaterialFiner75Line(models.Model):
    _name = "fine.material.finer.75.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of oven dry sample taken (W1)")
    w2 = fields.Float("Weight retained on 75 micron sieve (W2)")

    w3 = fields.Float(
        "Weight passing 75 micron sieve (W1 - W2)",
        compute="_compute_values",
        store=True
    )

    finer_percent = fields.Float(
        "Material Finer than 75 micron =[(W1-W2)/W1]*100 (%)",
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

        return super(FineMaterialFiner75Line, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class FineSoftParticlesLine(models.Model):
    _name = "fine.soft.particles.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)


    w1 = fields.Float("Weight of total sample (W1)")
    w2 = fields.Float("Weight of Soft Fragment separated (W₂)")

    percent = fields.Float(
        "3. Deleterious Material = (W2/W1) x 100 (%)",
        compute="_compute_percent",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_percent(self):
        for rec in self:
            rec.percent = (rec.w2 / rec.w1) * 100 if rec.w1 else 0.0

    

    @api.model
    def create(self, vals):
        # Set the sample_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FineSoftParticlesLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class MoistureContentLine(models.Model):
    _name = "fine.moisture.content.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

    # W1
    w1 = fields.Float(
        string="Weight of Empty Container (W₁) gms",
        digits=(16, 2),
    )


    # W2
    w2 = fields.Float(
        string="Weight of Container + Wet Sand (W₂) gms",
        digits=(16, 2),
    )


    # W3
    w3 = fields.Float(
        string="Weight of Container + Dry Sand (W₃) gms",
        digits=(16, 2),
    )


    moisture_content = fields.Float(
        string="Moisture Content (%)=(W2-W3)​/(W3-W1)×100",
        compute="_compute_moisture_content",
        store=True,
        digits=(16, 2),
    )


    # MOISTURE CONTENT
    @api.depends(
        "w1",
        "w2",
        "w3",
    )
    def _compute_moisture_content(self):
        for line in self:

            line.moisture_content = 0.0

            denominator = line.w3 - line.w1

            if denominator > 0:
                line.moisture_content = (
                    (line.w2 - line.w3)
                    / denominator
                ) * 100.0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(MoistureContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1







class BulkingSandLine(models.Model):
    _name = "fine.bulking.sand.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

    h1 = fields.Float(
        string="Initial Height of Moist Sand (H₁) mm",
        digits=(16, 2),
    )

    h2 = fields.Float(
        string="Height of sand after adding water (fully saturated) (H₂) mm",
        digits=(16, 2),
    )

    bulking_percent = fields.Float(
        string="Bulking (%)=(H1​−H2)/H2​​×100 ",
        compute="_compute_bulking_percent",
        store=True,
        digits=(16, 2),
    )

    # ========================================================
    # COMPUTE BULKING %
    # ========================================================

    @api.depends("h1", "h2")
    def _compute_bulking_percent(self):
        for line in self:
            line.bulking_percent = 0.0

            if line.h2 > 0:
                line.bulking_percent = round(
                    ((line.h1 - line.h2) / line.h2) * 100.0,
                    2,
                )
    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(BulkingSandLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FineAggregateSpecificGravityLine(models.Model):
    _name = "fine.aggregate.specific.gravity.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

    temperature = fields.Float(
        string="Temperature of Water (°C)",
        digits=(16, 2),
    )

    pycnometer_bottle_number = fields.Char(
        string="Pycnometer Bottle Number",
    )

    # W1 = Weight of Saturated Surface Dry Sample

    w1 = fields.Float(
        string="Weight of Saturated Surface Dry Sample, W1 (gm)",
        digits=(16, 2),
    )

    # W2 = Weight of Pycnometer Bottle + Water + Sample

    w2 = fields.Float(
        string="Weight of Pycnometer Bottle + Water + Sample, W2 (gm)",
        digits=(16, 2),
    )

    # W3 = Weight of Pycnometer Bottle + Water

    w3 = fields.Float(
        string="Weight of Pycnometer Bottle + Water, W3 (gm)",
        digits=(16, 2),
    )

    # W4 = Weight of Oven Dry Sample

    w4 = fields.Float(
        string="Weight of Oven Dry Sample, W4 (gm)",
        digits=(16, 2),
    )

    specific_gravity = fields.Float(
        string="Specific Gravity = W4/[W1-(W2-W3)]",
        compute="_compute_test_results",
        store=True,
        digits=(16, 3),
    )

    apparent_specific_gravity = fields.Float(
        string="Apparent Specific Gravity = W4/[W4-(W2-W3)]",
        compute="_compute_test_results",
        store=True,
        digits=(16, 3),
    )

    water_absorption = fields.Float(
        string="Water Absorption (%) = 100 x (W1 - W4)/W4",
        compute="_compute_test_results",
        store=True,
        digits=(16, 3),
    )

    @api.depends("w1", "w2", "w3", "w4")
    def _compute_test_results(self):
        for line in self:
            line.specific_gravity = 0.0
            line.apparent_specific_gravity = 0.0
            line.water_absorption = 0.0

            # ------------------------------------------------
            # Specific Gravity
            #
            # W4 / [W1 - (W2 - W3)]
            # ------------------------------------------------

            specific_gravity_denominator = (
                line.w1 - (line.w2 - line.w3)
            )

            if specific_gravity_denominator != 0:
                line.specific_gravity = (
                    line.w4 / specific_gravity_denominator
                )

            # ------------------------------------------------
            # Apparent Specific Gravity
            #
            # W4 / [W4 - (W2 - W3)]
            # ------------------------------------------------

            apparent_gravity_denominator = (
                line.w4 - (line.w2 - line.w3)
            )

            if apparent_gravity_denominator != 0:
                line.apparent_specific_gravity = (
                    line.w4 / apparent_gravity_denominator
                )

            # ------------------------------------------------
            # Water Absorption
            #
            # 100 × (W1 - W4) / W4
            # ------------------------------------------------

            if line.w4 > 0:
                line.water_absorption = (
                    100.0 * (line.w1 - line.w4) / line.w4
                )
    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FineAggregateSpecificGravityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FineLooseBulkDensityLine(models.Model):
    _name = "fine.loose.bulk.density.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id",ondelete='cascade')
   
    serial_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)

   
    container_with_material = fields.Float("Weight of Material in Container after pouring, W  (Kg)",digits=(10,3))

    volume_of_cont = fields.Float(string="Volume of calibrating container ,V (Lit)")
    loose_bulk_density = fields.Float(string="Loose Bulk Density of Material,W/V (Kg/Lit)",compute="_compute_loose_bulk_density",digits=(10,3))


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

        return super(FineLooseBulkDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FineRoddedBulkDensityLine(models.Model):
    _name = "fine.rodded.bulk.density.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id",ondelete='cascade')
   
    serial_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)

    
    container_with_material = fields.Float("Weight of Material in Container after pouring, W  (Kg)",digits=(10,3))

    volume_of_cont = fields.Float(string="Volume of calibrating container ,V (Lit)")
    rodded_bulk_density = fields.Float(string="Rodded Bulk Density of Material,W/V (Kg/Lit)",compute="_compute_rodded_bulk_density",digits=(10,3))

   

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

        return super(FineRoddedBulkDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1






class FineSodiumSulphateLine(models.Model):
    _name = "fine.sodium.sulphate.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id",ondelete='cascade')

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Orignal Sample Percent (%)")

    weight_before = fields.Float("Weight of Test Fraction Before Test (gm)")
    weight_after = fields.Float("Weight of Test Fraction After Test (gm)")

    percent_loss = fields.Float(
        "Percentage Passing Finer Sieve After Test ( Actual Percentage Loss) (%)",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average ( Corrected Percent Loss )",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after))
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class FineMagnesiumSulphateLine(models.Model):
    _name = "fine.magnesium.sulphate.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Orignal Sample Percent (%)")

    weight_before = fields.Float("Weight of Test Fraction Before Test (gm)")
    weight_after = fields.Float("Weight of Test Fraction After Test (gm)")

    percent_loss = fields.Float(
        "Percentage Passing Finer Sieve After Test ( Actual Percentage Loss) (%)",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average ( Corrected Percent Loss )",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after))
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


    
    
class OrganicImpuritiesLine(models.Model):
    _name = "organic.impurities.line"
    _description = "Organic Impurities Trial"

    parent_id = fields.Many2one('mechanical.fine.aggregate', string="Parent Id")

    serial_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)


    total_weight = fields.Float(
        string="Total Weight of Sample (W)"
    )

    weight_after_removing = fields.Float(
        string="Total Weight of Sample After Removing Clay Lumps (R) g"
    )

    clay_percentage = fields.Float(
        string="Percentage of Clay (%); (L = (W-R)/(W) x 100)",
        compute="_compute_percentage",
        store=True,
        digits=(16, 2)
    )

    @api.depends('total_weight', 'weight_after_removing')
    def _compute_percentage(self):
        for rec in self:
            if rec.total_weight:
                rec.clay_percentage = (
                    (rec.total_weight - rec.weight_after_removing)
                    / rec.total_weight
                ) * 100
            else:
                rec.clay_percentage = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(OrganicImpuritiesLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





class FineAggregateNotes(models.Model):
    _name = "mechanical.fine.aggregate.notes"

    parent_id = fields.Many2one('mechanical.fine.aggregate', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
