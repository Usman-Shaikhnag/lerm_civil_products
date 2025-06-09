from odoo import api, fields, models
from odoo.exceptions import UserError



class SampleRangeLine(models.Model):
    _name ='sample.range.line'

    # group_id = fields.Many2one('lerm_civil.group', string='Group', required=True)
    # discipline_id = fields.Many2one('lerm_civil.discipline', string='Discipline', related='group_id.discipline')
   

    # @api.depends('group_id.discipline.lab_no')
    # def _compute_lab_no(self):
    #     for record in self:
    #         lab_no = record.group_id.discipline.lab_no
    #         record.lab_no = lab_no


    srf_id = fields.Many2one('lerm.civil.srf' , string="SRF ID" )
    sample_range = fields.Char(string="Sample Range." ,required=True,readonly=True, default=lambda self: 'New')
    sample_qty = fields.Integer(string="Sample Quantity")
    casting = fields.Boolean(string="Casting")
    discipline_id = fields.Many2one('lerm_civil.discipline',string="Discipline")
    lab_no_value = fields.Char(string="Value")
    # lab_l_id = fields.Integer(string="Lab Location")
    # lab_l_id = fields.Many2one('lab.location', string="Lab Locations")
    group_id = fields.Many2one('lerm_civil.group',string="Group")
    # department_id = fields.Many2one('hr.department', string='Department')
    department_id = fields.Char(string='Department')
    material_id = fields.Many2one('product.template',string="Material")
    material_id_lab_name = fields.Char(string="Material",compute="compute_material_id_lab_name",store=True)
    brand = fields.Char(string="Brand")
    size_id = fields.Many2one('lerm.size.line',string="Size")
    grade_id = fields.Many2one('lerm.grade.line',string="Grade")
    received_by_id = fields.Many2one('res.partner',string="Received By")
    sample_received_date = fields.Date(string="Sample Received Date")
    sample_condition = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non_satisfactory', 'Non-Satisfactory'),
    ], string='Sample Condition', default='satisfactory')
    # technicians = fields.Many2one("res.users",string="Technicians")
    location = fields.Char(string="Location")
    sample_reject_reason = fields.Char(string="Sample Reject Reason")
    has_witness = fields.Boolean(string='Witness')
    witness = fields.Char(string="Witness Name")
    scope = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),
    ], string='Scope', default='nabl')
    sample_description = fields.Text(string="Sample Description")
    group_ids = fields.Many2many('lerm_civil.group',string="Group Ids")
    material_ids = fields.Many2many('product.template',string="Material Ids")
    size_ids = fields.Many2many('lerm.size.line',string="Size Ids")
    grade_ids = fields.Many2many('lerm.grade.line',string="Grade Ids")
    qty_ids = fields.Many2many('lerm.qty.line',string="Qty Ids")
    days_casting = fields.Selection([
        ('3', '3 Days'),
        ('7', '7 Days'),
        ('14', '14 Days'),
        ('21', '21 Days'),
        ('28', '28 Days'),
        ('56', '56 Days'),
        ('112', '112 Days'),
    ], string='Days of casting', default='3')
    customer_id = fields.Many2one('res.partner' , string="Customer")
    product_alias = fields.Many2one('product.product',string="Product Alias")
    parameters = fields.Many2many('lerm.parameter.master',string="Parameter")
    # parameters_ids = fields.Many2many('lerm.datasheet.line',string="Parameter" , compute="compute_param_ids")
    kes_range = fields.Char("KES Range",required=True,readonly=True, default=lambda self: 'New')
    casting_date = fields.Date(string="No. of days of test")
    days_casting = fields.Selection([
        ('3', '3 Days'),
        ('7', '7 Days'),
        ('14', '14 Days'),
        ('21', '21 Days'),
        ('28', '28 Days'),
        ('56', '56 Days'),
        ('112', '112 Days'),
    ], string='Days of casting', default='3')
    date_casting = fields.Date("Date of Casting")
    casting = fields.Boolean(string="Casting")
    client_sample_id = fields.Char(string="Client Sample Id")
    conformity = fields.Boolean(string='Conformity')
    volume = fields.Char(string="Volume")
    product_name = fields.Many2one('product.template',string="Product Name")
    main_name = fields.Char(string="Product Name")
    price = fields.Float(string="Price")

    
    status = fields.Selection([
        ('1-pending', 'Pending'),
        ('2-confirmed', 'Confirmed'),
    ], string='Status', default='1-pending')

    state = fields.Selection([
        ('1-allotment_pending', 'Assignment Pending'),
        ('2-alloted', 'Alloted'),
        ('3-in_report', 'In-Report'),
    ], string='State',default='1-allotment_pending')


    @api.depends('material_id')
    def compute_material_id_lab_name(self):
        for record in self:
            record.material_id_lab_name = record.material_id.lab_name



    