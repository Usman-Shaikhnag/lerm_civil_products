import logging
from odoo import models, fields ,api

_logger = logging.getLogger(__name__)


class PriceListInherited(models.Model):
    _inherit = 'product.pricelist.item'
    parameter_id = fields.Many2one(
        'lerm.parameter.master',
        string="Parameter",
        help="If set, this price applies to this specific parameter only.",
        domain="[('material', '=', product_tmpl_id)]"
    )

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
        super(AccountMoveInheritedLerm,self).action_post()
        for record in self.invoice_line_ids.report_no1:
            if record.invoice_number != self:
                record.sudo().write({'invoice_number': self.id})
            record.sudo()._compute_invoice_status()

    def button_draft(self):
        super(AccountMoveInheritedLerm,self).button_draft()
        for record in self.invoice_line_ids.report_no1:
            if not record.invoice_number:
                record.sudo().write({'invoice_number': self.id})
            record.sudo()._compute_invoice_status()

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
    report_no1 = fields.Many2many("lerm.srf.sample", string="Report No",domain="[('state', '=', '4-in_report'),('invoice_status', 'in', ('1-uninvoiced',)),('srf_id.customer', '=', partner_id),('material_id', '=', product_tmpl_id)]")
    
    parameters = fields.Many2many('lerm.parameter.master', string='Parameters')
    product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id', string='Product Template')


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

    @api.depends('parameters', 'product_id', 'move_id.pricelist_id')
    def _compute_price_unit(self):
        res = super()._compute_price_unit()
        for line in self:
            if line.parameters and line.move_id.pricelist_id and line.product_id:
                total = line._get_price_with_pricelist()
                line.price_unit = total
            elif not line.parameters and line.move_id.pricelist_id and line.product_id:
                # No parameters selected — check if pricelist has a whole-product price
                # (i.e. an item WITHOUT parameter_id for this product)
                pt_id = line.product_id.product_tmpl_id._origin.id if line.product_id.product_tmpl_id._origin else line.product_id.product_tmpl_id.id
                prod_id = line.product_id._origin.id if line.product_id._origin else line.product_id.id

                # Look for whole-product pricelist items (no parameter_id)
                whole_product_price = line.move_id.pricelist_id.item_ids.filtered(
                    lambda i: (
                        ((i.product_tmpl_id._origin.id if i.product_tmpl_id._origin else i.product_tmpl_id.id) == pt_id
                         or (i.product_id._origin.id if i.product_id._origin else i.product_id.id) == prod_id)
                        and not i.parameter_id
                    )
                )
                if whole_product_price:
                    # Use the first matching whole-product pricelist item
                    line.price_unit = whole_product_price[0].fixed_price
                else:
                    # Check if ONLY parameter-specific prices exist (no whole-product entry)
                    has_param_prices = line.move_id.pricelist_id.item_ids.filtered(
                        lambda i: (
                            ((i.product_tmpl_id._origin.id if i.product_tmpl_id._origin else i.product_tmpl_id.id) == pt_id
                             or (i.product_id._origin.id if i.product_id._origin else i.product_id.id) == prod_id)
                            and i.parameter_id
                        )
                    )
                    if has_param_prices:
                        # Only parameter-specific prices exist, no whole-product price — force 0
                        line.price_unit = 0.0



    def _get_price_with_pricelist(self):
        self.ensure_one()
        _logger.info(f"--- _get_price_with_pricelist called for line {self.id} ---")
        _logger.info(f"Parameters: {self.parameters.ids if self.parameters else 'None'}")
        
        # Resolve the pricelist - prefer the DB-stored value over the virtual onchange value
        pricelist_rec = self.move_id.pricelist_id
        move_origin = self.move_id._origin if self.move_id._origin else self.move_id
        if move_origin and move_origin.id and move_origin.pricelist_id:
            pricelist_rec = move_origin.pricelist_id
        
        _logger.info(f"Pricelist resolved: {pricelist_rec.id if pricelist_rec else 'None'} | Name: {pricelist_rec.name if pricelist_rec else 'None'}")
        _logger.info(f"Product: {self.product_id.id if self.product_id else 'None'}")

        if self.parameters and pricelist_rec and self.product_id:
            total = 0.0
            pt_id = self.product_id.product_tmpl_id._origin.id if self.product_id.product_tmpl_id._origin else self.product_id.product_tmpl_id.id
            prod_id = self.product_id._origin.id if self.product_id._origin else self.product_id.id
            
            # Search pricelist items directly from DB for reliability
            PricelistItem = self.env['product.pricelist.item'].sudo()
            pricelist_items = PricelistItem.search([
                ('pricelist_id', '=', pricelist_rec.id),
                ('parameter_id', '!=', False),
                '|',
                ('product_tmpl_id', '=', pt_id),
                ('applied_on', '=', '3_global'),
            ])
            
            _logger.info(f"Found {len(pricelist_items)} pricelist items via search for pricelist {pricelist_rec.id}")
            for debug_item in pricelist_items:
                _logger.info(f"  Item ID: {debug_item.id} | param: {debug_item.parameter_id.id} | price: {debug_item.fixed_price}")
            
            for param in self.parameters:
                p_id = param._origin.id if param._origin else param.id
                
                matching = pricelist_items.filtered(
                    lambda i: i.parameter_id.id == p_id or (
                        i.parameter_id.parameter_name and param.parameter_name and
                        i.parameter_id.parameter_name.strip().lower() == param.parameter_name.strip().lower()
                    )
                )
                if matching:
                    _logger.info(f"Match found for param {p_id}! Adding {matching[0].fixed_price}")
                    total += matching[0].fixed_price
                else:
                    _logger.info(f"No match found for param {p_id}.")
            
            _logger.info(f"Final calculated total: {total}")
            return total
        
        fallback_price = super()._get_price_with_pricelist()
        _logger.info(f"Falling back to super(). Price: {fallback_price}")
        return fallback_price