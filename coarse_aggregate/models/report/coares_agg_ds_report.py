from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree




class CoarseAggregateReport(models.AbstractModel):
    _name = 'report.coarse_aggregate.lerm_coarse_aggregate_mech_report'
    _description = 'Coarse Aggregate Report'
    
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
        
        # Define All unique internal_ids At Once
        internal_ids = [
            'c2168fff-e47c-4155-99ff-9d7dc223e768',  # Sieve Analysis
            'ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71',  # Crushing Value
            '37f2161e-5cc0-413f-b76c-10478c65baf9',  # Abrasion Value 
            '3114db41-cfa7-49ad-9324-fcdbc9661038',     # Specific Gravity
            '22ee804f-41a3-4fd1-a301-a8d9180fba10',     # Water Absorption
            '2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2',  # Impact Value
            '5f506c08-4369-491d-93a6-030514c29661',  # Fine10 Load
            '8b80bc59-f49e-483e-8ccd-2fb4b076620e',  # Soundness Magnesium
            '9effe915-e5a3-45a7-aaeb-10caababd667',  # Elongation Table
            'be7a60bc-bb2c-410d-b91a-4f8730a4ac6f',  # Flakiness Table
            '65a41d1f-d557-438e-8fd1-2c619a334d02',  # Loose Density
            '357f579d-a310-4015-bc11-28a85c53ac83',  # Compacted Density
            '04a95dc1-4b45-4817-a9b2-dd722bbe6281',  # Void Compacted Density
            '919587f2-5b45-4da1-bb73-10164b861833',  # Void Loose Density
            '8e9d9c62-e634-47a2-a689-2c6c8538493c',  # Rate Of Evaporation
            'c8cd69bd-1f89-4f22-bae6-b81de73e6c2',  # Soundness Sodium



        ]

        # ✅ सर्व parameter.master records dictionary मध्ये साठवा
        ParamMaster = self.env['lerm.parameter.master'].sudo()
        parameters = {}
        for iid in internal_ids:
            record = ParamMaster.search([('internal_id', '=', iid)], limit=1)
            parameters[iid] = record

        # 🧩 QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/coarse/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

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
            'data': general_data,
            'qrcode': qr_code,
            'qrcode_static': qr_static_b64,
            'nabl':nabl,
            'parameters': parameters,  
        }


class CoarseAggregateDataSheet(models.AbstractModel):
    _name = 'report.coarse_aggregate.coarse_aggregate_datasheet'
    _description = 'Coarse Aggregate DataSheet'
    
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