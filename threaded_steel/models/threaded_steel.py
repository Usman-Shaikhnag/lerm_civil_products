from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re



class ThreadedSteel(models.Model):
    _name = "mech.threaded.steel"
    _inherit = "lerm.eln"
    _rec_name = "name"
   
    
    name = fields.Char("Name",default="Threaded Steel")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    
    
    diameter = fields.Float(string="Gauge Dia, mm")
    area = fields.Float(string="Area, mm²",compute="_compute_area")
    gauge_length = fields.Float(string="Gauge Length",digits=(10, 4),compute="_compute_gauge_length")
    final_diameter = fields.Float(string="Final Dia, mm")
    final_length = fields.Float(string="Final Length",digits=(10, 2))
    proof_load = fields.Float(string="0.2% Proof Load / Yield Load, KN")
    ultimate_load = fields.Float(string="Ultimate Load, KN")
    
    yield_visible = fields.Boolean(string="yield visible",compute="_compute_visible")
    yield_stress = fields.Float(string="0.2% Proof Load / Yield Stress, N/mm²",compute="_compute_yield_stress")
    
    uts_visible = fields.Boolean(string="uts visible",compute="_compute_visible")
    ult_tens_strgth = fields.Float(string="Ultimate Tensile Strength, N/mm2",compute="_compute_ult_tens_strgth",store=True)
    
    elongation_visible = fields.Boolean(string="elongation visible",compute="_compute_visible")
    percent_elongation = fields.Float(string="Elongation %",compute="_compute_elongation_percent",store=True)
    
    reduction_visible = fields.Boolean(string="reduction visible",compute="_compute_visible")
    reduction_area = fields.Float(string="Reduction Area",compute="_compute_reduction_area",store=True)
    fracture = fields.Char("Fracture",default="W.G.L")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    @api.depends('diameter')
    def _compute_area(self):
        for record in self:
            area = record.diameter * record.diameter * 3.1416/4
            record.area = round(area,2)

    
    @api.depends('area')
    def _compute_gauge_length(self):
        for record in self:
            gauge_length = 5.65 * math.sqrt(record.area)
            record.gauge_length = round(gauge_length,0)

    @api.depends('proof_load','area')
    def _compute_yield_stress(self):
        for record in self:
            if record.area != 0:
                yield_stress = record.proof_load / record.area * 1000
                record.yield_stress = round(yield_stress,2)
            else:
                record.yield_stress = 0

    @api.depends('ultimate_load','area')
    def _compute_ult_tens_strgth(self):
        for record in self:
            if record.area != 0:
                ult_tens_strgth = record.ultimate_load/record.area * 1000
                record.ult_tens_strgth = round(ult_tens_strgth,2)
            else:
                record.ult_tens_strgth = 0

    @api.depends('final_length','gauge_length')
    def _compute_elongation_percent(self):
        for record in self:
            if record.gauge_length != 0:
                percent_elongation = (record.final_length - record.gauge_length)/record.gauge_length * 100
                record.percent_elongation = round(percent_elongation,2)
            else:
                record.percent_elongation = 0

    
    @api.depends('final_diameter','area')
    def _compute_reduction_area(self):
        for record in self:
            if record.area != 0:
                reduction_area = -((record.final_diameter * record.final_diameter * 3.1416 / 4)- record.area)/record.area *100
                record.reduction_area = round(reduction_area,2)
            else:
                record.reduction_area = 0

        

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.yield_visible = False
            record.uts_visible  = False  
            record.elongation_visible = False
            record.reduction_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '4d303b20-3c0d-406a-99fd-2342f5284def':
                    record.yield_visible = True
                if sample.internal_id == 'cfd57c73-61d9-4c56-a219-cb99719ef035':
                    record.uts_visible = True
                if sample.internal_id == '0fa60911-adbd-4beb-a10b-7a2447c6a92a':
                    record.elongation_visible = True
                if sample.internal_id == 'de8d91bc-9326-45d1-b35c-8c777f0e665b':
                    record.reduction_visible = True

    @api.model
    def create(self, vals):
        record = super(ThreadedSteel, self).create(vals)
        # import wdb;wdb.set_trace()
        # record.get_all_fields()
        self._compute_size_id()
        self._compute_grade_id()
        self._compute_sample_parameters()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self._compute_size_id()
        self._compute_grade_id()
 

        return super(ThreadedSteel, self).read(fields=fields, load=load)


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # @api.onchange('bend_test1')
    # def _compute_wdb(self):
    #     import wdb; wdb.set_trace()
        
    

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size = self.eln_ref.size_id.id



    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '4d303b20-3c0d-406a-99fd-2342f5284def':
                result.result_char = round(self.yield_stress,2)
                # if self.uts_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'cfd57c73-61d9-4c56-a219-cb99719ef035':
                result.result_char = round(self.ult_tens_strgth,2)
                # if self.yield_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '0fa60911-adbd-4beb-a10b-7a2447c6a92a':
                result.result_char = self.percent_elongation
                # if self.elongation_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'de8d91bc-9326-45d1-b35c-8c777f0e665b':
                result.result_char = round(self.reduction_area,2)
                # if self.ts_ys_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }
        # return {'type': 'ir.actions.client', 'tag': 'history_back'}

    


    
    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)
            