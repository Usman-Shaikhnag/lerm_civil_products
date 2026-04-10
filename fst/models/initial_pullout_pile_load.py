from odoo import api, fields, models
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
import base64
import io
import math
import re
import matplotlib.pyplot as plt

GRAPH_MAJOR_GRID_COLOR = '#d28b5c'
GRAPH_MINOR_GRID_COLOR = '#f0c7a0'


# =========================================================
# PARENT MODEL
# =========================================================
class PulloutPileLoadTestParent(models.Model):
    _name = "pullout.pile.load.test.parent"
    _description = "Initial Pull-Out Pile Load Test Report"
    _order = "rec_date desc, id desc"

    # ================= BASIC INFO =================
    name = fields.Char("Project Name", required=True)
    rec_date = fields.Date("Report Date")
    
    work_name = fields.Char("Name of Work")
    client = fields.Many2one("res.partner", string="Client")
    contractor = fields.Many2one(
        "lerm.contractor.line",
        string="Contractor",
        domain="[('partner_id', '=', client)]"
    )

    ulr = fields.Char("ULR No", copy=False, readonly=True)
    report_no = fields.Char("Report No", copy=False, readonly=True)
    pile_no = fields.Char("Pile No")
    site_location = fields.Char("Site Location")
    test_standard = fields.Char("Test Standard")

    introduction = fields.Text("Introduction")
    objective = fields.Text("Objective")
    test_equipment = fields.Text("Testing Equipment")
    test_procedure = fields.Text("Test Procedure")

    interpretation = fields.Text("Interpretation")
    conclusion = fields.Text("Conclusion")

    allowable_capacity = fields.Float("Allowable Uplift Load (Tonne)")

    # ================= RELATIONS =================
    loading_reading_ids = fields.One2many(
        "pullout.pile.load.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    unloading_reading_ids = fields.One2many(
        "pullout.pile.load.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )
    
    content_ids = fields.One2many(
        "pullout.pile.load.report.content",
        "parent_id",
        string="Contents",
        copy=False
    )

    basic_data_ids = fields.One2many(
        "pullout.pile.load.basic.data",
        "parent_id",
        string="Basic Data",
        copy=False
    )

    site_image_ids = fields.One2many(
        "pullout.pile.load.test.image",
        "parent_id",
        string="Site Photographs",
        copy=False
    )

    graph_image = fields.Binary("Load Displacement Graph")

    # ================= DISPLACEMENT SUMMARY =================
    gross_settlement = fields.Float(
        compute="_compute_settlement_values",
        store=True
    )
    net_settlement = fields.Float(
        compute="_compute_settlement_values",
        store=True
    )
    rebound = fields.Float(
        compute="_compute_settlement_values",
        store=True
    )
    
    rec_date_str = fields.Char(
        "Report Date (Text)",
        compute="_compute_rec_date_str",
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

            # Extract only the numeric part (with optional suffix like F)
            match = re.search(r'(\d+F?)$', seq_raw)
            seq = match.group(1) if match else ''

            # import wdb;wdb.set_trace()
            rec.ulr = f"{cert}{year}{loc}{seq}"

    # ================= COMPUTE LOGIC =================
    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_settlement_values(self):
        for rec in self:

            loading_map = {}

            # ❌ removed .sorted('id')
            for r in rec.loading_reading_ids:
                loading_map[r.load_tonne] = r.mean_mm

            if loading_map:
                gross = max(loading_map.values())
                first_load = min(loading_map.keys())
            else:
                gross = 0.0
                first_load = 0.0

            rebound_lines = rec.unloading_reading_ids.filtered(
                lambda r: r.load_tonne == first_load
            )

            rebound = rebound_lines[-1].mean_mm if rebound_lines else 0.0
            net = gross - rebound

            rec.gross_settlement = round(gross, 2)
            rec.rebound = round(rebound, 2)
            rec.net_settlement = round(net, 2)


    # ================= GRAPH =================
    def action_generate_graph(self):
        """Generate Load-Settlement graph exactly like PDF"""
        self.ensure_one()

        def loading_points(readings):
            result = []

            prev_load = None
            last_mean = None

            for r in readings.sorted('reading_datetime'):

                if prev_load is None:
                    prev_load = r.load_tonne
                    last_mean = r.mean_mm
                    continue

                # same step if:
                #   same load OR zero (continuation)
                if r.load_tonne == prev_load or r.load_tonne == 0:
                    last_mean = r.mean_mm
                else:
                    result.append((prev_load, last_mean))
                    prev_load = r.load_tonne
                    last_mean = r.mean_mm

            if prev_load is not None:
                result.append((prev_load, last_mean))
            # import wdb;wdb.set_trace()
            return result

        def unloading_points(readings):
            return [
                (r.load_tonne, r.mean_mm)
                for r in readings.sorted('reading_datetime')
            ]
        # loading_all = self.loading_reading_ids.sorted('reading_datetime')
        # unloading_all = self.unloading_reading_ids.sorted('reading_datetime')

        loading = loading_points(self.loading_reading_ids)
        unloading = unloading_points(self.unloading_reading_ids)

        # import wdb;wdb.set_trace()
        if not loading and not unloading:
            self.graph_image = False
            return

        fig, ax = plt.subplots(figsize=(7.5, 5.5))

        # ================= LOADING =================
        if loading:
            load_vals = [0] + [l for l, m in loading]
            settle_vals = [0] + [m for l, m in loading]

            ax.plot(
                settle_vals,
                load_vals,
                marker='o',
                markersize=6,
                markeredgewidth=1.2,
                linewidth=1.8,
                label='Loading',
                zorder=3,
                clip_on=False
            )


        # ================= UNLOADING =================
        if unloading:
            load_vals = [l for l,m in unloading]
            settle_vals = [m for l,m in unloading]

            ax.plot(
                settle_vals,
                load_vals,
                marker='o',
                markersize=6,
                markeredgewidth=1.2,
                linestyle='--',
                linewidth=1.8,
                label='Unloading',
                zorder=3,
                clip_on=False
            )


        # ================= AXES & STYLE =================
        ax.set_xlabel("DISPLACEMENT (MM)", fontsize=10, fontweight='bold')
        ax.set_ylabel("LOAD (TONNE)", fontsize=10, fontweight='bold')
        ax.set_title("LOAD - SETTLEMENT GRAPH", fontsize=12, fontweight='bold', pad=12)

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

        all_loads = [l for l, m in (loading + unloading)]
        y_max = max(all_loads) if all_loads else 20

        major = load_major_step(y_max)
        if major < 5:
            minor = major / 2
        else:
            minor = major / 5

        ax.set_ylim(0, math.ceil(y_max / major) * major)
        ax.yaxis.set_major_locator(plt.MultipleLocator(major))
        ax.yaxis.set_minor_locator(plt.MultipleLocator(minor))

        def settlement_major_step(x_max):
            if x_max <= 2:
                return 0.2
            elif x_max <= 15:
                return 1
            elif x_max <= 30:
                return 2
            else:
                return 5

        all_means = [m for l, m in (loading + unloading)]
        x_max = max(all_means) if all_means else 1

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
        """
        Force recomputation of all computed fields.
        Use this after SQL inserts or bulk imports.
        Safe to call from Server Action.
        """
        for rec in self:

            # 1️⃣ Recompute mean displacement on LOADING readings
            for line in rec.loading_reading_ids:
                line._compute_mean()
                line._compute_split_dt()

            # 2️⃣ Recompute mean displacement on UNLOADING readings
            for line in rec.unloading_reading_ids:
                line._compute_mean()
                line._compute_split_dt()

            # 3️⃣ Recompute displacement summary on parent
            rec._compute_settlement_values()

    def print_report(self):
        self.ensure_one()
        report = self.env.ref('fst.initial_pullout_pile_load_report_py3o')
        filename = f"{self.name or 'Lateral Pile Report'}"
        return report.report_action(self, config={'report_name': filename})

    def action_duplicate_parent(self):
        """Duplicate Pile Load Test with all linked records cleanly"""
        for record in self:

            # 1️⃣ Create clean new parent (prevent auto O2M copy)
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'loading_reading_ids': False,
                'unloading_reading_ids': False,
                'basic_data_ids': False,
                'site_image_ids': False,
                'graph_image': False,  # graph must be regenerated
            })

            # 2️⃣ Duplicate Loading Readings
            for line in record.loading_reading_ids:
                line.copy({
                    'parent_id': new_parent.id,
                })

            # 3️⃣ Duplicate Unloading Readings
            for line in record.unloading_reading_ids:
                line.copy({
                    'parent_id': new_parent.id,
                })

            # 5️⃣ Duplicate Basic Data
            for line in record.basic_data_ids:
                line.copy({
                    'parent_id': new_parent.id,
                })

            # 6️⃣ Duplicate Site Images
            for line in record.site_image_ids:
                line.copy({
                    'parent_id': new_parent.id,
                })

            # 7️⃣ Recompute computed fields safely
            new_parent.action_recompute_all()

            return True 

    def action_delete_line(self):
        for rec in self:
            
            rec.unlink()

    last_reading_datetime = fields.Datetime(
        compute="_compute_last_reading_datetime",
        store=False,
        copy=False
    )

    @api.depends('loading_reading_ids.reading_datetime')
    def _compute_last_reading_datetime(self):
        for rec in self:
            dates = rec.loading_reading_ids.mapped('reading_datetime')
            dates = [d for d in dates if d]
            rec.last_reading_datetime = max(dates) if dates else False

