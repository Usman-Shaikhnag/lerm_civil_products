from odoo import models, fields, api


class BentoniteDatasheet(models.AbstractModel):
    _name = 'report.bentonite.bentonite_datasheet'
    _description = 'Bentonite DataSheet'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}

        if data.get('fromsample'):
            if 'active_id' in data.get('context', {}):
                eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids)
        else:
            eln = self.env['lerm.eln'].sudo().browse(data.get('eln_id'))

        model_id = eln.model_id
        model_name = (
            eln.material.product_based_calculation[0].ir_model.name
            if eln.material.product_based_calculation else False
        )
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)

        return {
            'eln': eln,
            'data': general_data,
        }


class BentoniteReport(models.AbstractModel):
    _name = 'report.bentonite.bentonite_report'
    _description = 'Bentonite Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}

        if data.get('report_wizard'):
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data.get('sample'))])
        elif 'active_id' in data.get('context', {}):
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)

        model_id = eln.model_id
        model_name = (
            eln.material.product_based_calculation[0].ir_model.name
            if eln.material.product_based_calculation else False
        )
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)

        return {
            'eln': eln,
            'data': general_data,
        }
