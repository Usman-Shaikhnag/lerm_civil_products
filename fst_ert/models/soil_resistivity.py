from odoo import api, fields, models
import math
import base64
import io
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

_logger = logging.getLogger(__name__)


class ErtSoilResistivity(models.Model):
    _name = "ert.soil.resistivity"
    _rec_name = "name"

    name = fields.Char("Name", required=True, readonly=True, default='New')
    ert_parent_id = fields.Many2one('lerm.ert.parent')
    graph_images = fields.One2many('ert.soil.resistivity.line', 'parent_id', string="Graphs")
    line_ids = fields.One2many('ert.soil.resistivity.line', 'parent_id', string="Resistivity Table")
    ert_point = fields.Char(string="ERT")
    factor_multiplied = fields.Float(string="Multiplication Factor")
    temperature_site = fields.Char(string="Temperature At Site")
    last_weather = fields.Char(string="Last 2 Days Weather")
    current = fields.Char(string="Current")
    voltage = fields.Char(string="Voltage")
    present_weather = fields.Char(string="Present Weather")
    pin_line_ids = fields.One2many('ert.soil.resistivity.pin.line', 'parent_id', string="Resistivity Table")
    ert_recommended = fields.Char(string="Recommended ERT")
    avg_equivalent_radius = fields.Float(string="Average Equivalent Radius")
    class_of_soil = fields.Char(string="Class Of Soil As Per IS 3043:2018")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ert.soil.resistivity.seq') or 'New'
        res = super(ErtSoilResistivity, self).create(vals)
        if not self._context.get('skip_auto_copy') and vals.get('ert_parent_id'):
            self.env['ert.lines'].create({
                'parent_id': vals['ert_parent_id'],
                'soil_resistivity_id': res.id,
            })
        return res

    def copy(self, default=None):
        if default is None:
            default = {}
        default['line_ids'] = []
        default['pin_line_ids'] = []
        return super(ErtSoilResistivity, self).copy(default)

    def save_ert(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'lerm.ert.parent',
            'target': 'current',
            'res_id': self.ert_parent_id.id,
        }

    def action_print_soil_resistivity_report(self):
        report = self.env.ref('fst_ert.soil_resistivity_report_single_py3o')
        return report.report_action(self)

    def button_add_footer(self):
        for record in self:
            if not record.line_ids:
                raise models.ValidationError("No lines to compute average.")
            for line in record.line_ids:
                resistivities = [
                    line.resistivity_n, line.resistivity_ne, line.resistivity_e,
                    line.resistivity_se, line.resistivity_s, line.resistivity_sw,
                    line.resistivity_w, line.resistivity_nw,
                ]
                valid = [r for r in resistivities if r and r > 0]
                if not valid:
                    continue
                n_dir = len(valid)

                def spacing_from_n2(corrected, n1_field, field_name):
                    for rec in record.line_ids:
                        n1_val = getattr(rec, n1_field, None)
                        if n1_val and n1_val > 0:
                            r2 = corrected
                            s = r2 / (2 * math.pi * n1_val)
                            return s
                    return None

                readings = []
                for i, (r_val, n1_field) in enumerate(zip(valid, [
                    'resistivity_n1', 'resistivity_ne1', 'resistivity_e1',
                    'resistivity_se1', 'resistivity_s1', 'resistivity_sw1',
                    'resistivity_w1', 'resistivity_nw1'
                ])):
                    avg_n2 = r_val
                    n1 = getattr(line, n1_field, None)
                    if n1 and n1 > 0:
                        spacing_val = avg_n2 / (2 * math.pi * n1)
                        readings.append(spacing_val)

                if readings:
                    avg_spacing = sum(readings) / len(readings)
                    avg_resistivity = sum(valid) / n_dir
                    r = avg_resistivity
                    a = avg_spacing
                    equivalent_radius = a * (1 + (2 * a) / (math.sqrt(a**2 + (2 * a)**2) - 2 * a))
                    record.write({
                        'avg_equivalent_radius': equivalent_radius,
                        'ert_recommended': f"{avg_resistivity:.2f}",
                    })

    def action_copy_spacing_to_pin(self):
        for record in self:
            record.pin_line_ids.unlink()
            spacings = set()
            for line in record.line_ids:
                if line.spacing and line.spacing > 0:
                    spacings.add(line.spacing)
            pin_data = []
            for line in record.line_ids:
                resistivities = [
                    line.resistivity_n, line.resistivity_ne, line.resistivity_e,
                    line.resistivity_se, line.resistivity_s, line.resistivity_sw,
                    line.resistivity_w, line.resistivity_nw,
                ]
                valid = [r for r in resistivities if r and r > 0]
                if not valid:
                    continue
                n_dir = len(valid)
                avg_resistivity = sum(valid) / n_dir
                a = line.spacing or 1.0
                equivalent_radius = a * (1 + (2 * a) / (math.sqrt(a**2 + (2 * a)**2) - 2 * a))
                pin_data.append((0, 0, {
                    'pin_spacing': a,
                    'equivalent_radius': equivalent_radius,
                }))
            for pd in pin_data:
                record.write({'pin_line_ids': [(0, 0, pd[2])]})

            pin_radii = [p.equivalent_radius for p in record.pin_line_ids if p.equivalent_radius]
            if pin_radii:
                avg_eq_radius = sum(pin_radii) / len(pin_radii)
                record.avg_equivalent_radius = avg_eq_radius
                if avg_eq_radius < 25:
                    record.class_of_soil = "Severely Corrosive"
                elif 25 <= avg_eq_radius < 50:
                    record.class_of_soil = "Moderately Corrosive"
                elif 50 <= avg_eq_radius <= 100:
                    record.class_of_soil = "Mildly Corrosive"
                else:
                    record.class_of_soil = "Very Mild Corrosive"

    def action_generate_graph(self):
        for record in self:
            if not record.line_ids:
                raise models.ValidationError("Add lines before generating graphs.")
            max_resistivity = 0
            for line in record.line_ids:
                resistivities = [
                    line.resistivity_n, line.resistivity_ne, line.resistivity_e,
                    line.resistivity_se, line.resistivity_s, line.resistivity_sw,
                    line.resistivity_w, line.resistivity_nw,
                ]
                valid = [r for r in resistivities if r is not None]
                if valid:
                    max_resistivity = max(max_resistivity, max(valid))
            ymax = math.ceil(max_resistivity / 10) * 10 if max_resistivity else 100
            for line in record.line_ids:
                line.action_generate_graph(ymax)


