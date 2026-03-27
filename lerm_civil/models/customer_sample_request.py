from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError


class CustomerSampleRequests(models.Model):
    _name = 'customer.sample.requests'

    partner_id = fields.Many2one('res.partner')
    project = fields.Many2one('res.partner.project',string="Name of Work")
    date = fields.Date('Date')
    billing_customer = fields.Many2one('res.partner')
    samples = fields.One2many('customer.sample.line','csr_id',string="Samples")
    attachment = fields.Binary("Attachment")
    attachment_name = fields.Char("Attachent Name")

    state = fields.Selection([
        ('draft', "Draft"),
        ('confirmed', "Confirmed"),
    ], default='draft', string="State")

    def confirm_sample_request(self):
        for record in self:
            
            
            srf = record.env['lerm.civil.srf'].sudo().create({
                'customer':record.partner_id.id,
                'srf_date':record.date,
                'name_work':record.project.id,
                'billing_customer':record.billing_customer.id,
                'customer_portal_request':record.id,
                'attachment':record.attachment,
                'attachment_name':record.attachment_name
            })
            srf_id = srf.id
            sample_records = record.samples
            samples = []
            
            sample_range_id = None
            for sam1 in sample_records:
                sample_range = self.env['sample.range.line'].sudo().create({
                    'srf_id':srf_id,
                    'discipline_id':sam1.discipline_id.id,
                    'group_id':sam1.group_id.id,
                    'material_id':sam1.product_id.id,
                    'grade_id':sam1.grade_id.id,
                    'size_id':sam1.size_id.id,
                    'parameters':sam1.parameters
                })
                sample_range_id = sample_range.id
                break
            for sam in sample_records:
                sample = {
                'srf_id':srf_id,
                'discipline_id':sam.discipline_id.id,
                'group_id':sam.group_id.id,
                'material_id':sam.product_id.id,
                'grade_id':sam.grade_id.id,
                'size_id':sam.size_id.id,
                'parameters':sam.parameters,
                'customer_id':record.partner_id.id,
                'customer_portal_sample':sam.id,
                'sample_range_id':sample_range_id
                }
                samples.append((0, 0, sample))
            # import wdb; wdb.set_trace()
            srf.sudo().write({
                'samples':samples
                # 'sample_range_table':samples
                

            })
            record.state = 'confirmed'



    def reset_draft(self):
        self.state = 'draft'
class CustomerSampleLines(models.Model):
    _name = 'customer.sample.line'

    csr_id = fields.Many2one('customer.sample.requests')
    discipline_id = fields.Many2one('lerm_civil.discipline',string="Discipline")
    group_id = fields.Many2one('lerm_civil.group',string="Group")
    product_id = fields.Many2one("product.template")
    product_description = fields.Text("Product Description")
    grade_id = fields.Many2one('lerm.grade.line',string="Grade")
    size_id = fields.Many2one('lerm.size.line',string="Size")
    parameters = fields.Many2many('lerm.parameter.master',string="Parameter")

    # state = fields.Selection([
    #     ('1-allotment_pending', 'Assignment Pending'),
    #     ('2-alloted', 'Alloted'),
    #     ('3-pending_verification','Pending Verification'),
    #     ('5-pending_approval','Pending Approval'),
    #     ('4-in_report', 'In-Report'),
    #     ('6-cancelled', 'Cancelled'),
    # ], string='State',default='1-allotment_pending')

class LermPortalUserMaster(models.Model):
    _name = 'portal.user.master'

    customer = fields.Many2one('res.partner')

    child_users = fields.One2many('child.user.master','parent_id',string="Related Customers")

class LermChildPortalUserMaster(models.Model):
    _name = 'child.user.master'

    parent_id = fields.Many2one('portal.user.master')

    partner_id = fields.Many2one('res.partner')