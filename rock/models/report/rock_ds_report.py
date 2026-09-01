from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree
from odoo.modules.module import get_module_resource


class RockDatasheet(models.AbstractModel):
        _name = 'report.rock.rock_datasheet'
        _description = 'Rock DataSheet'
    
        @api.model
        def _get_report_values(self, docids, data):
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
            model_id = eln.model_id
            # differnt location for product based
            # model_name = eln.material.product_based_calculation[0].ir_model.name 
            model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
            if model_name:
                general_data = self.env[model_name].sudo().browse(model_id)
            else:
                general_data = self.env['lerm.eln'].sudo().browse(docids)
            return {
                'eln': eln,
                'data' : general_data
            }
        
class RockReport(models.AbstractModel):
    _name = 'report.rock.rock_report'
    _description = 'Rock Report'
    
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

        # Static QR
        qr_static = qrcode.QRCode(box_size=6, border=2)
        qr_static.add_data("https://nablwp.qci.org.in/CertificateScopenew?x=VnSUYFrXOFAdSMq5zAgzIw==&p=1&src=P&LS=balhcraes")
        qr_static.make(fit=True)
        buf_static = BytesIO()
        qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
        qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

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
        report_url = f"{base_url}/download_report/rock/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

        qr.add_data(report_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'qrcode_static': qr_static_b64,
            'nabl' : nabl
        }


class RockReportFirst(models.AbstractModel):
    _name = 'report.rock.rock_report_first'
    _description = 'Rock Report First Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.env['report.rock.rock_report']._get_report_values(docids, data)


class RockReportRest(models.AbstractModel):
    _name = 'report.rock.rock_report_rest'
    _description = 'Rock Report Rest Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        return self.env['report.rock.rock_report']._get_report_values(docids, data)


class SoilReportTriaxial(models.AbstractModel):
    _name = 'report.rock.report_triaxial_template'
    _description = 'CBR Report Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Mechanical Soil records fetch kara
        docs = self.env['mechanical.rock'].browse(docids)
        
        # ELN records shodha
        eln_records = self.env['lerm.eln'].search([
            ('sample_id', 'in', docs.ids)
        ])

        logo_path = get_module_resource(
       'lerm_civil',
       'static',
       'src',
       'img',
       'genstru_logo.png')   

        logo_base64 = False
        if logo_path:
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        print("LOGO PATH:", logo_path)
        print("LOGO BASE64 EXISTS:", bool(logo_base64))

        

        return {
            'doc_ids': docids,
            'doc_model': 'mechanical.rock',
            'data': docs,
            'eln': eln_records,
            'docs': docs,
            'logo_base64': logo_base64,
        }



class SoilReportTriaxial(models.AbstractModel):
    _name = 'report.rock.report_elasticity_template'
    _description = 'CBR Report Parser'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Mechanical Soil records fetch kara
        docs = self.env['mechanical.rock'].browse(docids)
        
        # ELN records shodha
        eln_records = self.env['lerm.eln'].search([
            ('sample_id', 'in', docs.ids)
        ])

        logo_path = get_module_resource(
            'lerm_civil', 'static/src/img', 'genstru_logo.png'
        )

        logo_base64 = False
        if logo_path:
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')

        

        return {
            'doc_ids': docids,
            'doc_model': 'mechanical.rock',
            'data': docs,
            'eln': eln_records,
            'docs': docs,
            'logo_base64': logo_base64,
        }
