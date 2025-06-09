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

class DataSheetReport(models.AbstractModel):
    _name = 'report.lerm_civil.datasheet_generaltemplate_report'
    _description = 'DataSheet Report'
    
    
    def get_visible_table_fields(self, model_name):
        form_view = self.env['ir.ui.view'].sudo().search([
            ('model', '=', model_name),
            ('type', '=', 'form')
        ], limit=1)
        visible_fields = []
        if form_view and form_view.arch:
            form_view_dom = etree.fromstring(form_view.arch.encode('utf-8'))
            tree_element = form_view_dom.find(".//field[@name='child_lines']//tree")
            if tree_element is not None:
                for field_node in tree_element.findall(".//field"):
                    modifiers = field_node.get('modifiers')
                    if not modifiers or 'invisible' not in modifiers or 'invisible' in modifiers and eval(modifiers)['invisible']:
                        field_name = field_node.get('name')
                        field_label = field_node.get('string')
                        to_show = field_node.get('invisible')
                        if to_show is None:
                            to_show = False
                        else:
                            to_show = True
                        visible_fields.append((field_name,field_label,to_show))
        return visible_fields
    
    def get_visible_result_fields(self, model_name):
        form_view = self.env['ir.ui.view'].sudo().search([
            ('model', '=', model_name),
            ('type', '=', 'form')
        ], limit=1)
        visible_fields = []
        if form_view and form_view.arch:
            form_view_dom = etree.fromstring(form_view.arch.encode('utf-8'))
            result_elemnt = form_view_dom.findall(".//field[@identity='result']")
            for field in result_elemnt:
                field_name = field.get('name')
                field_label = field.get('string')
                to_show = field.get('invisible')
                if to_show is None:
                    to_show = False
                else:
                    to_show = True
                visible_fields.append((field_name,field_label,to_show))
                print(visible_fields , 'visv')
        return visible_fields

    

    
    def get_visible_additonal_fields(self, model_name):
        form_view = self.env['ir.ui.view'].sudo().search([
            ('model', '=', model_name),
            ('type', '=', 'form')
        ], limit=1)
        visible_fields = []
        if form_view and form_view.arch:
            form_view_dom = etree.fromstring(form_view.arch.encode('utf-8'))
            extra_elemnt = form_view_dom.findall(".//field[@identity='extra']")
            for field in extra_elemnt:
                field_name = field.get('name')
                field_label = field.get('string')
                to_show = field.get('invisible')
                if to_show is None:
                    to_show = False
                else:
                    to_show = True
                visible_fields.append((field_name,field_label,to_show))
        return visible_fields
    
    @api.model
    def _get_report_values(self, docids, data):
        # if 'active_id' in data['context']:
        #     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        # else:
        #     eln = self.env['lerm.eln'].sudo().browse(docids) 
        # model_id = eln.parameters_result.model_id
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
        model_name = eln.parameters_result.parameter[0].ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
            columns = self.get_visible_table_fields(model_name)
            resultfields = self.get_visible_result_fields(model_name)
            extrafields = self.get_visible_additonal_fields(model_name)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        print(columns , 'columns data')
        print(extrafields , 'extrafields')
        print(resultfields , 'result fie;ds')
        return {
            'eln': eln,
            'data' : general_data,
            'tabledata' : columns,
            'resultdata' : resultfields,
            'extradata' : extrafields
        }
    
