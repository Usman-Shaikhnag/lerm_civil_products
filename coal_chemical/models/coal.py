from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ChemicalCoal(models.Model):
    _name = "chemical.coal"
    _inherit = "lerm.eln"
    _rec_name = "name1"

    name1 = fields.Char("Name",default="Coal")
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

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'chemical.coal.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    notes_id = fields.One2many('chem.coal.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(ChemicalCoal, self).default_get(fields)

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


    
    # moisture

    moisture_name = fields.Char("Name",default="Moisture")
    moisture_visible = fields.Boolean("Moisture",compute="_compute_visible")

    moisture_cruciblew1_1 = fields.Float(string="Weight of Empty Crucible, (W1)",digits=(12,4))
    moisture_cruciblew1_2 = fields.Float(string="Weight of Empty Crucible, (W1)",digits=(12,4))
    moisture_cruciblew1_3 = fields.Float(string="Weight of Empty Crucible, (W1)",digits=(12,4))
    moisture_cruciblew1_4 = fields.Float(string="Weight of Empty Crucible, (W1)",digits=(12,4))
    moisture_cruciblew1_5 = fields.Float(string="Weight of Empty Crucible, (W1)",digits=(12,4))

    moisture_cruciblew2_1 = fields.Float(string="Weight of Crucible and Sample (W2)",digits=(12,4))
    moisture_cruciblew2_2 = fields.Float(string="Weight of Crucible and Sample (W2)",digits=(12,4))
    moisture_cruciblew2_3 = fields.Float(string="Weight of Crucible and Sample (W2)",digits=(12,4))
    moisture_cruciblew2_4 = fields.Float(string="Weight of Crucible and Sample (W2)",digits=(12,4))
    moisture_cruciblew2_5 = fields.Float(string="Weight of Crucible and Sample (W2)",digits=(12,4))

    moisture_cruciblew3_1 = fields.Float(string="Weight of Crucible and sample after ignition (W3)",digits=(12,4))
    moisture_cruciblew3_2 = fields.Float(string="Weight of Crucible and sample after ignition (W3)",digits=(12,4))
    moisture_cruciblew3_3 = fields.Float(string="Weight of Crucible and sample after ignition (W3)" ,digits=(12,4))
    moisture_cruciblew3_4 = fields.Float(string="Weight of Crucible and sample after ignition (W3)",digits=(12,4) )
    moisture_cruciblew3_5 = fields.Float(string="Weight of Crucible and sample after ignition (W3)",digits=(12,4) )

    

    moisture_residue1 = fields.Float(string="Moisture %",  compute="_compute_moisture", store=True)
    moisture_residue2 = fields.Float(string="Moisture %",  compute="_compute_moisture", store=True)
    moisture_residue3 = fields.Float(string="Moisture %",  compute="_compute_moisture", store=True)
    moisture_residue4 = fields.Float(string="Moisture %",  compute="_compute_moisture", store=True)
    moisture_residue5 = fields.Float(string="Moisture %",  compute="_compute_moisture", store=True)

    avg_moisture = fields.Float(string="Average Moisture % ",compute="_compute_avg_moisture",store=True)

    @api.depends('moisture_residue1', 'moisture_residue2', 'moisture_residue3', 'moisture_residue4', 'moisture_residue5')
    def _compute_avg_moisture(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            moisture = [
                rec.moisture_residue1,
                rec.moisture_residue2,
                rec.moisture_residue3,
                rec.moisture_residue4,
                rec.moisture_residue5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_moisture = [c for c in moisture if c]  # ya (c for c in moisture if c not in [False, None, 0.0])
            
            if valid_moisture:
                rec.avg_moisture = sum(valid_moisture) / len(valid_moisture)
            else:
                rec.avg_moisture = 0.0


    @api.depends(
    'moisture_cruciblew1_1','moisture_cruciblew2_1','moisture_cruciblew3_1',
    'moisture_cruciblew1_2','moisture_cruciblew2_2','moisture_cruciblew3_2',
    'moisture_cruciblew1_3','moisture_cruciblew2_3','moisture_cruciblew3_3',
    'moisture_cruciblew1_4','moisture_cruciblew2_4','moisture_cruciblew3_4',
    'moisture_cruciblew1_5','moisture_cruciblew2_5','moisture_cruciblew3_5',
    )
    def _compute_moisture(self):
        for rec in self:

            rec.moisture_residue1 = (
                ((rec.moisture_cruciblew2_1 - rec.moisture_cruciblew3_1) * 100) /
                (rec.moisture_cruciblew2_1 - rec.moisture_cruciblew1_1)
            ) if (rec.moisture_cruciblew2_1 - rec.moisture_cruciblew1_1) else 0.0

            rec.moisture_residue2 = (
                ((rec.moisture_cruciblew2_2 - rec.moisture_cruciblew3_2) * 100) /
                (rec.moisture_cruciblew2_2 - rec.moisture_cruciblew1_2)
            ) if (rec.moisture_cruciblew2_2 - rec.moisture_cruciblew1_2) else 0.0

            rec.moisture_residue3 = (
                ((rec.moisture_cruciblew2_3 - rec.moisture_cruciblew3_3) * 100) /
                (rec.moisture_cruciblew2_3 - rec.moisture_cruciblew1_3)
            ) if (rec.moisture_cruciblew2_3 - rec.moisture_cruciblew1_3) else 0.0

            rec.moisture_residue4 = (
                ((rec.moisture_cruciblew2_4 - rec.moisture_cruciblew3_4) * 100) /
                (rec.moisture_cruciblew2_4 - rec.moisture_cruciblew1_4)
            ) if (rec.moisture_cruciblew2_4 - rec.moisture_cruciblew1_4) else 0.0

            rec.moisture_residue5 = (
                ((rec.moisture_cruciblew2_5 - rec.moisture_cruciblew3_5) * 100) /
                (rec.moisture_cruciblew2_5 - rec.moisture_cruciblew1_5)
            ) if (rec.moisture_cruciblew2_5 - rec.moisture_cruciblew1_5) else 0.0

    

    avg_moisture_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_moisture_conformity", store=True)

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_conformity(self):
            # remove this first when making changes
            self.avg_moisture_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_moisture_conformity = 'na'
                    continue

                record.avg_moisture_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6677pou-645d-4794-a0fd-3daa0124r0014')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6677pou-645d-4794-a0fd-3daa0124r0014')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_moisture - record.avg_moisture*mu_value
                        upper = record.avg_moisture + record.avg_moisture*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_moisture_conformity = 'pass'
                            break
                        else:
                            record.avg_moisture_conformity = 'fail'

    avg_moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_moisture_nabl", store=True)

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_nabl(self):
        # remove this first
        self.avg_moisture_nabl = 'fail'
        
        for record in self:
            record.avg_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6677pou-645d-4794-a0fd-3daa0124r0014')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6677pou-645d-4794-a0fd-3daa0124r0014')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_moisture - record.avg_moisture*mu_value
            upper = record.avg_moisture + record.avg_moisture*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_moisture_nabl = 'pass'
                break
            else:
                record.avg_moisture_nabl = 'fail'


     # ash

    ash_name = fields.Char("Name",default="DETERMINATION OF ASH")
    ash_visible = fields.Boolean("DETERMINATION OF ASH",compute="_compute_visible")

    ash_dishw1_1 = fields.Float(string="Weight of dish (W1)",digits=(12,4))
    ash_dishw1_2 = fields.Float(string="Weight of dish (W1)",digits=(12,4))
    ash_dishw1_3 = fields.Float(string="Weight of dish (W1)",digits=(12,4))
    ash_dishw1_4 = fields.Float(string="Weight of dish (W1)",digits=(12,4))
    ash_dishw1_5 = fields.Float(string="Weight of dish (W1)",digits=(12,4))

    ash_dishw2_1 = fields.Float(string="Weight of dish and sample (W2)",digits=(12,4))
    ash_dishw2_2 = fields.Float(string="Weight of dish and sample (W2)",digits=(12,4))
    ash_dishw2_3 = fields.Float(string="Weight of dish and sample (W2)",digits=(12,4))
    ash_dishw2_4 = fields.Float(string="Weight of dish and sample (W2)",digits=(12,4))
    ash_dishw2_5 = fields.Float(string="Weight of dish and sample (W2)",digits=(12,4))

    ash_dishw3_1 = fields.Float(string="Weight of dish and ash (W3)",digits=(12,4))
    ash_dishw3_2 = fields.Float(string="Weight of dish and ash (W3)",digits=(12,4))
    ash_dishw3_3 = fields.Float(string="Weight of dish and ash (W3)",digits=(12,4) )
    ash_dishw3_4 = fields.Float(string="Weight of dish and ash (W3)" ,digits=(12,4))
    ash_dishw3_5 = fields.Float(string="Weight of dish and ash (W3)" ,digits=(12,4))

    ash_dishw4_1 = fields.Float(string="Weight of dish after brushing out the ash and on reweighing (W4)",digits=(12,4))
    ash_dishw4_2 = fields.Float(string="Weight of dish after brushing out the ash and on reweighing (W4)",digits=(12,4))
    ash_dishw4_3 = fields.Float(string="Weight of dish after brushing out the ash and on reweighing (W4)",digits=(12,4) )
    ash_dishw4_4 = fields.Float(string="Weight of dish after brushing out the ash and on reweighing (W4)",digits=(12,4) )
    ash_dishw4_5 = fields.Float(string="Weight of dish after brushing out the ash and on reweighing (W4)",digits=(12,4) )

    

    ash_1 = fields.Float(string="Ash %", compute="_compute_ash_dish", store=True)
    ash_2 = fields.Float(string="Ash %", compute="_compute_ash_dish", store=True)
    ash_3 = fields.Float(string="Ash %", compute="_compute_ash_dish", store=True)
    ash_4 = fields.Float(string="Ash %", compute="_compute_ash_dish", store=True)
    ash_5 = fields.Float(string="Ash %", compute="_compute_ash_dish", store=True)

    avg_ash = fields.Float(string="Average Ash % ",compute="_compute_avg_ash",store=True)

    @api.depends('ash_1', 'ash_2', 'ash_3', 'ash_4', 'ash_5')
    def _compute_avg_ash(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            ash = [
                rec.ash_1,
                rec.ash_2,
                rec.ash_3,
                rec.ash_4,
                rec.ash_5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_ash = [c for c in ash if c]  # ya (c for c in ash if c not in [False, None, 0.0])
            
            if valid_ash:
                rec.avg_ash = sum(valid_ash) / len(valid_ash)
            else:
                rec.avg_ash = 0.0

    # @api.depends(
    # 'ash_dishw1_1','ash_dishw2_1','ash_dishw3_1','ash_dishw4_1',
    # 'ash_dishw1_2','ash_dishw2_2','ash_dishw3_2','ash_dishw4_2',
    # 'ash_dishw1_3','ash_dishw2_3','ash_dishw3_3','ash_dishw4_3',
    # 'ash_dishw1_4','ash_dishw2_4','ash_dishw3_4','ash_dishw4_4',
    # 'ash_dishw1_5','ash_dishw2_5','ash_dishw3_5','ash_dishw4_5',
    # )
    # def _compute_ash_dish(self):
    #     for rec in self:

    #         rec.ash_1 = (
    #             ((rec.ash_dishw3_1 - rec.ash_dishw4_1) * 100) /
    #             (rec.ash_dishw2_1 - rec.ash_dishw1_1)
    #         ) if (rec.ash_dishw2_1 - rec.ash_dishw1_1) else 0.0

    #         rec.ash_2 = (
    #             ((rec.ash_dishw3_2 - rec.ash_dishw4_2) * 100) /
    #             (rec.ash_dishw2_2 - rec.ash_dishw1_2)
    #         ) if (rec.ash_dishw2_2 - rec.ash_dishw1_2) else 0.0

    #         rec.ash_3 = (
    #             ((rec.ash_dishw3_3 - rec.ash_dishw4_3) * 100) /
    #             (rec.ash_dishw2_3 - rec.ash_dishw1_3)
    #         ) if (rec.ash_dishw2_3 - rec.ash_dishw1_3) else 0.0

    #         rec.ash_4 = (
    #             ((rec.ash_dishw3_4 - rec.ash_dishw4_4) * 100) /
    #             (rec.ash_dishw2_4 - rec.ash_dishw1_4)
    #         ) if (rec.ash_dishw2_4 - rec.ash_dishw1_4) else 0.0

    #         rec.ash_5 = (
    #             ((rec.ash_dishw3_5 - rec.ash_dishw4_5) * 100) /
    #             (rec.ash_dishw2_5 - rec.ash_dishw1_5)
    #         ) if (rec.ash_dishw2_5 - rec.ash_dishw1_5) else 0.0

    @api.depends(
    'ash_dishw1_1',
    'ash_dishw1_2',
    'ash_dishw1_3',
    'ash_dishw1_4',
    'ash_dishw1_5',
    'ash_dishw2_1',
    'ash_dishw2_2',
    'ash_dishw2_3',
    'ash_dishw2_4',
    'ash_dishw2_5',
    'ash_dishw3_1',
    'ash_dishw3_2',
    'ash_dishw3_3',
    'ash_dishw3_4',
    'ash_dishw3_5',
    'ash_dishw4_1',
    'ash_dishw4_2',
    'ash_dishw4_3',
    'ash_dishw4_4',
    'ash_dishw4_5',
    )
    def _compute_ash_dish(self):
        for record in self:

            record.ash_1 = 0.0
            record.ash_2 = 0.0
            record.ash_3 = 0.0
            record.ash_4 = 0.0
            record.ash_5 = 0.0

            if record.ash_dishw2_1 != record.ash_dishw1_1:
                record.ash_1 = (
                    (
                        (record.ash_dishw3_1 - record.ash_dishw4_1)
                        / (record.ash_dishw2_1 - record.ash_dishw1_1)
                    ) * 100
                )
                record.ash_1 = int(record.ash_1 * 100) / 100

            if record.ash_dishw2_2 != record.ash_dishw1_2:
                record.ash_2 = (
                    (
                        (record.ash_dishw3_2 - record.ash_dishw4_2)
                        / (record.ash_dishw2_2 - record.ash_dishw1_2)
                    ) * 100
                )
                record.ash_2 = int(record.ash_2 * 100) / 100

            if record.ash_dishw2_3 != record.ash_dishw1_3:
                record.ash_3 = (
                    (
                        (record.ash_dishw3_3 - record.ash_dishw4_3)
                        / (record.ash_dishw2_3 - record.ash_dishw1_3)
                    ) * 100
                )
                record.ash_3 = int(record.ash_3 * 100) / 100

            if record.ash_dishw2_4 != record.ash_dishw1_4:
                record.ash_4 = (
                    (
                        (record.ash_dishw3_4 - record.ash_dishw4_4)
                        / (record.ash_dishw2_4 - record.ash_dishw1_4)
                    ) * 100
                )
                record.ash_4 = int(record.ash_4 * 100) / 100

            if record.ash_dishw2_5 != record.ash_dishw1_5:
                record.ash_5 = (
                    (
                        (record.ash_dishw3_5 - record.ash_dishw4_5)
                        / (record.ash_dishw2_5 - record.ash_dishw1_5)
                    ) * 100
                )
                record.ash_5 = int(record.ash_5 * 100) / 100


    

    avg_ash_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_ash_conformity", store=True)

    @api.depends('avg_ash','eln_ref','grade')
    def _compute_avg_ash_conformity(self):
            # remove this first when making changes
            self.avg_ash_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_ash_conformity = 'na'
                    continue

                record.avg_ash_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','999oo00-645d-4794-a0fd-3daa0124r00110')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','999oo00-645d-4794-a0fd-3daa0124r00110')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_ash - record.avg_ash*mu_value
                        upper = record.avg_ash + record.avg_ash*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_ash_conformity = 'pass'
                            break
                        else:
                            record.avg_ash_conformity = 'fail'

    avg_ash_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_ash_nabl", store=True)

    @api.depends('avg_ash','eln_ref','grade')
    def _compute_avg_ash_nabl(self):
        # remove this first
        self.avg_ash_nabl = 'fail'
        
        for record in self:
            record.avg_ash_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','999oo00-645d-4794-a0fd-3daa0124r00110')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','999oo00-645d-4794-a0fd-3daa0124r00110')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_ash - record.avg_ash*mu_value
            upper = record.avg_ash + record.avg_ash*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_ash_nabl = 'pass'
                break
            else:
                record.avg_ash_nabl = 'fail'
   

    # Volatile Matter
    
    volatile_matter_name = fields.Char("Name",default="Volatile Matter")
    volatile_matter_visible = fields.Boolean("Volatile Matter",compute="_compute_visible")

    volatile_matter_cruciblew1_1 = fields.Float(string="Weight of empty crucible and lid (W1)" ,digits=(12,4))
    volatile_matter_cruciblew1_2 = fields.Float(string="Weight of empty crucible and lid (W1)",digits=(12,4))
    volatile_matter_cruciblew1_3 = fields.Float(string="Weight of empty crucible and lid (W1)",digits=(12,4))
    volatile_matter_cruciblew1_4 = fields.Float(string="Weight of empty crucible and lid (W1)",digits=(12,4))
    volatile_matter_cruciblew1_5 = fields.Float(string="Weight of empty crucible and lid (W1)",digits=(12,4))

    volatile_matter_cruciblew2_1 = fields.Float(string="Weight of crucible plus lid and sample before heating (W2)",digits=(12,4))
    volatile_matter_cruciblew2_2 = fields.Float(string="Weight of crucible plus lid and sample before heating (W2)",digits=(12,4))
    volatile_matter_cruciblew2_3 = fields.Float(string="Weight of crucible plus lid and sample before heating (W2)",digits=(12,4))
    volatile_matter_cruciblew2_4 = fields.Float(string="Weight of crucible plus lid and sample before heating (W2)",digits=(12,4))
    volatile_matter_cruciblew2_5 = fields.Float(string="Weight of crucible plus lid and sample before heating (W2)",digits=(12,4))

    volatile_matter_cruciblew3_1 = fields.Float(string="Weight of crucible plus lid and sample after heating (W3)",digits=(12,4))
    volatile_matter_cruciblew3_2 = fields.Float(string="Weight of crucible plus lid and sample after heating (W3)",digits=(12,4))
    volatile_matter_cruciblew3_3 = fields.Float(string="Weight of crucible plus lid and sample after heating (W3)" ,digits=(12,4))
    volatile_matter_cruciblew3_4 = fields.Float(string="Weight of crucible plus lid and sample after heating (W3)" ,digits=(12,4))
    volatile_matter_cruciblew3_5 = fields.Float(string="Weight of crucible plus lid and sample after heating (W3)" ,digits=(12,4))

    volatile_matter_driedw4_1 = fields.Float(string="Percentage of moisture in the sample on air dried basis (W°)")
    volatile_matter_driedw4_2 = fields.Float(string="Percentage of moisture in the sample on air dried basis (W°)")
    volatile_matter_driedw4_3 = fields.Float(string="Percentage of moisture in the sample on air dried basis (W°)" )
    volatile_matter_driedw4_4 = fields.Float(string="Percentage of moisture in the sample on air dried basis (W°)" )
    volatile_matter_driedw4_5 = fields.Float(string="Percentage of moisture in the sample on air dried basis (W°)" )

    

    volatile_matter_1 = fields.Float(string="Volatile Matter %", compute="_compute_volatile_matter", store=True)
    volatile_matter_2 = fields.Float(string="Volatile Matter %", compute="_compute_volatile_matter", store=True)
    volatile_matter_3 = fields.Float(string="Volatile Matter %", compute="_compute_volatile_matter", store=True)
    volatile_matter_4 = fields.Float(string="Volatile Matter %", compute="_compute_volatile_matter", store=True)
    volatile_matter_5 = fields.Float(string="Volatile Matter %", compute="_compute_volatile_matter", store=True)

    avg_volatile_matter = fields.Float(string="Average Volatile Matter % ",compute="_compute_avg_vm",store=True)

    @api.depends('volatile_matter_1', 'volatile_matter_2', 'volatile_matter_3', 'volatile_matter_4', 'volatile_matter_5')
    def _compute_avg_vm(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            volatile_matter = [
                rec.volatile_matter_1,
                rec.volatile_matter_2,
                rec.volatile_matter_3,
                rec.volatile_matter_4,
                rec.volatile_matter_5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_volatile_matter = [c for c in volatile_matter if c]  # ya (c for c in volatile_matter if c not in [False, None, 0.0])
            
            if valid_volatile_matter:
                rec.avg_volatile_matter = sum(valid_volatile_matter) / len(valid_volatile_matter)
            else:
                rec.avg_volatile_matter = 0.0

    @api.depends(
    'volatile_matter_cruciblew1_1',
    'volatile_matter_cruciblew1_2',
    'volatile_matter_cruciblew1_3',
    'volatile_matter_cruciblew1_4',
    'volatile_matter_cruciblew1_5',
    'volatile_matter_cruciblew2_1',
    'volatile_matter_cruciblew2_2',
    'volatile_matter_cruciblew2_3',
    'volatile_matter_cruciblew2_4',
    'volatile_matter_cruciblew2_5',
    'volatile_matter_cruciblew3_1',
    'volatile_matter_cruciblew3_2',
    'volatile_matter_cruciblew3_3',
    'volatile_matter_cruciblew3_4',
    'volatile_matter_cruciblew3_5',
    'volatile_matter_driedw4_1',
    'volatile_matter_driedw4_2',
    'volatile_matter_driedw4_3',
    'volatile_matter_driedw4_4',
    'volatile_matter_driedw4_5',
    )
    def _compute_volatile_matter(self):
        for record in self:
            record.volatile_matter_1 = 0.0
            record.volatile_matter_2 = 0.0
            record.volatile_matter_3 = 0.0
            record.volatile_matter_4 = 0.0
            record.volatile_matter_5 = 0.0

            if record.volatile_matter_cruciblew2_1 != record.volatile_matter_cruciblew1_1:
                record.volatile_matter_1 = (
                    (
                        (record.volatile_matter_cruciblew2_1
                        - record.volatile_matter_cruciblew3_1)
                        / (record.volatile_matter_cruciblew2_1
                        - record.volatile_matter_cruciblew1_1)
                    ) * 100
                    - record.volatile_matter_driedw4_1
                )
                record.volatile_matter_1 = int(
                    record.volatile_matter_1 * 100
                ) / 100

            if record.volatile_matter_cruciblew2_2 != record.volatile_matter_cruciblew1_2:
                record.volatile_matter_2 = (
                    (
                        (record.volatile_matter_cruciblew2_2
                        - record.volatile_matter_cruciblew3_2)
                        / (record.volatile_matter_cruciblew2_2
                        - record.volatile_matter_cruciblew1_2)
                    ) * 100
                    - record.volatile_matter_driedw4_2
                )
                record.volatile_matter_2 = int(
                    record.volatile_matter_2 * 100
                ) / 100

            if record.volatile_matter_cruciblew2_3 != record.volatile_matter_cruciblew1_3:
                record.volatile_matter_3 = (
                    (
                        (record.volatile_matter_cruciblew2_3
                        - record.volatile_matter_cruciblew3_3)
                        / (record.volatile_matter_cruciblew2_3
                        - record.volatile_matter_cruciblew1_3)
                    ) * 100
                    - record.volatile_matter_driedw4_3
                )
                record.volatile_matter_3 = int(
                    record.volatile_matter_3 * 100
                ) / 100

            if record.volatile_matter_cruciblew2_4 != record.volatile_matter_cruciblew1_4:
                record.volatile_matter_4 = (
                    (
                        (record.volatile_matter_cruciblew2_4
                        - record.volatile_matter_cruciblew3_4)
                        / (record.volatile_matter_cruciblew2_4
                        - record.volatile_matter_cruciblew1_4)
                    ) * 100
                    - record.volatile_matter_driedw4_4
                )
                record.volatile_matter_4 = int(
                    record.volatile_matter_4 * 100
                ) / 100

            if record.volatile_matter_cruciblew2_5 != record.volatile_matter_cruciblew1_5:
                record.volatile_matter_5 = (
                    (
                        (record.volatile_matter_cruciblew2_5
                        - record.volatile_matter_cruciblew3_5)
                        / (record.volatile_matter_cruciblew2_5
                        - record.volatile_matter_cruciblew1_5)
                    ) * 100
                    - record.volatile_matter_driedw4_5
                )
                record.volatile_matter_5 = int(
                    record.volatile_matter_5 * 100
                ) / 100


    

    avg_volatile_matter_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_volatile_matter_conformity", store=True)

    @api.depends('avg_volatile_matter','eln_ref','grade')
    def _compute_avg_volatile_matter_conformity(self):
            # remove this first when making changes
            self.avg_volatile_matter_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_volatile_matter_conformity = 'na'
                    continue

                record.avg_volatile_matter_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3330077-645d-4794-a0fd-3daa0124r001144')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3330077-645d-4794-a0fd-3daa0124r001144')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_volatile_matter - record.avg_volatile_matter*mu_value
                        upper = record.avg_volatile_matter + record.avg_volatile_matter*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_volatile_matter_conformity = 'pass'
                            break
                        else:
                            record.avg_volatile_matter_conformity = 'fail'

    avg_volatile_matter_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_volatile_matter_nabl", store=True)

    @api.depends('avg_volatile_matter','eln_ref','grade')
    def _compute_avg_volatile_matter_nabl(self):
        # remove this first
        self.avg_volatile_matter_nabl = 'fail'
        
        for record in self:
            record.avg_volatile_matter_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3330077-645d-4794-a0fd-3daa0124r001144')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3330077-645d-4794-a0fd-3daa0124r001144')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_volatile_matter - record.avg_volatile_matter*mu_value
            upper = record.avg_volatile_matter + record.avg_volatile_matter*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_volatile_matter_nabl = 'pass'
                break
            else:
                record.avg_volatile_matter_nabl = 'fail'

    #  DETERMINATION OF Fixed carbon
    carbon_name = fields.Char("Name",default="DETERMINATION OF Fixed Carbon")
    carbon_visible = fields.Boolean("DETERMINATION OF Fixed Carbon",compute="_compute_visible")

    carbon_mosturem_1 = fields.Float(string="Moisture % (M %)",compute="_compute_carbon_moisture")
    carbon_mosturem_2 = fields.Float(string="Moisture % (M %)",compute="_compute_carbon_moisture")
    carbon_mosturem_3 = fields.Float(string="Moisture % (M %)",compute="_compute_carbon_moisture")
    carbon_mosturem_4 = fields.Float(string="Moisture % (M %)",compute="_compute_carbon_moisture")
    carbon_mosturem_5 = fields.Float(string="Moisture % (M %)",compute="_compute_carbon_moisture")

    

    carbon_vm_1 = fields.Float(string="Volatile Matter % (VM %)",compute="_compute_carbon_vm")
    carbon_vm_2 = fields.Float(string="Volatile Matter % (VM %)",compute="_compute_carbon_vm")
    carbon_vm_3 = fields.Float(string="Volatile Matter % (VM %)",compute="_compute_carbon_vm")
    carbon_vm_4 = fields.Float(string="Volatile Matter % (VM %)",compute="_compute_carbon_vm")
    carbon_vm_5 = fields.Float(string="Volatile Matter % (VM %)",compute="_compute_carbon_vm")

    carbon_asha_1 = fields.Float(string="Ash % (A %)",compute="_compute_carbon_ash")
    carbon_asha_2 = fields.Float(string="Ash % (A %)",compute="_compute_carbon_ash")
    carbon_asha_3 = fields.Float(string="Ash % (A %)" ,compute="_compute_carbon_ash")
    carbon_asha_4 = fields.Float(string="Ash % (A %)" ,compute="_compute_carbon_ash")
    carbon_asha_5 = fields.Float(string="Ash % (A %)" ,compute="_compute_carbon_ash")

    

    carbon_1 = fields.Float(string="Fixed Carbon %",  compute="_compute_fixed_carbon")
    carbon_2 = fields.Float(string="Fixed Carbon %",  compute="_compute_fixed_carbon")
    carbon_3 = fields.Float(string="Fixed Carbon %",  compute="_compute_fixed_carbon")
    carbon_4 = fields.Float(string="Fixed Carbon %",  compute="_compute_fixed_carbon")
    carbon_5 = fields.Float(string="Fixed Carbon %",  compute="_compute_fixed_carbon")

    avg_carbon = fields.Float(string="Average Fixed Carbon % ",compute="_compute_avg_fc")


    @api.depends('carbon_1', 'carbon_2', 'carbon_3', 'carbon_4', 'carbon_5')
    def _compute_avg_fc(self):
        for rec in self:
            # Sagle values ek list madhe gheun fakt non-zero/valid values filter karu
            carbon = [
                rec.carbon_1,
                rec.carbon_2,
                rec.carbon_3,
                rec.carbon_4,
                rec.carbon_5
            ]
            
            # Fakt tyach values count hotil jya fields madhe data ahe (non-zero / truthy)
            valid_carbon = [c for c in carbon if c]  # ya (c for c in carbon if c not in [False, None, 0.0])
            
            if valid_carbon:
                rec.avg_carbon = sum(valid_carbon) / len(valid_carbon)
            else:
                rec.avg_carbon = 0.0


    @api.depends(
    'moisture_residue1',
    'moisture_residue2',
    'moisture_residue3',
    'moisture_residue4',
    'moisture_residue5'
    )
    def _compute_carbon_moisture(self):
        for rec in self:

            rec.carbon_mosturem_1 = rec.moisture_residue1 or 0.0
            rec.carbon_mosturem_2 = rec.moisture_residue2 or 0.0
            rec.carbon_mosturem_3 = rec.moisture_residue3 or 0.0
            rec.carbon_mosturem_4 = rec.moisture_residue4 or 0.0
            rec.carbon_mosturem_5 = rec.moisture_residue5 or 0.0

    @api.depends(
    'volatile_matter_1',
    'volatile_matter_2',
    'volatile_matter_3',
    'volatile_matter_4',
    'volatile_matter_5'
    )
    def _compute_carbon_vm(self):
        for rec in self:

            rec.carbon_vm_1 = rec.volatile_matter_1 or 0.0
            rec.carbon_vm_2 = rec.volatile_matter_2 or 0.0
            rec.carbon_vm_3 = rec.volatile_matter_3 or 0.0
            rec.carbon_vm_4 = rec.volatile_matter_4 or 0.0
            rec.carbon_vm_5 = rec.volatile_matter_5 or 0.0

    @api.depends(
    'ash_1',
    'ash_2',
    'ash_3',
    'ash_4',
    'ash_5'
    )
    def _compute_carbon_ash(self):
        for rec in self:

            rec.carbon_asha_1 = rec.ash_1 or 0.0
            rec.carbon_asha_2 = rec.ash_2 or 0.0
            rec.carbon_asha_3 = rec.ash_3 or 0.0
            rec.carbon_asha_4 = rec.ash_4 or 0.0
            rec.carbon_asha_5 = rec.ash_5 or 0.0


    @api.depends(
    'carbon_mosturem_1', 'carbon_vm_1', 'carbon_asha_1',
    'carbon_mosturem_2', 'carbon_vm_2', 'carbon_asha_2',
    'carbon_mosturem_3', 'carbon_vm_3', 'carbon_asha_3',
    'carbon_mosturem_4', 'carbon_vm_4', 'carbon_asha_4',
    'carbon_mosturem_5', 'carbon_vm_5', 'carbon_asha_5',
    )
    def _compute_fixed_carbon(self):
        for rec in self:

            rec.carbon_1 = 0.0
            rec.carbon_2 = 0.0
            rec.carbon_3 = 0.0
            rec.carbon_4 = 0.0
            rec.carbon_5 = 0.0

            if (
                rec.carbon_mosturem_1
                or rec.carbon_vm_1
                or rec.carbon_asha_1
            ):
                rec.carbon_1 = 100 - (
                    (rec.carbon_mosturem_1 or 0.0) +
                    (rec.carbon_vm_1 or 0.0) +
                    (rec.carbon_asha_1 or 0.0)
                )

            if (
                rec.carbon_mosturem_2
                or rec.carbon_vm_2
                or rec.carbon_asha_2
            ):
                rec.carbon_2 = 100 - (
                    (rec.carbon_mosturem_2 or 0.0) +
                    (rec.carbon_vm_2 or 0.0) +
                    (rec.carbon_asha_2 or 0.0)
                )

            if (
                rec.carbon_mosturem_3
                or rec.carbon_vm_3
                or rec.carbon_asha_3
            ):
                rec.carbon_3 = 100 - (
                    (rec.carbon_mosturem_3 or 0.0) +
                    (rec.carbon_vm_3 or 0.0) +
                    (rec.carbon_asha_3 or 0.0)
                )

            if (
                rec.carbon_mosturem_4
                or rec.carbon_vm_4
                or rec.carbon_asha_4
            ):
                rec.carbon_4 = 100 - (
                    (rec.carbon_mosturem_4 or 0.0) +
                    (rec.carbon_vm_4 or 0.0) +
                    (rec.carbon_asha_4 or 0.0)
                )

            if (
                rec.carbon_mosturem_5
                or rec.carbon_vm_5
                or rec.carbon_asha_5
            ):
                rec.carbon_5 = 100 - (
                    (rec.carbon_mosturem_5 or 0.0) +
                    (rec.carbon_vm_5 or 0.0) +
                    (rec.carbon_asha_5 or 0.0)
                )



    avg_carbon_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_carbon_conformity", store=True)

    @api.depends('avg_carbon','eln_ref','grade')
    def _compute_avg_carbon_conformity(self):
            # remove this first when making changes
            self.avg_carbon_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_carbon_conformity = 'na'
                    continue

                record.avg_carbon_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6661147-645d-4794-a0fd-3daa0124r0022004')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6661147-645d-4794-a0fd-3daa0124r0022004')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_carbon - record.avg_carbon*mu_value
                        upper = record.avg_carbon + record.avg_carbon*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_carbon_conformity = 'pass'
                            break
                        else:
                            record.avg_carbon_conformity = 'fail'

    avg_carbon_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_carbon_nabl", store=True)

    @api.depends('avg_carbon','eln_ref','grade')
    def _compute_avg_carbon_nabl(self):
        # remove this first
        self.avg_carbon_nabl = 'fail'
        
        for record in self:
            record.avg_carbon_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6661147-645d-4794-a0fd-3daa0124r0022004')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6661147-645d-4794-a0fd-3daa0124r0022004')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_carbon - record.avg_carbon*mu_value
            upper = record.avg_carbon + record.avg_carbon*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_carbon_nabl = 'pass'
                break
            else:
                record.avg_carbon_nabl = 'fail'


    #  Gross Calorific Value
    
    gross_calorific_name = fields.Char("Name",default="Gross Calorific Value")
    gross_calorific_visible = fields.Boolean("Gross Calorific Value",compute="_compute_visible")

    gsv = fields.Integer(string="Gross Calorific Value")

    # gross_calorific_w_1 = fields.Float(string="Sample Weight (W)",digits=(12,4))
    # gross_calorific_w_2 = fields.Float(string="Sample Weight (W)",digits=(12,4))
    # gross_calorific_w_3 = fields.Float(string="Sample Weight (W)",digits=(12,4))
    # gross_calorific_w_4 = fields.Float(string="Sample Weight (W)",digits=(12,4))
    # gross_calorific_w_5 = fields.Float(string="Sample Weight (W)",digits=(12,4))

    

    # gross_calorific_t_1 = fields.Float(string="Rise in Temperature, (ΔT)")
    # gross_calorific_t_2 = fields.Float(string="Rise in Temperature, (ΔT)")
    # gross_calorific_t_3 = fields.Float(string="Rise in Temperature, (ΔT)")
    # gross_calorific_t_4 = fields.Float(string="Rise in Temperature, (ΔT)")
    # gross_calorific_t_5 = fields.Float(string="Rise in Temperature, (ΔT)")

    # gross_calorific_e1_1 = fields.Float(string="Cotton thread Correction (E1)")
    # gross_calorific_e1_2 = fields.Float(string="Cotton thread Correction (E1)")
    # gross_calorific_e1_3 = fields.Float(string="Cotton thread Correction (E1)")
    # gross_calorific_e1_4 = fields.Float(string="Cotton thread Correction (E1)")
    # gross_calorific_e1_5 = fields.Float(string="Cotton thread Correction (E1)")

    

    # gross_calorific_e2_1 = fields.Float(string="Ignition Wire (E2)")
    # gross_calorific_e2_2 = fields.Float(string="Ignition Wire (E2)")
    # gross_calorific_e2_3 = fields.Float(string="Ignition Wire (E2)")
    # gross_calorific_e2_4 = fields.Float(string="Ignition Wire (E2)")
    # gross_calorific_e2_5 = fields.Float(string="Ignition Wire (E2)")

    # gross_calorific_weqv_1 = fields.Float(string="Water Equivalent Weight (Weqv)")
    # gross_calorific_weqv_2 = fields.Float(string="Water Equivalent Weight (Weqv)")
    # gross_calorific_weqv_3 = fields.Float(string="Water Equivalent Weight (Weqv)")
    # gross_calorific_weqv_4 = fields.Float(string="Water Equivalent Weight (Weqv)")
    # gross_calorific_weqv_5 = fields.Float(string="Water Equivalent Weight (Weqv)")


    # gross_calorific_gcv_1 = fields.Float(string="GCV, Kcal/Kg",compute="_compute_gcv", store=True )
    # gross_calorific_gcv_2 = fields.Float(string="GCV, Kcal/Kg",compute="_compute_gcv", store=True)
    # gross_calorific_gcv_3 = fields.Float(string="GCV, Kcal/Kg",compute="_compute_gcv", store=True)
    # gross_calorific_gcv_4 = fields.Float(string="GCV, Kcal/Kg",compute="_compute_gcv", store=True)
    # gross_calorific_gcv_5 = fields.Float(string="GCV, Kcal/Kg",compute="_compute_gcv", store=True)

    # avg_gross_calorific = fields.Float(string="Average GCV, Kcal/Kg ",compute="_compute_avg_gcv",store=True)


    # @api.depends(
    # 'gross_calorific_w_1','gross_calorific_t_1','gross_calorific_weqv_1','gross_calorific_e1_1','gross_calorific_e2_1',
    # 'gross_calorific_w_2','gross_calorific_t_2','gross_calorific_weqv_2','gross_calorific_e1_2','gross_calorific_e2_2',
    # 'gross_calorific_w_3','gross_calorific_t_3','gross_calorific_weqv_3','gross_calorific_e1_3','gross_calorific_e2_3',
    # 'gross_calorific_w_4','gross_calorific_t_4','gross_calorific_weqv_4','gross_calorific_e1_4','gross_calorific_e2_4',
    # 'gross_calorific_w_5','gross_calorific_t_5','gross_calorific_weqv_5','gross_calorific_e1_5','gross_calorific_e2_5',
    # )
    # def _compute_gcv(self):
    #     for rec in self:

    #         rec.gross_calorific_gcv_1 = (
    #             (rec.gross_calorific_t_1 * rec.gross_calorific_weqv_1) -
    #             ((rec.gross_calorific_e1_1 or 0.0) + (rec.gross_calorific_e2_1 or 0.0))
    #         ) / rec.gross_calorific_w_1 if rec.gross_calorific_w_1 else 0.0

    #         rec.gross_calorific_gcv_2 = (
    #             (rec.gross_calorific_t_2 * rec.gross_calorific_weqv_2) -
    #             ((rec.gross_calorific_e1_2 or 0.0) + (rec.gross_calorific_e2_2 or 0.0))
    #         ) / rec.gross_calorific_w_2 if rec.gross_calorific_w_2 else 0.0

    #         rec.gross_calorific_gcv_3 = (
    #             (rec.gross_calorific_t_3 * rec.gross_calorific_weqv_3) -
    #             ((rec.gross_calorific_e1_3 or 0.0) + (rec.gross_calorific_e2_3 or 0.0))
    #         ) / rec.gross_calorific_w_3 if rec.gross_calorific_w_3 else 0.0

    #         rec.gross_calorific_gcv_4 = (
    #             (rec.gross_calorific_t_4 * rec.gross_calorific_weqv_4) -
    #             ((rec.gross_calorific_e1_4 or 0.0) + (rec.gross_calorific_e2_4 or 0.0))
    #         ) / rec.gross_calorific_w_4 if rec.gross_calorific_w_4 else 0.0

    #         rec.gross_calorific_gcv_5 = (
    #             (rec.gross_calorific_t_5 * rec.gross_calorific_weqv_5) -
    #             ((rec.gross_calorific_e1_5 or 0.0) + (rec.gross_calorific_e2_5 or 0.0))
    #         ) / rec.gross_calorific_w_5 if rec.gross_calorific_w_5 else 0.0


    # @api.depends(
    # 'gross_calorific_gcv_1',
    # 'gross_calorific_gcv_2',
    # 'gross_calorific_gcv_3',
    # 'gross_calorific_gcv_4',
    # 'gross_calorific_gcv_5'
    # )
    # def _compute_avg_gcv(self):
    #     for rec in self:

    #         rec.avg_gross_calorific = (
    #             rec.gross_calorific_gcv_1 +
    #             rec.gross_calorific_gcv_2 +
    #             rec.gross_calorific_gcv_3 +
    #             rec.gross_calorific_gcv_4 +
    #             rec.gross_calorific_gcv_5
    #         ) / 5


    gsv_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_gsv_conformity", store=True)

    @api.depends('gsv','eln_ref','grade')
    def _compute_gsv_conformity(self):
            # remove this first when making changes
            self.gsv_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.gsv_conformity = 'na'
                    continue

                record.gsv_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9977882-645d-4794-a0fd-3daa0124r0021147')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9977882-645d-4794-a0fd-3daa0124r0021147')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.gsv - record.gsv*mu_value
                        upper = record.gsv + record.gsv*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.gsv_conformity = 'pass'
                            break
                        else:
                            record.gsv_conformity = 'fail'

    gsv_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_gsv_nabl", store=True)

    @api.depends('gsv','eln_ref','grade')
    def _compute_gsv_nabl(self):
        # remove this first
        self.gsv_nabl = 'fail'
        
        for record in self:
            record.gsv_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9977882-645d-4794-a0fd-3daa0124r0021147')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9977882-645d-4794-a0fd-3daa0124r0021147')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.gsv - record.gsv*mu_value
            upper = record.gsv + record.gsv*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.gsv_nabl = 'pass'
                break
            else:
                record.gsv_nabl = 'fail'




   

    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.moisture_visible = False
            record.ash_visible = False
            record.volatile_matter_visible = False
            record.carbon_visible = False
            record.gross_calorific_visible = False
            
          

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
               
                if sample.internal_id == '6677pou-645d-4794-a0fd-3daa0124r0014':
                    record.moisture_visible = True

                if sample.internal_id == '999oo00-645d-4794-a0fd-3daa0124r00110':
                    record.ash_visible = True

                if sample.internal_id == '3330077-645d-4794-a0fd-3daa0124r001144':
                    record.volatile_matter_visible = True

                if sample.internal_id == '6661147-645d-4794-a0fd-3daa0124r0022004':
                    record.carbon_visible = True

                if sample.internal_id == '9977882-645d-4794-a0fd-3daa0124r0021147':
                    record.gross_calorific_visible = True

                




    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

        
            if result.parameter.internal_id == '6677pou-645d-4794-a0fd-3daa0124r0014':
                result.result_char = round(self.avg_moisture,2)
                result.calculated = True
                if self.avg_moisture_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '999oo00-645d-4794-a0fd-3daa0124r00110':
                result.result_char = round(self.avg_ash,2)
                result.calculated = True
                if self.avg_ash_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3330077-645d-4794-a0fd-3daa0124r001144':
                result.result_char = round(self.avg_volatile_matter,2)
                result.calculated = True
                if self.avg_volatile_matter_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6661147-645d-4794-a0fd-3daa0124r0022004':
                result.result_char = round(self.avg_carbon,2)
                result.calculated = True
                if self.avg_carbon_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '9977882-645d-4794-a0fd-3daa0124r0021147':
                result.result_char = round(self.gsv,2)
                result.calculated = True
                if self.gsv_nabl == 'pass':
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
        record = super(ChemicalCoal, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['chemical.coal'].browse(self.ids[0])
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








class ChemCoalNotes(models.Model):
    _name = "chem.coal.notes"

    parent_id = fields.Many2one('chemical.coal',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
    