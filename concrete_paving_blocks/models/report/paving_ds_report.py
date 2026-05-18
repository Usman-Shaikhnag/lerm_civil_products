from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree

class PavingBlockDatasheet1(models.AbstractModel):
        _name = 'report.concrete_paving_block.paving_block_datasheet'
        _description = 'Concrete Paving Block DataSheet'
    
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
        
# class PavingBlockReport1(models.AbstractModel):
#     _name = 'report.paver_block.paving_block_report'
#     _description = 'Concrete Paving Block Report'
    
#     @api.model
#     def _get_report_values(self, docids, data):
#         # eln = self.env['lerm.eln'].sudo().browse(docids)
#         inreport_value = data.get('inreport', None)
#         nabl = data.get('nabl')
#         if 'active_id' in data['context']:
#             eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
#         else:
#             eln = self.env['lerm.eln'].sudo().browse(docids) 

#         qr_static = qrcode.QRCode(box_size=6, border=2)
#         qr_static.add_data("https://www.lerm.in")
#         qr_static.make(fit=True)
#         buf_static = BytesIO()
#         qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
#         qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

#         qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
#         qr.add_data(eln.kes_no)
#         qr.make(fit=True)
#         qr_image = qr.make_image()

#         # Convert the QR code image to base64 string
#         buffered = BytesIO()
#         qr_image.save(buffered, format="PNG")
#         qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

#         # Assign the base64 string to a field in the 'srf' object
#         qr_code = qr_image_base64
#         model_id = eln.model_id
#         # differnt location for product based
#         model_name = eln.material.product_based_calculation[0].ir_model.name 
#         if model_name:
#             general_data = self.env[model_name].sudo().browse(model_id)
#         else:
#             general_data = self.env['lerm.eln'].sudo().browse(docids)
#         return {
#             'eln': eln,
#             'data' : general_data,
#             'qrcode': qr_code,
#             'qrcode_static': qr_static_b64,
#             'stamp' : inreport_value,
#             'nabl' : nabl
#         }


class PavingBlockReport1(models.AbstractModel):
    _name = 'report.concrete_paving_block.paving_block_report'
    _description = 'Paving Block'
    
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

        # Static QR
        qr_static = qrcode.QRCode(box_size=6, border=2)
        qr_static.add_data("https://nablwp.qci.org.in/CertificateScopenew?x=4Rf+3mOSznNeFNvAasH49g==&a=MTI0NDAx")
        qr_static.make(fit=True)
        buf_static = BytesIO()
        qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
        qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

        # 🧩 QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/paving/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

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
            'notes_list': general_data.notes_id if hasattr(general_data, 'notes_id') and general_data.notes_id else [],
            'qrcode': qr_code,
            'nabl' : nabl,
            'qrcode_static': qr_static_b64,
            # 'stamp' : inreport_value,
            'nabl' : nabl
        }