class GeneralReport(models.AbstractModel):
    _name = 'report.lerm_civil.general_report_template'
    _description = 'General Report'
    
    
    def get_visible_result_fields(self, model_name):
        form_view = self.env['ir.ui.view'].sudo().search([
            ('model', '=', model_name),
            ('type', '=', 'form')
        ], limit=1)
        visible_fields = []
        if form_view and form_view.arch:
            form_view_dom = etree.fromstring(form_view.arch.encode('utf-8'))
            result_elemnt = form_view_dom.findall(".//field[@identity='result']")
            

            for field in result_elemnt:
                field_name = field.get('name')
                field_label = field.get('string')
                to_show = field.get('invisible')
                if to_show is None:
                    to_show = False
                else:
                    to_show = True
                # if 'selection' in field.get('widget', ''):
                #     field_value = self.env[model_name]._fields[field_name].selection_label(field_value)
                #     import wdb;wdb.set_trace()


                visible_fields.append((field_name,field_label,to_show))
                print(visible_fields , 'visv')
        # import wdb;wdb.set_trace()
        return visible_fields
   
    

    def get_visible_table_fields(self, model_name):
        form_view = self.env['ir.ui.view'].sudo().search([
            ('model', '=', model_name),
            ('type', '=', 'form')
        ], limit=1)
        visible_fields = []
        if form_view and form_view.arch:
            form_view_dom = etree.fromstring(form_view.arch.encode('utf-8'))
            tree_element = form_view_dom.find(".//field[@name='child_lines']//tree")
            if tree_element is not None:
                for field_node in tree_element.findall(".//field"):
                    
                    modifiers = field_node.get('modifiers')
                    if not modifiers or 'invisible' not in modifiers or 'invisible' in modifiers and eval(modifiers)['invisible']:
                        field_name = field_node.get('name')
                        field_label = field_node.get('string')
                        to_show = field_node.get('invisible')
                        if to_show is None:
                            to_show = False
                        else:
                            to_show = True
                        # if 'selection' in field_node.get('widget', ''):
                        #     field_value = self.env[model_name]._fields[field_name].selection_label(field_value)
                        #     import wdb;wdb.set_trace()

                        
                        visible_fields.append((field_name,field_label,to_show))
  
        
        return visible_fields
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        inreport_value = data.get('inreport', None)
        print(data['context'])
        nabl = data.get('nabl')
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        elif 'active_id' in data.get('context', {}):
            # stamp = data['context']['inreport']
            # print(stamp , 'stamp value')
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids) 
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
        
        model_id = eln.parameters_result.model_id
        model_name = eln.parameters_result.parameter[0].ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
            columns = self.get_visible_table_fields(model_name)
            resultfields = self.get_visible_result_fields(model_name)
            # import wdb;wdb.set_trace()
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
            # import wdb;wdb.set_trace()
        print('columns dataa',resultfields)

        return {
            'eln': eln,
            'data' : general_data,
            'tabledata' : columns,
            'resultdata' : resultfields,
            'qrcode': qr_code,
            'nabl':nabl,
            'stamp' : inreport_value,
        }

class SteelTmtBar(models.AbstractModel):
    _name = 'report.lerm_civil.steel_tmt_bar_report'
    _description = 'Steel TMT Bar'
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        elif 'active_id' in data.get('context', {}):
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids) 
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
            'stamp' : inreport_value,
            'nabl' : nabl

        }

    

class SteelTmtBarDataSheet(models.AbstractModel):
    _name = 'report.lerm_civil.steel_tmt_bar_datasheet'
    _description = 'Steel TMT Bar DataSheet'
    
    @api.model
    def _get_report_values(self, docids, data):
        # import wdb ; wdb.set_trace()

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
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }

class CementDataSheet(models.AbstractModel):
    _name = 'report.lerm_civil.cement_datasheet'
    _description = 'Cement DataSheet'
    
    @api.model
    def _get_report_values(self, docids, data):
        if data['fromsample'] == True:
            if 'active_id' in data['context']:
                eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids) 
        else:
            if data['report_wizard']:
                if data['report_wizard'] == True:
                    eln = self.env['lerm.eln'].sudo().search([('id','=',data['eln'])])
                else:
                    eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
            else:
                eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
        # differnt location for product based
        # model_name = eln.material.product_based_calculation[0].ir_model.name 
        model_id = eln.model_id
        model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }

