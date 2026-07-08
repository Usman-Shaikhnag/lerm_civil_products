from odoo import api, fields, models
from datetime import timedelta
import base64
import io
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class RoutineVpltTest(models.Model):
    _name = "routine.vplt.test"
    _description = "Routine Vertical Pile Load Test Report"
    _order = "rec_date desc, id desc"

    name = fields.Char("Project Name", required=True)
    rec_date = fields.Date("Report Date")
    work_name = fields.Char("Name of Work")
    client = fields.Char("Client")
    contractor = fields.Char("Contractor")

    ulr = fields.Char("ULR No", copy=False, readonly=True)
    report_no = fields.Char("Report No", copy=False, readonly=True)
    pile_no = fields.Char("Pile No")
    site_location = fields.Char("Site Location")
    test_standard = fields.Char("Test Standard")
    test_equipment = fields.Text("Testing Equipment")
    introduction = fields.Text("Introduction")
    objective = fields.Text("Objective")
    test_procedure = fields.Text("Test Procedure")

    allowable_capacity = fields.Float("Allowable Capacity")
    interpretation = fields.Text("Interpretation")
    conclusion = fields.Text("Conclusion")

    signatory_name = fields.Char("Authorized Signatory")
    signatory_designation = fields.Char("Designation")

    pile_diameter = fields.Float("Diameter of Pile (mm)")
    safe_load = fields.Float("Estimated Safe Load (Tonne)")
    test_load = fields.Float("Test Load (Tonne)")

    rec_date_str = fields.Char(
        "Report Date (Text)",
        compute="_compute_rec_date_str",
        store=True
    )

    loading_reading_ids = fields.One2many(
        "routine.vplt.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    unloading_reading_ids = fields.One2many(
        "routine.vplt.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )

    loading_mean_ids = fields.One2many(
        "routine.vplt.loading.mean",
        "parent_id",
        string="Loading Means",
        copy=False
    )

    unloading_mean_ids = fields.One2many(
        "routine.vplt.unloading.mean",
        "parent_id",
        string="Unloading Means",
        copy=False
    )

    content_ids = fields.One2many(
        "routine.vplt.report.content",
        "parent_id",
        string="Contents",
        copy=False
    )

    basic_data_ids = fields.One2many(
        "routine.vplt.basic.data",
        "parent_id",
        string="Basic Data",
        copy=False
    )

    site_image_ids = fields.One2many(
        "routine.vplt.image",
        "parent_id",
        string="Site Photographs",
        copy=False
    )

    graph_image = fields.Binary("Load Settlement Graph")

    gross_settlement = fields.Float(
        compute="_compute_settlement_values", store=True
    )
    net_settlement = fields.Float(
        compute="_compute_settlement_values", store=True
    )
    rebound = fields.Float(
        compute="_compute_settlement_values", store=True
    )
    percent_rebound = fields.Float(
        "% Rebound",
        compute="_compute_percent_rebound",
        store=True
    )

    max_settlement = fields.Float(
        "Maximum Settlement",
        compute="_compute_max_settlement",
        store=True,
        readonly=True
    )

    two_percent_dia = fields.Float(
        "2% of Diameter (mm)",
        compute="_compute_two_percent_dia",
        store=True
    )

    criterion_18_or_12 = fields.Float(
        "Criterion (12 or 18 mm)",
        compute="_compute_criterion",
        store=True
    )

    settlement_15mm_interpolated = fields.Float(
        "Interpolated Load at 15mm (Tonne)",
        compute="_compute_interpolated_loads",
        store=True
    )

    settlement_18mm_interpolated = fields.Float(
        "Interpolated Load at 18mm (Tonne)",
        compute="_compute_interpolated_loads",
        store=True
    )

    min_a_b = fields.Float(
        "Min A,B (mm)",
        compute="_compute_min_ab",
        store=True
    )

    analysis_text = fields.Text("Analysis of Test Results")

    @api.depends('rec_date')
    def _compute_rec_date_str(self):
        for rec in self:
            if rec.rec_date:
                rec.rec_date_str = rec.rec_date.strftime("%d-%m-%Y")
            else:
                rec.rec_date_str = False

    @api.depends('pile_diameter')
    def _compute_two_percent_dia(self):
        for rec in self:
            if rec.pile_diameter:
                rec.two_percent_dia = round(rec.pile_diameter * 0.02, 2)
            else:
                rec.two_percent_dia = 0.0

    @api.depends('pile_diameter')
    def _compute_criterion(self):
        for rec in self:
            if rec.pile_diameter:
                if rec.pile_diameter <= 600:
                    rec.criterion_18_or_12 = 12.0
                else:
                    rec.criterion_18_or_12 = 18.0
            else:
                rec.criterion_18_or_12 = 0.0

    @api.depends('gross_settlement', 'test_load', 'two_percent_dia', 'criterion_18_or_12')
    def _compute_interpolated_loads(self):
        for rec in self:
            if rec.gross_settlement and rec.test_load and rec.gross_settlement > 0:
                slope = rec.test_load / rec.gross_settlement
                rec.settlement_15mm_interpolated = round(15.0 * slope, 2)
                rec.settlement_18mm_interpolated = round(18.0 * slope, 2)
            else:
                rec.settlement_15mm_interpolated = 0.0
                rec.settlement_18mm_interpolated = 0.0

    @api.depends('gross_settlement', 'two_percent_dia', 'criterion_18_or_12')
    def _compute_min_ab(self):
        for rec in self:
            if rec.two_percent_dia and rec.criterion_18_or_12:
                rec.min_a_b = min(rec.two_percent_dia, rec.criterion_18_or_12)
            elif rec.two_percent_dia:
                rec.min_a_b = rec.two_percent_dia
            else:
                rec.min_a_b = rec.criterion_18_or_12

    @api.depends('rebound', 'gross_settlement')
    def _compute_percent_rebound(self):
        for rec in self:
            if rec.gross_settlement and rec.gross_settlement > 0:
                rec.percent_rebound = round(
                    (rec.rebound / rec.gross_settlement) * 100, 2
                )
            else:
                rec.percent_rebound = 0.0

    def action_generate_report_no(self):
        for rec in self:
            if not rec.report_no:
                rec.report_no = self.env['ir.sequence'].next_by_code(
                    'lerm.srf.sample.kes'
                )

    def action_generate_ulr_no(self):
        for rec in self:
            if rec.ulr:
                return

            lab = self.env['lerm.lab.master'].search([], limit=1)
            if not lab:
                return

            year = fields.Date.today().strftime('%y')

            cert = (lab.lab_certificate_no or '').split('(')[0]
            loc = (lab.lab_location_line[:1].location_code or '').split('(')[0]

            seq_raw = self.env['ir.sequence'].next_by_code(
                lab.ulr_sequence.code
            )

            import re
            match = re.search(r'(\d+F?)$', seq_raw)
            seq = match.group(1) if match else ''

            rec.ulr = f"{cert}{year}{loc}{seq}"

    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_max_settlement(self):
        for rec in self:
            values = (
                rec.loading_reading_ids.mapped('mean_mm') +
                rec.unloading_reading_ids.mapped('mean_mm')
            )
            rec.max_settlement = max(values) if values else 0.0

    @api.depends('loading_mean_ids.loading_mean', 'unloading_mean_ids.unloading_mean')
    def _compute_settlement_values(self):
        for rec in self:
            loading_map = {}
            for r in rec.loading_mean_ids:
                loading_map[r.load_value_tonne] = r.loading_mean

            if loading_map:
                gross = max(loading_map.values())
                first_load = min(loading_map.keys())
            else:
                loading_map_raw = {}
                for r in rec.loading_reading_ids:
                    loading_map_raw[r.load_tonne] = r.mean_mm
                if loading_map_raw:
                    gross = max(loading_map_raw.values())
                    first_load = min(loading_map_raw.keys())
                else:
                    gross = 0.0
                    first_load = 0.0

            rebound_lines = rec.unloading_mean_ids.filtered(
                lambda r: r.load_value_tonne == first_load
            )
            if not rebound_lines:
                rebound_lines = rec.unloading_reading_ids.filtered(
                    lambda r: r.load_tonne == first_load
                )

            rebound = rebound_lines[-1].unloading_mean if rebound_lines else 0.0
            if not rebound_lines and rec.unloading_reading_ids:
                rebound = rec.unloading_reading_ids[-1].mean_mm if rec.unloading_reading_ids else 0.0

            net = gross - rebound

            rec.gross_settlement = round(gross, 2)
            rec.rebound = round(rebound, 2)
            rec.net_settlement = round(net, 2)

    def action_generate_graph(self):
        self.ensure_one()

        loading_data = [(r.load_value_tonne, r.loading_mean) for r in self.loading_mean_ids]
        unloading_data = [(r.load_value_tonne, r.unloading_mean) for r in self.unloading_mean_ids]

        if not loading_data:
            loading_data = [(r.load_tonne, r.mean_mm) for r in self.loading_reading_ids]
            loading_data = list(dict(sorted(loading_data)).items())

        if not loading_data and not unloading_data:
            self.graph_image = False
            return

        fig, ax = plt.subplots(figsize=(7.5, 5.5))

        if loading_data:
            load_vals = [l for l, m in loading_data]
            settle_vals = [m for l, m in loading_data]

            ax.plot(
                settle_vals, load_vals,
                marker='o', markersize=6, markeredgewidth=1.2,
                linewidth=1.8, label='Loading', zorder=3, clip_on=False
            )

        if unloading_data:
            load_vals = [l for l, m in unloading_data]
            settle_vals = [m for l, m in unloading_data]

            ax.plot(
                settle_vals, load_vals,
                marker='o', markersize=6, markeredgewidth=1.2,
                linestyle='--', linewidth=1.8, label='Unloading',
                zorder=3, clip_on=False
            )

        ax.set_xlabel("SETTLEMENT (MM)", fontsize=10, fontweight='bold')
        ax.set_ylabel("LOAD (TONNE)", fontsize=10, fontweight='bold')
        ax.set_title("LOAD - SETTLEMENT GRAPH", fontsize=12, fontweight='bold', pad=12)

        all_loads = [l for l, m in (loading_data + unloading_data)]
        y_max = max(all_loads) if all_loads else 20

        def load_major_step(max_load):
            if max_load < 20:
                return 2
            elif max_load <= 25:
                return 5
            elif max_load <= 80:
                return 10
            elif max_load <= 150:
                return 20
            elif max_load <= 400:
                return 50
            elif max_load <= 1000:
                return 100
            else:
                return 200

        major = load_major_step(y_max)
        minor = major / 5 if major >= 5 else major / 2

        ax.set_ylim(0, math.ceil(y_max / major) * major)
        ax.yaxis.set_major_locator(plt.MultipleLocator(major))
        ax.yaxis.set_minor_locator(plt.MultipleLocator(minor))

        all_means = [m for l, m in (loading_data + unloading_data)]
        x_max = max(all_means) if all_means else 1

        def settlement_major_step(x_max):
            if x_max <= 2:
                return 0.2
            elif x_max <= 5:
                return 0.5
            elif x_max <= 15:
                return 1
            elif x_max <= 30:
                return 2
            else:
                return 5

        major = settlement_major_step(x_max)
        minor = major / 5

        ax.set_xlim(0, math.ceil(x_max / major) * major)
        ax.xaxis.set_major_locator(plt.MultipleLocator(major))
        ax.xaxis.set_minor_locator(plt.MultipleLocator(minor))

        ax.grid(which='major', linestyle='-', linewidth=0.8, color='#d28b5c')
        ax.grid(which='minor', linestyle='-', linewidth=0.4, color='#f0c7a0')
        ax.legend(loc='lower right', frameon=False)

        buffer = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format='png', dpi=150)
        plt.close(fig)

        self.graph_image = base64.b64encode(buffer.getvalue())

    def action_recompute_all(self):
        for rec in self:
            for line in rec.loading_reading_ids:
                line._compute_mean()
                line._compute_split_dt()
            for line in rec.unloading_reading_ids:
                line._compute_mean()
                line._compute_split_dt()
            rec._compute_settlement_values()
            rec._compute_max_settlement()
            rec._compute_percent_rebound()

    def action_duplicate_parent(self):
        for record in self:
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'loading_reading_ids': False,
                'unloading_reading_ids': False,
                'loading_mean_ids': False,
                'unloading_mean_ids': False,
                'content_ids': False,
                'basic_data_ids': False,
                'site_image_ids': False,
                'graph_image': False,
            })

            for line in record.loading_reading_ids:
                line.copy({'parent_id': new_parent.id})
            for line in record.unloading_reading_ids:
                line.copy({'parent_id': new_parent.id})
            for line in record.loading_mean_ids:
                line.copy({'parent_id': new_parent.id})
            for line in record.unloading_mean_ids:
                line.copy({'parent_id': new_parent.id})
            for line in record.content_ids:
                line.copy({'parent_id': new_parent.id})
            for line in record.basic_data_ids:
                line.copy({'parent_id': new_parent.id})
            for line in record.site_image_ids:
                line.copy({'parent_id': new_parent.id})

            new_parent.action_recompute_all()

        return True

    def action_delete_line(self):
        self.unlink()

    last_reading_datetime = fields.Datetime(
        compute="_compute_last_reading_datetime",
        store=False, copy=False
    )

    @api.depends('loading_reading_ids.reading_datetime')
    def _compute_last_reading_datetime(self):
        for rec in self:
            dates = rec.loading_reading_ids.mapped('reading_datetime')
            dates = [d for d in dates if d]
            rec.last_reading_datetime = max(dates) if dates else False


