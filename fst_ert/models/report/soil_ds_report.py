from odoo import api, models


class SoilResistivityReport(models.AbstractModel):
    _name = "report.fst.soil_resistivity"
    _description = "Soil Resistivity Report (Py3o)"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env["ert.soil.resistivity"].browse(docids)
        return {
            "objects": records,
        }
