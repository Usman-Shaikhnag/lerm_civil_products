from odoo import models, fields ,api


class AccountMoveInheritedLerm(models.Model):
    _inherit = 'account.move'

    # @api.model
    # def create(self,vals):
    #     import wdb; wdb.set_trace()
    #     print("Insideeeeeeeee move")
    #     # res = super(AccountMoveInheritedLerm,self).create(vals)
    #     # return res

    def action_post(self):
        self.invoice_user_id = self.partner_id.user_id.id
        for rec in self.invoice_line_ids.report_no1:
            rec.sudo().write({
                'invoice_status' : '2-invoiced'
            })
                
        super(AccountMoveInheritedLerm,self).action_post()
        for record in self.invoice_line_ids.report_no1:
            record.sudo().write({
            'invoice_number' :self
            })

    def button_draft(self):
        for rec in self.invoice_line_ids.report_no1:
            rec.sudo().write({
                'invoice_status' : '1-uninvoiced'
            })
        super(AccountMoveInheritedLerm,self).button_draft()
        for record in self.invoice_line_ids.report_no1:
            record.sudo().write({
            'invoice_number' :None
            })

    # Field to set Invoice Salesperson
    invoice_user_id = fields.Many2one(
        'res.users', 
        string='Salesperson', 
        readonly=False,
        help='Salesperson for this invoice.')

    @api.onchange('partner_id')
    def _onchange_partner_id_set_salesperson(self):
        """
        Automatically fetch and set the `user_id` (Salesperson) from the partner
        to the invoice_user_id field in account.move when the partner is selected.
        """
        for record in self:
            if record.partner_id:
                record.invoice_user_id = record.partner_id.user_id



class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Field to set Salesperson (user_id)
    user_id = fields.Many2one(
        'res.users', 
        string='Salesperson', 
        help='Default salesperson for this customer.')
