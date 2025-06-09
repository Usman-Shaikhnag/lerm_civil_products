from odoo import models, fields ,api

class LabMaster(models.Model):
    _name = 'lerm.lab.master'
    _rec_name = 'lab_name'


    lab_name = fields.Char("Lab Name")
    lab_location = fields.Char("Lab Location")
    lab_certificate_no = fields.Char('Lab Certificate No')
    upi_id = fields.Char("UPI Id")
    ulr_sequence = fields.Many2one('ir.sequence')

    gst = fields.Char("GST")
    street = fields.Char("Street1")
    street2 = fields.Char("Street2")
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state',string="State")
    zip = fields.Char("ZIP")
    country_id = fields.Many2one('res.country',string="Country")

    header_image = fields.Binary('NABL Header Image')
    header_filename = fields.Char("Header FileName")

    non_nabl_header = fields.Binary('Non NABL Header Image')
    non_nabl_header_filename = fields.Char("Header FileName")

    watermark_image = fields.Binary('Watermark Image')
    watermark_filename = fields.Char("Watermark filename")

    footer_image = fields.Binary('Footer Image')
    footer_filename = fields.Char("Footer filename")

    lab_location_line = fields.One2many('lerm.lab.location.master','parent_id',string="Lab Location")








class LabLocationMaster(models.Model):
    _name = 'lerm.lab.location.master'
    _rec_name = 'location_name'

    parent_id = fields.Many2one('lerm.lab.master')
    location_name = fields.Char("Location Name")
    location_code = fields.Char("Location Code")