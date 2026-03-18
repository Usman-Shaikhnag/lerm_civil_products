from odoo import api, fields, models

class CoverblockMechanical(models.Model):
    _name = "mechanical.cover.block"
    _inherit = "lerm.eln"
    _description = "Mechanical Cover Block"
    _rec_name = "name"

    name = fields.Char(default="Cover Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")



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
    abrasion_visible = fields.Boolean(compute="_compute_visible")

    @api.depends("sample_parameters")
    def _compute_visible(self):

        for rec in self:

            rec.crushing_visible = False
            rec.abrasion_visible = False

            for param in rec.sample_parameters:

                if param.internal_id == "3dea9034-e36c-4bfb-9e1a-f9ed5101d49b":
                    rec.crushing_visible = True

                if param.internal_id == "37f2161e-5cc0-413f-b76c-10478c65baf9":
                    rec.abrasion_visible = True



    def open_eln_page(self):


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



   
    # ABRASION VALUE
   
    total_weight_sample_abrasion = fields.Float( "Total weight of Sample" )
    weight_passing_sample_abrasion = fields.Float( "Weight Passing Sample")
    weight_retain_sample_abrasion = fields.Float(  compute="_compute_weight_retain_sample_abrasion")
    abrasion_value_percentage = fields.Float( compute="_compute_abrasion" )

    @api.depends(
        "total_weight_sample_abrasion",
        "weight_passing_sample_abrasion"
    )
    def _compute_weight_retain_sample_abrasion(self):

        for rec in self:

            rec.weight_retain_sample_abrasion = (
                rec.total_weight_sample_abrasion
                - rec.weight_passing_sample_abrasion
            )

    @api.depends(
        "total_weight_sample_abrasion",
        "weight_passing_sample_abrasion"
    )
    def _compute_abrasion(self):

        for rec in self:

            if rec.total_weight_sample_abrasion:

                rec.abrasion_value_percentage = (
                    rec.weight_passing_sample_abrasion
                    / rec.total_weight_sample_abrasion
                ) * 100

            else:
                rec.abrasion_value_percentage = 0

    # -------------------------------------------------------
    # CREATE FIX
    # -------------------------------------------------------

    @api.model
    def create(self, vals):

        record = super().create(vals)

        if record.eln_ref:
            record.eln_ref.write({
                "model_id": record.id
            })

        return record



# CHILD MODEL



# class CrushingValueLine(models.Model):

#     _name = "mechanical.crushing.value.line"

#     parent_id = fields.Many2one(
#         "mechanical.cover.block",
#         string="Parent"
#     )

#     sample_no = fields.Integer(default=1)
#     total_wt_aggregate = fields.Float("Wt Aggregate (W1)")
#     wt_of_aggregate_retained = fields.Float( "Wt Retained (W2)" )
#     wt_of_aggregate_passing = fields.Float( compute="_compute_passing"  )
#     crushing_value = fields.Float( compute="_compute_crushing" )

#     @api.depends(
#         "total_wt_aggregate",
#         "wt_of_aggregate_retained"
#     )
#     def _compute_passing(self):

#         for rec in self:

#             rec.wt_of_aggregate_passing = (
#                 rec.total_wt_aggregate
#                 - rec.wt_of_aggregate_retained
#             )

#     @api.depends(
#         "wt_of_aggregate_passing",
#         "total_wt_aggregate"
#     )
#     def _compute_crushing(self):

#         for rec in self:

#             if rec.total_wt_aggregate:

#                 rec.crushing_value = (
#                     rec.wt_of_aggregate_passing
#                     / rec.total_wt_aggregate
#                 ) * 100

#             else:
#                 rec.crushing_value = 0

#     @api.model
#     def create(self, vals):

#         if vals.get("parent_id"):

#             records = self.search([
#                 ("parent_id", "=", vals["parent_id"])
#             ])

#             vals["sample_no"] = len(records) + 1

#         return super().create(vals)