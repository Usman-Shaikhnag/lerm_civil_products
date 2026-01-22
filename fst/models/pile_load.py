from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import base64
import io
import math
import matplotlib.pyplot as plt

# Constants for graph styling
GRAPH_MAJOR_GRID_COLOR = '#d28b5c'
GRAPH_MINOR_GRID_COLOR = '#f0c7a0'


class PileLoadTestParent(models.Model):
    _name = "pile.load.test.parent"
    _description = "Initial Vertical Pile Load Test Report"
    _order = "rec_date desc, id desc"

    name = fields.Char("Project Name", required=True)
    rec_date = fields.Date("Report Date")
    report_no = fields.Char("Report No")
    ulr = fields.Char("ULR No")
    site_location = fields.Char("Site Location")
    test_standard = fields.Char("Test Standard")

    introduction = fields.Text("Introduction")
    objective = fields.Text("Objective")
    test_procedure = fields.Text("Test Procedure")

    allowable_capacity = fields.Float("Allowable Capacity")
    interpretation = fields.Text("Interpretation")
    conclusion = fields.Text("Conclusion")

    signatory_name = fields.Char("Authorized Signatory")
    signatory_designation = fields.Char("Designation")

    # DIRECT One2many - no related fields!
    loading_reading_ids = fields.One2many(
        "pile.load.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    unloading_reading_ids = fields.One2many(
        "pile.load.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )

    content_ids = fields.One2many(
        "pile.load.report.content",
        "parent_id",
        string="Contents",
        copy=False
    )

    basic_data_ids = fields.One2many(
        "pile.load.basic.data",
        "parent_id",
        string="Basic Data",
        copy=False
    )

    site_image_ids = fields.One2many(
        "pile.load.test.image",
        "parent_id",
        string="Site Photographs",
        copy=False
    )

    graph_image = fields.Binary("Load Settlement Graph")

    # Settlement Summary
    gross_settlement = fields.Float(
        "Gross Settlement (mm)",
        compute="_compute_settlement_summary",
        store=True,
        readonly=True
    )

    net_settlement = fields.Float(
        "Net Settlement (mm)",
        compute="_compute_settlement_summary",
        store=True,
        readonly=True
    )

    rebound = fields.Float(
        "Rebound (mm)",
        compute="_compute_settlement_summary",
        store=True,
        readonly=True
    )

    max_settlement = fields.Float(
        "Maximum Settlement",
        compute="_compute_max_settlement",
        store=True,
        readonly=True
    )

    analysis_text = fields.Text("Analysis of Test Results")

    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_max_settlement(self):
        for rec in self:
            values = (
                rec.loading_reading_ids.mapped('mean_mm') +
                rec.unloading_reading_ids.mapped('mean_mm')
            )
            rec.max_settlement = max(values) if values else 0.0

    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_settlement_values(self):
        for rec in self:

            # ---------------- LOADING ----------------
            # Take FINAL mean at each load (last reading per load)
            loading_map = {}
            for r in rec.loading_reading_ids.sorted('id'):
                loading_map[r.load_tonne] = r.mean_mm

            if loading_map:
                gross = max(loading_map.values())
            else:
                gross = 0.0

            # ---------------- UNLOADING ----------------
            # Settlement at ZERO load after unloading
            unloading_zero = rec.unloading_reading_ids.filtered(
                lambda r: r.load_tonne == 0
            )

            if unloading_zero:
                final_settlement = unloading_zero[-1].mean_mm
            else:
                final_settlement = 0.0

            rebound = gross - final_settlement

            rec.gross_settlement = round(gross, 2)
            rec.net_settlement = round(final_settlement, 2)
            rec.rebound = round(rebound, 2)

    def action_generate_graph(self):
        """Generate Load–Settlement graph exactly like PDF"""
        self.ensure_one()

        def unique_by_load(readings):
            """Keep only first occurrence per load"""
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
            settle_vals = [0] + [r.mean_mm for r in loading]

            plt.plot(
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
            load_vals = [r.load_tonne for r in unloading]
            settle_vals = [r.mean_mm for r in unloading]

            plt.plot(
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
        plt.xlabel("SETTLEMENT (MM)", fontsize=10, fontweight='bold')
        plt.ylabel("LOAD (TONNE)", fontsize=10, fontweight='bold')
        plt.title("LOAD - SETTLEMENT GRAPH", fontsize=12, fontweight='bold', pad=12)

        all_means = [r.mean_mm for r in (loading + unloading)]
        x_max = math.ceil(max(all_means)) if all_means else 1
        plt.xlim(0, x_max)
        plt.gca().xaxis.set_major_locator(plt.MultipleLocator(1))
        plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(0.2))

        all_loads = [r.load_tonne for r in (loading + unloading)]
        y_max = int(math.ceil(max(all_loads) / 20.0) * 20) if all_loads else 20
        plt.ylim(0, y_max)
        plt.gca().yaxis.set_major_locator(plt.MultipleLocator(20))
        plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(5))

        plt.grid(which='major', linestyle='-', linewidth=0.8, color='#d28b5c')
        plt.grid(which='minor', linestyle='-', linewidth=0.4, color='#f0c7a0')
        plt.legend(loc='lower right', frameon=False)

        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=150)
        plt.close()

        self.graph_image = base64.b64encode(buffer.getvalue())


    def action_recompute_all(self):
        """
        Force recomputation of readings and settlement values.
        Use this when data is inserted via SQL.
        Safe to call from Server Action.
        """
        for rec in self:
            # 1️⃣ Recompute mean_mm on loading readings
            for line in rec.loading_reading_ids:
                line._compute_mean()

            # 2️⃣ Recompute mean_mm on unloading readings
            for line in rec.unloading_reading_ids:
                line._compute_mean()

            # 3️⃣ Force recompute of parent computed fields
            rec._compute_settlement_values()
            rec._compute_max_settlement()



    def print_report(self):
        self.ensure_one()
        report = self.env.ref('fst.vertical_pile_load_report_py3o')
        filename = f"{self.name or 'Vertical Pile Report'}"
        return report.report_action(self, config={'report_name': filename})

    
    def action_duplicate_parent(self):
        """Duplicate Pile Load Test with all linked records cleanly"""
        for record in self:

            # 1️⃣ Create clean new parent (prevent auto O2M copy)
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'loading_reading_ids': False,
                'unloading_reading_ids': False,
                'content_ids': False,
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

            # 4️⃣ Duplicate Report Contents
            for line in record.content_ids:
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
# NEW: Separate Loading Model
class PileLoadReadingLoading(models.Model):
    _name = "pile.load.reading.loading"
    _description = "Pile Load Reading - Loading"
    _order = "id"

    parent_id = fields.Many2one(
        "pile.load.test.parent",
        ondelete="cascade",
        required=True,
        index=True
    )

    date = fields.Date(string="Date")
    time_hours = fields.Char(string="Time (Hours)")
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

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_mean(self):
        for rec in self:
            values = [rec.dial_a, rec.dial_b, rec.dial_c, rec.dial_d]
            valid = [v for v in values if v is not False]
            rec.mean_mm = round(sum(valid) / len(valid), 2) if valid else 0.0


