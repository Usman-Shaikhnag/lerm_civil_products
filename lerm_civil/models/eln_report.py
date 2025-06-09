from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO



class ElnReport(models.AbstractModel):
    _name = 'report.lerm_civil.eln_report_template'
    _description = 'ELN Report'

    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        print(data , 'dataaaaaaaaaaaaaa')
        # stamp = data['inreport']
        # import wdb;wdb.set_trace();
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        elif 'active_id' in data.get('context', {}):
            # stamp = data['inreport']
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)
        print()
        # qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        # qr.add_data(eln.kes_no)
        # qr.make(fit=True)
        # qr_image = qr.make_image()

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        # qr.add_data(eln.kes_no)
        url = self.env['ir.config_parameter'].sudo().search([('key','=','web.base.url')]).value

        if nabl:
            url = url +'/download_report/nabl/'+ str(eln.id)
        else:
            url = url +'/download_report/nonnabl/'+ str(eln.id)
        qr.add_data(url)
        qr.make(fit=True)
        qr_image = qr.make_image()

        # Convert the QR code image to base64 string
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Assign the base64 string to a field in the 'srf' object
        qr_code = qr_image_base64
        return {
            'eln': eln,
            'qrcode': qr_code,
            'stamp' : inreport_value,
            'nabl' : nabl,
            'srf_id': eln.srf_id,
        }
 


class DataSheetReport(models.AbstractModel):
    _name = 'report.lerm_civil.datasheet_report_template'
    _description = 'DataSheet Report'

    @api.model
    def _get_report_values(self, docids, data):
        # import wdb ; wdb.set_trace()
        if data['fromsample'] == True:
            if 'active_id' in data['context']:
                # import wdb ; wdb.set_trace()
                eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            else:
                # import wdb ; wdb.set_trace()
                eln = self.env['lerm.eln'].sudo().browse(docids)
        else:
            if data['report_wizard'] == True:
                eln = self.env['lerm.eln'].sudo().search([('id','=',data['eln'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
        model_id = eln.model_id
        
        datasheet_data = []
        prev_data = None
        for i, input_data in enumerate(eln.parameters_input):
            datasheet_data.append({'parameter_name': input_data.parameter_result.parameter.parameter_name, 'identifier': input_data.identifier, 'inputs' : input_data.inputs.label ,'value': input_data.value , 'decimal': input_data.parameter_result.parameter.parameter_name})
            if i > 0 and input_data.parameter_result.parameter.parameter_name != prev_data:
                index = datasheet_data.index({'parameter_name': input_data.parameter_result.parameter.parameter_name, 'identifier': input_data.identifier,'inputs' : input_data.inputs.label ,'value': input_data.value , 'decimal': input_data.parameter_result.parameter.parameter_name})
                datasheet_data.insert(index,{'parameter_name': prev_data, 'identifier': 'Formula', 'inputs': prev_formula , 'value' : prev_result , 'decimal': input_data.parameter_result.parameter.parameter_name})
            if i == (len(eln.parameters_input) - 1):
                datasheet_data.append({'parameter_name': input_data.parameter_result.parameter.parameter_name, 'identifier': 'Formula', 'inputs': input_data.parameter_result.parameter.formula , 'value' : input_data.parameter_result.result , 'decimal': input_data.parameter_result.parameter.parameter_name})
            prev_data = input_data.parameter_result.parameter.parameter_name
            prev_formula = input_data.parameter_result.parameter.formula
            prev_result = input_data.parameter_result.result
        return {
            'eln': eln,
            'datasheet' : datasheet_data,
            'datasheet_name' : 'Afzal'
        }
        