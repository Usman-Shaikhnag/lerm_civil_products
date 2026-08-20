from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from math import pi


class MechanicalRock(models.Model):
    _name = "mechanical.rock"
    _inherit = "lerm.eln"
    _rec_name = "name_rock"

    name_rock = fields.Char("Name",default="ROCK")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id


    # Specific Gravity
    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    specific_gravity_line_ids = fields.One2many(
        'rock.specific.gravity.water.absorption.line',
        'parent_id',
        string="Test Readings"
    )

    avg_specific_gravity = fields.Float(
        string="Average Specific Gravity",
        compute="_compute_aaverage",
        store=True
    )

    avg_water_absorption = fields.Float(
        string="Average Water Absorption (%)",
        compute="_compute_aaverage",
        store=True
    )

    @api.depends(
        'specific_gravity_line_ids.specific_gravity',
        'specific_gravity_line_ids.water_absorption'
    )
    def _compute_aaverage(self):
        for rec in self:
            sg = rec.specific_gravity_line_ids.mapped('specific_gravity')
            wa = rec.specific_gravity_line_ids.mapped('water_absorption')

            rec.avg_specific_gravity = round(
                sum(sg) / len(sg), 2
            ) if sg else 0.0

            rec.avg_water_absorption = round(
                sum(wa) / len(wa), 2
            ) if wa else 0.0


    avg_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue
            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf5d3d97-9a52-4242-9a36-2e40e5fc8247')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf5d3d97-9a52-4242-9a36-2e40e5fc8247')]).parameter_table
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
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_specific_gravity_nabl", store=True)

    @api.depends('avg_specific_gravity','eln_ref')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf5d3d97-9a52-4242-9a36-2e40e5fc8247')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf5d3d97-9a52-4242-9a36-2e40e5fc8247')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
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



    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87312f3d6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87312f3d6')]).parameter_table
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
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87312f3d6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87312f3d6')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
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


    water_absorption_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    water_absorption_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_water_absorption_final_report", store=True)
    
    @api.depends('avg_water_absorption_nabl', 'water_absorption_report_type')
    def _compute_water_absorption_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.water_absorption_report_type == 'nabl':
                rec.water_absorption_final_report = 'nabl'
    
            elif rec.water_absorption_report_type == 'non_nabl':
                rec.water_absorption_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.avg_water_absorption_nabl == 'pass':
                    rec.water_absorption_final_report = 'nabl'
                else:
                    rec.water_absorption_final_report = 'non_nabl'

    # Water Content

    water_content_name = fields.Char("Name",default="Water Content")
    water_content_visible = fields.Boolean("Water Content Visible",compute="_compute_visible")

    water_content_line_ids = fields.One2many(
        'rock.water.content.line',
        'parent_id',
        string="Samples"
    )

    avg_water_content = fields.Float(
        string="Average Water Content (%)",
        compute="_compute_average",
        store=True,
        digits=(16, 2)
    )

    @api.depends('water_content_line_ids.water_content')
    def _compute_average(self):
        for rec in self:
            values = rec.water_content_line_ids.mapped('water_content')
            rec.avg_water_content = round(
                sum(values) / len(values), 2
            ) if values else 0.0

    avg_water_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_water_content_conformity", store=True)

    @api.depends('avg_water_content','eln_ref','grade')
    def _compute_avg_water_content_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_content_conformity = 'na'
                continue
            record.avg_water_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_content - record.avg_water_content*mu_value
                    upper = record.avg_water_content + record.avg_water_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_water_content_conformity = 'pass'
                        break
                    else:
                        record.avg_water_content_conformity = 'fail'

    avg_water_content_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_water_content_nabl", store=True)

    @api.depends('avg_water_content','eln_ref','grade')
    def _compute_avg_water_content_nabl(self):
        
        for record in self:
            record.avg_water_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_water_content - record.avg_water_content*mu_value
            upper = record.avg_water_content + record.avg_water_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_water_content_nabl = 'pass'
                break
            else:
                record.avg_water_content_nabl = 'fail'


    water_content_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    water_content_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_water_content_final_report", store=True)
    
    @api.depends('avg_water_content_nabl', 'water_content_report_type')
    def _compute_water_content_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.water_content_report_type == 'nabl':
                rec.water_content_final_report = 'nabl'
    
            elif rec.water_content_report_type == 'non_nabl':
                rec.water_content_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.avg_water_content_nabl == 'pass':
                    rec.water_content_final_report = 'nabl'
                else:
                    rec.water_content_final_report = 'non_nabl'
    
    

   
    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.specific_gravity_visible = False
            record.water_content_visible = False


            

          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)


                if sample.internal_id == "bf5d3d97-9a52-4242-9a36-2e40e5fc8247":
                    record.specific_gravity_visible = True

                if sample.internal_id == "71e24ae1-b9a9-41cb-86a5-89d87312f3d6":
                    record.specific_gravity_visible = True

                if sample.internal_id == "a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d":
                    record.water_content_visible = True

                
                

                
                
              
               

                
    
   
            
           

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            
            
            
            # Specific Gravity
            if result.parameter.internal_id == 'bf5d3d97-9a52-4242-9a36-2e40e5fc8247':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Water Absorption
            if result.parameter.internal_id == '71e24ae1-b9a9-41cb-86a5-89d87312f3d6':
                result.result_char = round(self.avg_water_absorption,2)
                result.calculated = True
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



            # Water Content
            if result.parameter.internal_id == 'a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d':
                result.result_char = round(self.avg_water_content,2)
                result.calculated = True
                if self.avg_water_content_nabl == 'pass':
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
        record = super(MechanicalRock, self).create(vals)
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
        record = self.env['mechanical.rock'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    notes_id = fields.One2many('mechanical.rock.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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





class RockSpecificGravityLine(models.Model):
    _name = "rock.specific.gravity.water.absorption.line"
    _description = "Specific Gravity Line"

    parent_id = fields.Many2one('mechanical.rock', string="Parent Id")

    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)


    dry_weight = fields.Float(
        string="Dry Weight of Sample, A (g)"
    )

    ssd_weight = fields.Float(
        string="Saturated Surface Dry Weight, B (g)"
    )

    water_weight = fields.Float(
        string="Weight in Water,  C (g)"
    )

    volume_sample = fields.Float(
        string="Volume of Sample (B−C) (cm³)",
        compute="_compute_values",
        store=True
    )

    specific_gravity = fields.Float(
        string="Specific Gravity (A/(B−C))",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    water_absorption = fields.Float(
        string="Water Absorption (%) ((B−A)/A ×100)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    remarks = fields.Char(string="Remarks")

    @api.depends('dry_weight', 'ssd_weight', 'water_weight')
    def _compute_values(self):
        for rec in self:

            volume = rec.ssd_weight - rec.water_weight
            rec.volume_sample = round(volume, 2)

            if volume:
                rec.specific_gravity = round(
                    rec.dry_weight / volume,
                    2
                )
            else:
                rec.specific_gravity = 0.0

            if rec.dry_weight:
                rec.water_absorption = round(
                    ((rec.ssd_weight - rec.dry_weight) / rec.dry_weight) * 100,
                    2
                )
            else:
                rec.water_absorption = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(RockSpecificGravityLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1





class RockWaterContentLine(models.Model):
    _name = "rock.water.content.line"
    _description = "Water Content Sample"

    parent_id = fields.Many2one('mechanical.rock', string="Parent Id")

    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)

    container_no = fields.Char(string="Container No.")

    w1 = fields.Float(
        string="Weight of Empty Container, W₁ (g)"
    )

    w2 = fields.Float(
        string="Weight of Container + Wet Rock, W₂ (g)"
    )

    w3 = fields.Float(
        string="Weight of Container + Dry Rock, W₃ (g)"
    )

    weight_water = fields.Float(
        string="Weight of Water (W₂ − W₃) (g)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    weight_dry_rock = fields.Float(
        string="Weight of Dry Rock (W₃ − W₁) (g)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    water_content = fields.Float(
        string="Water Content (%) [(W₂ − W₃)/(W₃ − W₁) ×100]",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    @api.depends('w1', 'w2', 'w3')
    def _compute_values(self):
        for rec in self:

            rec.weight_water = rec.w2 - rec.w3
            rec.weight_dry_rock = rec.w3 - rec.w1

            if rec.weight_dry_rock:
                rec.water_content = round(
                    (rec.weight_water / rec.weight_dry_rock) * 100,
                    2
                )
            else:
                rec.water_content = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(RockWaterContentLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class MechanicalRockNotes(models.Model):
    _name = "mechanical.rock.notes"

    parent_id = fields.Many2one('mechanical.rock', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
