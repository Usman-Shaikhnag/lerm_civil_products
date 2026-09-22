from odoo import models, fields ,api

class SampleRegister(models.Model):
    _name = 'lerm.sample.register'
    _rec_name = 'sample'

    sample = fields.Many2one('lerm.srf.sample',string="Sample")
    quantity = fields.Integer(string="Quantity")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")  
    quantity_received = fields.Integer(string="Quantity Received")
    quantity_consumed = fields.Integer(string="Quantity Consumed")
    quantity_discarded = fields.Integer(string="Quantity Discarded")
    quantity_balance = fields.Integer(string="Quantity Balance",compute="compute_quantity_balance")
    resample_id = fields.Many2one('lerm.srf.sample',string="Sample")
    discard_date = fields.Date("Discard Date")
    discard_reason = fields.Char("Discard Reason")
    attachment = fields.Binary("Attachment")
    attachment_name = fields.Char("Attachment Name")
    sample_received_date = fields.Date("Sample Received Date")
    report_issued_date = fields.Date("Report Issued Date")
    test_end_date = fields.Date("Test End Date")

    @api.depends('quantity_received', 'quantity_consumed','quantity_discarded')
    def compute_quantity_balance(self):
        for rec in self:
            rec.quantity_balance = rec.quantity_received - rec.quantity_consumed - rec.quantity_discarded

    def resample_rec(self):
        # import wdb ; wdb.set_trace()
        action = self.env.ref('lerm_civil.resample_wizard')
        return {
            'name': "Resample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sample.register.resample',
            'view_id': action.id,
            'target': 'new'
            }
    
    def discard_sample(self):
        # import wdb ; wdb.set_trace()
        action = self.env.ref('lerm_civil.discard_sample_quantity')
        return {
            'name': "Discard Quantity",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sample.register.discard',
            'view_id': action.id,
            'target': 'new'
            }

class DiscardSampleRegister(models.TransientModel):
    _name = 'sample.register.discard'

    discard_date = fields.Date("Discard Date")
    discard_reason = fields.Char("Discard Reason")
    discard_quantity = fields.Float("Discard Quantity")
    discard_quantity_unit = fields.Many2one('uom.uom',string="Unit",default=lambda self: self._get_default_unit())
    attachment = fields.Binary("Attachment")
    attachment_name = fields.Char("Attachment Name")

    def _get_default_unit(self):
        # import wdb;wdb.set_trace()
        sample_register = self.env['lerm.sample.register'].sudo().search([('id','=',self._context['active_id'])])
        return sample_register.uom_id.id if sample_register else False

    def discard_sample_quantity(self):
        sample_register = self.env['lerm.sample.register'].sudo().search([('id','=',self._context['active_id'])])
        sample = sample_register.sample
        
        sample_register.sudo().write({
            'discard_date':self.discard_date,
            'discard_reason':self.discard_reason,
            'quantity_discarded':self.discard_quantity,
            'attachment':self.attachment,
            'attachment_name':self.attachment_name
        })
        if sample:
            sample.sudo().write({
                'quantity_discarded':self.discard_quantity
            })

    
    def cancel_sample_discard(self):
        return {'type': 'ir.actions.act_window_close'}



class ReSampleRegister(models.TransientModel):
    _name = 'sample.register.resample'

    resample_date = fields.Date("Resample Date")
    resample_quantity = fields.Float("Resample Quantity")
    resample_quantity_unit = fields.Many2one('uom.uom',string="Unit",default=lambda self: self._get_default_unit())
    

    def _get_default_unit(self):
        # import wdb;wdb.set_trace()
        sample_register = self.env['lerm.sample.register'].sudo().search([('id','=',self._context['active_id'])])
        return sample_register.uom_id.id if sample_register else False

    def action_resample(self):
        pass

    
    def cancel_resample(self):
        return {'type': 'ir.actions.act_window_close'}