class GypsumDataSheet(models.AbstractModel):
    _name = 'report.lerm_civil.gypsum_datasheet'
    _description = 'Gypsum DataSheet'
    
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
        # differnt location for product based
        # model_name = eln.material.product_based_calculation[0].ir_model.name 
        model_id = eln.model_id
        model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }

class FlyashDatasheet(models.AbstractModel):
    _name = 'report.lerm_civil.flyash_datasheet'
    _description = 'Fly Ash DataSheet'
    
    @api.model
    def _get_report_values(self, docids, data):
        # if 'active_id' in data['context']:
        #     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        # else:
        #     eln = self.env['lerm.eln'].sudo().browse(docids) 
        # model_id = eln.model_id
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
        # model_name = eln.material.product_based_calculation[0].ir_model.name 
        model_id = eln.model_id
        model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }

class GgbsDataSheet(models.AbstractModel):
    _name = 'report.lerm_civil.ggbs_datasheet'
    _description = 'GGBS DataSheet'
    
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
        # differnt location for product based
        # model_name = eln.material.product_based_calculation[0].ir_model.name 
        model_id = eln.model_id
        model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }
    
class MicrosilicaDatasheet(models.AbstractModel):
        _name = 'report.lerm_civil.microsilica_datasheet'
        _description = 'Microsilica DataSheet'
    
        @api.model
        def _get_report_values(self, docids, data):
            if data['fromsample'] == True:
                if 'active_id' in data['context']:
                    eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
                else:
                    eln = self.env['lerm.eln'].sudo().browse(docids) 
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

    
class PTGroutDatasheet(models.AbstractModel):
    _name = 'report.lerm_civil.pt_grout_datasheet'
    _description = 'PT Grout DataSheet'
    
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
        # model_name = eln.material.product_based_calculation[0].ir_model.name 
        model_id = eln.model_id
        model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }
        
class ConcreteCubeCompresiveReport(models.AbstractModel):
    _name = 'report.lerm_civil.compresive_concrete_cube_report'
    _description = 'Cube Compresive Report'
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        elif 'active_id' in data.get('context', {}):
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)
        


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
        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        # import wdb;wdb.set_trace()
        
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'stamp' : inreport_value,
            'nabl' : nabl,
            
        }
        
class ConcreteCubeCompresiveDatasheet(models.AbstractModel):
    _name = 'report.lerm_civil.compresive_concrete_cube_datasheet'
    _description = 'Compresive strength Cube DataSheet'
    
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

class SoilReport(models.AbstractModel):
    _name = 'report.lerm_civil.soil_report'
    _description = 'Soil Report'
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
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
        # if 'active_id' in data['context']:
        #     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        # else:
        #     eln = self.env['lerm.eln'].sudo().browse(docids) 
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
        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
            
    

       
