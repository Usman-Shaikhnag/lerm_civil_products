from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging



class ReallocationWizard(models.TransientModel):
    _name = "sample.reallocation.wizard"


    technicians = fields.Many2one('res.users')


    def reallocate_current_sample(self):
        for record in self:
            
            eln_id = record.env['lerm.eln'].search([('sample_id','=',record.env.context.get('active_id'))])
            compressive_strength_id = record.env['mechanical.concrete.cube'].search([('sample_id','=',record.env.context.get('active_id'))])
            # compressive_strength_lines = record.env['mechanical.concrete.cube.line'].search([('parent_id','=',compressive_strength_id.id)])

            parameters_result_ids = record.env['eln.parameters.result'].search([('eln_id','=',eln_id.id)])
            parameters_inputs_ids = record.env['eln.parameters.inputs'].search([('eln_id','=',eln_id.id)])

            for comp_records in compressive_strength_id:
                compressive_strength_lines = record.env['mechanical.concrete.cube.line'].search([('parent_id','=',comp_records.id)])
                compressive_strength_lines.unlink()
            compressive_strength_id.unlink()
            # import wdb ; wdb.set_trace()

            parameters_result_ids.unlink()
            parameters_inputs_ids.unlink()
            eln_id.unlink()
            sample = record.env['lerm.srf.sample'].sudo().search([('id','=',record.env.context.get('active_id'))])


            parameters = []
            parameters_result = []
            
            for parameter in sample.parameters:
                parameters.append((0,0,{'parameter':parameter.id ,'spreadsheet_template':parameter.spreadsheet_template.id}))
                parameters_result.append((0,0,{'parameter':parameter.id,'unit': parameter.unit.id,'test_method':parameter.test_method.id}))
            
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
                           'file_upload':False,
                           'report_upload':False
                           })

            return {'type': 'ir.actions.act_window_close'}

    def discard_reallocation(self):
        return {'type': 'ir.actions.act_window_close'}