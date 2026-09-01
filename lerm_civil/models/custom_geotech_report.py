from odoo import models,api
from odoo.modules.module import get_module_resource
import base64



# class SrfReport(models.AbstractModel):
#     _name = 'report.lerm_civil.custom_geotech_report'
#     _description = 'SRF Report'

#     @api.model
#     def _get_report_values(self, docids, data=None):

#         srf = self.env['lerm.civil.srf'].sudo().browse(docids)

#         # ------------------ LOGO LOAD ------------------
#         logo_path = get_module_resource(
#             'lerm_civil', 'static/src/img', 'genstru_logo.png'
#         )

#         logo_base64 = False
#         if logo_path:
#             with open(logo_path, 'rb') as f:
#                 logo_base64 = base64.b64encode(f.read()).decode('utf-8')
#         # ------------------------------------------------

#         # Get samples of this SRF
#         samples = self.env['lerm.srf.sample'].search([
#             ('srf_id', 'in', srf.ids)
#         ])

#         # Get reviews of those samples
#         review = self.env['sample.request.review'].search([
#             ('sample_id', 'in', samples.ids)
#         ])

#         return {
#             'doc_ids': docids,
#             'doc_model': 'lerm.civil.srf',
#             'srf': srf,
#             'samples': samples,
#             'review': review,

#             # 👇 LOGO FOR XML
#             'logo_base64': logo_base64,
#         }


# class SrfReport(models.AbstractModel):
#     _name = 'report.lerm_civil.custom_geotech_report'
#     _description = 'SRF Report'

#     @api.model
#     def _get_report_values(self, docids, data=None):

#         srf = self.env['lerm.civil.srf'].sudo().browse(docids)

#         # ---------- LOGO ----------
#         logo_path = get_module_resource(
#             'lerm_civil', 'static/src/img', 'genstru_logo.png'
#         )

#         logo_base64 = False
#         if logo_path:
#             with open(logo_path, 'rb') as f:
#                 logo_base64 = base64.b64encode(f.read()).decode('utf-8')
#         # --------------------------

#         # Samples of SRF
#         samples = self.env['lerm.srf.sample'].search([
#             ('srf_id', 'in', srf.ids)
#         ])

#         # Map: sample -> review
#         sample_review_map = {}
#         for sample in samples:
#             review = self.env['sample.request.review'].search([
#                 ('sample_id', '=', sample.id)
#             ], limit=1)
#             sample_review_map[sample.id] = review

#         return {
#             'doc_ids': docids,
#             'doc_model': 'lerm.civil.srf',
#             'srf': srf,
#             'samples': samples,
#             'sample_review_map': sample_review_map,
#             'logo_base64': logo_base64,
#         }

class SrfReport(models.AbstractModel):
    _name = 'report.lerm_civil.custom_geotech_report'
    _description = 'SRF Report'

    @api.model
    def _get_report_values(self, docids, data=None):

        srf = self.env['lerm.civil.srf'].sudo().browse(docids)

        # ---------------- LOGO ----------------
        logo_path = get_module_resource(
            'lerm_civil', 'static/src/img', 'genstru_logo.png'
        )

        logo_base64 = False
        if logo_path:
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')
        # -------------------------------------

        # SRF Samples
        samples = self.env['lerm.srf.sample'].search([
            ('srf_id', 'in', srf.ids)
        ])

        # Map sample -> latest review (avoid singleton error)
        sample_review_map = {}
        Review = self.env['sample.request.review']

        for sample in samples:
            review = Review.search(
                [('sample_id', '=', sample.id)],
                order='id desc',
                limit=1
            )
            sample_review_map[sample.id] = review

        return {
            'doc_ids': docids,
            'doc_model': 'lerm.civil.srf',
            'srf': srf,
            'samples': samples,
            'sample_review_map': sample_review_map,
            'logo_base64': logo_base64,
        }









class CustomGeotechReport(models.AbstractModel):
    _name = 'report.lerm_civil.rr_report'
    _description = 'Custom Geotech Report'

    def _get_report_values(self, docids, data=None):

        docs = self.env['sample.request.review'].browse(docids)

        logo_path = get_module_resource(
            'lerm_civil', 'static/src/img', 'genstru_logo.png'
        )

        logo_base64 = False
        if logo_path:
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')

        return {
            'docs': docs,
            'logo_base64': logo_base64,
        }