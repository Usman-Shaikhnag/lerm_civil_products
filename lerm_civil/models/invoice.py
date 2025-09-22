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


class AccountMoveLineInherited(models.Model):
    _inherit = 'account.move.line'
    
    report_no = fields.Char(string="Report No")
    pricelist_id = fields.Many2one("product.pricelist",string="Pricelist",compute='_compute_pricelist')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    report_no1 = fields.Many2many("lerm.srf.sample", string="Report No",domain="[('state', '=', '4-in_report'),('invoice_status', '!=', '2-invoiced'),('srf_id.customer', '=', partner_id)]")
    
    # @api.onchange('partner_id', 'product_id')
    # def _onchange_partner_or_product(self):
    #     for rec in self:
    #         domain = [
    #             '&',
    #             '|',
    #             ('srf_id.customer', '=', rec.partner_id.id),
    #             ('srf_id.billing_customer', '=', rec.partner_id.id),
    #             ('state', '=', '4-in_report'),
    #             ('invoice_status', '!=', '2-invoiced'),
    #             ('material_id', '=', rec.product_id.id)
    #         ]
    #         return {'domain': {'report_no1': domain}}

    @api.onchange("pricelist_id")
    def onchange_pricelist_id(self):
        for record in self:
            # import wdb; wdb.set_trace();
            # data = []
            if self.pricelist_id:
                data = self.pricelist_id.item_ids.product_tmpl_id.product_variant_ids.ids
                # for product in self.pricelist_id.item_ids:
                #     data.append(product.product_tmpl_id.id)
                return {'domain': {'product_id': [('id','in', data)]}}
            else:
                return{}
    


    @api.depends("move_id.pricelist_id")
    def _compute_pricelist(self):
        # import wdb; wdb.set_trace();
        self.pricelist_id = self.move_id.pricelist_id.id