# NEW: Separate Unloading Model
class PileLoadReadingUnloading(models.Model):
    _name = "pile.load.reading.unloading"
    _description = "Pile Load Reading - Unloading"
    _order = "id"

    parent_id = fields.Many2one(
        "pile.load.test.parent",
        ondelete="cascade",
        required=True,
        index=True
    )

    date = fields.Date(string="Date")
    time_hours = fields.Char(string="Time (Hours)")
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

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_mean(self):
        for rec in self:
            values = [rec.dial_a, rec.dial_b, rec.dial_c, rec.dial_d]
            valid = [v for v in values if v is not False]
            rec.mean_mm = round(sum(valid) / len(valid), 2) if valid else 0.0


# Keep these models as-is
class PileLoadReportContent(models.Model):
    _name = "pile.load.report.content"
    _description = "Report Contents"
    _order = "sequence, id"

    parent_id = fields.Many2one(
        "pile.load.test.parent",
        ondelete="cascade",
        required=True,
        index=True
    )
    sequence = fields.Float("Sl. No")
    description = fields.Char("Description", required=True)
    page_no = fields.Char("Page No")


class PileLoadBasicData(models.Model):
    _name = "pile.load.basic.data"
    _description = "Pile Load Test Basic Data"
    _order = "sr_no, id"

    parent_id = fields.Many2one(
        "pile.load.test.parent",
        ondelete="cascade",
        required=True,
        index=True
    )
    sr_no = fields.Integer('Sl No')
    parameter = fields.Char("Parameter", required=True)
    value = fields.Char("Value")


class PileLoadTestImage(models.Model):
    _name = "pile.load.test.image"
    _description = "Pile Load Test Site Photograph"
    _order = "sequence, id"

    parent_id = fields.Many2one(
        "pile.load.test.parent",
        ondelete="cascade",
        required=True,
        index=True
    )
    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph", required=True)
    caption = fields.Char("Caption / Description")