#         plt.close()
        plt.figure(figsize=(12, 6))
        x_values = []
        y_values = []
        # import wdb;wdb.set_trace()
        for line in general_data.heavy_table:
            x_values.append(line.moisture)
            y_values.append(line.dry_density)


        if general_data.heavy_table:
            try:
                max_y = max(y_values)
            except:
                max_y = 100
            try:
                min_y = round(min(y_values),2)
            except:
                min_y = 0
            try:
                # max_x = round(max(x_values),2)
                max_x = x_values[y_values.index(max_y)]
            except:
                max_x = 100
            try:
                min_x = round(min(x_values),2)
            except:
                min_x = 0 
            
            


            # Format max_y and max_x to display 2 digits after the decimal point
            max_y = round(max_y , 2)
            max_x = round(max_x, 2)

    

        
            # Perform cubic spline interpolation
            x_smooth = np.linspace(min(x_values), max(x_values), 100)
            # cs = CubicSpline(x_values, y_values,1)
            # cs = interp1d(x_values, y_values,kind='cubic')
            cs = Akima1DInterpolator(x_values, y_values)

            # Create the line chart with a connected smooth line and markers
            plt.plot(x_smooth, cs(x_smooth), color='red', label='Smooth Curve')
            plt.scatter(x_values, y_values, marker='o', color='blue', s=30, label='Data Points')

            
            # Add a horizontal line with a label(, linestyle='--', label=f'Max Y = {max_y}', linestyle='--', label=f'Max X = {max_x}')
            plt.axhline(y=max_y, color='green',linestyle='--')

            # Add a vertical line with a label
            plt.axvline(x=max_x, color='orange',linestyle='--')

            
            # Set the grid
            ax = plt.gca()
            ax.grid(which='both', linestyle='--', linewidth=0.5)

            # Set the x-axis major and minor tick marks
            ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
            ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

            # Set the y-axis tick marks
            # plt.yticks([1.60, 1.62, 1.64, 1.66, 1.68, 1.70, 1.72, 1.74, 1.76, 1.78, 1.80])

            # edit range here
            plt.yticks(np.arange(min_y , round(max_y,2) + 0.2 , (max_y - min_y) / 5))


            if max_x != min_x:
                plt.xticks(np.arange(min_x, round(max(x_values),2) + 1.0, (max_x - min_x) / 5))
            
            plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
            plt.xlabel('% Moisture')
            plt.ylabel('Dry density in gm/cc')
            plt.title('% Moisture vs Dry density in gm/cc')
            plt.legend()

            # Save the Matplotlib plot to a BytesIO object
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            graph_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Close the Matplotlib plot to free up resources
            plt.close()
        else:
            graph_image = None
            max_y = 0
            max_x = 0

            # Light Compaction-OMC

        plt.figure(figsize=(12, 6))
        x_values = []
        y_values = []
        # import wdb;wdb.set_trace()
        for line in general_data.light_omc_table:
            x_values.append(line.moisture)
            y_values.append(line.dry_density)


        if general_data.light_omc_table:
            try:
                max_y = max(y_values)
            except:
                max_y = 100
            try:
                min_y = round(min(y_values),2)
            except:
                min_y = 0
            try:
                # max_x = round(max(x_values),2)
                max_x = x_values[y_values.index(max_y)]
            except:
                max_x = 100
            try:
                min_x = round(min(x_values),2)
            except:
                min_x = 0 
            
            


            # Format max_y and max_x to display 2 digits after the decimal point
            max_y = round(max_y , 2)
            max_x = round(max_x, 2)

    

        
            # Perform cubic spline interpolation
            x_smooth = np.linspace(min(x_values), max(x_values), 100)
            # cs = CubicSpline(x_values, y_values,1)
            # cs = interp1d(x_values, y_values,kind='cubic')
            cs = Akima1DInterpolator(x_values, y_values)

            # Create the line chart with a connected smooth line and markers
            plt.plot(x_smooth, cs(x_smooth), color='red', label='Smooth Curve')
            plt.scatter(x_values, y_values, marker='o', color='blue', s=30, label='Data Points')

            
            # Add a horizontal line with a label(, linestyle='--', label=f'Max Y = {max_y}', linestyle='--', label=f'Max X = {max_x}')
            plt.axhline(y=max_y, color='green',linestyle='--')

            # Add a vertical line with a label
            plt.axvline(x=max_x, color='orange',linestyle='--')

            
            # Set the grid
            ax = plt.gca()
            ax.grid(which='both', linestyle='--', linewidth=0.5)

            # Set the x-axis major and minor tick marks
            ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
            ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

            # Set the y-axis tick marks
            # plt.yticks([1.60, 1.62, 1.64, 1.66, 1.68, 1.70, 1.72, 1.74, 1.76, 1.78, 1.80])

            # edit range here
            plt.yticks(np.arange(min_y , round(max_y,2) + 0.2 , (max_y - min_y) / 5))


            if max_x != min_x:
                plt.xticks(np.arange(min_x, round(max(x_values),2) + 1.0, (max_x - min_x) / 5))
            
            plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
            plt.xlabel('% Moisture')
            plt.ylabel('Dry density in gm/cc')
            plt.title('% Moisture vs Dry density in gm/cc')
            plt.legend()

            # Save the Matplotlib plot to a BytesIO object
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            graph_image_light = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Close the Matplotlib plot to free up resources
            plt.close()
        else:
            graph_image_light = None
            max_y = 0
            max_x = 0

            

        plt.figure(figsize=(12, 6))
        cbrx_values = []
        cbry_values = []

        # Check if cbr_table exists and populate cbrx_values and cbry_values
        if general_data.soil_table:
            for line in general_data.soil_table:
                cbrx_values.append(line.penetration)
                cbry_values.append(line.load)

            try:
                max_y = max(cbry_values)
            except ValueError:
                max_y = 100  # Default value if cbry_values is empty
            try:
                min_y = round(min(cbry_values), 2)
            except ValueError:
                min_y = 0
            try:
                max_x = cbrx_values[cbry_values.index(max_y)]
            except ValueError:
                max_x = 100
            try:
                min_x = round(min(cbrx_values), 2)
            except ValueError:
                min_x = 0

            # Format max_y and max_x to display 2 digits after the decimal point
            max_y = round(max_y, 2)
            max_x = round(max_x, 2)

            # Perform cubic spline interpolation if there are enough data points
            if len(cbrx_values) > 1 and len(cbry_values) > 1:
                cbrx_smooth = np.linspace(min(cbrx_values), max(cbrx_values), 100)
                cbrcs = CubicSpline(cbrx_values, cbry_values)

                # Create the line chart with a connected smooth line and markers
                plt.plot(cbrx_smooth, cbrcs(cbrx_smooth), color='red', label='Smooth Curve')
                plt.scatter(cbrx_values, cbry_values, marker='o', color='blue', s=30, label='Data Points')

                # Add horizontal lines with labels
                if len(cbry_values) > 8:  # Ensure indices 5 and 8 exist
                    plt.axhline(y=cbry_values[5], color='green', linestyle='--', label=f'Load at 2.5 mm = {cbry_values[5]}')
                    plt.axhline(y=cbry_values[8], color='green', linestyle='--', label=f'Load at 5 mm = {cbry_values[8]}')

                # Add vertical lines at specific penetration values
                plt.axvline(x=2.5, color='orange', linestyle='--')
                plt.axvline(x=5.0, color='orange', linestyle='--')

                # Set the grid
                ax = plt.gca()
                ax.grid(which='both', linestyle='--', linewidth=0.5)

                # Set the x-axis major and minor tick marks
                ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
                ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

                # Set the y-axis tick marks
                plt.yticks(np.arange(min_y, max_y + 0.2, (max_y - min_y) / 5))

                # Set the x-axis tick marks
                if max_x != min_x:
                    plt.xticks(np.arange(min_x, max_x + 1.0, (max_x - min_x) / 5))

                # Set labels and title
                plt.xlabel('Penetration in mm')
                plt.ylabel('Load')
                plt.title('Penetration in mm vs Load')
                plt.legend()

            # Save the Matplotlib plot to a BytesIO object
            buffer2 = BytesIO()
            plt.savefig(buffer2, format='png')
            cbr_graph_image = base64.b64encode(buffer2.getvalue()).decode('utf-8')
            plt.close()
        else:
            cbr_graph_image = None
            cbry_values = []  # Reset to empty list
            cbrx_values = []


    # CBR Infra
        plt.figure(figsize=(12, 6))
        cbrx_values1 = []
        cbry_values1= []

        # Check if cbr_table exists and populate cbrx_values and cbry_values
        if general_data.soil_infra_table:
            for line in general_data.soil_infra_table:
                cbrx_values1.append(line.penetration1)
                cbry_values1.append(line.load1)

            try:
                max_y = max(cbry_values1)
            except ValueError:
                max_y = 100  # Default value if cbry_values is empty
            try:
                min_y = round(min(cbry_values1), 2)
            except ValueError:
                min_y = 0
            try:
                max_x = cbrx_values1[cbry_values1.index(max_y)]
            except ValueError:
                max_x = 100
            try:
                min_x = round(min(cbrx_values1), 2)
            except ValueError:
                min_x = 0

            # Format max_y and max_x to display 2 digits after the decimal point
            max_y = round(max_y, 2)
            max_x = round(max_x, 2)

            # Perform cubic spline interpolation if there are enough data points
            if len(cbrx_values1) > 1 and len(cbry_values1) > 1:
                cbrx_smooth = np.linspace(min(cbrx_values1), max(cbrx_values1), 100)
                cbrcs = CubicSpline(cbrx_values1, cbry_values1)

                # Create the line chart with a connected smooth line and markers
                plt.plot(cbrx_smooth, cbrcs(cbrx_smooth), color='red', label='Smooth Curve')
                plt.scatter(cbrx_values1, cbry_values1, marker='o', color='blue', s=30, label='Data Points')

                # Add horizontal lines with labels
                if len(cbry_values1) > 8:  # Ensure indices 5 and 8 exist
                    plt.axhline(y=cbry_values1[5], color='green', linestyle='--', label=f'Load at 2.5 mm = {cbry_values1[5]}')
                    plt.axhline(y=cbry_values1[8], color='green', linestyle='--', label=f'Load at 5 mm = {cbry_values1[8]}')

                # Add vertical lines at specific penetration values
                plt.axvline(x=2.5, color='orange', linestyle='--')
                plt.axvline(x=5.0, color='orange', linestyle='--')

                # Set the grid
                ax = plt.gca()
                ax.grid(which='both', linestyle='--', linewidth=0.5)

                # Set the x-axis major and minor tick marks
                ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
                ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

                # Set the y-axis tick marks
                plt.yticks(np.arange(min_y, max_y + 0.2, (max_y - min_y) / 5))

                # Set the x-axis tick marks
                if max_x != min_x:
                    plt.xticks(np.arange(min_x, max_x + 1.0, (max_x - min_x) / 5))

                # Set labels and title
                plt.xlabel('Penetration in mm')
                plt.ylabel('Load')
                plt.title('Penetration in mm vs Load')
                plt.legend()

            # Save the Matplotlib plot to a BytesIO object
            buffer2 = BytesIO()
            plt.savefig(buffer2, format='png')
            cbr_graph_image_infra = base64.b64encode(buffer2.getvalue()).decode('utf-8')
            plt.close()
        else:
            cbr_graph_image_infra = None
            cbry_values1 = []  # Reset to empty list
            cbrx_values1 = []
        
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'stamp' : inreport_value,
            'nabl' : nabl,
            'graphHeavy' : graph_image,
            'graphLight' : graph_image_light,
            # 'mdd' : max_y,
            # 'omc' : max_x,
            # 'graphCbr' : cbr_graph_image,
            # 'load2' : cbry_values[5] if cbry_values else 0,
            # 'load5' : cbry_values[8] if cbry_values else 0,
            'mdd': max_y if cbry_values else 0,
            'omc': max_x if cbrx_values else 0,
            'graphCbr': cbr_graph_image,

            'graphCbr1': cbr_graph_image_infra,
            'load2': cbry_values[5] if len(cbry_values) > 5 else 0,
            'load5': cbry_values[8] if len(cbry_values) > 8 else 0,

             'load2': cbry_values1[5] if len(cbry_values1) > 5 else 0,
            'load5': cbry_values1[8] if len(cbry_values1) > 8 else 0,
        }
        
      
        # # Prepare data for the chart
        # plt.figure(figsize=(12, 6))
        # cbrx_values = []
        # cbry_values = []
        # if general_data.soil_table:
        #     for line in general_data.soil_table:
        #         cbrx_values.append(line.penetration)
        #         cbry_values.append(line.load)

        #     try:
        #         max_y = max(cbry_values)
        #     except:
        #         max_y = 100
        #     try:
        #         min_y = round(min(cbry_values),2)
        #     except:
        #         min_y = 0
        #     try:
        #         # max_x = round(max(x_values),2)
        #         max_x = cbrx_values[cbry_values.index(max_y)]
        #     except:
        #         max_x = 100
        #     try:
        #         min_x = round(min(cbrx_values),2)
        #     except:
        #         min_x = 0 
            
            


        #     # Format max_y and max_x to display 2 digits after the decimal point
        #     max_y = round(max_y , 2)
        #     max_x = round(max_x, 2)

            
        #     # Perform cubic spline interpolation
        #     cbrx_smooth = np.linspace(min(cbrx_values), max(cbrx_values), 100)
        #     cbrcs = CubicSpline(cbrx_values, cbry_values)

        #     # Create the line chart with a connected smooth line and markers
        #     plt.plot(cbrx_smooth, cbrcs(cbrx_smooth), color='red', label='Smooth Curve')
        #     plt.scatter(cbrx_values, cbry_values, marker='o', color='blue', s=30, label='Data Points')

        #     # # Add a horizontal line with a label
        #     plt.axhline(y=cbry_values[5], color='green', linestyle='--' , label=f'Load at 2.5 mm = {cbry_values[5]}')
        #     plt.axhline(y=cbry_values[8], color='green', linestyle='--' , label=f'Load at 5 mm = {cbry_values[8]}')

        #     # Add a vertical line with a label
        #     plt.axvline(x=2.5, color='orange', linestyle='--')
        #     plt.axvline(x=5.0, color='orange', linestyle='--')
            
        #     # Set the grid
        #     ax = plt.gca()
        #     ax.grid(which='both', linestyle='--', linewidth=0.5)

        #     # Set the x-axis major and minor tick marks
        #     ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
        #     ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

        #     # Set the y-axis tick marks
        #     # plt.xticks(range(0 , 15 , 1))
        #     # plt.yticks(range(0 , 481 , 50))

        #     plt.yticks(np.arange(min_y , max_y + 0.2 , (max_y - min_y) / 5))


        #     if max_x != min_x:
        #         plt.xticks(np.arange(min_x, round(max(x_values),2) + 1.0, (max_x - min_x) / 5))
            
        #     plt.xlabel('Penetration in mm')
        #     plt.ylabel('Load')
        #     plt.title('Penetration in mm vs Load')
        #     plt.legend()

        #     # Save the Matplotlib plot to a BytesIO object
        #     buffer2 = BytesIO()
        #     plt.savefig(buffer2, format='png')
        #     cbr_graph_image = base64.b64encode(buffer2.getvalue()).decode('utf-8')
        #     plt.close()
        # else:
        #     cbr_graph_image = None
        #     cbry_values = []  # Set to an empty list instead of 0
        #     cbrx_values = []
        
        # return {
        #     'eln': eln,
        #     'data' : general_data,
        #     'qrcode': qr_code,
        #     'stamp' : inreport_value,
        #     'nabl' : nabl,
        #     'graphHeavy' : graph_image,
        #     'mdd' : max_y,
        #     'omc' : max_x,
        #     'graphCbr' : cbr_graph_image,
        #     'load2' : cbry_values[5] if cbry_values else 0,
        #     'load5' : cbry_values[8] if cbry_values else 0,
        # }


        
class SoilDatasheet(models.AbstractModel):
    _name = 'report.lerm_civil.soil_datasheet'
    _description = 'Soil DataSheet'
    
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
        

class FineAggregateRep(models.AbstractModel):
    _name = 'report.lerm_civil.fine_aggregte_mech_report'
    _description = 'Fine'
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        print('this is eln')
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        if 'active_id' in data['context']:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids) 
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
        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        print(eln , 'this is eln')
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'stamp' : inreport_value,
            'nabl' : nabl
        }