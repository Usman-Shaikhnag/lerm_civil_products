from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging



# class ReallocationWizard(models.TransientModel):
#     _name = "sample.reallocation.wizard"


#     technicians = fields.Many2one('res.users')


#     def reallocate_current_sample(self):
#         for record in self:
#             # import wdb ; wdb.set_trace()
#             eln_id = record.env['lerm.eln'].search([('sample_id','=',record.env.context.get('active_id'))])
#             sample = record.env['lerm.srf.sample'].sudo().search([('id','=',record.env.context.get('active_id'))])
#             # import wdb ; wdb.set_trace()    
#             product_based= eln_id.material.is_product_based_calculation
#             grade = eln_id.grade_id
#             if product_based:
#                 product_grade_table = eln_id.material.product_based_calculation
#                 for rec in product_grade_table:
#                     if rec.grade == grade:
#                         model = rec.ir_model
#                         if model:
#                             product_record = record.env[model.name].sudo().search([('sample_id','=',record.env.context.get('active_id'))],limit=1)
#                             exclude_fields = {
#                                 'activity_ids',
#                                 'message_follower_ids',
#                                 'message_ids',
#                                 'website_message_ids',
#                                 'parameters',
#                                 'parameters_result',
#                                 'parameters_input',
#                             }

#                             one2many_fields = {
#                                 name: field.comodel_name
#                                 for name, field in product_record._fields.items()
#                                 if field.type == 'one2many' and name not in exclude_fields
#                             }
                           
#                             one2many_models = [
#                                 product_record._fields[field_name].comodel_name
#                                 for field_name in one2many_fields
#                             ]
#                             # import wdb ; wdb.set_trace()
#                             for mod in one2many_models:
#                                 try:
#                                     model_n = record.env[mod].sudo().search([('parent_id','=',product_record.id)])
#                                     model_n.sudo().unlink()
#                                 except:
#                                     pass

#                             product_record.sudo().unlink()
                        

#             parameters_result_ids = record.env['eln.parameters.result'].sudo().search([('eln_id','=',eln_id.id)])
#             parameters_inputs_ids = record.env['eln.parameters.inputs'].sudo().search([('eln_id','=',eln_id.id)])
#             parameters_result_ids.sudo().unlink()
#             parameters_inputs_ids.sudo().unlink()

           
#             # import wdb ; wdb.set_trace()
#             eln_id.sudo().unlink()
#             # sample = record.env['lerm.srf.sample'].sudo().search([('id','=',record.env.context.get('active_id'))])

#             parameters = []
#             parameters_result = []
#             # import wdb ; wdb.set_trace()
#             for parameter in sample.parameters:
#                 parameters_result.append((0,0,{'parameter':parameter.id,'unit': parameter.unit.id,'test_method':parameter.test_method.id}))
#             # import wdb ; wdb.set_trace()
#             record.env['lerm.eln'].sudo().create({
#                     'srf_id': sample.srf_id.id,
#                     'srf_date':sample.srf_id.srf_date,
#                     'kes_no':sample.kes_no,
#                     'discipline':sample.discipline_id.id,
#                     'group': sample.group_id.id,
#                     'material': sample.material_id.id,
#                     'witness_name': sample.witness,
#                     'sample_id':sample.id,
#                     'parameters':parameters,
#                     'technician': record.technicians.id,
#                     'parameters_result':parameters_result,
#                     'conformity':sample.conformity,
#                     'has_witness':sample.has_witness,
#                     'size_id':sample.size_id.id,
#                     'grade_id':sample.grade_id.id,
#                     'casting_date':sample.date_casting,

#                 })
#             sample.write({'state':'2-alloted' ,
#                            'technicians':record.technicians.id,
#                            'filled_by':record.technicians.id,
#                            })

#             return {'type': 'ir.actions.act_window_close'}

#     def discard_reallocation(self):
#         return {'type': 'ir.actions.act_window_close'}

