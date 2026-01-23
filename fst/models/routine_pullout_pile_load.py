from odoo import api, fields, models
import base64
import io
import math
import matplotlib.pyplot as plt

GRAPH_MAJOR_GRID_COLOR = '#d28b5c'
GRAPH_MINOR_GRID_COLOR = '#f0c7a0'


class RoutinePulloutPileLoadTestParent(models.Model):
    _name = "routine.pullout.pile.load.test.parent"
    _description = "Routine Pull-Out Pile Load Test Report"
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
        "routine.pullout.pile.load.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    unloading_reading_ids = fields.One2many(
        "routine.pullout.pile.load.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )

    basic_data_ids = fields.One2many(
        "routine.pullout.pile.load.basic.data",
        "parent_id",
        string="Basic Data",
        copy=False
    )

    site_image_ids = fields.One2many(
        "routine.pullout.pile.load.test.image",
        "parent_id",
        string="Site Photographs",
        copy=False
    )

    graph_image = fields.Binary("Load Displacement Graph")

    # ================= DISPLACEMENT SUMMARY =================
    gross_displacement = fields.Float(compute="_compute_displacement", store=True)
    net_displacement = fields.Float(compute="_compute_displacement", store=True)
    rebound = fields.Float(compute="_compute_displacement", store=True)

    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_displacement(self):
        for rec in self:
            loading_vals = rec.loading_reading_ids.mapped('mean_mm')
            gross = max(loading_vals) if loading_vals else 0.0

            unloading_zero = rec.unloading_reading_ids.filtered(
                lambda r: r.load_tonne == 0
            )
            rebound = unloading_zero[-1].mean_mm if unloading_zero else 0.0
            net = gross - rebound

            rec.gross_displacement = round(gross, 2)
            rec.rebound = round(rebound, 2)
            rec.net_displacement = round(net, 2)

    # ================= GRAPH =================
    def action_generate_graph(self):
        """Generate Load-Displacement graph exactly like Initial Pull-Out PDF"""
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

        # ================= AXES & STYLE (PDF MATCH) =================
        plt.xlabel("DISPLACEMENT (MM)", fontsize=10, fontweight='bold')
        plt.ylabel("LOAD (TONNE)", fontsize=10, fontweight='bold')
        plt.title(
            "LOAD - DISPLACEMENT GRAPH (ROUTINE PULL OUT)",
            fontsize=12,
            fontweight='bold',
            pad=12
        )

        # -------- X AXIS (THIS IS THE IMPORTANT PART) --------
        # PDF shows:
        # - starts exactly at 0
        # - major ticks = 1 mm
        # - minor ticks = 0.2 mm
        # - slight padding so points don’t touch axis
        all_disp = [r.mean_mm for r in (loading + unloading)]
        max_disp = max(all_disp) if all_disp else 1.0

        # Add small padding like PDF (0.1 mm)
        x_max = round(max_disp + 0.1, 1)

        plt.xlim(0, 1.4)
        plt.gca().xaxis.set_major_locator(plt.MultipleLocator(0.2))
        plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(0.02))

        # -------- Y AXIS --------
        all_loads = [r.load_tonne for r in (loading + unloading)]
        y_max = int(math.ceil(max(all_loads) / 5.0) * 5) if all_loads else 10

        plt.ylim(0, 16)
        plt.gca().yaxis.set_major_locator(plt.MultipleLocator(2))
        plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(0.2))

        # -------- GRID --------
        plt.grid(
            which='major',
            linestyle='-',
            linewidth=0.8,
            color=GRAPH_MAJOR_GRID_COLOR
        )
        plt.grid(
            which='minor',
            linestyle='-',
            linewidth=0.4,
            color=GRAPH_MINOR_GRID_COLOR
        )

        plt.legend(loc='lower right', frameon=False)

        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=150)
        plt.close()

        self.graph_image = base64.b64encode(buffer.getvalue())



    def action_recompute_all(self):
        for rec in self:
            for line in rec.loading_reading_ids:
                line._compute_mean()
            for line in rec.unloading_reading_ids:
                line._compute_mean()
            rec._compute_displacement()

    def print_report(self):
        self.ensure_one()
        report = self.env.ref('fst.routine_pullout_pile_load_report_py3o')
        filename = f"{self.name or 'Routine Pullout Pile Load Report'}"
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

            # 4️⃣ Duplicate Basic Data
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


# =================CHILD MODELS =================
class RoutinePulloutPileLoadReadingLoading(models.Model):
    _name = "routine.pullout.pile.load.reading.loading"
    _description = "Routine Pull-Out Loading Reading"
    _order = "id"

    parent_id = fields.Many2one(
        "routine.pullout.pile.load.test.parent",
        ondelete="cascade", required=True
    )
    date = fields.Date("Date")
    time_hours = fields.Char("Time (Hours)")
    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    mean_mm = fields.Float(
        "Mean Displacement (mm)",
        compute="_compute_mean", store=True, readonly=True
    )

    @api.depends('dial_a', 'dial_b')
    def _compute_mean(self):
        for rec in self:
            vals = [v for v in [rec.dial_a, rec.dial_b] if v is not False]
            rec.mean_mm = round(sum(vals) / len(vals), 2) if vals else 0.0


class RoutinePulloutPileLoadReadingUnloading(models.Model):
    _name = "routine.pullout.pile.load.reading.unloading"
    _description = "Routine Pull-Out Unloading Reading"
    _order = "id"

    parent_id = fields.Many2one(
        "routine.pullout.pile.load.test.parent",
        ondelete="cascade", required=True
    )
    date = fields.Date("Date")
    time_hours = fields.Char("Time (Hours)")
    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    mean_mm = fields.Float(
        "Mean Displacement (mm)",
        compute="_compute_mean", store=True, readonly=True
    )

    @api.depends('dial_a', 'dial_b')
    def _compute_mean(self):
        for rec in self:
            vals = [v for v in [rec.dial_a, rec.dial_b] if v is not False]
            rec.mean_mm = round(sum(vals) / len(vals), 2) if vals else 0.0


class RoutinePulloutPileLoadBasicData(models.Model):
    _name = "routine.pullout.pile.load.basic.data"
    _description = "Routine Pull-Out Basic Data"

    parent_id = fields.Many2one(
        "routine.pullout.pile.load.test.parent",
        ondelete="cascade"
    )
    sr_no = fields.Integer("Sl No")
    parameter = fields.Char("Parameter")
    value = fields.Char("Value")


class RoutinePulloutPileLoadTestImage(models.Model):
    _name = "routine.pullout.pile.load.test.image"
    _description = "Routine Pull-Out Site Photograph"

    parent_id = fields.Many2one(
        "routine.pullout.pile.load.test.parent",
        ondelete="cascade"
    )
    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph")
    caption = fields.Char("Caption")
