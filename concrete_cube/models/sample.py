from odoo import models


class LermSrfSample(models.Model):
    _inherit = 'lerm.srf.sample'

    def _is_cube_report_sample(self, eln):
        try:
            if eln.is_product_based_calculation:
                template_name = eln.material.product_based_calculation[0].main_report_template.report_name
            else:
                template_name = eln.parameters_result.parameter[0].main_report_template.report_name
            return template_name == 'concrete_cube.compresive_concrete_cube_report'
        except Exception:
            return False

    def _open_cube_report_wizard(self, nabl):
        eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', self.id)], limit=1)
        if eln and self._is_cube_report_sample(eln):
            return {
                'name': 'Cube Compressive Report',
                'type': 'ir.actions.act_window',
                'res_model': 'cube.report.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_sample_id': self.id,
                    'default_nabl': nabl,
                },
            }
        if nabl:
            return super(LermSrfSample, self).print_nabl_report()
        return super(LermSrfSample, self).print_non_nabl_report()

    def print_nabl_report(self):
        return self._open_cube_report_wizard(True)

    def print_non_nabl_report(self):
        return self._open_cube_report_wizard(False)
