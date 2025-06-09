from odoo import api, fields, models

class Material(models.Model):
    _inherit = "product.template"

    is_sample = fields.Boolean(string="Is Sample?")
    casting_required = fields.Boolean(string="Casting Required")
    is_product_based_calculation = fields.Boolean(string="Product Based Calculation")
    test_parameter = fields.Char("Test Column Title")
    results = fields.Char("Result Column Title")
    specifications = fields.Char("Specifications Column Title")
    unit = fields.Char("Unit Column Title")
    method_reference = fields.Char("Method Reference Column Title")
    result_remark = fields.Char("Results Remark Column Title")
    discipline = fields.Many2one('lerm_civil.discipline',string="Discipline")
    group = fields.Many2one('lerm_civil.group',string="Group")
    department_ids = fields.Many2one('hr.department', string='Department')
    test_format_no = fields.Char(string="Test Format No")
    data_sheet_format_no = fields.Many2one('lerm.datasheet.master',string="Data Sheet Format No")
    group_ids = fields.Many2many('lerm_civil.group',string="Group Ids",compute="compute_group_ids")
    # parameter_table = fields.One2many('lerm.parameter.line','parameter_id',string="Parameter")
    size_table = fields.One2many('lerm.size.line','product_id',string="Size")
    qty_table = fields.One2many('lerm.qty.line','product_id',string="Qty")
    grade_table = fields.One2many('lerm.grade.line','product_id',string="Grade")
    alias_table = fields.One2many('lerm.alias.line','product_id',string="Alias")
    datasheet_table = fields.One2many('lerm.material.datasheet.line','product_id',string="Datasheet Table")
    parameter_master_ids = fields.Many2many('lerm.parameter.master',string="Parameter Master IDS",compute="compute_parameter_master_ids")
    parameter_table1 = fields.Many2many('lerm.parameter.master',string="Parameters",)
    volume = fields.Char("Volume")
    lab_name = fields.Char(string="Lab Name")
    product_based_calculation = fields.One2many('lerm.product.based.calculation','product_id',string="Product Based Calculation")
    sop = fields.Html(string='SOP')


    @api.onchange('department_id')
    def update_department_name(self):
        if self.env.context.get('update_department_name'):
            self.department_id = self.department_id

   
    @api.model
    def create(self, values):
        record = super(Material, self).create(values)
        record.update_department_name()
        return record


    


   

    # discipline2 = fields.One2many('material.discipline.line')


    def action_open_product_grade_wizard(self):
        wizard_action = self.env.ref('lerm_civil.action_product_grade_wizard')
        return {
            'name': 'Add Grade Line',
            'type': 'ir.actions.act_window',
            'res_model': 'product.grade.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id},
        }

    def name_get(self):
        res = []
        for product in self:
            # print("saa" + str(self.env.context.get('hide_reference')))
            if self.env.context.get('lab_name'):
                # import wdb; wdb.set_trace()
                if product.lab_name:
                    name = product.lab_name
                    print("from lab")
                    print("name" + str(name))
                    res.append((product.id, name))
                else:
                    print("from elsse")
                    name = product.name
                    print("name" + str(name))
                    res.append((product.id, name))
            elif self.env.context.get('main_name'):
                print("from main")
                name = product.name
                print("name" + str(name))
                res.append((product.id, name))
            else:
                print("from elsse")
                name = product.name
                print("name" + str(name))
                res.append((product.id, name))
        return res

    @api.depends('discipline')
    def compute_parameter_master_ids(self):
        for record in self:
            parameter_master_ids = self.env['lerm.parameter.master'].search([('discipline', '=', record.discipline.id)])
            record.parameter_master_ids = parameter_master_ids

    @api.depends('discipline')
    def compute_group_ids(self):
        for record in self:
            # record.group = None
            group_ids = self.env['lerm_civil.group'].search([('discipline', '=', record.discipline.id)])
            record.group_ids = group_ids

   


    

class DatasheetLine(models.Model):
    _name = 'lerm.material.datasheet.line'

    product_id = fields.Many2one('product.template',string="Product ID")
    datasheet = fields.Many2one('lerm.datasheet.master',string="Datasheet")

class ParameterMasterAliasLine(models.Model):
    _name = 'lerm.alias.line'

    product_id = fields.Many2one('product.template',string="Parameter Id")
    product_alias = fields.Many2one('product.product',string="Product Alias")
    customer = fields.Many2one('res.partner',string="Customer")
    
    @api.onchange('customer')
    def onchange_customer(self):
        
        if self.customer:
            products = self.customer.property_product_pricelist.item_ids.product_tmpl_id.product_variant_ids.ids
            # print(self.customer.property_product_pricelist.item_ids.product_tmpl_id.product_variant_ids)
            domain = [('id','in',products)]

            return {'domain': {'product_alias': domain}}
        else:
            domain = [('id','in', [])]
            
            return {'domain': {'product_alias': domain}}
            


# class ParameterLine(models.Model):
#     _name = 'lerm.parameter.line'

