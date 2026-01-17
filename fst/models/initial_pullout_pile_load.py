from odoo import api, fields, models
import base64
import io
import math
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
    report_no = fields.Char("Report No")
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
    gross_displacement = fields.Float(
        compute="_compute_displacement_values",
        store=True
    )
    net_displacement = fields.Float(
        compute="_compute_displacement_values",
        store=True
    )
    rebound = fields.Float(
        compute="_compute_displacement_values",
        store=True
    )

    # ================= COMPUTE LOGIC =================
    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_displacement_values(self):
        for rec in self:

            # -------- GROSS (max during loading) --------
            loading_vals = rec.loading_reading_ids.mapped('mean_mm')
            gross = max(loading_vals) if loading_vals else 0.0

            # -------- REBOUND (at zero load after unloading) --------
            unloading_zero = rec.unloading_reading_ids.filtered(
                lambda r: r.load_tonne == 0
            )
            rebound = unloading_zero[-1].mean_mm if unloading_zero else 0.0

            # -------- NET --------
            net = gross - rebound

            rec.gross_displacement = round(gross, 2)
            rec.rebound = round(rebound, 2)
            rec.net_displacement = round(net, 2)

    # ================= GRAPH =================
    def action_generate_graph(self):
        """Load vs Displacement graph (Pull-Out Test)"""
        self.ensure_one()

        def unique_by_load(readings):
            seen = set()
            result = []
            for r in readings:
                if r.load_tonne not in seen:
                    seen.add(r.load_tonne)
                    result.append(r)
            return result

        loading = unique_by_load(self.loading_reading_ids.sorted('id'))
        unloading = unique_by_load(self.unloading_reading_ids.sorted('id'))

        if not loading and not unloading:
            self.graph_image = False
            return

        plt.figure(figsize=(7.5, 5.5))

        # -------- LOADING --------
        if loading:
            x = [0] + [r.mean_mm for r in loading]
            y = [0] + [r.load_tonne for r in loading]
            plt.plot(
                x, y,
                marker='o',
                markersize=6,
                markeredgewidth=1.2,
                linewidth=1.8,
                label='Loading',
                zorder=3,
                clip_on=False
            )

        # -------- UNLOADING --------
        if unloading:
            x = [r.mean_mm for r in unloading]
            y = [r.load_tonne for r in unloading]
            plt.plot(
                x, y,
                marker='o',
                markersize=6,
                markeredgewidth=1.2,
                linestyle='--',
                linewidth=1.8,
                label='Unloading',
                zorder=3,
                clip_on=False
            )

        # -------- AXES --------
        plt.xlabel("DISPLACEMENT (MM)", fontsize=10, fontweight='bold')
        plt.ylabel("LOAD (TONNE)", fontsize=10, fontweight='bold')
        plt.title("LOAD - DISPLACEMENT GRAPH (PULL OUT)", fontsize=12, fontweight='bold', pad=12)

        all_x = [r.mean_mm for r in (loading + unloading)]
        x_max = math.ceil(max(all_x)) if all_x else 1
        plt.xlim(0, x_max)
        plt.gca().xaxis.set_major_locator(plt.MultipleLocator(1))
        plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(0.2))

        all_y = [r.load_tonne for r in (loading + unloading)]
        y_max = int(math.ceil(max(all_y) / 10.0) * 10) if all_y else 10
        plt.ylim(0, y_max)
        plt.gca().yaxis.set_major_locator(plt.MultipleLocator(10))
        plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(2))

        plt.grid(which='major', linewidth=0.8, color=GRAPH_MAJOR_GRID_COLOR)
        plt.grid(which='minor', linewidth=0.4, color=GRAPH_MINOR_GRID_COLOR)
        plt.legend(loc='lower right', frameon=False)

        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=150)
        plt.close()

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

            # 2️⃣ Recompute mean displacement on UNLOADING readings
            for line in rec.unloading_reading_ids:
                line._compute_mean()

            # 3️⃣ Recompute displacement summary on parent
            rec._compute_displacement_values()

    def print_report(self):
        self.ensure_one()
        report = self.env.ref('fst.initial_pullout_pile_load_report_py3o')
        filename = f"{self.name or 'Lateral Pile Report'}"
        return report.report_action(self, config={'report_name': filename})



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

    date = fields.Date("Date")
    time_hours = fields.Char("Time (Hours)")
    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial Gauge A (mm)")
    dial_b = fields.Float("Dial Gauge B (mm)")

    mean_mm = fields.Float(
        "Mean Displacement (mm)",
        compute="_compute_mean",
        store=True,
        readonly=True
    )

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

    date = fields.Date("Date")
    time_hours = fields.Char("Time (Hours)")
    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial Gauge A (mm)")
    dial_b = fields.Float("Dial Gauge B (mm)")

    mean_mm = fields.Float(
        "Mean Displacement (mm)",
        compute="_compute_mean",
        store=True,
        readonly=True
    )

    @api.depends('dial_a', 'dial_b')
    def _compute_mean(self):
        for rec in self:
            vals = [v for v in [rec.dial_a, rec.dial_b] if v is not False]
            rec.mean_mm = round(sum(vals) / len(vals), 2) if vals else 0.0


# =========================================================
# SUPPORT TABLES
# =========================================================
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
