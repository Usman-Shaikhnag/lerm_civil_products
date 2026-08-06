# -*- coding: utf-8 -*-
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError

NDT_DISCIPLINE_INTERNAL_ID = '742c99ff-c484-4806-bb68-11b4271d6147'


class SaleOrderSrfWizardLine(models.TransientModel):
    _name = 'sale.order.srf.wizard.line'
    _description = 'Sales Order to SRF Wizard Line'

    wizard_id = fields.Many2one('sale.order.srf.wizard', string='Wizard', ondelete='cascade')
    selected = fields.Boolean(string='Include', default=True)

    sale_order_line_ids = fields.Many2many(
        'sale.order.line',
        string='Sales Order Lines',
        readonly=True,
    )
    material_id = fields.Many2one('product.template', string='Material', readonly=True)
    grade_id = fields.Many2one('lerm.grade.line', string='Grade', readonly=True)
    size_id = fields.Many2one('lerm.size.line', string='Size', readonly=True)
    conformity = fields.Boolean(string='Conformity', readonly=True)
    parameters = fields.Many2many(
        'lerm.parameter.master',
        string='Parameter',
    )
    product_uom_qty = fields.Float(string='Sample Qty')
    price = fields.Float(string='Price', readonly=True)


class SaleOrderSrfWizard(models.TransientModel):
    _name = 'sale.order.srf.wizard'
    _description = 'Create SRF from Sales Order'

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Reporting Customer')
    name_work_id = fields.Many2one('res.partner.project', string='Name of Work')
    srf_date = fields.Date(string='SRF Date', default=fields.Date.context_today)
    lab_location = fields.Many2one(
        'lerm.lab.master',
        string='Lab Name',
        default=lambda self: self._get_oldest_lab(),
    )
    location_name = fields.Many2one('lerm.lab.location.master', string='Location Name')
    report_due_date = fields.Date(string='Report Due Date')
    line_ids = fields.One2many('sale.order.srf.wizard.line', 'wizard_id', string='Samples')

    @api.model
    def _get_oldest_lab(self):
        oldest_lab = self.env['lerm.lab.master'].search([], order='create_date asc', limit=1)
        return oldest_lab.id if oldest_lab else False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        order_id = res.get('sale_order_id') or self.env.context.get('default_sale_order_id')
        if not order_id:
            return res
        order = self.env['sale.order'].browse(order_id)
        res['sale_order_id'] = order.id
        res['partner_id'] = order.partner_id.id
        res['customer_id'] = order.customer_id.id or order.partner_id.id
        res['name_work_id'] = order.name_work_id.id
        groups = self._build_groups(order)
        res['line_ids'] = [(0, 0, g) for g in groups]
        return res

    @api.onchange('lab_location')
    def _onchange_lab_location(self):
        for record in self:
            if record.lab_location and record.lab_location.lab_location_line:
                if not record.location_name or record.location_name.parent_id != record.lab_location:
                    line = record.lab_location.lab_location_line[0]
                    record.location_name = line
            else:
                record.location_name = False

    def _build_groups(self, order):
        """Group SO lines into one row per (material, grade, size, conformity).

        Sales Order lines carry one parameter each, so the parameters of every
        line sharing the same product are merged into a single wizard row.
        """
        groups = []
        seen = {}
        for line in order.order_line:
            if not line.product_id or not line.product_id.product_tmpl_id.is_sample:
                continue
            tmpl = line.product_id.product_tmpl_id
            key = (tmpl.id, line.grade_id.id, line.size_id.id, bool(line.conformity))
            if key not in seen:
                seen[key] = len(groups)
                groups.append({
                    'sale_order_line_ids': [(6, 0, [])],
                    'material_id': tmpl.id,
                    'grade_id': line.grade_id.id,
                    'size_id': line.size_id.id,
                    'conformity': line.conformity,
                    'parameters': [(6, 0, [])],
                    'product_uom_qty': 0.0,
                    'price': 0.0,
                })
            group = groups[seen[key]]
            group['sale_order_line_ids'][0][2].append(line.id)
            group['parameters'][0][2].extend(line.parameters.ids)
            group['product_uom_qty'] = max(
                group['product_uom_qty'], line.product_uom_qty or 0.0)
            group['price'] += line.price_subtotal or 0.0
        return groups

    def _get_order(self):
        order = self.sale_order_id
        if not order:
            order_id = self.env.context.get('default_sale_order_id') or self.env.context.get('active_id')
            order = self.env['sale.order'].browse(order_id)
        if not order:
            raise UserError(_('Sales Order is missing. Please reopen the wizard.'))
        return order

    def action_create_srf(self):
        self.ensure_one()
        order = self._get_order()
        groups = self._build_groups(order)

        client_lines = self.line_ids
        if len(client_lines) != len(groups):
            raise UserError(_(
                'The sales order lines were modified (lines added or removed). '
                'Please close and reopen the wizard.'))
        for idx, group in enumerate(groups):
            group['selected'] = client_lines[idx].selected
            group['product_uom_qty'] = client_lines[idx].product_uom_qty
            group['parameters'] = client_lines[idx].parameters

        srf_vals = {
            'sale_order_id': order.id,
            'customer': self.customer_id.id or order.partner_id.id,
            'billing_customer': order.partner_id.id,
            'name_work': self.name_work_id.id,
            'srf_date': self.srf_date,
            'price_snapshot': self._build_price_snapshot(groups),
        }
        srf = self.env['lerm.civil.srf'].create(srf_vals)

        for group in groups:
            if not group['selected']:
                continue
            if not group['parameters']:
                raise UserError(_(
                    'Material "%s" has no parameters selected. Add at least one parameter.'
                    % (self.env['product.template'].browse(group['material_id']).display_name or '')))
            qty = int(group['product_uom_qty'] or 0)
            if qty <= 0:
                raise UserError(_(
                    'Sample Quantity Must be Greater Than Zero for "%s".'
                    % (self.env['product.template'].browse(group['material_id']).display_name or '')))

            line_ids = group['sale_order_line_ids'][0][2]
            sale_order_line_id = line_ids[0] if line_ids else False
            material = self.env['product.template'].browse(group['material_id'])
            discipline = material.discipline
            group_obj = material.group[:1]

            if discipline.internal_id == NDT_DISCIPLINE_INTERNAL_ID and len(group['parameters']) > 1:
                raise UserError(_('Only one Parameter is allowed in Non Destructive Testing'))

            range_line = self.env['sample.range.line'].create({
                'srf_id': srf.id,
                'discipline_id': discipline.id,
                'lab_no_value': discipline.lab_no if discipline else False,
                'group_id': group_obj.id,
                'material_id': material.id,
                'grade_id': group['grade_id'],
                'size_id': group['size_id'],
                'parameters': [(6, 0, group['parameters'].ids)],
                'conformity': group['conformity'],
                'sample_qty': qty,
                'casting': material.casting_required,
                'product_name': material.id,
                'main_name': material.name,
                'price': group['price'],
                'sample_received_date': self.srf_date,
            })

            for _i in range(qty):
                sample = self.env['lerm.srf.sample'].create({
                    'srf_id': srf.id,
                    'sample_range_id': range_line.id,
                    'sale_order_line_id': sale_order_line_id,
                    'discipline_id': discipline.id,
                    'lab_no_value': discipline.lab_no if discipline else False,
                    'group_id': group_obj.id,
                    'material_id': material.id,
                    'grade_id': group['grade_id'],
                    'size_id': group['size_id'],
                    'department_id': material.department_ids.name,
                    'parameters': [(6, 0, group['parameters'].ids)],
                    'conformity': group['conformity'],
                    'casting': material.casting_required,
                    'sample_received_date': self.srf_date,
                    'product_name': material.id,
                    'main_name': material.name,
                    'price': group['price'],
                    'customer_id': self.customer_id.id or order.partner_id.id,
                    'lab_location': self.lab_location.id,
                    'location_name': self.location_name.id,
                    'report_due_date': self.report_due_date,
                })
                self.env['lerm.sample.register'].sudo().create({
                    'sample': sample.id,
                    'quantity': qty,
                })

        action = self.env['ir.actions.act_window']._for_xml_id('lerm_civil.srf_form_id')
        action['view_mode'] = 'form'
        action['res_id'] = srf.id
        return action

    def _build_price_snapshot(self, groups):
        snapshot = []
        for group in groups:
            snapshot.append({
                'material_id': group['material_id'],
                'grade_id': group['grade_id'],
                'size_id': group['size_id'],
                'conformity': group['conformity'],
                'product_uom_qty': group['product_uom_qty'],
                'parameters': group['parameters'].ids,
                'price': group['price'],
                'sale_order_line_ids': group['sale_order_line_ids'][0][2],
            })
        return json.dumps(snapshot)
