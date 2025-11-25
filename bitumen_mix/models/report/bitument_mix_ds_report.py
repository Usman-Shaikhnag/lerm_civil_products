from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree

class BitumenConcreteDatasheet(models.AbstractModel):
        _name = 'report.bitumen_mix.bitumen_mix_datasheet_sm'
        _description = 'Bitumen Concrete Datasheet'
    
        @api.model
        def _get_report_values(self, docids, data):
            # if 'active_id' in data['context']:
            #     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            # else:
            #     eln = self.env['lerm.eln'].sudo().browse(docids) 
            if data['fromsample'] == True:
                if 'active_id' in data['context']:
                    eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
                else:
                    eln = self.env['lerm.eln'].sudo().browse(docids) 
            else:
                if data['report_wizard'] == True:
                    eln = self.env['lerm.eln'].sudo().search([('id','=',data['eln'])])
                else:
                    eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
            # differnt location for product based
            print(eln.material.parameter_table1[0].parameter_name , 'parameter')
            parameter_data = self.env['lerm.parameter.master'].sudo().search([('internal_id','=',eln.material.parameter_table1[0].internal_id)])
            model_id = eln.model_id
            model_name = eln.material.product_based_calculation[0].ir_model.name 
            if model_name:
                general_data = self.env[model_name].sudo().browse(model_id)
            else:
                general_data = self.env['lerm.eln'].sudo().browse(docids)
            return {
                'eln': eln,
                'data' : general_data,
                'parameter' : parameter_data
            }
        
class BitumenConcreteReport(models.AbstractModel):
    _name = 'report.bitumen_mix.bitumen_mix_report_sm'
    _description = 'Bitumen Concrete Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        nabl = data.get('nabl', False)

        # 🧩 ELN Record मिळवा
        if data.get('report_wizard'):
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data.get('sample'))])
        elif 'active_id' in data.get('context', {}):
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)

        if not eln:
            raise ValueError("ELN record not found")

        # 🧩 QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/bitumenm/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

        qr.add_data(report_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()
            
          # ✅ General Data मिळवा
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
            'data' : general_data,
            'qrcode': qr_code,
            # 'stamp' : inreport_value,
            'nabl' : nabl
        }