class ReallocationWizard(models.TransientModel):
    _name = "sample.reallocation.wizard"

    allocation_type = fields.Selection(
        [('sample','Sample'), ('parameter','Parameter')],
        default='sample',
        required=True,
    )

    reallocation_mode = fields.Selection(
        [('partial','Partial'), ('full','Full')],
        default='full',
        required=True,
    )

    technicians = fields.Many2one("res.users", string="Technician")
    technician_ids = fields.Many2many('res.users', string='Technicians')
    line_ids = fields.One2many(
        'sample.reallocation.line',
        'wizard_id',
        string='Parameters'
        )
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_ids = self.env.context.get('active_ids') or []
        if not active_ids:
            return res

        sample = self.env['lerm.srf.sample'].browse(active_ids[0])
        eln = sample.eln_id.sudo()

        # Default to parameter mode if ELN exists
        if eln:
            res['allocation_type'] = 'parameter'

        lines = []
        technician_set = set()

        for param in sample.parameters:
            assigned_tech = False

            if eln:
                pr = eln.parameters_result.filtered(
                    lambda r: r.parameter.id == param.id
                )
                if pr:
                    assigned_tech = pr[0].technician.id if pr[0].technician else False
                    technician_set |= set(pr.mapped('technician').ids)

            lines.append((0, 0, {
                'sample_id': sample.id,
                'parameter_id': param.id,
                'technician': assigned_tech,
                'is_locked': False,
            }))

        res['line_ids'] = lines

        # Prefill technician_ids (union of all assigned techs)
        if technician_set:
            res['technician_ids'] = [(6, 0, list(technician_set))]

        return res

    def reallocate_current_sample(self):
        active_ids = self.env.context.get('active_ids') or []
        if not active_ids:
            raise UserError(_("No sample selected."))

        #full reallocation    
        sample = self.env['lerm.srf.sample'].browse(active_ids[0])
        if self.reallocation_mode == 'full':
            eln = sample.eln_id
            if eln:
                # 1. Fetch calculation form model
                model_record = eln.material.product_based_calculation.filtered(lambda r: r.grade.id == eln.grade_id.id)
                model_name = model_record.ir_model.model if model_record and model_record.ir_model else False
                
                # 2. Delete calculation form if it exists
                if model_name and eln.model_id:
                    calc_record = self.env[model_name].sudo().browse(eln.model_id)
                    if calc_record.exists():
                        calc_record.unlink()
                
                # 3. Disconnect and delete ELN
                sample.write({'eln_id': False})
                eln.unlink()
        
        # 🔑 Pass context flag to indicate this is a reallocation
        allot_wizard = self.env['sample.allotment.wizard'].sudo().with_context(
            is_reallocation=True  # 🔑 ADD THIS CONTEXT FLAG
        ).create({
            'allocation_type': self.allocation_type,
            'technicians': self.technicians.id,
            'technician_ids': [(6, 0, self.technician_ids.ids)],
            'line_ids': [
                (0, 0, {
                    'sample_id': l.sample_id.id,
                    'parameter_id': l.parameter_id.id,
                    'technician': l.technician.id,
                    'is_locked': False,  # 🔑 FORCE UNLOCK
                }) for l in self.line_ids
            ],
        })

        allot_wizard.with_context(active_ids=active_ids, is_reallocation=True).allot_sample()

        return {'type': 'ir.actions.act_window_close'}

class SampleReallocationLine(models.TransientModel):
    _name = 'sample.reallocation.line'

    wizard_id = fields.Many2one(
        'sample.reallocation.wizard',
        ondelete='cascade'
    )

    sample_id = fields.Many2one('lerm.srf.sample')
    parameter_id = fields.Many2one(
        'lerm.parameter.master',
        required=True
    )
    technician = fields.Many2one('res.users')
    is_locked = fields.Boolean(string="Locked", default=False)  # 🔑 ADD THIS FIELD

    allowed_technician_ids = fields.Many2many(
        'res.users',
        compute='_compute_allowed_technicians',
        store=False
    )

    @api.depends('parameter_id')
    def _compute_allowed_technicians(self):
        for line in self:
            line.allowed_technician_ids = (
                line.parameter_id.allowed_technicians
                if line.parameter_id
                else self.env['res.users']
            )
