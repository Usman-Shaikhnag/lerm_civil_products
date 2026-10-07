from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class AlccofineMechanical(models.Model):
    _name = "mechanical.alccofine"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="ALCCOFINE")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.alccofine.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    notes_id = fields.One2many('mechanical.alccofine.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(AlccofineMechanical, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an # received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Knack.',
            }),
        ]

        res['notes_id'] = default_notes
        return res



    # Specific Gravity

    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    temp_specific_gravity = fields.Float("Temperature °C")
    humidity_specific_gravity = fields.Float("Humidity %")

    mass_alccofine = fields.Float(
        string="Mass of Alccofine (g)"
    )

    initial_volume = fields.Float(
        string="Initial Volume of Kerosene (ml) V1"
    )

    final_volume = fields.Float(
        string="Final Volume of Kerosene and Alccofine (ml) V2"
    )

    displaced_volume = fields.Float(
        string="Displaced Volume (cm³)",
        compute="_compute_specific_gravity",
        store=True
    )

    specific_gravity = fields.Float(
        string="Specific Gravity",
        compute="_compute_specific_gravity",
        store=True
    )

    @api.depends('mass_alccofine', 'initial_volume', 'final_volume')
    def _compute_specific_gravity(self):
        for record in self:
            # V2 - V1
            record.displaced_volume = (
                record.final_volume - record.initial_volume
            )

            # Specific Gravity = Mass / Displaced Volume
            if record.displaced_volume:
                record.specific_gravity = (
                    record.mass_alccofine / record.displaced_volume
                )
            else:
                record.specific_gravity = 0.0


    
    specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_specific_gravity_conformity", store=True)

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_conformity(self):
        
        for record in self:
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e539f02d-9ff6-4e70-95ef-7a1ccbd7696f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e539f02d-9ff6-4e70-95ef-7a1ccbd7696f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.specific_gravity_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.specific_gravity - record.specific_gravity*mu_value
                    upper = record.specific_gravity + record.specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_conformity = 'fail'

    specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_specific_gravity_nabl", store=True)
    
    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e539f02d-9ff6-4e70-95ef-7a1ccbd7696f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e539f02d-9ff6-4e70-95ef-7a1ccbd7696f')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.specific_gravity - record.specific_gravity*mu_value
            upper = record.specific_gravity + record.specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.specific_gravity_nabl = 'pass'
                break
            else:
                record.specific_gravity_nabl = 'fail'


    # Dry Loose Bulk Density
    dry_loose_bulk_density_name = fields.Char("Name",default="Dry Loose Bulk Density")
    dry_loose_bulk_density_visible = fields.Boolean("Dry Loose Bulk Density Visible",compute="_compute_visible")

    temp_percent_normal = fields.Float("Temperature °C")
    humidity_percent_normal = fields.Float("Humidity %")


    dry_trial_ids = fields.One2many(
        'alccofine.bulk.density.line',
        'parent_id',
        string="Trials"
    )

    average_density = fields.Float(
        string="Average Dry Loose Bulk Density (kg/m³)",
        compute="_compute_average_density",
        store=True
    )

    @api.depends('dry_trial_ids.dry_loose_bulk_density')
    def _compute_average_density(self):
        for record in self:
            densities = record.dry_trial_ids.mapped('dry_loose_bulk_density')

            if densities:
                record.average_density = sum(densities) / len(densities)
            else:
                record.average_density = 0.0



    average_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_average_density_conformity", store=True)

    @api.depends('average_density','eln_ref','grade')
    def _compute_average_density_conformity(self):
        
        for record in self:
            record.average_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2312fb35-8ec2-4906-92f1-5f246a0f27d7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2312fb35-8ec2-4906-92f1-5f246a0f27d7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_density_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_density_conformity = 'pass'
                        break
                    else:
                        record.average_density_conformity = 'fail'

    average_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_density_nabl", store=True)
    
    @api.depends('average_density','eln_ref','grade')
    def _compute_average_density_nabl(self):
        
        for record in self:
            record.average_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2312fb35-8ec2-4906-92f1-5f246a0f27d7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2312fb35-8ec2-4906-92f1-5f246a0f27d7')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_density - record.average_density*mu_value
            upper = record.average_density + record.average_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_density_nabl = 'pass'
                break
            else:
                record.average_density_nabl = 'fail'



    
    

    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        

        for record in self:
            record.specific_gravity_visible = False
            record.dry_loose_bulk_density_visible = False
            
            
            
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == 'e539f02d-9ff6-4e70-95ef-7a1ccbd7696f':
                    record.specific_gravity_visible = True
                    
                if sample.internal_id == '2312fb35-8ec2-4906-92f1-5f246a0f27d7':
                    record.dry_loose_bulk_density_visible = True

                

                

                


    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:

            # Specific Gravity
            if result.parameter.internal_id == 'e539f02d-9ff6-4e70-95ef-7a1ccbd7696f':
                result.result_char = round(self.specific_gravity,2)
                result.calculated = True
                if self.specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            
            # Dry Loose Bulk Density
            if result.parameter.internal_id == '2312fb35-8ec2-4906-92f1-5f246a0f27d7':
                result.result_char = round(self.average_density,2)
                result.calculated = True
                if self.average_density_nabl == 'pass':
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
        record = super(AlccofineMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.alccofine'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

class AlccofineBulkDensityLine(models.Model):
    _name = "alccofine.bulk.density.line"

    parent_id = fields.Many2one('mechanical.alccofine',string="Parent Id")
    
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    weight_empty_cylinder = fields.Float(
        string="Weight of empty Cylinder (w1) (kg)"
    )

    weight_cylinder_microsilica = fields.Float(
        string="Weight of empty Cylinder + Microsilica (w2) (kg)"
    )

    weight_microsilica = fields.Float(
        string="Weight of Microsilica (w3) (kg)",
        compute="_compute_values",
        store=True
    )

    cylinder_volume = fields.Float(
        string="Volume of Cylinder (m³)",digits=(16, 3)
    )

    dry_loose_bulk_density = fields.Float(
        string="Dry Loose Bulk Density (kg/m³)",
        compute="_compute_values",
        store=True
    )

    @api.depends('weight_empty_cylinder','weight_cylinder_microsilica','cylinder_volume' )
    def _compute_values(self):
        for record in self:

            # w3 = w2 - w1
            record.weight_microsilica = (
                record.weight_cylinder_microsilica
                - record.weight_empty_cylinder
            )

            # Density = w3 / Volume
            if record.cylinder_volume:
                record.dry_loose_bulk_density = (
                    record.weight_microsilica
                    / record.cylinder_volume
                )
            else:
                record.dry_loose_bulk_density = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(AlccofineBulkDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

   


class AlccofineNotes(models.Model):
    _name = "mechanical.alccofine.notes"

    parent_id = fields.Many2one('mechanical.alccofine',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