class ErtSoilResistivityLine(models.Model):
    _name = "ert.soil.resistivity.line"
    _order = "sr_no asc"

    parent_id = fields.Many2one('ert.soil.resistivity', string="Test Point")
    sr_no = fields.Integer("Sr. No")
    spacing = fields.Float("Pin Spacing (m)")
    resistivity_n1 = fields.Float("Site Reading N")
    resistivity_ne1 = fields.Float("Site Reading NE")
    resistivity_e1 = fields.Float("Site Reading E")
    resistivity_se1 = fields.Float("Site Reading SE")
    resistivity_s1 = fields.Float("Site Reading S")
    resistivity_sw1 = fields.Float("Site Reading SW")
    resistivity_w1 = fields.Float("Site Reading W")
    resistivity_nw1 = fields.Float("Site Reading NW")
    resistivity_n2 = fields.Float("Corrected N")
    resistivity_ne2 = fields.Float("Corrected NE")
    resistivity_e2 = fields.Float("Corrected E")
    resistivity_se2 = fields.Float("Corrected SE")
    resistivity_s2 = fields.Float("Corrected S")
    resistivity_sw2 = fields.Float("Corrected SW")
    resistivity_w2 = fields.Float("Corrected W")
    resistivity_nw2 = fields.Float("Corrected NW")
    resistivity_n = fields.Float("N Resistivity", compute="_compute_resistivity_n", store=True)
    resistivity_ne = fields.Float("NE Resistivity", compute="_compute_resistivity_ne", store=True)
    resistivity_e = fields.Float("E Resistivity", compute="_compute_resistivity_e", store=True)
    resistivity_se = fields.Float("SE Resistivity", compute="_compute_resistivity_se", store=True)
    resistivity_s = fields.Float("S Resistivity", compute="_compute_resistivity_s", store=True)
    resistivity_sw = fields.Float("SW Resistivity", compute="_compute_resistivity_sw", store=True)
    resistivity_w = fields.Float("W Resistivity", compute="_compute_resistivity_w", store=True)
    resistivity_nw = fields.Float("NW Resistivity", compute="_compute_resistivity_nw", store=True)
    area = fields.Float("Area", compute="_compute_area", store=True)
    radius = fields.Float("Equivalent Radius", compute="_compute_radius", store=True)
    sr_no_label = fields.Char("Sr No Label")
    graph_image = fields.Binary("Graph")

    @api.depends('spacing', 'resistivity_n2', 'resistivity_n1')
    def _compute_resistivity_n(self):
        for rec in self:
            n2 = rec.resistivity_n2 or rec.resistivity_n1
            if n2 and rec.spacing:
                rec.resistivity_n = 2 * math.pi * rec.spacing * n2
            else:
                rec.resistivity_n = 0

    @api.depends('spacing', 'resistivity_ne2', 'resistivity_ne1')
    def _compute_resistivity_ne(self):
        for rec in self:
            n2 = rec.resistivity_ne2 or rec.resistivity_ne1
            if n2 and rec.spacing:
                rec.resistivity_ne = 2 * math.pi * rec.spacing * n2
            else:
                rec.resistivity_ne = 0

    @api.depends('spacing', 'resistivity_e2', 'resistivity_e1')
    def _compute_resistivity_e(self):
        for rec in self:
            n2 = rec.resistivity_e2 or rec.resistivity_e1
            if n2 and rec.spacing:
                rec.resistivity_e = 2 * math.pi * rec.spacing * n2
            else:
                rec.resistivity_e = 0

    @api.depends('spacing', 'resistivity_se2', 'resistivity_se1')
    def _compute_resistivity_se(self):
        for rec in self:
            n2 = rec.resistivity_se2 or rec.resistivity_se1
            if n2 and rec.spacing:
                rec.resistivity_se = 2 * math.pi * rec.spacing * n2
            else:
                rec.resistivity_se = 0

    @api.depends('spacing', 'resistivity_s2', 'resistivity_s1')
    def _compute_resistivity_s(self):
        for rec in self:
            n2 = rec.resistivity_s2 or rec.resistivity_s1
            if n2 and rec.spacing:
                rec.resistivity_s = 2 * math.pi * rec.spacing * n2
            else:
                rec.resistivity_s = 0

    @api.depends('spacing', 'resistivity_sw2', 'resistivity_sw1')
    def _compute_resistivity_sw(self):
        for rec in self:
            n2 = rec.resistivity_sw2 or rec.resistivity_sw1
            if n2 and rec.spacing:
                rec.resistivity_sw = 2 * math.pi * rec.spacing * n2
            else:
                rec.resistivity_sw = 0

    @api.depends('spacing', 'resistivity_w2', 'resistivity_w1')
    def _compute_resistivity_w(self):
        for rec in self:
            n2 = rec.resistivity_w2 or rec.resistivity_w1
            if n2 and rec.spacing:
                rec.resistivity_w = 2 * math.pi * rec.spacing * n2
            else:
                rec.resistivity_w = 0

    @api.depends('spacing', 'resistivity_nw2', 'resistivity_nw1')
    def _compute_resistivity_nw(self):
        for rec in self:
            n2 = rec.resistivity_nw2 or rec.resistivity_nw1
            if n2 and rec.spacing:
                rec.resistivity_nw = 2 * math.pi * rec.spacing * n2
            else:
                rec.resistivity_nw = 0

    @api.depends('resistivity_n', 'resistivity_ne', 'resistivity_e', 'resistivity_se',
                 'resistivity_s', 'resistivity_sw', 'resistivity_w', 'resistivity_nw')
    def _compute_area(self):
        for rec in self:
            values = [
                rec.resistivity_n, rec.resistivity_ne, rec.resistivity_e,
                rec.resistivity_se, rec.resistivity_s, rec.resistivity_sw,
                rec.resistivity_w, rec.resistivity_nw
            ]
            if all(v and v > 0 for v in values):
                angles = np.linspace(0, 2 * np.pi, len(values), endpoint=False)
                x = values * np.cos(angles)
                y = values * np.sin(angles)
                rec.area = 0.5 * abs(sum(x[i] * y[i + 1] - x[i + 1] * y[i] for i in range(-1, len(x) - 1)))
            else:
                rec.area = 0

    @api.depends('area')
    def _compute_radius(self):
        for rec in self:
            if rec.area:
                rec.radius = math.sqrt(rec.area / math.pi)
            else:
                rec.radius = 0

    @api.model
    def create(self, vals):
        if not vals.get('sr_no'):
            last = self.search([('parent_id', '=', vals.get('parent_id'))], order='sr_no desc', limit=1)
            vals['sr_no'] = (last.sr_no or 0) + 1
        return super(ErtSoilResistivityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        lines = self.search([('parent_id', '=', self.parent_id.id)], order='sr_no asc')
        for idx, line in enumerate(lines, start=1):
            line.sr_no = idx

    def action_generate_graph(self, ymax=None):
        self.ensure_one()
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        field_map = {
            'N': 'resistivity_n', 'NE': 'resistivity_ne', 'E': 'resistivity_e',
            'SE': 'resistivity_se', 'S': 'resistivity_s', 'SW': 'resistivity_sw',
            'W': 'resistivity_w', 'NW': 'resistivity_nw',
        }
        values = [getattr(self, field_map[d], 0) or 0 for d in directions]

        angles = np.linspace(0, 2 * np.pi, len(directions), endpoint=False).tolist()
        values_closed = values + [values[0]]
        angles_closed = angles + [angles[0]]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.fill(angles_closed, values_closed, alpha=0.25, color='#4b0082')
        ax.plot(angles_closed, values_closed, color='#4b0082', linewidth=2, marker='o', markersize=6)

        ax.set_xticks(angles)
        ax.set_xticklabels(directions, fontsize=12, fontweight='bold')
        ax.set_ylim(0, ymax or (max(values) * 1.2 if max(values) else 100))
        ax.yaxis.set_major_locator(plt.MaxNLocator(5))
        ax.grid(True, linestyle='--', alpha=0.6)

        avg_val = sum(values) / len(values) if values else 0
        ax.plot(angles_closed, [avg_val] * len(angles_closed),
                color='red', linewidth=1.5, linestyle='--', label=f'Avg: {avg_val:.1f}')
        ax.legend(loc='upper right', fontsize=10)

        area = self.area
        eq_radius = self.radius
        ax.set_title(f'Sr. No: {self.sr_no}\nArea: {area:.2f} m²  Radius: {eq_radius:.2f} m',
                     fontsize=12, fontweight='bold', pad=20)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        self.graph_image = base64.b64encode(buf.getvalue())


class ErtSoilResistivityPinLine(models.Model):
    _name = "ert.soil.resistivity.pin.line"

    parent_id = fields.Many2one('ert.soil.resistivity', string="Test Point")
    pin_spacing = fields.Float("Pin Spacing (m)")
    equivalent_radius = fields.Float("Equivalent Radius")
