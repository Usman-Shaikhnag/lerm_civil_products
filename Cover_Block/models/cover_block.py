from odoo import api, fields, models

class CoverblockMechanical(models.Model):
    _name = "mechanical.cover.block"
    _inherit = "lerm.eln"
    _description = "mechanical.cover.block"
    _rec_name = "name"

    name = fields.Char(default="Cover Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)




    eln_ref = fields.Many2one('lerm.eln', string="ELN")
    sample_parameters = fields.Many2many(
        'lerm.parameter.master', compute="_compute_sample_parameters",string="Parameters",store=True  )
    size_id = fields.Many2one( 'lerm.size.line', compute="_compute_size_id" )
    grade = fields.Many2one('lerm.grade.line', compute="_compute_grade_id", store=True )
    avg_compacted_unit = fields.Char( "Compacted Density", compute="_compute_units" )


   
    def _get_unit(self, internal_id):
        param = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', internal_id)
        ], limit=1)

        return param.unit.name if param.unit else ""


       

# remark
#remarkkk
    notes_id = fields.One2many('cover.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(CoverblockMechanical, self).default_get(fields)

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
    





       # Water Absorption


    water_absorption_name = fields.Char("Name",default="Water Absorption ")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

    water_absorption_child_lines = fields.One2many('water.absorption.line','parent_id',string="Water Line")

    avg_water_absorption = fields.Float(
        string="Avg. Water Absorption (%)",
        compute="_compute_avg_water_absorption", store=True
    )

    @api.depends('water_absorption_child_lines.water_absorption')
    def _compute_avg_water_absorption(self):
        for rec in self:
            lines = rec.water_absorption_child_lines
            if lines:
                total = sum(line.water_absorption for line in lines)
                rec.avg_water_absorption = round(total / len(lines), 2)
            else:
                rec.avg_water_absorption = 0.0

    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a43a33a4-834e-40d4-afb3-80a4e61ece05')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a43a33a4-834e-40d4-afb3-80a4e61ece05')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a43a33a4-834e-40d4-afb3-80a4e61ece05')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a43a33a4-834e-40d4-afb3-80a4e61ece05')]).parameter_table
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




     # Crushing Value

    crushing_name = fields.Char("Name",default="Crushing Value")
    crushing_visible = fields.Boolean("Crushing Visible",compute="_compute_visible")
    crushing_child_lines = fields.One2many('mechanical.crushing.value.line','parent_id',string="Parameter")
    average_crushing = fields.Float(string="Average Aggregate Crushing Value", compute="_compute_average_crushing")
    average_crushing_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_crushing_conformity", store=True)

    @api.depends('average_crushing','eln_ref','grade')
    def _compute_average_crushing_conformity(self):
        
        for record in self:
            record.average_crushing_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_crushing - record.average_crushing*mu_value
                    upper = record.average_crushing + record.average_crushing*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_crushing_conformity = 'pass'
                        break
                    else:
                        record.average_crushing_conformity = 'fail'

    average_crushing_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_crushing_nabl", store=True)

    @api.depends('average_crushing','eln_ref','grade')
    def _compute_average_crushing_nabl(self):
        
        for record in self:
            record.average_crushing_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_crushing - record.average_crushing*mu_value
                    upper = record.average_crushing + record.average_crushing*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_crushing_nabl = 'pass'
                        break
                    else:
                        record.average_crushing_nabl = 'fail'




    @api.depends('crushing_child_lines.crushing_value')
    def _compute_average_crushing(self):
        for record in self:
            if record.crushing_child_lines:
                sum_crushing_values = sum(record.crushing_child_lines.mapped('crushing_value'))
                record.average_crushing = sum_crushing_values / len(record.crushing_child_lines)
            else:
                record.average_crushing = 0.0
   

    


 
    # COMPUTE METHODS
   
    def _compute_units(self):
        for rec in self:
            rec.avg_compacted_unit = rec._get_unit(
                "357f579d-a310-4015-bc11-28a85c53ac83"
            )


    

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for rec in self:
            rec.size_id = rec.eln_ref.size_id.id if rec.eln_ref else False

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        for rec in self:
            rec.grade = rec.eln_ref.grade_id.id if rec.eln_ref else False

    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):

        current_user = self.env.user

        for rec in self:

            if not rec.eln_ref:
                rec.sample_parameters = [(6, 0, [])]
                continue

            results = rec.eln_ref.parameters_result.filtered(
                lambda r: r.technician and r.technician.id == current_user.id
            )
            parameter_ids = results.mapped('parameter').ids
            rec.sample_parameters = [(6, 0, parameter_ids)]

   
    # VISIBILITY 
   
    crushing_visible = fields.Boolean(compute="_compute_visible")
    water_absorption_visible = fields.Boolean(compute="_compute_visible")

    @api.depends("sample_parameters")
    def _compute_visible(self):

        for rec in self:

            rec.crushing_visible = False
            rec.water_absorption_visible = False

            for param in rec.sample_parameters:

                if param.internal_id == "3dea9034-e36c-4bfb-9e1a-f9ed5101d49b":
                    rec.crushing_visible = True

                if param.internal_id == "a43a33a4-834e-40d4-afb3-80a4e61ece05":
                    rec.water_absorption_visible = True



                
                

    def open_eln_page(self):
       
        current_user = self.env.user
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )



        for result in technician_results:
            
            if result.parameter.internal_id == '3dea9034-e36c-4bfb-9e1a-f9ed5101d49b':
                result.result_char = round(self.average_crushing,2)
                result.calculated = True
                if self.average_crushing_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


          