class RoutineVpltReadingLoading(models.Model):
    _name = "routine.vplt.reading.loading"
    _description = "Pile Load Reading - Loading"
    _order = "id"

    parent_id = fields.Many2one(
        "routine.vplt.test", ondelete="cascade", required=True, index=True
    )

    reading_datetime = fields.Datetime("Date & Time", required=True)

    reading_date_str = fields.Char(
        "Date", compute="_compute_split_dt", store=True
    )

    reading_time_str = fields.Char(
        "Time", compute="_compute_split_dt", store=True
    )

    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    dial_c = fields.Float("Dial C (mm)")
    dial_d = fields.Float("Dial D (mm)")

    mean_mm = fields.Float(
        string="Mean (mm)",
        compute="_compute_mean",
        store=True,
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'reading_datetime' in fields_list and 'reading_datetime' not in res:
            res['reading_datetime'] = fields.Datetime.now()
        return res

    @api.onchange('parent_id')
    def _onchange_set_datetime(self):
        if self.parent_id:
            latest_datetime = None

            unsaved_lines = [
                r for r in self.parent_id.loading_reading_ids
                if r.reading_datetime and r != self
            ]

            if unsaved_lines:
                latest = max(unsaved_lines, key=lambda x: x.reading_datetime)
                latest_datetime = latest.reading_datetime
            else:
                saved_lines = self.search(
                    [('parent_id', '=', self.parent_id.id)],
                    order='id desc', limit=1
                )
                if saved_lines and saved_lines.reading_datetime:
                    latest_datetime = saved_lines.reading_datetime

            if latest_datetime:
                self.reading_datetime = latest_datetime + timedelta(minutes=15)
            else:
                self.reading_datetime = fields.Datetime.now()

    @api.model
    def create(self, vals):
        if 'reading_datetime' not in vals or not vals.get('reading_datetime'):
            parent_id = vals.get('parent_id') or self.env.context.get('default_parent_id')
            if parent_id:
                last_line = self.search(
                    [('parent_id', '=', parent_id)],
                    order='id desc', limit=1
                )
                if last_line and last_line.reading_datetime:
                    vals['reading_datetime'] = last_line.reading_datetime + timedelta(minutes=15)
                else:
                    vals['reading_datetime'] = fields.Datetime.now()
            else:
                vals['reading_datetime'] = fields.Datetime.now()
        return super().create(vals)

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_mean(self):
        for rec in self:
            values = [rec.dial_a, rec.dial_b, rec.dial_c, rec.dial_d]
            valid = [v for v in values if v is not False]
            rec.mean_mm = round(sum(valid) / len(valid), 2) if valid else 0.0

    @api.depends('reading_datetime')
    def _compute_split_dt(self):
        for rec in self:
            if rec.reading_datetime:
                dt = fields.Datetime.context_timestamp(rec, rec.reading_datetime)
                rec.reading_date_str = dt.strftime("%d/%m/%y")
                rec.reading_time_str = dt.strftime("%H:%M")
            else:
                rec.reading_date_str = False
                rec.reading_time_str = False


class RoutineVpltReadingUnloading(models.Model):
    _name = "routine.vplt.reading.unloading"
    _description = "Pile Load Reading - Unloading"
    _order = "id"

    parent_id = fields.Many2one(
        "routine.vplt.test", ondelete="cascade", required=True, index=True
    )

    reading_datetime = fields.Datetime("Date & Time", required=True)

    reading_date_str = fields.Char(
        "Date", compute="_compute_split_dt", store=True
    )

    reading_time_str = fields.Char(
        "Time", compute="_compute_split_dt", store=True
    )

    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    dial_c = fields.Float("Dial C (mm)")
    dial_d = fields.Float("Dial D (mm)")

    mean_mm = fields.Float(
        string="Mean (mm)",
        compute="_compute_mean",
        store=True,
        readonly=True
    )

    @api.onchange('parent_id')
    def _onchange_set_datetime(self):
        if self.parent_id:
            latest_datetime = None

            unsaved_lines = [
                r for r in self.parent_id.unloading_reading_ids
                if r.reading_datetime and r != self
            ]

            if unsaved_lines:
                latest = max(unsaved_lines, key=lambda x: x.reading_datetime)
                latest_datetime = latest.reading_datetime
            else:
                saved_lines = self.search(
                    [('parent_id', '=', self.parent_id.id)],
                    order='id desc', limit=1
                )
                if saved_lines and saved_lines.reading_datetime:
                    latest_datetime = saved_lines.reading_datetime

            if latest_datetime:
                self.reading_datetime = latest_datetime + timedelta(minutes=15)
            else:
                self.reading_datetime = fields.Datetime.now()

    @api.model
    def create(self, vals):
        if 'reading_datetime' not in vals or not vals.get('reading_datetime'):
            parent_id = vals.get('parent_id') or self.env.context.get('default_parent_id')
            if parent_id:
                last_line = self.search(
                    [('parent_id', '=', parent_id)],
                    order='id desc', limit=1
                )
                if last_line and last_line.reading_datetime:
                    vals['reading_datetime'] = last_line.reading_datetime + timedelta(minutes=15)
                else:
                    vals['reading_datetime'] = fields.Datetime.now()
            else:
                vals['reading_datetime'] = fields.Datetime.now()
        return super().create(vals)

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_mean(self):
        for rec in self:
            values = [rec.dial_a, rec.dial_b, rec.dial_c, rec.dial_d]
            valid = [v for v in values if v is not False]
            rec.mean_mm = round(sum(valid) / len(valid), 2) if valid else 0.0

    @api.depends('reading_datetime')
    def _compute_split_dt(self):
        for rec in self:
            if rec.reading_datetime:
                dt = fields.Datetime.context_timestamp(rec, rec.reading_datetime)
                rec.reading_date_str = dt.strftime("%d/%m/%y")
                rec.reading_time_str = dt.strftime("%H:%M")
            else:
                rec.reading_date_str = False
                rec.reading_time_str = False


class RoutineVpltLoadingMean(models.Model):
    _name = "routine.vplt.loading.mean"
    _description = "Pile Load Loading Mean Values"
    _order = "seq, id"

    parent_id = fields.Many2one(
        "routine.vplt.test", ondelete="cascade", required=True, index=True
    )

    seq = fields.Integer("Seq")
    load_number = fields.Char("Load Nos")
    loading_mean = fields.Float("Loading Mean (mm)")
    load_value_tonne = fields.Float("Load value (Tonne)")


class RoutineVpltUnloadingMean(models.Model):
    _name = "routine.vplt.unloading.mean"
    _description = "Pile Load Unloading Mean Values"
    _order = "seq, id"

    parent_id = fields.Many2one(
        "routine.vplt.test", ondelete="cascade", required=True, index=True
    )

    seq = fields.Integer("Seq")
    unload_number = fields.Char("Unload Nos")
    unloading_mean = fields.Float("Unloading Mean (mm)")
    load_value_tonne = fields.Float("Load value (Tonne)")


class RoutineVpltReportContent(models.Model):
    _name = "routine.vplt.report.content"
    _description = "Report Contents"
    _order = "sequence, id"

    parent_id = fields.Many2one(
        "routine.vplt.test", ondelete="cascade", required=True, index=True
    )
    sequence = fields.Float("Sl. No")
    description = fields.Char("Description", required=True)
    page_no = fields.Char("Page No")


class RoutineVpltBasicData(models.Model):
    _name = "routine.vplt.basic.data"
    _description = "Pile Load Test Basic Data"
    _order = "sr_no, id"

    parent_id = fields.Many2one(
        "routine.vplt.test", ondelete="cascade", required=True, index=True
    )
    sr_no = fields.Integer('Sl No')
    parameter = fields.Char("Parameter", required=True)
    value = fields.Char("Value")


class RoutineVpltImage(models.Model):
    _name = "routine.vplt.image"
    _description = "Pile Load Test Site Photograph"
    _order = "sequence, id"

    parent_id = fields.Many2one(
        "routine.vplt.test", ondelete="cascade", required=True, index=True
    )
    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph", required=True)
    caption = fields.Char("Caption / Description")
