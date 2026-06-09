from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from decimal import Decimal
import matplotlib.pyplot as plt
import io
import base64

class SandreplacementMechanical(models.Model):
    _name = "mechanical.sand.replacement"
    _inherit = "lerm.eln"
    _rec_name = "name"



    name = fields.Char("Name",default="Sand Replacement")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


    notes_id = fields.One2many('sand.replacement.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(SandreplacementMechanical, self).default_get(fields)

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

        

            if result.parameter.internal_id == '1245201457838w-372f-4775-9bcb-e999987hy':
                # result.result_char = self.avg_specific_gravity
                result.calculated = True

            if result.parameter.internal_id == '321t78874gtre-372f-4775-9bcb-32001478bgg':
                result.result_char = round(self.avg_compaction,2)
                result.calculated = True
                if self.avg_compaction_nabl == 'pass':
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
        record = super(SandreplacementMechanical, self).create(vals)
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
        record = self.env['mechanical.sand.replacement'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    # added
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


   

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.density_relation_visible = False
            record.core_cutter_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '1245201457838w-372f-4775-9bcb-e999987hy':
                    record.density_relation_visible = True

                if sample.internal_id == '321t78874gtre-372f-4775-9bcb-32001478bgg':
                    record.core_cutter_visible = True









   


    


    # Modified Compaction Test 
       # Density Relation Heavy Compaction
    density_relation_name = fields.Char("Name",default="Density Relation Using Heavy Compaction")
    density_relation_visible = fields.Boolean("Density Relation Visible",compute="_compute_visible")

    density_relation_table = fields.One2many('mech.sand.replacement.line','parent_id',string="Density Relation")
    wt_of_modul = fields.Float('Weight of Mould in gm')
    vl_of_modul = fields.Float('Volume of Mould in cc')
    chart_image_density = fields.Binary("Line Chart", compute="_compute_chart_image_density", store=True)

    mmd = fields.Float(string="MMD gm/cc", compute="_compute_max_dry_density_heavy", store=True)
    omc = fields.Float(string="OMC %", compute="_compute_max_omc_heavy", store=True)

    @api.depends('density_relation_table.dry_density')
    def _compute_max_dry_density_heavy(self):
        for record in self:
            max_dry_density_heavy = max(record.density_relation_table.mapped('dry_density'), default=0.0)
            record.mmd = max_dry_density_heavy

    @api.depends('density_relation_table.dry_density', 'density_relation_table.moisture', 'mmd')
    def _compute_max_omc_heavy(self):
        for record in self:
            max_dry_density_light_omc = record.mmd
            corresponding_moisture_heavy = next((line.moisture for line in record.density_relation_table if line.dry_density == max_dry_density_light_omc), 0.0)
            record.omc = corresponding_moisture_heavy



    def generate_line_chart_density(self):
        # Prepare data for the chart
        x_values = []
        y_values = []
        for line in self.density_relation_table:
            x_values.append(line.moisture)
            y_values.append(line.dry_density)
        
        # Create the line chart
        plt.plot(x_values, y_values, marker='o')
        plt.xlabel('% Moisture')
        plt.ylabel('Dry Density')
        plt.title('Density Relation Using Heavy Compaction')


        plt.ylim(bottom=0, top=max(y_values) + 10)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the figure to free up resources
        buffer.seek(0)
    
        # Convert the chart image to base64
        chart_image = base64.b64encode(buffer.read()).decode('utf-8')  
        return chart_image
    
    @api.depends('density_relation_table')
    def _compute_chart_image_density(self):
        try:
            for record in self:
                chart_image = record.generate_line_chart_density()
                record.chart_image_density = chart_image
        except:
            pass 


    core_cutter_visible = fields.Boolean("Sand Replacement Method:",compute="_compute_visible")
    core_cutter_name = fields.Char("Name",default="Sand Replacement Method")

    bulk_density_1 = fields.Float(string="Bulk Density ")
    bulk_density_2 = fields.Float(string="Bulk Density ")
    bulk_density_3 = fields.Float(string="Bulk Density ")

    moisture_content_1 = fields.Float(string="Field Moisture Content")
    moisture_content_2 = fields.Float(string="Field Moisture Content")
    moisture_content_3 = fields.Float(string="Field Moisture Content")

    dry_density_1 = fields.Float(string="Field Dry Density")
    dry_density_2 = fields.Float(string="Field Dry Density")
    dry_density_3 = fields.Float(string="Field Dry Density")

    compaction_1 = fields.Float(string="Compaction Achieved",compute="_compute_compaction", store=True)
    compaction_2 = fields.Float(string="Compaction Achieved",compute="_compute_compaction", store=True)
    compaction_3 = fields.Float(string="Compaction Achieved",compute="_compute_compaction", store=True)

    avg_compaction = fields.Float(string="Avg. Compaction Achieved-%",compute="_compute_compaction", store=True)

    site_image = fields.Binary(string="Site Photograph")

    @api.depends('dry_density_1', 'dry_density_2', 'dry_density_3', 'mmd')
    def _compute_compaction(self):
        for rec in self:
            values = []

            if rec.mmd:
                rec.compaction_1 = (rec.mmd / rec.dry_density_1) * 100 if rec.dry_density_1 else 0.0
                rec.compaction_2 = (rec.mmd / rec.dry_density_2) * 100 if rec.dry_density_2 else 0.0
                rec.compaction_3 = (rec.mmd / rec.dry_density_3) * 100 if rec.dry_density_3 else 0.0

                # collect valid values
                if rec.compaction_1:
                    values.append(rec.compaction_1)
                if rec.compaction_2:
                    values.append(rec.compaction_2)
                if rec.compaction_3:
                    values.append(rec.compaction_3)

                # average
                rec.avg_compaction = sum(values) / len(values) if values else 0.0

            else:
                rec.compaction_1 = 0.0
                rec.compaction_2 = 0.0
                rec.compaction_3 = 0.0
                rec.avg_compaction = 0.0

    avg_compaction_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avg_compaction_conformity")

    avg_compaction_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_compaction_nabl")


    @api.depends('avg_compaction','eln_ref','grade')
    def _compute_avg_compaction_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_compaction_conformity = 'na'
                continue
            record.avg_compaction_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321t78874gtre-372f-4775-9bcb-32001478bgg')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321t78874gtre-372f-4775-9bcb-32001478bgg')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_compaction - record.avg_compaction*mu_value
                    upper = record.avg_compaction + record.avg_compaction*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_compaction_conformity = 'pass'
                        break
                    else:
                        record.avg_compaction_conformity = 'fail'

    @api.depends('avg_compaction','eln_ref','grade')
    def _compute_avg_compaction_nabl(self):
        
        for record in self:
            
            record.avg_compaction_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321t78874gtre-372f-4775-9bcb-32001478bgg')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321t78874gtre-372f-4775-9bcb-32001478bgg')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_compaction - record.avg_compaction*mu_value
            upper = record.avg_compaction + record.avg_compaction*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_compaction_nabl = 'pass'
                break
            else:
                record.avg_compaction_nabl = 'fail'
    



 