# water absorption

            if result.parameter.internal_id == 'a43a33a4-834e-40d4-afb3-80a4e61ece05':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
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
        record = super(CoverblockMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(CoverblockMechanical, self).read(fields=fields, load=load)




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
        record = self.env['mechanical.cover.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



           


   
    # CRUSHING VALUE



class CrushingValueLine(models.Model):
    _name = "mechanical.crushing.value.line"
    parent_id = fields.Many2one('mechanical.cover.block',string="Parent Id")

    

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)
    # wt_of_cylinder = fields.Integer(string="Weight of the empty cylinder in gms")
    # total_wt_of_dried = fields.Integer(string="Total weight of oven dried ( 4.0 hrs ) aggregate sample filling the cylindrical measure in gms")
    total_wt_aggregate = fields.Float(string="Wt of Aggregate Passing I.S Sieve 12.5 mm but retained in I.S. Sieve 10 mm Gms (W1)")
    wt_of_aggregate_retained = fields.Float(string="Wt of Aggregate Retained on  I.S Sieve 2.36  mm after the test Gms (W2)")
    wt_of_aggregate_passing = fields.Float(string="Wt of Stone Pieces Passing I.S Sieve 2.36 mm after the test ( W3)", compute="_compute_wt_of_aggregate_retained")
    crushing_value = fields.Float(string="Aggregate Crushing value", compute="_compute_crushing_value")


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







class WaterLine(models.Model):
    _name = "water.absorption.line"
    parent_id = fields.Many2one('mechanical.cover.block',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identification = fields.Float(string="Sample Identification")
    dry_wt_w1 = fields.Float(string="Dry wt (W1)")
    wet_w2 = fields.Float(string="Wet wt (W2)")
    water_absorption = fields.Float(string="  Water Absorption %",compute="_compute_water_absorption")

    @api.depends('dry_wt_w1', 'wet_w2')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.dry_wt_w1:  # avoid division by zero
                rec.water_absorption = round(((rec.wet_w2 - rec.dry_wt_w1) / rec.dry_wt_w1) * 100, 2)
            else:
                rec.water_absorption = 0.0

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WaterLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





class coverblockNotes(models.Model):
    _name = "cover.notes"

    parent_id = fields.Many2one('mechanical.cover.block',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



   
    
   
   