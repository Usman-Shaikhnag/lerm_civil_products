from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import zipfile
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import io, base64, math, logging
import matplotlib.pyplot as plt
from matplotlib import patches as mpatches
from matplotlib.ticker import MultipleLocator




class PileLoadTestParent(models.Model):
    _name = "pile.load.test.parent"
    _description = "Initial Vertical Pile Load Test Report"

    name = fields.Char("Project Name", required=True)
    rec_date = fields.Date("Report Date")

    # Cover / report metadata
    report_no = fields.Char("Report No")
    ulr = fields.Char("ULR No")
    site_location = fields.Char("Site Location")
    test_standard = fields.Char("Test Standard")

    # Narrative sections
    introduction = fields.Text("Introduction")
    objective = fields.Text("Objective")
    test_procedure = fields.Text("Test Procedure")

    # Analysis
    max_settlement = fields.Float(
        "Maximum Settlement",
        compute="_compute_max_settlement",
        store=True,
        readonly=True
    )

    allowable_capacity = fields.Float("Allowable Capacity")
    interpretation = fields.Text("Interpretation")
    conclusion = fields.Text("Conclusion")

    # Signatory
    signatory_name = fields.Char("Authorized Signatory")
    signatory_designation = fields.Char("Designation")

    pile_load_test_ids = fields.One2many(
        "pile.load.test",
        "parent_id",
        copy=False
    )

    # --- ASSUME ONLY ONE TEST PER REPORT ---
    pile_load_test_id = fields.Many2one(
        "pile.load.test",
        compute="_compute_single_test",
        store=True
    )

    loading_reading_ids = fields.One2many(
        related="pile_load_test_id.loading_reading_ids",
        readonly=False
    )

    unloading_reading_ids = fields.One2many(
        related="pile_load_test_id.unloading_reading_ids",
        readonly=False
    )

    graph_image = fields.Binary(
        related="pile_load_test_id.graph_image",
        readonly=False
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

    # --- Settlement Summary ---
    gross_settlement = fields.Float(
        "Gross Settlement (mm)",
        compute="_compute_settlement_summary",
        store=True
    )

    net_settlement = fields.Float(
        "Net Settlement (mm)",
        compute="_compute_settlement_summary",
        store=True
    )

    rebound = fields.Float(
        "Rebound (mm)",
        compute="_compute_settlement_summary",
        store=True
    )

    analysis_text = fields.Text(
        "Analysis of Test Results"
    )

    site_image_ids = fields.One2many(
        "pile.load.test.image",
        "parent_id",
        string="Site Photographs",
        copy=False
    )



    @api.depends('pile_load_test_ids')
    def _compute_single_test(self):
        for rec in self:
            rec.pile_load_test_id = rec.pile_load_test_ids[:1]


    @api.constrains('pile_load_test_ids')
    def _check_single_test(self):
        for rec in self:
            if len(rec.pile_load_test_ids) > 1:
                raise ValidationError(
                    "Only one Pile Load Test is allowed per report."
                )

    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_max_settlement(self):
        for rec in self:
            values = (
                rec.loading_reading_ids.mapped('mean_mm') +
                rec.unloading_reading_ids.mapped('mean_mm')
            )
            rec.max_settlement = max(values) if values else 0.0

    def create_pile_load_test(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pile.load.test',
            'target': 'current',
            'context': {
                'default_parent_id': self.id
            }
        }

    def action_generate_graph(self):
        for rec in self:
            if not rec.pile_load_test_id:
                raise UserError("Please create a Pile Load Test first.")
            rec.pile_load_test_id.action_generate_graph()
    
    def recompute_mean(self):
        for rec in self:
            readings = rec.loading_reading_ids | rec.unloading_reading_ids
            for r in readings:
                r._compute_mean()

    def print_report(self):
        report = self.env.ref('fst.vertical_pile_load_report_py3o')
        filename = f"{self.name or 'Vertical Pile Report'}"
        return report.report_action(self, config={'report_name': filename})
    

    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_settlement_summary(self):
        for rec in self:
            if not rec.loading_reading_ids:
                rec.gross_settlement = 0.0
                rec.net_settlement = 0.0
                rec.rebound = 0.0
                continue

            gross = max(rec.loading_reading_ids.mapped('mean_mm'))
            net = 0.0
            rebound = 0.0

            if rec.unloading_reading_ids:
                net = max(rec.unloading_reading_ids.mapped('mean_mm'))
                rebound = gross - net

            rec.gross_settlement = round(gross, 2)
            rec.net_settlement = round(net, 2)
            rec.rebound = round(rebound, 2)


class PileLoadReading(models.Model):
    _name = "pile.load.reading"

    test_id = fields.Many2one(
        "pile.load.test",
        ondelete="cascade",
        copy=False
    )

    date = fields.Date(string="Date")
    time_hours = fields.Char(string="Time (Hours)")

    reading_type = fields.Selection(
        [('loading', 'Loading'), ('unloading', 'Unloading')],
        required=True,readonly=True
    )

    load_tonne = fields.Float("Load (Tonne)")
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    dial_c = fields.Float("Dial C (mm)")
    dial_d = fields.Float("Dial D (mm)")

    mean_mm = fields.Float(
        string="Mean (mm)",
        compute="_compute_mean",
        store=True
    )

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_mean(self):
        for rec in self:
            values = [rec.dial_a, rec.dial_b, rec.dial_c, rec.dial_d]
            valid = [v for v in values if v is not False]
            rec.mean_mm = round(sum(valid) / len(valid), 2) if valid else 0.0


class PileLoadTest(models.Model):
    _name = "pile.load.test"

    name = fields.Char(default="Pile Load Test")
    parent_id = fields.Many2one("pile.load.test.parent", ondelete="cascade")

    loading_reading_ids = fields.One2many(
        "pile.load.reading",
        "test_id",
        string="Loading Readings",
        domain=[('reading_type', '=', 'loading')],
        context={'default_reading_type': 'loading'},
        copy=False
    )

    unloading_reading_ids = fields.One2many(
        "pile.load.reading",
        "test_id",
        string="Unloading Readings",
        domain=[('reading_type', '=', 'unloading')],
        context={'default_reading_type': 'unloading'},
        copy=False
    )

    graph_image = fields.Binary("Load Settlement Graph")


    def action_generate_graph(self):
        """
        Generate Load-Settlement graph:
        - One point per load
        - First occurrence of each load is plotted
        - Dynamic axis scaling
        - PDF-style grid
        """
        for rec in self:

            def unique_by_load(readings):
                """Return readings keeping only first occurrence per load"""
                seen = set()
                result = []
                for r in readings:
                    if r.load_tonne not in seen:
                        seen.add(r.load_tonne)
                        result.append(r)
                return result

            # -------- PREPARE DATA --------
            loading_all = rec.loading_reading_ids.sorted('id')
            unloading_all = rec.unloading_reading_ids.sorted('id')

            loading = unique_by_load(loading_all)
            unloading = unique_by_load(unloading_all)

            if not loading and not unloading:
                rec.graph_image = False
                continue

            plt.figure(figsize=(7.5, 5.5))

            # -------- LOADING CURVE --------
            if loading:
                plt.plot(
                    [r.mean_mm for r in loading],
                    [r.load_tonne for r in loading],
                    marker='o',
                    linewidth=1.8,
                    label='Loading'
                )

            # -------- UNLOADING CURVE --------
            if unloading:
                plt.plot(
                    [r.mean_mm for r in unloading],
                    [r.load_tonne for r in unloading],
                    marker='o',
                    linestyle='--',
                    linewidth=1.8,
                    label='Unloading'
                )

            # -------- LABELS --------
            plt.xlabel("SETTLEMENT (MM)", fontsize=10, fontweight='bold')
            plt.ylabel("LOAD (TONNE)", fontsize=10, fontweight='bold')
            plt.title("LOAD - SETTLEMENT GRAPH", fontsize=12, fontweight='bold', pad=12)

            # -------- DYNAMIC X AXIS --------
            all_means = [r.mean_mm for r in (loading + unloading)]
            x_max = math.ceil(max(all_means)) if all_means else 1

            plt.xlim(0, x_max)
            plt.gca().xaxis.set_major_locator(plt.MultipleLocator(1))
            plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(0.2))

            # -------- DYNAMIC Y AXIS --------
            all_loads = [r.load_tonne for r in (loading + unloading)]
            y_max = int(math.ceil(max(all_loads) / 20.0) * 20) if all_loads else 20

            plt.ylim(0, y_max)
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(20))
            plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(5))

            # -------- GRID (PDF STYLE) --------
            plt.grid(which='major', linestyle='-', linewidth=0.8, color='#d28b5c')
            plt.grid(which='minor', linestyle='-', linewidth=0.4, color='#f0c7a0')

            # -------- LEGEND --------
            plt.legend(loc='lower right', frameon=False)

            # -------- SAVE IMAGE --------
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=150)
            plt.close()

            rec.graph_image = base64.b64encode(buffer.getvalue())





class PileLoadReportContent(models.Model):
    _name = "pile.load.report.content"
    _description = "Report Contents"

    parent_id = fields.Many2one(
        "pile.load.test.parent",
        ondelete="cascade",
        required=True
    )

    sequence = fields.Float("Sl. No")
    description = fields.Char("Description", required=True)
    page_no = fields.Char("Page No")



class PileLoadBasicData(models.Model):
    _name = "pile.load.basic.data"
    _description = "Pile Load Test Basic Data"

    parent_id = fields.Many2one(
        "pile.load.test.parent",
        ondelete="cascade",
        required=True
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
        required=True
    )

    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph", required=True)
    caption = fields.Char("Caption / Description")
