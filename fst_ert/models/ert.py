from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class LermErtParent(models.Model):
    _name = "lerm.ert.parent"
    _rec_name = "name"

    name = fields.Char("Project Name")
    ert_lines = fields.One2many('ert.lines', 'parent_id', "ERT Lines", copy=False)
    rec_date = fields.Date("Date")

    def create_ert(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ert.soil.resistivity',
            'target': 'current',
            'context': {
                'default_ert_parent_id': self.id
            }
        }

    def open_editor(self):
        self.ensure_one()
        frontend_base_url = "http://localhost:5173"
        url = f'{frontend_base_url}/report?id={self.id}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def print_report(self):
        report = self.env.ref('fst_ert.soil_resistivity_report_py3o1')
        filename = f"{self.name or 'ERT'}"
        return report.report_action(self, config={'report_name': filename})

    def copy_data(self, default=None):
        data = super().copy_data(default)[0]
        data['ert_lines'] = []
        return [data]

    def action_duplicate_parent(self):
        for record in self:
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'ert_lines': False,
            })
            for line in record.ert_lines:
                if line.soil_resistivity_id:
                    new_res = line.soil_resistivity_id.with_context(skip_auto_copy=True).copy({
                        'ert_parent_id': new_parent.id,
                        'name': f"{line.soil_resistivity_id.name} Copy",
                    })
                    self.env['ert.lines'].create({
                        'parent_id': new_parent.id,
                        'soil_resistivity_id': new_res.id,
                    })
                else:
                    self.env['ert.lines'].create({'parent_id': new_parent.id})
        return True


class LermErtLines(models.Model):
    _name = "ert.lines"

    parent_id = fields.Many2one('lerm.ert.parent', copy=False)
    soil_resistivity_id = fields.Many2one('ert.soil.resistivity', copy=False)

    def action_duplicate_ert(self):
        for record in self:
            if not record.soil_resistivity_id:
                raise UserError("No Borehole is linked to duplicate.")
            original_name = record.soil_resistivity_id.name
            new_borehole = record.soil_resistivity_id.copy({
                'name': f"{original_name} Copy",
                'ert_parent_id': record.parent_id.id,
            })
        return True

    def action_delete_line(self):
        for rec in self:
            rec.unlink()
