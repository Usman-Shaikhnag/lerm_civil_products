from odoo import api, models


class LateralPileLoadReport(models.AbstractModel):
    _name = 'report.fst_lateral_pile_load.lateral_pile_load_template'
    _description = 'Lateral Pile Load Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['fst.lateral.pile.load.test'].browse(docids)

        header_image = False
        for rec in docs:
            lab = rec.lab_id.sudo() if rec.lab_id else False
            if not lab or not lab.header_image:
                lab = self.env['lerm.lab.master'].sudo().search([], limit=1)
            if lab and lab.header_image:
                header_image = 'data:image/png;base64,' + lab.header_image.decode('utf-8')
                break

        first = docs[:1]
        return {
            'doc_ids': docs.ids,
            'doc_model': 'fst.lateral.pile.load.test',
            'docs': docs,
            'header_image': header_image,
            'report_no': first.report_no,
            'report_date': first.rec_date_str,
            'ulr': first.ulr,
        }