#     parameter_id = fields.Many2one('product.template')
#     parameter = fields.Many2one('lerm.parameter.master',string="Parameter")
#     discipline = fields.Many2one('lerm_civil.discipline',readonly=True)
#     parameters_ids = fields.Many2many('lerm.parameter.master',string="Parameters")
    # minimum = fields.Float("min")
    # maximum = fields.Float("max")
    # mu_value = fields.Float("MU Value")
    # specification1 = fields.Char("Specification 1")
    # specification2 = fields.Char("Specifications 2")
    # unit = fields.Char("Unit")
    # test_method = fields.Many2one('lerm_civil.test_method',string="Test Parameter")

    # @api.onchange('parameter')
    # def compute_discipline(self):
    #     for record in self:
    #         self.discipline = self.parameter.discipline

    # @api.depends('discipline')
    # def compute_parameter_ids(self):
    #     for rec in self:
    #         parameters_ids = self.env['lerm.parameter.master'].search(['discipline','=',rec.discipline.id])
    #         rec.parameters_ids = parameters_ids

           
    

class SizeLine(models.Model):
    _name = 'lerm.size.line'
    _rec_name = 'size'

    product_id = fields.Many2one('product.template')
    size = fields.Char("Size")

class QtyLine(models.Model):
    _name = 'lerm.qty.line'
    _rec_name = 'qty'
    
    product_id = fields.Many2one('product.template')
    qty = fields.Char("Qty")

class GradeLine(models.Model):
    _name = 'lerm.grade.line'
    _rec_name = 'grade'
    
    product_id = fields.Many2one('product.template')
    grade = fields.Char("Grade")


class ProductBasedCalculation(models.Model):
    _name = 'lerm.product.based.calculation'
    _rec_name = 'grade'
    product_id = fields.Many2one('product.template')
    grade_ids = fields.Many2many("lerm.grade.line",string="Grade IDs")
    grade = fields.Many2one("lerm.grade.line",string="Grade")
    main_report_template = fields.Many2one('ir.actions.report',string="Main Report Template")
    datasheet_report_template = fields.Many2one('ir.actions.report',string="DataSheet Report Template")
    ir_model = fields.Many2one('ir.model',string="Model")

    # @api.depends('product_id','product_id.grade_table')
    # def compute_grade_table(self):
    #     for rec in self:
    #         table_data = self.env.context.get("grade_table_datas")
    #         print(self.env.context)
    #         grade_ids = []
    #         if table_data:          
    #             for data in table_data:
    #                 grade_ids.append(data[1])
    #         print(grade_ids)
    #         grade_ids = self.env["lerm.grade.line"].search([("id","in",grade_ids)])
    #         print(grade_ids)
    #         rec.grade_ids = grade_ids
            
                

class ProductGradeWizard(models.TransientModel):
    _name = 'product.grade.wizard'
    _description = 'Product Grade Wizard'

    product_id = fields.Many2one('product.template', string="Product")
    grade = fields.Many2one("lerm.grade.line", string="Grade")
    main_report_template = fields.Many2one('ir.actions.report', string="Main Report Template")
    datasheet_report_template = fields.Many2one('ir.actions.report', string="DataSheet Report Template")
    ir_model = fields.Many2one('ir.model', string="Model")

    def add_grade_line(self):
        product_template = self.product_id
        grade_line_data = {
            'product_id': product_template.id,
            'grade': self.grade.id,
            'main_report_template': self.main_report_template.id,
            'datasheet_report_template': self.datasheet_report_template.id,
            'ir_model': self.ir_model.id,
        }
        product_template.write({'grade_ids': [(0, 0, grade_line_data)]})
        return {'type': 'ir.actions.act_window_close'}      


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_open_product_grade_wizard(self):
        wizard_action = self.env.ref('lerm_civil.action_product_grade_wizard')
        return {
            'name': 'Add Grade Line',
            'type': 'ir.actions.act_window',
            'res_model': 'product.grade.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_product': self.id},
        }
    

class AccountMoveLineInherited(models.Model):
    _inherit = 'account.move.line'
    report_no = fields.Char(string="Report No")
    pricelist_id = fields.Many2one("product.pricelist",string="Pricelist",compute='_compute_pricelist')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    # report_ids = fields.Many2many("lerm.srf.sample",compute="_compute_report_ids")
    report_no1 = fields.Many2many("lerm.srf.sample", string="KES No.",domain="['&',('state', '=', '4-in_report'),('invoice_status', '!=', '2-invoiced'),'|',('srf_id.customer', '=', partner_id),('srf_id.billing_customer', '=', partner_id)]")


    @api.onchange('partner_id')
    def _compute_report_ids(self):
        report_ids = []
        samples = self.env['lerm.srf.sample'].sudo().search([('state', '=', '4-in_report'),('invoice_status', '!=', '2-invoiced')])
        # for sample in samples:
        #     if sample.srf_id.billing_customer.id == self.partner_id.id:
        #         report_ids.append(sample)
        # import wdb; wdb.set_trace();
        # self.report_ids = samples
        

                


    
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
