from odoo import api, fields, models
from odoo.exceptions import UserError



class ProductGradeWizard(models.TransientModel):
    _name = 'product.grade.wizard'
    _description = 'Product Grade Wizard'

    product_id = fields.Many2one('product.template', string="Product")
    product_product = fields.Many2one('product.product', string="Product")
    product_template_visible = fields.Boolean("Product visible",compute="_compute_visible")
    product_product_visible = fields.Boolean("Product visible",compute="_compute_visible")

    grade = fields.Many2one("lerm.grade.line", string="Grade")
    grade_ids = fields.Many2many("lerm.grade.line", string="Grade",compute="compute_grade_table")
    main_report_template = fields.Many2one('ir.actions.report', string="Main Report Template")
    datasheet_report_template = fields.Many2one('ir.actions.report', string="DataSheet Report Template")
    ir_model = fields.Many2one('ir.model', string="Model")


    @api.depends('product_id','product_id.grade_table')
    def compute_grade_table(self):
        for rec in self:
            # active_id = self.env.context.get("active_id")
            # product = self.env["product.template"].search([("id","=",active_id)])
            # print("grades",product.grade_table)
            # grade_ids = []
            # for grade in product.grade_table:
            #     grade_ids.append(grade)
            # print("Grade",grade_ids)
            # rec.grade_ids = grade_ids
            
            if rec.product_id:
                grade_ids = rec.product_id.grade_table.ids
                rec.grade_ids = [(6, 0, grade_ids)]
            elif rec.product_product:
                grade_ids = rec.product_product.grade_table.ids
                rec.grade_ids = [(6, 0, grade_ids)]
            else:
                rec.grade_ids = []
    

    @api.depends('product_id','product_product')
    def _compute_visible(self):
        for rec in self:
            # import wdb; wdb.set_trace();

            if len(rec.product_id) > 0:
                rec.product_template_visible = True
                rec.product_product_visible = False

            elif len(rec.product_product) > 0:
                rec.product_template_visible = False
                rec.product_product_visible = True

            else:
                rec.product_template_visible = False
                rec.product_product_visible = True



    def add_grade_line(self):
        product_template = self.product_id
        product_product = self.product_product

        grade_line_data = {
            'product_id': product_template.id,
            # 'product_product': product_product.id,

            'grade': self.grade.id,
            'main_report_template': self.main_report_template.id,
            'datasheet_report_template': self.datasheet_report_template.id,
            'ir_model': self.ir_model.id,
        }
        product_template.write({'product_based_calculation': [(0, 0, grade_line_data)]})
        return {'type': 'ir.actions.act_window_close'}