class SandReplacemetLine(models.Model):
    _name = "mech.sand.replacement.line"
    parent_id = fields.Many2one('mechanical.sand.replacement',string="Parent Id")

    determination_no = fields.Float(string="Determination No")
    wt_of_modul_compact = fields.Integer(string="Weight of Mould + Compacted sample in gm")
    wt_of_compact = fields.Integer(string="Weight of compacted sample in gm", compute="_compute_wt_of_compact")
    bulk_density = fields.Float(string="Bulk Density of sample in gm/cc", compute="_compute_bulk_density")
    container_no = fields.Integer(string="Container No")
    wt_of_container = fields.Float(string="Weight of Container in gm")
    wt_of_container_wet = fields.Float(string="Weight of Container + wet sample in gm")
    wt_of_container_dry = fields.Float(string="Weight of Container + dry sample in gm")
    wt_of_dry_sample = fields.Float(string="Weight of dry sample in gm", compute="_compute_wt_of_dry_sample")
    wt_of_moisture = fields.Float(string="Weight of moisture in gm", compute="_compute_wt_of_moisture")
    moisture = fields.Float(string="% Moisture", compute="_compute_moisture")
    dry_density = fields.Float(string="Dry density in gm/cc", compute="_compute_dry_density")


    @api.depends('wt_of_modul_compact', 'parent_id.wt_of_modul')
    def _compute_wt_of_compact(self):
        for line in self:
            line.wt_of_compact = round(line.wt_of_modul_compact - line.parent_id.wt_of_modul,2)



    @api.depends('wt_of_compact', 'parent_id.vl_of_modul')
    def _compute_bulk_density(self):
        for line in self:
            if line.parent_id.vl_of_modul != 0:
                line.bulk_density = round(line.wt_of_compact / line.parent_id.vl_of_modul,2)
            else:
                line.bulk_density = 0.0



    @api.depends('wt_of_container_dry', 'wt_of_container')
    def _compute_wt_of_dry_sample(self):
        for line in self:
            line.wt_of_dry_sample = round(line.wt_of_container_dry - line.wt_of_container,2)


    @api.depends('wt_of_container_wet','wt_of_container_dry')
    def _compute_wt_of_moisture(self):
        for record in self:
            record.wt_of_moisture = round((record.wt_of_container_wet - record.wt_of_container_dry),2)


    @api.depends('wt_of_moisture', 'wt_of_dry_sample')
    def _compute_moisture(self):
        for line in self:
            if line.wt_of_dry_sample != 0:
                line.moisture = round(line.wt_of_moisture / line.wt_of_dry_sample * 100,2)
            else:
                line.moisture = 0.0


    @api.depends('bulk_density', 'moisture')
    def _compute_dry_density(self):
        for line in self:
            line.dry_density = round((100 * line.bulk_density) / (100 + line.moisture),2)


 





class SandreplacementNotes(models.Model):
    _name = "sand.replacement.notes"

    parent_id = fields.Many2one('mechanical.sand.replacement',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")