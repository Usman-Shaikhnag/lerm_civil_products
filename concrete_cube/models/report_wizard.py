from odoo import fields, models


class CubeReportWizard(models.TransientModel):
    _name = 'cube.report.wizard'
    _description = 'Cube Compressive Report Wizard'

    sample_id = fields.Many2one('lerm.srf.sample', string="Sample")
    nabl = fields.Boolean(string="NABL Report", default=True)
    sector_type = fields.Selection([
        ('govt', 'Govt'),
        ('non_govt', 'Non Govt'),
        ('normal', 'Normal'),
    ], string="Sector", default='non_govt', required=True)

    def print_report(self):
        sample = self.sample_id
        eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', sample.id)], limit=1)
        if eln.is_product_based_calculation:
            template_name = eln.material.product_based_calculation[0].main_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].main_report_template.report_name
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': template_name,
            'report_file': template_name,
            'data': {
                'sample': sample.id,
                'nabl': self.nabl,
                'fromEln': False,
                'report_wizard': True,
                'sector_type': self.sector_type,
            },
        }