# =========================================================
# LOADING MODEL
# =========================================================
class PulloutPileLoadReadingLoading(models.Model):
    _name = "pullout.pile.load.reading.loading"
    _description = "Pull-Out Pile Load Reading - Loading"
    _order = "id"

    parent_id = fields.Many2one(
        "pullout.pile.load.test.parent",
        ondelete="cascade",
        required=True
    )

    reading_datetime = fields.Datetime(
        "Date & Time",
        required=True,
    )

    reading_date_str = fields.Char(
        "Date",
        compute="_compute_split_dt",
        store=True
    )

    reading_time_str = fields.Char(
        "Time",
        compute="_compute_split_dt",
        store=True
    )
    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial Gauge A (mm)")
    dial_b = fields.Float("Dial Gauge B (mm)")

    mean_mm = fields.Float(
        "Mean Displacement (mm)",
        compute="_compute_mean",
        store=True,
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        """Minimal default - just set current time as fallback"""
        res = super().default_get(fields_list)
        
        # Don't set reading_datetime here - let onchange handle it
        # This is just a safety fallback
        if 'reading_datetime' in fields_list and 'reading_datetime' not in res:
            res['reading_datetime'] = fields.Datetime.now()
        
        return res

    @api.onchange('parent_id')
    def _onchange_set_datetime(self):
        """Auto-fill datetime when adding new line in tree"""
        # Always run for new records
        if self.parent_id:
            latest_datetime = None
            
            # First, check unsaved lines in the current form (these have priority)
            unsaved_lines = [
                r for r in self.parent_id.loading_reading_ids 
                if r.reading_datetime and r != self  # Exclude current line
            ]
            
            if unsaved_lines:
                # Get the one with the latest datetime from unsaved lines
                latest = max(unsaved_lines, key=lambda x: x.reading_datetime)
                latest_datetime = latest.reading_datetime
            else:
                # No unsaved lines, check saved lines from database
                saved_lines = self.search(
                    [('parent_id', '=', self.parent_id.id)],
                    order='id desc',
                    limit=1
                )
                if saved_lines and saved_lines.reading_datetime:
                    latest_datetime = saved_lines.reading_datetime
            
            # Set the datetime
            if latest_datetime:
                self.reading_datetime = latest_datetime + timedelta(minutes=15)
            else:
                self.reading_datetime = fields.Datetime.now()

    @api.model 
    def create(self, vals):
        """Ensure datetime is set on create (when form is saved)"""
        if 'reading_datetime' not in vals or not vals.get('reading_datetime'):
            parent_id = vals.get('parent_id') or self.env.context.get('default_parent_id')
            
            if parent_id:
                last_line = self.search(
                    [('parent_id', '=', parent_id)],
                    order='id desc',
                    limit=1
                )
                
                if last_line and last_line.reading_datetime:
                    vals['reading_datetime'] = last_line.reading_datetime + timedelta(minutes=15)
                else:
                    vals['reading_datetime'] = fields.Datetime.now()
            else:
                vals['reading_datetime'] = fields.Datetime.now()
        
        return super().create(vals)

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

    @api.depends('dial_a', 'dial_b')
    def _compute_mean(self):
        for rec in self:
            vals = [v for v in [rec.dial_a, rec.dial_b] if v is not False]
            rec.mean_mm = round(sum(vals) / len(vals), 2) if vals else 0.0


# =========================================================
# UNLOADING MODEL
# =========================================================
class PulloutPileLoadReadingUnloading(models.Model):
    _name = "pullout.pile.load.reading.unloading"
    _description = "Pull-Out Pile Load Reading - Unloading"
    _order = "id"

    parent_id = fields.Many2one(
        "pullout.pile.load.test.parent",
        ondelete="cascade",
        required=True
    )

    reading_datetime = fields.Datetime(
        "Date & Time",
        required=True,
    )

    reading_date_str = fields.Char(
        "Date",
        compute="_compute_split_dt",
        store=True
    )

    reading_time_str = fields.Char(
        "Time",
        compute="_compute_split_dt",
        store=True
    )

    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial Gauge A (mm)")
    dial_b = fields.Float("Dial Gauge B (mm)")

    mean_mm = fields.Float(
        "Mean Displacement (mm)",
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
                    order='id desc',
                    limit=1
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
                    order='id desc',
                    limit=1
                )

                if last_line and last_line.reading_datetime:
                    vals['reading_datetime'] = last_line.reading_datetime + timedelta(minutes=15)
                else:
                    vals['reading_datetime'] = fields.Datetime.now()
            else:
                vals['reading_datetime'] = fields.Datetime.now()

        return super().create(vals)


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

                
    @api.depends('dial_a', 'dial_b')
    def _compute_mean(self):
        for rec in self:
            vals = [v for v in [rec.dial_a, rec.dial_b] if v is not False]
            rec.mean_mm = round(sum(vals) / len(vals), 2) if vals else 0.0


# =========================================================
# SUPPORT TABLES
# =========================================================
class PulloutPileLoadReportContent(models.Model):
    _name = "pullout.pile.load.report.content"
    _description = "Pull-Out Pile Load Test Report Content"

    parent_id = fields.Many2one("pullout.pile.load.test.parent", ondelete="cascade")
    sequence = fields.Float("Sl. No")
    description = fields.Char("Description")
    page_no = fields.Char("Page No")


class PulloutPileLoadBasicData(models.Model):
    _name = "pullout.pile.load.basic.data"
    _description = "Pull-Out Pile Load Test Basic Data"

    parent_id = fields.Many2one("pullout.pile.load.test.parent", ondelete="cascade")
    sr_no = fields.Integer("Sl No")
    parameter = fields.Char("Parameter")
    value = fields.Char("Value")


class PulloutPileLoadTestImage(models.Model):
    _name = "pullout.pile.load.test.image"
    _description = "Pull-Out Pile Load Test Site Photograph"

    parent_id = fields.Many2one("pullout.pile.load.test.parent", ondelete="cascade")
    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph")
    caption = fields.Char("Caption")
