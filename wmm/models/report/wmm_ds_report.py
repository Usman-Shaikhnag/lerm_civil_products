from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar



class WMMReport(models.AbstractModel):
    _name = 'report.wmm.wmm_mec_report'
    _description = 'WMM Report '
    
    @api.model
    def _get_report_values(self, docids, data):
       
        nabl = data.get('nabl')
        fromEln = data.get('fromEln')
        inreport_value = data.get('inreport', None)
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        elif fromEln == False:
            if 'active_id' in data['context']:
                eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids)
        else:
            if 'active_id' in data['context']:
                eln = self.env['lerm.eln'].sudo().search([('id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids)
        
        qr_static = qrcode.QRCode(box_size=6, border=2)
        qr_static.add_data("https://www.lerm.in")
        qr_static.make(fit=True)
        buf_static = BytesIO()
        qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
        qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/wmm/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

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
            
        
        # import wdb; wdb.set_trace();
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'qrcode_static': qr_static_b64,
            'stamp' : inreport_value,
            'nabl' : nabl,
            'fromEln':fromEln,
            
        }

class WmmDatasheet1(models.AbstractModel):
    _name = 'report.wmm.wmm_mech_datasheet'
    _description = 'WMM DataSheet'
    
    @api.model
    def _get_report_values(self, docids, data):
        # if data['fromsample'] == True:
        #     if 'active_id' in data['context']:
        #         eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        #     else:
        #         eln = self.env['lerm.eln'].sudo().browse(docids) 
        #     model_id = eln.model_id
        # else:
        #     eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
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