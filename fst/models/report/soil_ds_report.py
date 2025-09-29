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
from matplotlib.ticker import MultipleLocator, StrMethodFormatter
import io
from matplotlib.ticker import LogLocator, MultipleLocator
from py3o.template import Template


class SoilDatasheet(models.AbstractModel):
    _name = 'report.soil_resistivity.soil_resistivity_datasheet'
    _description = 'Soil Resistivity DataSheet'
    
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


class SoilResistivityReport(models.AbstractModel):
    _name = "report.fst.soil_resistivity"
    _description = "Soil Resistivity Report (Py3o)"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env["ert.soil.resistivity"].browse(docids)
        return {
            "objects": records,       # py3o expects this
        }