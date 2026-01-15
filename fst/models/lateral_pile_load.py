from odoo import api, fields, models
import base64
import io
import math
import matplotlib.pyplot as plt

GRAPH_MAJOR_GRID_COLOR = '#d28b5c'
GRAPH_MINOR_GRID_COLOR = '#f0c7a0'


class LateralPileLoadTestParent(models.Model):
    _name = "lateral.pile.load.test.parent"
    _description = "Initial Lateral Pile Load Test Report"
    _order = "rec_date desc, id desc"

    # ================= BASIC INFO =================
    name = fields.Char("Project Name", required=True)
    rec_date = fields.Date("Report Date")
    report_no = fields.Char("Report No")
    ulr = fields.Char("ULR No")
    site_location = fields.Char("Site Location")
    test_standard = fields.Char("Test Standard")

    introduction = fields.Text("Introduction")
    objective = fields.Text("Objective")
    test_procedure = fields.Text("Test Procedure")

    allowable_capacity = fields.Float("Allowable Lateral Capacity")
    interpretation = fields.Text("Interpretation")
    conclusion = fields.Text("Conclusion")

    signatory_name = fields.Char("Authorized Signatory")
    signatory_designation = fields.Char("Designation")
    test_equipment = fields.Text("Test Equipment")

    # ================= RELATIONS =================
    loading_reading_ids = fields.One2many(
        "lateral.pile.load.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    unloading_reading_ids = fields.One2many(
        "lateral.pile.load.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )

    content_ids = fields.One2many(
        "lateral.pile.load.report.content",
        "parent_id",
        string="Contents",
        copy=False
    )

    basic_data_ids = fields.One2many(
        "lateral.pile.load.basic.data",
        "parent_id",
        string="Basic Data",
        copy=False
    )

    site_image_ids = fields.One2many(
        "lateral.pile.load.test.image",
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

    max_displacement = fields.Float(
        "Maximum Displacement",
        compute="_compute_max_displacement",
        store=True,
        readonly=True
    )

    analysis_text = fields.Text("Analysis of Test Results")

    # ================= COMPUTES =================
    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_max_displacement(self):
        for rec in self:
            values = (
                rec.loading_reading_ids.mapped('mean_mm') +
                rec.unloading_reading_ids.mapped('mean_mm')
            )
            rec.max_displacement = max(values) if values else 0.0

    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_displacement_values(self):
        for rec in self:

            # ---------------- LOADING ----------------
            loading_map = {}
            for r in rec.loading_reading_ids.sorted('id'):
                loading_map[r.load_tonne] = r.mean_mm

            gross = max(loading_map.values()) if loading_map else 0.0

            # ---------------- UNLOADING ----------------
            # Rebound = displacement at zero load after unloading
            unloading_zero = rec.unloading_reading_ids.filtered(
                lambda r: r.load_tonne == 0
            )

            rebound = unloading_zero[-1].mean_mm if unloading_zero else 0.0

            # ---------------- NET ----------------
            net = gross - rebound

            rec.gross_displacement = round(gross, 2)
            rec.net_displacement = round(net, 2)
            rec.rebound = round(rebound, 2)


    # ================= GRAPH =================
    def action_generate_graph(self):
        """Generate Load-Displacement graph exactly like PDF"""
        self.ensure_one()

        def unique_by_load(readings):
            seen = set()
            result = []
            for r in readings:
                if r.load_tonne not in seen:
                    seen.add(r.load_tonne)
                    result.append(r)
            return result

        loading_all = self.loading_reading_ids.sorted('id')
        unloading_all = self.unloading_reading_ids.sorted('id')

        loading = unique_by_load(loading_all)
        unloading = unique_by_load(unloading_all)

        if not loading and not unloading:
            self.graph_image = False
            return

        plt.figure(figsize=(7.5, 5.5))

        # ================= LOADING =================
        if loading:
            load_vals = [0] + [r.load_tonne for r in loading]
            disp_vals = [0] + [r.mean_mm for r in loading]

            plt.plot(
                disp_vals,
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
            load_vals = [r.load_tonne for r in unloading]
            disp_vals = [r.mean_mm for r in unloading]

            plt.plot(
                disp_vals,
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
        plt.xlabel("DISPLACEMENT (MM)", fontsize=10, fontweight='bold')
        plt.ylabel("LOAD (TONNE)", fontsize=10, fontweight='bold')
        plt.title("LOAD - DISPLACEMENT GRAPH", fontsize=12, fontweight='bold', pad=12)

        # ---- X AXIS (Displacement) ----
        all_disp = [r.mean_mm for r in (loading + unloading)]
        x_max = math.ceil(max(all_disp)) if all_disp else 1
        plt.xlim(0, x_max)

        plt.gca().xaxis.set_major_locator(plt.MultipleLocator(1))
        plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(0.2))

        # ---- Y AXIS (Load) ----
        all_loads = [r.load_tonne for r in (loading + unloading)]
        y_max = int(math.ceil(max(all_loads) / 5.0) * 5) if all_loads else 10
        plt.ylim(0, y_max)

        plt.gca().yaxis.set_major_locator(plt.MultipleLocator(5))
        plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(1))

        # ---- GRID ----
        plt.grid(which='major', linestyle='-', linewidth=0.8, color=GRAPH_MAJOR_GRID_COLOR)
        plt.grid(which='minor', linestyle='-', linewidth=0.4, color=GRAPH_MINOR_GRID_COLOR)

        plt.legend(loc='lower right', frameon=False)

        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=150)
        plt.close()

        self.graph_image = base64.b64encode(buffer.getvalue())


    def action_recompute_all(self):
        """
        Force recomputation of readings and displacement values.
        Use this when data is inserted via SQL or bulk import.
        Safe to call from Server Action.
        """
        for rec in self:

            # 1️⃣ Recompute mean displacement on LOADING readings
            for line in rec.loading_reading_ids:
                line._compute_mean()

            # 2️⃣ Recompute mean displacement on UNLOADING readings
            for line in rec.unloading_reading_ids:
                line._compute_mean()

            # 3️⃣ Force recompute of parent computed fields
            rec._compute_displacement_values()
            rec._compute_max_displacement()



    def print_report(self):
        self.ensure_one()
        report = self.env.ref('fst.lateral_pile_load_report_py3o')
        filename = f"{self.name or 'Lateral Pile Report'}"
        return report.report_action(self, config={'report_name': filename})


# ================= LOADING =================
class LateralPileLoadReadingLoading(models.Model):
    _name = "lateral.pile.load.reading.loading"
    _description = "Lateral Pile Load Reading - Loading"
    _order = "id"

    parent_id = fields.Many2one(
        "lateral.pile.load.test.parent",
        ondelete="cascade",
        required=True
    )

    date = fields.Date("Date")
    time_hours = fields.Char("Time (Hours)")
    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")

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


# ================= UNLOADING =================
class LateralPileLoadReadingUnloading(models.Model):
    _name = "lateral.pile.load.reading.unloading"
    _description = "Lateral Pile Load Reading - Unloading"
    _order = "id"

    parent_id = fields.Many2one(
        "lateral.pile.load.test.parent",
        ondelete="cascade",
        required=True
    )

    date = fields.Date("Date")
    time_hours = fields.Char("Time (Hours)")
    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")

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


# ================= SUPPORT TABLES =================
class LateralPileLoadReportContent(models.Model):
    _name = "lateral.pile.load.report.content"
    _description = "Report Contents"

    parent_id = fields.Many2one("lateral.pile.load.test.parent", ondelete="cascade")
    sequence = fields.Float("Sl. No")
    description = fields.Char("Description")
    page_no = fields.Char("Page No")


class LateralPileLoadBasicData(models.Model):
    _name = "lateral.pile.load.basic.data"
    _description = "Lateral Pile Load Test Basic Data"

    parent_id = fields.Many2one("lateral.pile.load.test.parent", ondelete="cascade")
    sr_no = fields.Integer("Sl No")
    parameter = fields.Char("Parameter")
    value = fields.Char("Value")


class LateralPileLoadTestImage(models.Model):
    _name = "lateral.pile.load.test.image"
    _description = "Lateral Pile Load Test Site Photograph"

    parent_id = fields.Many2one("lateral.pile.load.test.parent", ondelete="cascade")
    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph")
    caption = fields.Char("Caption")
