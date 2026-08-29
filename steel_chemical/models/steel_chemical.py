from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class SteelChemical(models.Model):
    _name = "steel.chemical"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Steel Chemical")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")

    notes_id = fields.One2many('steel.chemical.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(SteelChemical, self).default_get(fields)

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


    carbon_name = fields.Char("Name",default="DETERMINATION OF CARBON IN STEEL-IS: 228 (PART-1) 2025")
    carbon_visible = fields.Boolean("pH",compute="_compute_visible")
    
    nomenclature = fields.Float("Nomenclature")
    dia = fields.Float("Dia (mm)")
    pressure = fields.Float("Bar. Pressure")
    ambient = fields.Float("Ambient Temp.")
    correction_factor = fields.Float("Pressure-Temp. Correction Factor (F)")


    type_of_sample1 = fields.Float(string="Type of sample")
    type_of_sample2 = fields.Float(string="Type of sample")
    type_of_sample3 = fields.Float(string="Type of sample")
    type_of_sample4 = fields.Float(string="Type of sample")
    type_of_sample5 = fields.Float(string="Type of sample")

    wt_of_sample1 = fields.Float(string="Wt. of sample (W)")
    wt_of_sample2 = fields.Float(string="Wt. of sample (W)")
    wt_of_sample3 = fields.Float(string="Wt. of sample (W)")
    wt_of_sample4 = fields.Float(string="Wt. of sample (W)")
    wt_of_sample5 = fields.Float(string="Wt. of sample (W)")

    br_reading_a1 = fields.Float(string="Burette Reading for sample (A)")
    br_reading_a2 = fields.Float(string="Burette Reading for sample (A)")
    br_reading_a3 = fields.Float(string="Burette Reading for sample (A)")
    br_reading_a4 = fields.Float(string="Burette Reading for sample (A)")
    br_reading_a5 = fields.Float(string="Burette Reading for sample (A)")

    br_reading_b1 = fields.Float(string="Burette Reading for Blank (B)")
    br_reading_b2 = fields.Float(string="Burette Reading for Blank (B)")
    br_reading_b3 = fields.Float(string="Burette Reading for Blank (B)")
    br_reading_b4 = fields.Float(string="Burette Reading for Blank (B)")
    br_reading_b5 = fields.Float(string="Burette Reading for Blank (B)")

    carbon_calculation1 = fields.Float(string="Calculation= (A - B) X F ",compute="_compute_carbon_calculation" )
    carbon_calculation2 = fields.Float(string="Calculation= (A - B) X F" ,compute="_compute_carbon_calculation" )
    carbon_calculation3 = fields.Float(string="Calculation= (A - B) X F" ,compute="_compute_carbon_calculation" )
    carbon_calculation4 = fields.Float(string="Calculation= (A - B) X F",compute="_compute_carbon_calculation"  )
    carbon_calculation5 = fields.Float(string="Calculation= (A - B) X F " ,compute="_compute_carbon_calculation" )

    carbon_percentage = fields.Float(string="Average of Carbon -",compute="_compute_avg_chloride")

    @api.depends('carbon_calculation1', 'carbon_calculation2', 'carbon_calculation3', 'carbon_calculation4', 'carbon_calculation5')
    def _compute_avg_chloride(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            carbon = [
                rec.carbon_calculation1,
                rec.carbon_calculation2,
                rec.carbon_calculation3,
                rec.carbon_calculation4,
                rec.carbon_calculation5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_carbon = [c for c in carbon if c]  # ya (c for c in carbon if c not in [False, None, 0.0])
            
            if valid_carbon:
                rec.carbon_percentage = sum(valid_carbon) / len(valid_carbon)
            else:
                rec.carbon_percentage = 0.0

    @api.depends(
    'br_reading_a1', 'br_reading_b1',
    'br_reading_a2', 'br_reading_b2',
    'br_reading_a3', 'br_reading_b3',
    'br_reading_a4', 'br_reading_b4',
    'br_reading_a5', 'br_reading_b5',
    'correction_factor'
    )
    def _compute_carbon_calculation(self):
        for record in self:
            record.carbon_calculation1 = (
                record.br_reading_a1 - record.br_reading_b1
            ) * record.correction_factor

            record.carbon_calculation2 = (
                record.br_reading_a2 - record.br_reading_b2
            ) * record.correction_factor

            record.carbon_calculation3 = (
                record.br_reading_a3 - record.br_reading_b3
            ) * record.correction_factor

            record.carbon_calculation4 = (
                record.br_reading_a4 - record.br_reading_b4
            ) * record.correction_factor

            record.carbon_calculation5 = (
                record.br_reading_a5 - record.br_reading_b5
            ) * record.correction_factor


    
    carbon_percentage_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_carbon_percentage_conformity", store=True)

    @api.depends('carbon_percentage','eln_ref','grade')
    def _compute_carbon_percentage_conformity(self):
            # remove this first when making changes
            self.carbon_percentage_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.carbon_percentage_conformity = 'na'
                    continue

                record.carbon_percentage_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1b8c8615-978b-483c-99dd-271530e3884e')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1b8c8615-978b-483c-99dd-271530e3884e')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.carbon_percentage - record.carbon_percentage*mu_value
                        upper = record.carbon_percentage + record.carbon_percentage*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.carbon_percentage_conformity = 'pass'
                            break
                        else:
                            record.carbon_percentage_conformity = 'fail'

    carbon_percentage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_carbon_percentage_nabl", store=True)

    @api.depends('carbon_percentage','eln_ref','grade')
    def _compute_carbon_percentage_nabl(self):
        # remove this first
        self.carbon_percentage_nabl = 'fail'
        
        for record in self:
            record.carbon_percentage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1b8c8615-978b-483c-99dd-271530e3884e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1b8c8615-978b-483c-99dd-271530e3884e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.carbon_percentage - record.carbon_percentage*mu_value
            upper = record.carbon_percentage + record.carbon_percentage*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.carbon_percentage_nabl = 'pass'
                break
            else:
                record.carbon_percentage_nabl = 'fail'

    #   Total Suspended Solids (mg/l)
    
    phosphorus_name = fields.Char("Name",default="DETERMINATION OF PHOSPHORUS IN STEEL- IS: 228 (PART-3) 2024")
    phosphorus_visible = fields.Boolean("DETERMINATION OF PHOSPHORUS IN STEEL- IS: 228 (PART-3) 2024",compute="_compute_visible")

    wt_sample_taken1 = fields.Float(string="Weight of sample taken in gm (D)")
    wt_sample_taken2 = fields.Float(string="Weight of sample taken in gm (D)")
    wt_sample_taken3 = fields.Float(string="Weight of sample taken in gm (D)")
    wt_sample_taken4 = fields.Float(string="Weight of sample taken in gm (D)")
    wt_sample_taken5 = fields.Float(string="Weight of sample taken in gm (D)")

    hno3_a1 = fields.Float(string="Std. HNO3 solution consumed in sample in ml (A)")
    hno3_a2 = fields.Float(string="Std. HNO3 solution consumed in sample in ml (A)")
    hno3_a3 = fields.Float(string="Std. HNO3 solution consumed in sample in ml (A)")
    hno3_a4 = fields.Float(string="Std. HNO3 solution consumed in sample in ml (A)")
    hno3_a5 = fields.Float(string="Std. HNO3 solution consumed in sample in ml (A)")

    hno3_b1 = fields.Float(string="Std. HNO3 solution consumed in Blank in ml (B)")
    hno3_b2 = fields.Float(string="Std. HNO3 solution consumed in Blank in ml (B)")
    hno3_b3 = fields.Float(string="Std. HNO3 solution consumed in Blank in ml (B)")
    hno3_b4 = fields.Float(string="Std. HNO3 solution consumed in Blank in ml (B)")
    hno3_b5 = fields.Float(string="Std. HNO3 solution consumed in Blank in ml (B)")

    hno3_c1 = fields.Float(string="Phosphorus equivalent of 1 ml std. HNO3 solution (C)")
    hno3_c2 = fields.Float(string="Phosphorus equivalent of 1 ml std. HNO3 solution (C)")
    hno3_c3 = fields.Float(string="Phosphorus equivalent of 1 ml std. HNO3 solution (C)")
    hno3_c4 = fields.Float(string="Phosphorus equivalent of 1 ml std. HNO3 solution (C)")
    hno3_c5 = fields.Float(string="Phosphorus equivalent of 1 ml std. HNO3 solution (C)")

    percentage_of_phosphorus1 = fields.Float(string="Percentage of phosphorus ((B - A) × C / D) × 100",compute="_compute_percentage_of_phosphorus")
    percentage_of_phosphorus2 = fields.Float(string="Percentage of phosphorus ((B - A) × C / D) × 100",compute="_compute_percentage_of_phosphorus")
    percentage_of_phosphorus3 = fields.Float(string="Percentage of phosphorus ((B - A) × C / D) × 100",compute="_compute_percentage_of_phosphorus")
    percentage_of_phosphorus4 = fields.Float(string="Percentage of phosphorus ((B - A) × C / D) × 100",compute="_compute_percentage_of_phosphorus")
    percentage_of_phosphorus5 = fields.Float(string="Percentage of phosphorus ((B - A) × C / D) × 100",compute="_compute_percentage_of_phosphorus")

    @api.depends(
    'wt_sample_taken1', 'hno3_a1', 'hno3_b1', 'hno3_c1',
    'wt_sample_taken2', 'hno3_a2', 'hno3_b2', 'hno3_c2',
    'wt_sample_taken3', 'hno3_a3', 'hno3_b3', 'hno3_c3',
    'wt_sample_taken4', 'hno3_a4', 'hno3_b4', 'hno3_c4',
    'wt_sample_taken5', 'hno3_a5', 'hno3_b5', 'hno3_c5'
    )
    def _compute_percentage_of_phosphorus(self):
        for record in self:

            # Sample 1
            if record.wt_sample_taken1:
                record.percentage_of_phosphorus1 = (
                    (record.hno3_b1 - record.hno3_a1)
                    * record.hno3_c1
                    / record.wt_sample_taken1
                ) * 100
            else:
                record.percentage_of_phosphorus1 = 0.0

            # Sample 2
            if record.wt_sample_taken2:
                record.percentage_of_phosphorus2 = (
                    (record.hno3_b2 - record.hno3_a2)
                    * record.hno3_c2
                    / record.wt_sample_taken2
                ) * 100
            else:
                record.percentage_of_phosphorus2 = 0.0

            # Sample 3
            if record.wt_sample_taken3:
                record.percentage_of_phosphorus3 = (
                    (record.hno3_b3 - record.hno3_a3)
                    * record.hno3_c3
                    / record.wt_sample_taken3
                ) * 100
            else:
                record.percentage_of_phosphorus3 = 0.0

            # Sample 4
            if record.wt_sample_taken4:
                record.percentage_of_phosphorus4 = (
                    (record.hno3_b4 - record.hno3_a4)
                    * record.hno3_c4
                    / record.wt_sample_taken4
                ) * 100
            else:
                record.percentage_of_phosphorus4 = 0.0

            # Sample 5
            if record.wt_sample_taken5:
                record.percentage_of_phosphorus5 = (
                    (record.hno3_b5 - record.hno3_a5)
                    * record.hno3_c5
                    / record.wt_sample_taken5
                ) * 100
            else:
                record.percentage_of_phosphorus5 = 0.0



    avg_phosphorus = fields.Float(string="Average of phosphorus =",compute="_compute_avg_phosphorus")

    @api.depends('percentage_of_phosphorus1', 'percentage_of_phosphorus2', 'percentage_of_phosphorus3', 'percentage_of_phosphorus4', 'percentage_of_phosphorus5')
    def _compute_avg_phosphorus(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            phosphorus = [
                rec.percentage_of_phosphorus1,
                rec.percentage_of_phosphorus2,
                rec.percentage_of_phosphorus3,
                rec.percentage_of_phosphorus4,
                rec.percentage_of_phosphorus5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_phosphorus = [c for c in phosphorus if c]  # ya (c for c in phosphorus if c not in [False, None, 0.0])
            
            if valid_phosphorus:
                rec.avg_phosphorus = sum(valid_phosphorus) / len(valid_phosphorus)
            else:
                rec.avg_phosphorus = 0.0

    

    avg_phosphorus_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_phosphorus_conformity", store=True)

    @api.depends('avg_phosphorus','eln_ref','grade')
    def _compute_avg_phosphorus_conformity(self):
            # remove this first when making changes
            self.avg_phosphorus_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_phosphorus_conformity = 'na'
                    continue

                record.avg_phosphorus_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ecdf1d7-5f58-494b-a898-28a0bb3f8242')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ecdf1d7-5f58-494b-a898-28a0bb3f8242')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_phosphorus - record.avg_phosphorus*mu_value
                        upper = record.avg_phosphorus + record.avg_phosphorus*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_phosphorus_conformity = 'pass'
                            break
                        else:
                            record.avg_phosphorus_conformity = 'fail'

    avg_phosphorus_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_phosphorus_nabl", store=True)

    @api.depends('avg_phosphorus','eln_ref','grade')
    def _compute_avg_phosphorus_nabl(self):
        # remove this first
        self.avg_phosphorus_nabl = 'fail'
        
        for record in self:
            record.avg_phosphorus_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ecdf1d7-5f58-494b-a898-28a0bb3f8242')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ecdf1d7-5f58-494b-a898-28a0bb3f8242')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_phosphorus - record.avg_phosphorus*mu_value
            upper = record.avg_phosphorus + record.avg_phosphorus*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_phosphorus_nabl = 'pass'
                break
            else:
                record.avg_phosphorus_nabl = 'fail'

    # SULPHUR
    sulphur_steel_name = fields.Char("Name",default="DETERMINATION OF SULPHUR IN STEEL- IS: 228 (PART-9) 1989 RA 2023")
    sulphur_steel_visible = fields.Boolean("DETERMINATION OF SULPHUR IN STEEL- IS: 228 (PART-9) 1989 RA 2023",compute="_compute_visible")

    sulpher_wt_sample1 = fields.Float(string="Weight of sample taken in gm (D)")
    sulpher_wt_sample2 = fields.Float(string="Weight of sample taken in gm (D)")
    sulpher_wt_sample3 = fields.Float(string="Weight of sample taken in gm (D)")
    sulpher_wt_sample4 = fields.Float(string="Weight of sample taken in gm (D)")
    sulpher_wt_sample5 = fields.Float(string="Weight of sample taken in gm (D)")

    sulpher_potassiumb1 = fields.Float(string="Volume in ml, of potassium iodate solution  used (B)")
    sulpher_potassiumb2 = fields.Float(string="Volume in ml, of potassium iodate solution  used (B)")
    sulpher_potassiumb3 = fields.Float(string="Volume in ml, of potassium iodate solution  used (B)")
    sulpher_potassiumb4 = fields.Float(string="Volume in ml, of potassium iodate solution  used (B)")
    sulpher_potassiumb5 = fields.Float(string="Volume in ml, of potassium iodate solution  used (B)")

    sulpher_potassiuma1 = fields.Float(string="Volume in ml, of potassium iodate solution added (A)")
    sulpher_potassiuma2 = fields.Float(string="Volume in ml, of potassium iodate solution added (A)")
    sulpher_potassiuma3 = fields.Float(string="Volume in ml, of potassium iodate solution added (A)")
    sulpher_potassiuma4 = fields.Float(string="Volume in ml, of potassium iodate solution added (A)")
    sulpher_potassiuma5 = fields.Float(string="Volume in ml, of potassium iodate solution added (A)")


    sulpher_potassiumc1 = fields.Float(string="Normality of potassium iodate solution (C)")
    sulpher_potassiumc2 = fields.Float(string="Normality of potassium iodate solution (C)")
    sulpher_potassiumc3 = fields.Float(string="Normality of potassium iodate solution (C)")
    sulpher_potassiumc4 = fields.Float(string="Normality of potassium iodate solution (C)")
    sulpher_potassiumc5 = fields.Float(string="Normality of potassium iodate solution (C)")


    percentage_sulpher1 = fields.Float(string="Percentage of Sulphur = [(A − B) × C × 1.6] / D",compute="_compute_percentage_sulphur")
    percentage_sulpher2 = fields.Float(string="Percentage of Sulphur = [(A − B) × C × 1.6] / D",compute="_compute_percentage_sulphur")
    percentage_sulpher3 = fields.Float(string="Percentage of Sulphur = [(A − B) × C × 1.6] / D",compute="_compute_percentage_sulphur")
    percentage_sulpher4 = fields.Float(string="Percentage of Sulphur = [(A − B) × C × 1.6] / D",compute="_compute_percentage_sulphur")
    percentage_sulpher5 = fields.Float(string="Percentage of Sulphur = [(A − B) × C × 1.6] / D",compute="_compute_percentage_sulphur")

    @api.depends(
        'sulpher_wt_sample1', 'sulpher_potassiuma1', 'sulpher_potassiumb1', 'sulpher_potassiumc1',
        'sulpher_wt_sample2', 'sulpher_potassiuma2', 'sulpher_potassiumb2', 'sulpher_potassiumc2',
        'sulpher_wt_sample3', 'sulpher_potassiuma3', 'sulpher_potassiumb3', 'sulpher_potassiumc3',
        'sulpher_wt_sample4', 'sulpher_potassiuma4', 'sulpher_potassiumb4', 'sulpher_potassiumc4',
        'sulpher_wt_sample5', 'sulpher_potassiuma5', 'sulpher_potassiumb5', 'sulpher_potassiumc5'
    )
    def _compute_percentage_sulphur(self):
        for record in self:

            # Sample 1
            if record.sulpher_wt_sample1:
                record.percentage_sulpher1 = (
                    (record.sulpher_potassiuma1 - record.sulpher_potassiumb1)
                    * record.sulpher_potassiumc1
                    * 1.6
                ) / record.sulpher_wt_sample1
            else:
                record.percentage_sulpher1 = 0.0

            # Sample 2
            if record.sulpher_wt_sample2:
                record.percentage_sulpher2 = (
                    (record.sulpher_potassiuma2 - record.sulpher_potassiumb2)
                    * record.sulpher_potassiumc2
                    * 1.6
                ) / record.sulpher_wt_sample2
            else:
                record.percentage_sulpher2 = 0.0

            # Sample 3
            if record.sulpher_wt_sample3:
                record.percentage_sulpher3 = (
                    (record.sulpher_potassiuma3 - record.sulpher_potassiumb3)
                    * record.sulpher_potassiumc3
                    * 1.6
                ) / record.sulpher_wt_sample3
            else:
                record.percentage_sulpher3 = 0.0

            # Sample 4
            if record.sulpher_wt_sample4:
                record.percentage_sulpher4 = (
                    (record.sulpher_potassiuma4 - record.sulpher_potassiumb4)
                    * record.sulpher_potassiumc4
                    * 1.6
                ) / record.sulpher_wt_sample4
            else:
                record.percentage_sulpher4 = 0.0

            # Sample 5
            if record.sulpher_wt_sample5:
                record.percentage_sulpher5 = (
                    (record.sulpher_potassiuma5 - record.sulpher_potassiumb5)
                    * record.sulpher_potassiumc5
                    * 1.6
                ) / record.sulpher_wt_sample5
            else:
                record.percentage_sulpher5 = 0.0

    
   

    avg_sulphur = fields.Float(string="Average of Sulphur =",compute="_compute_avg_sulphur")

    @api.depends('percentage_sulpher1', 'percentage_sulpher2', 'percentage_sulpher3', 'percentage_sulpher4', 'percentage_sulpher5')
    def _compute_avg_sulphur(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            sulphur = [
                rec.percentage_sulpher1,
                rec.percentage_sulpher2,
                rec.percentage_sulpher3,
                rec.percentage_sulpher4,
                rec.percentage_sulpher5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_sulphur = [c for c in sulphur if c]  # ya (c for c in sulphur if c not in [False, None, 0.0])
            
            if valid_sulphur:
                rec.avg_sulphur = sum(valid_sulphur) / len(valid_sulphur)
            else:
                rec.avg_sulphur = 0.0


    

    avg_sulphur_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_sulphur_conformity", store=True)

    @api.depends('avg_sulphur','eln_ref','grade')
    def _compute_avg_sulphur_conformity(self):
            # remove this first when making changes
            self.avg_sulphur_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_sulphur_conformity = 'na'
                    continue

                record.avg_sulphur_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2de1cf5a-ef5d-46e7-8183-048b1d415c86')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2de1cf5a-ef5d-46e7-8183-048b1d415c86')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_sulphur - record.avg_sulphur*mu_value
                        upper = record.avg_sulphur + record.avg_sulphur*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_sulphur_conformity = 'pass'
                            break
                        else:
                            record.avg_sulphur_conformity = 'fail'

    avg_sulphur_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_sulphur_nabl", store=True)

    @api.depends('avg_sulphur','eln_ref','grade')
    def _compute_avg_sulphur_nabl(self):
        # remove this first
        self.avg_sulphur_nabl = 'fail'
        
        for record in self:
            record.avg_sulphur_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2de1cf5a-ef5d-46e7-8183-048b1d415c86')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2de1cf5a-ef5d-46e7-8183-048b1d415c86')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_sulphur - record.avg_sulphur*mu_value
            upper = record.avg_sulphur + record.avg_sulphur*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_sulphur_nabl = 'pass'
                break
            else:
                record.avg_sulphur_nabl = 'fail'


    # MANGANESE
    manganese_name = fields.Char("Name",default="DETERMINATION OF MANGANESE IN STEEL- IS: 228 (PART-2) 2024")
    manganese_visible = fields.Boolean("DETERMINATION OF MANGANESE IN STEEL- IS: 228 (PART-2) 2024",compute="_compute_visible")

    manganese_wt_samplec1 = fields.Float(string="Weight of sample taken in gm (C)")
    manganese_wt_samplec2 = fields.Float(string="Weight of sample taken in gm (C)")
    manganese_wt_samplec3 = fields.Float(string="Weight of sample taken in gm (C)")
    manganese_wt_samplec4 = fields.Float(string="Weight of sample taken in gm (C)")
    manganese_wt_samplec5 = fields.Float(string="Weight of sample taken in gm (C)")

    manganese_sodiuma1 = fields.Float(string="Std. Sodium arsenite solution consumed in sample in ml (A)")
    manganese_sodiuma2 = fields.Float(string="Std. Sodium arsenite solution consumed in sample in ml (A)")
    manganese_sodiuma3 = fields.Float(string="Std. Sodium arsenite solution consumed in sample in ml (A)")
    manganese_sodiuma4 = fields.Float(string="Std. Sodium arsenite solution consumed in sample in ml (A)")
    manganese_sodiuma5 = fields.Float(string="Std. Sodium arsenite solution consumed in sample in ml (A)")

    manganese_sodiumb1 = fields.Float(string="Manganese equipment of std. sodium arsenite solution  (B) gm/ml")
    manganese_sodiumb2 = fields.Float(string="Manganese equipment of std. sodium arsenite solution  (B) gm/ml")
    manganese_sodiumb3 = fields.Float(string="Manganese equipment of std. sodium arsenite solution  (B) gm/ml")
    manganese_sodiumb4 = fields.Float(string="Manganese equipment of std. sodium arsenite solution  (B) gm/ml")
    manganese_sodiumb5 = fields.Float(string="Manganese equipment of std. sodium arsenite solution  (B) gm/ml")

    manganese_percentage1 = fields.Float(string="% of Manganese = [(A × B) / C] × 100)",compute="_compute_percentage_manganese")
    manganese_percentage2 = fields.Float(string="% of Manganese = [(A × B) / C] × 100)",compute="_compute_percentage_manganese")
    manganese_percentage3 = fields.Float(string="% of Manganese = [(A × B) / C] × 100)",compute="_compute_percentage_manganese")
    manganese_percentage4 = fields.Float(string="% of Manganese = [(A × B) / C] × 100)",compute="_compute_percentage_manganese")
    manganese_percentage5 = fields.Float(string="% of Manganese = [(A × B) / C] × 100)",compute="_compute_percentage_manganese")


    @api.depends(
        'manganese_wt_samplec1', 'manganese_sodiuma1', 'manganese_sodiumb1',
        'manganese_wt_samplec2', 'manganese_sodiuma2', 'manganese_sodiumb2',
        'manganese_wt_samplec3', 'manganese_sodiuma3', 'manganese_sodiumb3',
        'manganese_wt_samplec4', 'manganese_sodiuma4', 'manganese_sodiumb4',
        'manganese_wt_samplec5', 'manganese_sodiuma5', 'manganese_sodiumb5'
    )
    def _compute_percentage_manganese(self):
        for record in self:

            # Sample 1
            if record.manganese_wt_samplec1:
                record.manganese_percentage1 = (
                    (record.manganese_sodiuma1 * record.manganese_sodiumb1)
                    / record.manganese_wt_samplec1
                ) * 100
            else:
                record.manganese_percentage1 = 0.0

            # Sample 2
            if record.manganese_wt_samplec2:
                record.manganese_percentage2 = (
                    (record.manganese_sodiuma2 * record.manganese_sodiumb2)
                    / record.manganese_wt_samplec2
                ) * 100
            else:
                record.manganese_percentage2 = 0.0

            # Sample 3
            if record.manganese_wt_samplec3:
                record.manganese_percentage3 = (
                    (record.manganese_sodiuma3 * record.manganese_sodiumb3)
                    / record.manganese_wt_samplec3
                ) * 100
            else:
                record.manganese_percentage3 = 0.0

            # Sample 4
            if record.manganese_wt_samplec4:
                record.manganese_percentage4 = (
                    (record.manganese_sodiuma4 * record.manganese_sodiumb4)
                    / record.manganese_wt_samplec4
                ) * 100
            else:
                record.manganese_percentage4 = 0.0

            # Sample 5
            if record.manganese_wt_samplec5:
                record.manganese_percentage5 = (
                    (record.manganese_sodiuma5 * record.manganese_sodiumb5)
                    / record.manganese_wt_samplec5
                ) * 100
            else:
                record.manganese_percentage5 = 0.0

    avg_manganese = fields.Float(string="Average of Manganese =",compute="_compute_avg_manganese")



    @api.depends('manganese_percentage1', 'manganese_percentage2', 'manganese_percentage3', 'manganese_percentage4', 'manganese_percentage5')
    def _compute_avg_manganese(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            manganese = [
                rec.manganese_percentage1,
                rec.manganese_percentage2,
                rec.manganese_percentage3,
                rec.manganese_percentage4,
                rec.manganese_percentage5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_manganese = [c for c in manganese if c]  # ya (c for c in manganese if c not in [False, None, 0.0])
            
            if valid_manganese:
                rec.avg_manganese = sum(valid_manganese) / len(valid_manganese)
            else:
                rec.avg_manganese = 0.0

    

    avg_manganese_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_manganese_conformity", store=True)

    @api.depends('avg_manganese','eln_ref','grade')
    def _compute_avg_manganese_conformity(self):
            # remove this first when making changes
            self.avg_manganese_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_manganese_conformity = 'na'
                    continue

                record.avg_manganese_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9ad149fa-9fa0-4ff7-8168-c27d2505323e')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9ad149fa-9fa0-4ff7-8168-c27d2505323e')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_manganese - record.avg_manganese*mu_value
                        upper = record.avg_manganese + record.avg_manganese*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_manganese_conformity = 'pass'
                            break
                        else:
                            record.avg_manganese_conformity = 'fail'

    avg_manganese_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_manganese_nabl", store=True)

    @api.depends('avg_manganese','eln_ref','grade')
    def _compute_avg_manganese_nabl(self):
        # remove this first
        self.avg_manganese_nabl = 'fail'
        
        for record in self:
            record.avg_manganese_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9ad149fa-9fa0-4ff7-8168-c27d2505323e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9ad149fa-9fa0-4ff7-8168-c27d2505323e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_manganese - record.avg_manganese*mu_value
            upper = record.avg_manganese + record.avg_manganese*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_manganese_nabl = 'pass'
                break
            else:
                record.avg_manganese_nabl = 'fail'
  
    # SILICON
    
    silicon_name = fields.Char("Name",default="DETERMINATION OF SILICON IN STEEL- IS: 228 (PART-8) 1989 RA 2023")
    silicon_visible = fields.Boolean("DETERMINATION OF SILICON IN STEEL- IS: 228 (PART-8) 1989 RA 2023",compute="_compute_visible")

    wt_of_silicon1 = fields.Float(string="Weight of sample taken in gm (C)")
    wt_of_silicon2 = fields.Float(string="Weight of sample taken in gm (C)")
    wt_of_silicon3 = fields.Float(string="Weight of sample taken in gm (C)")
    wt_of_silicon4 = fields.Float(string="Weight of sample taken in gm (C)")
    wt_of_silicon5 = fields.Float(string="Weight of sample taken in gm (C)")

    mas_of_silicon1 = fields.Float(string="Mass in gm. Of silica obtained in sample (A)")
    mas_of_silicon2 = fields.Float(string="Mass in gm. Of silica obtained in sample (A)")
    mas_of_silicon3 = fields.Float(string="Mass in gm. Of silica obtained in sample (A)")
    mas_of_silicon4 = fields.Float(string="Mass in gm. Of silica obtained in sample (A)")
    mas_of_silicon5 = fields.Float(string="Mass in gm. Of silica obtained in sample (A)")

    mass_of_siliconb1 = fields.Float(string="Mass in gm. Of silica obtained in blank (B)")
    mass_of_siliconb2 = fields.Float(string="Mass in gm. Of silica obtained in blank (B)")
    mass_of_siliconb3 = fields.Float(string="Mass in gm. Of silica obtained in blank (B)")
    mass_of_siliconb4 = fields.Float(string="Mass in gm. Of silica obtained in blank (B)")
    mass_of_siliconb5 = fields.Float(string="Mass in gm. Of silica obtained in blank (B)")

    percent_of_silicon1 = fields.Float(string="% of Silicon = ((A - B) X 46.75 )/C",compute="_compute_percent_of_silicon")
    percent_of_silicon2 = fields.Float(string="% of Silicon = ((A - B) X 46.75 )/C",compute="_compute_percent_of_silicon")
    percent_of_silicon3 = fields.Float(string="% of Silicon = ((A - B) X 46.75 )/C",compute="_compute_percent_of_silicon")
    percent_of_silicon4 = fields.Float(string="% of Silicon = ((A - B) X 46.75 )/C",compute="_compute_percent_of_silicon")
    percent_of_silicon5 = fields.Float(string="% of Silicon = ((A - B) X 46.75 )/C",compute="_compute_percent_of_silicon")


    @api.depends(
        'wt_of_silicon1', 'mas_of_silicon1', 'mass_of_siliconb1',
        'wt_of_silicon2', 'mas_of_silicon2', 'mass_of_siliconb2',
        'wt_of_silicon3', 'mas_of_silicon3', 'mass_of_siliconb3',
        'wt_of_silicon4', 'mas_of_silicon4', 'mass_of_siliconb4',
        'wt_of_silicon5', 'mas_of_silicon5', 'mass_of_siliconb5'
    )
    def _compute_percent_of_silicon(self):
        for record in self:

            # Sample 1
            if record.wt_of_silicon1:
                record.percent_of_silicon1 = (
                    (record.mas_of_silicon1 - record.mass_of_siliconb1)
                    * 46.75
                ) / record.wt_of_silicon1
            else:
                record.percent_of_silicon1 = 0.0

            # Sample 2
            if record.wt_of_silicon2:
                record.percent_of_silicon2 = (
                    (record.mas_of_silicon2 - record.mass_of_siliconb2)
                    * 46.75
                ) / record.wt_of_silicon2
            else:
                record.percent_of_silicon2 = 0.0

            # Sample 3
            if record.wt_of_silicon3:
                record.percent_of_silicon3 = (
                    (record.mas_of_silicon3 - record.mass_of_siliconb3)
                    * 46.75
                ) / record.wt_of_silicon3
            else:
                record.percent_of_silicon3 = 0.0

            # Sample 4
            if record.wt_of_silicon4:
                record.percent_of_silicon4 = (
                    (record.mas_of_silicon4 - record.mass_of_siliconb4)
                    * 46.75
                ) / record.wt_of_silicon4
            else:
                record.percent_of_silicon4 = 0.0

            # Sample 5
            if record.wt_of_silicon5:
                record.percent_of_silicon5 = (
                    (record.mas_of_silicon5 - record.mass_of_siliconb5)
                    * 46.75
                ) / record.wt_of_silicon5
            else:
                record.percent_of_silicon5 = 0.0

    

    avg_silicon = fields.Float(string="Average Of Silicon =",compute="_compute_avg_silicon")


    @api.depends('percent_of_silicon1', 'percent_of_silicon2', 'percent_of_silicon3', 'percent_of_silicon4', 'percent_of_silicon5')
    def _compute_avg_silicon(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            silicon = [
                rec.percent_of_silicon1,
                rec.percent_of_silicon2,
                rec.percent_of_silicon3,
                rec.percent_of_silicon4,
                rec.percent_of_silicon5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_silicon = [c for c in silicon if c]  # ya (c for c in silicon if c not in [False, None, 0.0])
            
            if valid_silicon:
                rec.avg_silicon = sum(valid_silicon) / len(valid_silicon)
            else:
                rec.avg_silicon = 0.0

    
    avg_silicon_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_silicon_conformity", store=True)

    @api.depends('avg_silicon','eln_ref','grade')
    def _compute_avg_silicon_conformity(self):
            # remove this first when making changes
            self.avg_silicon_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_silicon_conformity = 'na'
                    continue

                record.avg_silicon_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e03281c-9961-44db-bd32-52bbdea0b56e')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e03281c-9961-44db-bd32-52bbdea0b56e')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_silicon - record.avg_silicon*mu_value
                        upper = record.avg_silicon + record.avg_silicon*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_silicon_conformity = 'pass'
                            break
                        else:
                            record.avg_silicon_conformity = 'fail'

    avg_silicon_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_silicon_nabl", store=True)

    @api.depends('avg_silicon','eln_ref','grade')
    def _compute_avg_silicon_nabl(self):
        # remove this first
        self.avg_silicon_nabl = 'fail'
        
        for record in self:
            record.avg_silicon_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e03281c-9961-44db-bd32-52bbdea0b56e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e03281c-9961-44db-bd32-52bbdea0b56e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_silicon - record.avg_silicon*mu_value
            upper = record.avg_silicon + record.avg_silicon*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_silicon_nabl = 'pass'
                break
            else:
                record.avg_silicon_nabl = 'fail'

    #  CHROMIUM
    
    chromium_name = fields.Char("Name",default="DETERMINATION OF CHROMIUM IN STEEL- IS: 228 (PART-6) 1989 RA 2023")
    chromium_visible = fields.Boolean("DETERMINATION OF CHROMIUM IN STEEL- IS: 228 (PART-6) 1989 RA 2023",compute="_compute_visible")


    chromium_voluma_1 = fields.Float(string="Volume in ml of std. Ferrous ammonium sulphate solution added, (A)")
    chromium_voluma_2 = fields.Float(string="Volume in ml of std. Ferrous ammonium sulphate solution added, (A)")
    chromium_voluma_3 = fields.Float(string="Volume in ml of std. Ferrous ammonium sulphate solution added, (A)")
    chromium_voluma_4 = fields.Float(string="Volume in ml of std. Ferrous ammonium sulphate solution added, (A)")
    chromium_voluma_5 = fields.Float(string="Volume in ml of std. Ferrous ammonium sulphate solution added, (A)")

    chromium_volumb_1 = fields.Float(string="Volume in ml of std. Potassium permanganate solution equivalent to 1 ml of Ferrous ammonium sulphate solution, (B)")
    chromium_volumb_2 = fields.Float(string="Volume in ml of std. Potassium permanganate solution equivalent to 1 ml of Ferrous ammonium sulphate solution, (B)")
    chromium_volumb_3 = fields.Float(string="Volume in ml of std. Potassium permanganate solution equivalent to 1 ml of Ferrous ammonium sulphate solution, (B)")
    chromium_volumb_4 = fields.Float(string="Volume in ml of std. Potassium permanganate solution equivalent to 1 ml of Ferrous ammonium sulphate solution, (B)")
    chromium_volumb_5 = fields.Float(string="Volume in ml of std. Potassium permanganate solution equivalent to 1 ml of Ferrous ammonium sulphate solution, (B)")

    chromium_volumc1 = fields.Float(string="Volume in ml of std. Potassium permanganate solution required for titration corrected for the blank, (C)")
    chromium_volumc2 = fields.Float(string="Volume in ml of std. Potassium permanganate solution required for titration corrected for the blank, (C)")
    chromium_volumc3 = fields.Float(string="Volume in ml of std. Potassium permanganate solution required for titration corrected for the blank, (C)")
    chromium_volumc4 = fields.Float(string="Volume in ml of std. Potassium permanganate solution required for titration corrected for the blank, (C)")
    chromium_volumc5 = fields.Float(string="Volume in ml of std. Potassium permanganate solution required for titration corrected for the blank, (C)")

    chromium_normalityd1 = fields.Float(string="Normality of Std. Potassium Permanganate solution, (D)")
    chromium_normalityd2 = fields.Float(string="Normality of Std. Potassium Permanganate solution, (D)")
    chromium_normalityd3 = fields.Float(string="Normality of Std. Potassium Permanganate solution, (D)")
    chromium_normalityd4 = fields.Float(string="Normality of Std. Potassium Permanganate solution, (D)")
    chromium_normalityd5 = fields.Float(string="Normality of Std. Potassium Permanganate solution, (D)")

    chromium_masse1 = fields.Float(string="Mass in gm of the sample taken for Test, (E)")
    chromium_masse2 = fields.Float(string="Mass in gm of the sample taken for Test, (E)")
    chromium_masse3 = fields.Float(string="Mass in gm of the sample taken for Test, (E)")
    chromium_masse4 = fields.Float(string="Mass in gm of the sample taken for Test, (E)")
    chromium_masse5 = fields.Float(string="Mass in gm of the sample taken for Test, (E)")

    percent_chromium1 = fields.Float(string="Percent of Chromium= ((AB-C) X 0.01733 X 100)/E",compute="_compute_percent_chromium")
    percent_chromium2 = fields.Float(string="Percent of Chromium= ((AB-C) X 0.01733 X 100)/E",compute="_compute_percent_chromium")
    percent_chromium3 = fields.Float(string="Percent of Chromium= ((AB-C) X 0.01733 X 100)/E",compute="_compute_percent_chromium")
    percent_chromium4 = fields.Float(string="Percent of Chromium= ((AB-C) X 0.01733 X 100)/E",compute="_compute_percent_chromium")
    percent_chromium5 = fields.Float(string="Percent of Chromium= ((AB-C) X 0.01733 X 100)/E",compute="_compute_percent_chromium")

    @api.depends(
        'chromium_voluma_1', 'chromium_volumb_1', 'chromium_volumc1', 'chromium_masse1',
        'chromium_voluma_2', 'chromium_volumb_2', 'chromium_volumc2', 'chromium_masse2',
        'chromium_voluma_3', 'chromium_volumb_3', 'chromium_volumc3', 'chromium_masse3',
        'chromium_voluma_4', 'chromium_volumb_4', 'chromium_volumc4', 'chromium_masse4',
        'chromium_voluma_5', 'chromium_volumb_5', 'chromium_volumc5', 'chromium_masse5'
    )
    def _compute_percent_chromium(self):
        for record in self:

            # Sample 1
            if record.chromium_masse1:
                record.percent_chromium1 = (
                    ((record.chromium_voluma_1 * record.chromium_volumb_1) - record.chromium_volumc1)
                    * 0.01733
                    * 100
                ) / record.chromium_masse1
            else:
                record.percent_chromium1 = 0.0

            # Sample 2
            if record.chromium_masse2:
                record.percent_chromium2 = (
                    ((record.chromium_voluma_2 * record.chromium_volumb_2) - record.chromium_volumc2)
                    * 0.01733
                    * 100
                ) / record.chromium_masse2
            else:
                record.percent_chromium2 = 0.0

            # Sample 3
            if record.chromium_masse3:
                record.percent_chromium3 = (
                    ((record.chromium_voluma_3 * record.chromium_volumb_3) - record.chromium_volumc3)
                    * 0.01733
                    * 100
                ) / record.chromium_masse3
            else:
                record.percent_chromium3 = 0.0

            # Sample 4
            if record.chromium_masse4:
                record.percent_chromium4 = (
                    ((record.chromium_voluma_4 * record.chromium_volumb_4) - record.chromium_volumc4)
                    * 0.01733
                    * 100
                ) / record.chromium_masse4
            else:
                record.percent_chromium4 = 0.0

            # Sample 5
            if record.chromium_masse5:
                record.percent_chromium5 = (
                    ((record.chromium_voluma_5 * record.chromium_volumb_5) - record.chromium_volumc5)
                    * 0.01733
                    * 100
                ) / record.chromium_masse5
            else:
                record.percent_chromium5 = 0.0


    avg_chromium = fields.Float(string="Average Of Chromium % =",compute="_compute_avg_chromium")

    @api.depends('percent_chromium1', 'percent_chromium2', 'percent_chromium3', 'percent_chromium4', 'percent_chromium5')
    def _compute_avg_chromium(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            chromium = [
                rec.percent_chromium1,
                rec.percent_chromium2,
                rec.percent_chromium3,
                rec.percent_chromium4,
                rec.percent_chromium5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_chromium = [c for c in chromium if c]  # ya (c for c in chromium if c not in [False, None, 0.0])
            
            if valid_chromium:
                rec.avg_chromium = sum(valid_chromium) / len(valid_chromium)
            else:
                rec.avg_chromium = 0.0


    

    avg_chromium_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_chromium_conformity", store=True)

    @api.depends('avg_chromium','eln_ref','grade')
    def _compute_avg_chromium_conformity(self):
            # remove this first when making changes
            self.avg_chromium_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_chromium_conformity = 'na'
                    continue

                record.avg_chromium_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6cb22710-89a6-44a0-8df1-379ef6230a4e')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6cb22710-89a6-44a0-8df1-379ef6230a4e')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_chromium - record.avg_chromium*mu_value
                        upper = record.avg_chromium + record.avg_chromium*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_chromium_conformity = 'pass'
                            break
                        else:
                            record.avg_chromium_conformity = 'fail'

    avg_chromium_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_chromium_nabl", store=True)

    @api.depends('avg_chromium','eln_ref','grade')
    def _compute_avg_chromium_nabl(self):
        # remove this first
        self.avg_chromium_nabl = 'fail'
        
        for record in self:
            record.avg_chromium_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6cb22710-89a6-44a0-8df1-379ef6230a4e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6cb22710-89a6-44a0-8df1-379ef6230a4e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_chromium - record.avg_chromium*mu_value
            upper = record.avg_chromium + record.avg_chromium*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_chromium_nabl = 'pass'
                break
            else:
                record.avg_chromium_nabl = 'fail'


    # CHLORIDE

    nickel_name = fields.Char("Name",default="DETERMINATION OF NICKEL IN STEEL- IS: 228 (PART-5) 1989 RA 2023")
    nickel_visible = fields.Boolean("DETERMINATION OF NICKEL IN STEEL- IS: 228 (PART-5) 1989 RA 2023",compute="_compute_visible")

    mass_nickela1 = fields.Float(string="Mass in gm of Nickel dimethylglyoximate in the aliquot, (A)")
    mass_nickela2 = fields.Float(string="Mass in gm of Nickel dimethylglyoximate in the aliquot, (A)")
    mass_nickela3 = fields.Float(string="Mass in gm of Nickel dimethylglyoximate in the aliquot, (A)")
    mass_nickela4 = fields.Float(string="Mass in gm of Nickel dimethylglyoximate in the aliquot, (A)")
    mass_nickela5 = fields.Float(string="Mass in gm of Nickel dimethylglyoximate in the aliquot, (A)")

    mass_nickelb1 = fields.Float(string="Mass in gm of the sample of aliquot representing the sample taken, (B)")
    mass_nickelb2 = fields.Float(string="Mass in gm of the sample of aliquot representing the sample taken, (B)")
    mass_nickelb3 = fields.Float(string="Mass in gm of the sample of aliquot representing the sample taken, (B)")
    mass_nickelb4 = fields.Float(string="Mass in gm of the sample of aliquot representing the sample taken, (B)")
    mass_nickelb5 = fields.Float(string="Mass in gm of the sample of aliquot representing the sample taken, (B)")

    percent_nickel_1 = fields.Float(string="Percent of Nickel= (A X 20.32)/B",compute="_compute_percent_nickel")
    percent_nickel_2 = fields.Float(string="Percent of Nickel= (A X 20.32)/B",compute="_compute_percent_nickel")
    percent_nickel_3 = fields.Float(string="Percent of Nickel= (A X 20.32)/B",compute="_compute_percent_nickel")
    percent_nickel_4 = fields.Float(string="Percent of Nickel= (A X 20.32)/B",compute="_compute_percent_nickel")
    percent_nickel_5 = fields.Float(string="Percent of Nickel= (A X 20.32)/B",compute="_compute_percent_nickel")

    @api.depends(
        'mass_nickela1', 'mass_nickelb1',
        'mass_nickela2', 'mass_nickelb2',
        'mass_nickela3', 'mass_nickelb3',
        'mass_nickela4', 'mass_nickelb4',
        'mass_nickela5', 'mass_nickelb5'
    )
    def _compute_percent_nickel(self):
        for record in self:

            # Sample 1
            if record.mass_nickelb1:
                record.percent_nickel_1 = (
                    record.mass_nickela1 * 20.32
                ) / record.mass_nickelb1
            else:
                record.percent_nickel_1 = 0.0

            # Sample 2
            if record.mass_nickelb2:
                record.percent_nickel_2 = (
                    record.mass_nickela2 * 20.32
                ) / record.mass_nickelb2
            else:
                record.percent_nickel_2 = 0.0

            # Sample 3
            if record.mass_nickelb3:
                record.percent_nickel_3 = (
                    record.mass_nickela3 * 20.32
                ) / record.mass_nickelb3
            else:
                record.percent_nickel_3 = 0.0

            # Sample 4
            if record.mass_nickelb4:
                record.percent_nickel_4 = (
                    record.mass_nickela4 * 20.32
                ) / record.mass_nickelb4
            else:
                record.percent_nickel_4 = 0.0

            # Sample 5
            if record.mass_nickelb5:
                record.percent_nickel_5 = (
                    record.mass_nickela5 * 20.32
                ) / record.mass_nickelb5
            else:
                record.percent_nickel_5 = 0.0

    

    avg_nickel = fields.Float(string="Average Of Nickel % =",compute="_compute_avg_nickel")


    @api.depends('percent_nickel_1', 'percent_nickel_2', 'percent_nickel_3', 'percent_nickel_4', 'percent_nickel_5')
    def _compute_avg_nickel(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            nickel = [
                rec.percent_nickel_1,
                rec.percent_nickel_2,
                rec.percent_nickel_3,
                rec.percent_nickel_4,
                rec.percent_nickel_5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_nickel = [c for c in nickel if c]  # ya (c for c in nickel if c not in [False, None, 0.0])
            
            if valid_nickel:
                rec.avg_nickel = sum(valid_nickel) / len(valid_nickel)
            else:
                rec.avg_nickel = 0.0


    
    avg_nickel_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_nickel_conformity", store=True)

    @api.depends('avg_nickel','eln_ref','grade')
    def _compute_avg_nickel_conformity(self):
            # remove this first when making changes
            self.avg_nickel_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_nickel_conformity = 'na'
                    continue

                record.avg_nickel_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','942ccb3a-4104-4a84-839e-0535d8dd39bc')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','942ccb3a-4104-4a84-839e-0535d8dd39bc')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_nickel - record.avg_nickel*mu_value
                        upper = record.avg_nickel + record.avg_nickel*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_nickel_conformity = 'pass'
                            break
                        else:
                            record.avg_nickel_conformity = 'fail'

    avg_nickel_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_nickel_nabl", store=True)

    @api.depends('avg_nickel','eln_ref','grade')
    def _compute_avg_nickel_nabl(self):
        # remove this first
        self.avg_nickel_nabl = 'fail'
        
        for record in self:
            record.avg_nickel_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','942ccb3a-4104-4a84-839e-0535d8dd39bc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','942ccb3a-4104-4a84-839e-0535d8dd39bc')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_nickel - record.avg_nickel*mu_value
            upper = record.avg_nickel + record.avg_nickel*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_nickel_nabl = 'pass'
                break
            else:
                record.avg_nickel_nabl = 'fail'

   


    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.carbon_visible = False
            record.phosphorus_visible = False
            record.sulphur_steel_visible = False
            record.manganese_visible = False
            record.silicon_visible = False
            record.chromium_visible = False
            record.nickel_visible = False
            
            
          

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '1b8c8615-978b-483c-99dd-271530e3884e':
                    record.carbon_visible = True

                if sample.internal_id == '3ecdf1d7-5f58-494b-a898-28a0bb3f8242':
                    record.phosphorus_visible = True

                if sample.internal_id == '2de1cf5a-ef5d-46e7-8183-048b1d415c86':
                    record.sulphur_steel_visible = True

                if sample.internal_id == '9ad149fa-9fa0-4ff7-8168-c27d2505323e':
                    record.manganese_visible = True
                
                if sample.internal_id == '8e03281c-9961-44db-bd32-52bbdea0b56e':
                    record.silicon_visible = True
                
                if sample.internal_id == '6cb22710-89a6-44a0-8df1-379ef6230a4e':
                    record.chromium_visible = True
                    
                if sample.internal_id == '942ccb3a-4104-4a84-839e-0535d8dd39bc':
                    record.nickel_visible = True

                
                
            



    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            
            
            # Water Absorbtion
            if result.parameter.internal_id == '1b8c8615-978b-483c-99dd-271530e3884e':
                result.result_char = round(self.carbon_percentage,2)
                result.calculated = True
                if self.carbon_percentage_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3ecdf1d7-5f58-494b-a898-28a0bb3f8242':
                result.result_char = round(self.avg_phosphorus,2)
                result.calculated = True
                if self.avg_phosphorus_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '2de1cf5a-ef5d-46e7-8183-048b1d415c86':
                result.result_char = round(self.avg_sulphur,2)
                result.calculated = True
                if self.avg_sulphur_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '9ad149fa-9fa0-4ff7-8168-c27d2505323e':
                result.result_char = round(self.avg_manganese,2)
                result.calculated = True
                if self.avg_manganese_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '8e03281c-9961-44db-bd32-52bbdea0b56e':
                result.result_char = round(self.avg_silicon,2)
                result.calculated = True
                if self.avg_silicon_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6cb22710-89a6-44a0-8df1-379ef6230a4e':
                result.result_char = round(self.avg_chromium,2)
                result.calculated = True
                if self.avg_chromium_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '942ccb3a-4104-4a84-839e-0535d8dd39bc':
                result.result_char = round(self.avg_nickel,2)
                result.calculated = True
                if self.avg_nickel_nabl == 'pass':
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
        record = super(SteelChemical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['steel.chemical'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


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

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id








class ChemWasteNotes(models.Model):
    _name = "steel.chemical.notes"

    parent_id = fields.Many2one('steel.chemical',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
    