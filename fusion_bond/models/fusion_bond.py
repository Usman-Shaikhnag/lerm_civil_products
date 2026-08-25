
from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class MechanicalFusionBondSteel(models.Model):
    _name = "mechanical.fusion.bond.steel"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Fusion Bond Epoxy Coated Steel")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    dia = fields.Char("DIA, mm")
    coating_thickness = fields.Char("Coating Thickness")
    continuity_coating = fields.Selection(
        [('satisfactory', 'Satisfactory'),
         ('unsatisfactory', 'UnSatisfactory')],
        string='Continuity of Coating',
        help='Choose an option from the list.'
    )

    adhesion_coating = fields.Selection(
        [('satisfactory', 'Satisfactory'),
         ('unsatisfactory', 'UnSatisfactory')],
        string='Adhesion of coating',
        help='Choose an option from the list.'
    )

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.fusion.bond.steel'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(MechanicalFusionBondSteel, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record
    

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self.default_get(fields)

        return super(MechanicalFusionBondSteel, self).read(fields=fields, load=load)
