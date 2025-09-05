from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging



class ReallocationWizard(models.TransientModel):
    _name = "sample.reallocation.wizard"


    technicians = fields.Many2one('res.users')


    def reallocate_current_sample(self):
        for record in self:
            # import wdb ; wdb.set_trace()
            eln_id = record.env['lerm.eln'].search([('sample_id','=',record.env.context.get('active_id'))])
            sample = record.env['lerm.srf.sample'].sudo().search([('id','=',record.env.context.get('active_id'))])
            # import wdb ; wdb.set_trace()    
            product_based= eln_id.material.is_product_based_calculation
            grade = eln_id.grade_id
            if product_based:
                product_grade_table = eln_id.material.product_based_calculation
                for rec in product_grade_table:
                    if rec.grade == grade:
                        model = rec.ir_model
                        if model:
                            product_record = record.env[model.name].sudo().search([('sample_id','=',record.env.context.get('active_id'))],limit=1)
                            exclude_fields = {
                                'activity_ids',
                                'message_follower_ids',
                                'message_ids',
                                'website_message_ids',
                                'parameters',
                                'parameters_result',
                                'parameters_input',
                            }

                            one2many_fields = {
                                name: field.comodel_name
                                for name, field in product_record._fields.items()
                                if field.type == 'one2many' and name not in exclude_fields
                            }
                           
                            one2many_models = [
                                product_record._fields[field_name].comodel_name
                                for field_name in one2many_fields
                            ]
                            # import wdb ; wdb.set_trace()
                            for mod in one2many_models:
                                try:
                                    model_n = record.env[mod].sudo().search([('parent_id','=',product_record.id)])
                                    model_n.sudo().unlink()
                                except:
                                    pass

                            product_record.sudo().unlink()
                        

            parameters_result_ids = record.env['eln.parameters.result'].sudo().search([('eln_id','=',eln_id.id)])
            parameters_inputs_ids = record.env['eln.parameters.inputs'].sudo().search([('eln_id','=',eln_id.id)])
            parameters_result_ids.sudo().unlink()
            parameters_inputs_ids.sudo().unlink()

           
            # import wdb ; wdb.set_trace()
            eln_id.sudo().unlink()
            # sample = record.env['lerm.srf.sample'].sudo().search([('id','=',record.env.context.get('active_id'))])

            parameters = []
            parameters_result = []
            # import wdb ; wdb.set_trace()
            for parameter in sample.parameters:
                parameters_result.append((0,0,{'parameter':parameter.id,'unit': parameter.unit.id,'test_method':parameter.test_method.id}))
            # import wdb ; wdb.set_trace()
            record.env['lerm.eln'].sudo().create({
                    'srf_id': sample.srf_id.id,
                    'srf_date':sample.srf_id.srf_date,
                    'kes_no':sample.kes_no,
                    'discipline':sample.discipline_id.id,
                    'group': sample.group_id.id,
                    'material': sample.material_id.id,
                    'witness_name': sample.witness,
                    'sample_id':sample.id,
                    'parameters':parameters,
                    'technician': record.technicians.id,
                    'parameters_result':parameters_result,
                    'conformity':sample.conformity,
                    'has_witness':sample.has_witness,
                    'size_id':sample.size_id.id,
                    'grade_id':sample.grade_id.id,
                    'casting_date':sample.date_casting,

                })
            sample.write({'state':'2-alloted' ,
                           'technicians':record.technicians.id,
                           'filled_by':record.technicians.id,
                           })

            return {'type': 'ir.actions.act_window_close'}

    def discard_reallocation(self):
        return {'type': 'ir.actions.act_window_close'}