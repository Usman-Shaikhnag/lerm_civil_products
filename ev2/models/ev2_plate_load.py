from odoo import models, fields, api
# from ..json_field import JsonField/
import json
import hmac
import hashlib
import base64
import qrcode
import io
from io import BytesIO
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfFileMerger


import logging
_logger = logging.getLogger(__name__)

class EV2PlateLoadTest(models.Model):
    _name = "ev2.plate.load.test"
    _description = "EV2 Plate Load Test"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "report_no"

    project_name = fields.Char("Project Name", compute="_compute_eln_data", store=True)
    site_address = fields.Char("Site Address", compute="_compute_eln_data", store=True)
    test_start_date = fields.Date("Test Start Date", compute="_compute_eln_data", store=True)
    test_end_date = fields.Date("Test End Date", compute="_compute_eln_data", store=True)
    location = fields.Char("Location")
    consultant = fields.Char("Consultant")
    plate_size = fields.Char("Size of Plate")
    epc_contractor = fields.Char("EPC Contractor")
    letter_dated = fields.Date("Letter Dated On")
    references = fields.Char("References")
    discipline = fields.Char("Discipline", compute="_compute_eln_data", store=True)
    group = fields.Char("Group", compute="_compute_eln_data", store=True)
    test_name = fields.Char("Test Name", compute="_compute_eln_data", store=True)
    report_no = fields.Char("Report No", compute="_compute_eln_data", store=True)
    ulr_no = fields.Char("ULR No", compute="_compute_eln_data", store=True)
    report_issue_date = fields.Date("Report Issue Date")
    client = fields.Char("Client")

    eln_ref = fields.Many2one('lerm.eln', string="ELN")
    srf_id = fields.Many2one('lerm.civil.srf', string="SRF")
    sample_id = fields.Many2one('lerm.srf.sample', string="Sample")

    ev2_report_upload = fields.Many2many(
        'ir.attachment',
        'ev2_report_upload_rel',
        'sample_id',
        'attachment_id',
        string='Report Upload',
        help='Attach multiple reports or PDFs to the sample',
    )

    @api.depends('eln_ref', 'srf_id', 'sample_id')
    def _compute_eln_data(self):
        for record in self:
            if record.eln_ref:
                eln = record.eln_ref
                srf = record.srf_id or eln.srf_id
                sample = record.sample_id or eln.sample_id
                
                record.project_name = srf.name_work.project_name if srf and srf.name_work else ""
                record.site_address = srf.site_address if srf else ""
                record.test_start_date = eln.start_date
                record.test_end_date = eln.end_date
                record.discipline = eln.discipline.discipline if eln.discipline else ""
                record.group = eln.group.group if eln.group else ""
                record.test_name = eln.material.name if eln.material else ""
                record.epc_contractor = srf.contractor.name if srf and srf.contractor else ""
                record.client = srf.client if srf and srf.client else ""
                record.report_no = sample.kes_no if sample else ""
                record.ulr_no = sample.ulr_no if sample else ""
                
                # Fetching test method from the first parameter
                record.references = eln.material.method_reference if eln.material and eln.material.method_reference else ""

                record.plate_size = eln.size_id.size if eln.size_id else ""

    # =====================================================
    # TEST DETAILS
    # =====================================================

    plate_diameter_mm = fields.Float(
        string="Plate Diameter (mm)",
        default=300.0,
        digits=(16, 2),
        required=True,
    )

    initial_reading = fields.Float(
        string="Initial Dial Gauge Reading",
        digits=(16, 2),
        required=True,
    )

    # =====================================================
    # OBSERVATIONS
    # =====================================================

    line_ids = fields.One2many(
        comodel_name="ev2.plate.load.test.line",
        inverse_name="test_id",
        string="Readings",
        copy=True,
    )

    # =====================================================
    # RESULTS
    # =====================================================

    ev1 = fields.Float(
        string="EV1 (MN/m²)",
        digits=(16, 2),
        compute="_compute_ev_results",
        store=True,
    )

    ev2 = fields.Float(
        string="EV2 (MN/m²)",
        digits=(16, 2),
        compute="_compute_ev_results",
        store=True,
    )

    ev_ratio = fields.Float(
        string="EV2 / EV1",
        digits=(16, 2),
        compute="_compute_ev_results",
        store=True,
    )

    # =====================================================
    # CURVE FITTING COEFFICIENTS
    # =====================================================

    ev1_a0 = fields.Float(
        string="EV1 A0",
        digits=(16, 4),
        compute="_compute_ev_results",
        store=True,
    )

    ev1_a1 = fields.Float(
        string="EV1 A1",
        digits=(16, 4),
        compute="_compute_ev_results",
        store=True,
    )

    ev1_a2 = fields.Float(
        string="EV1 A2",
        digits=(16, 4),
        compute="_compute_ev_results",
        store=True,
    )

    ev2_a0 = fields.Float(
        string="EV2 A0",
        digits=(16, 4),
        compute="_compute_ev_results",
        store=True,
    )

    ev2_a1 = fields.Float(
        string="EV2 A1",
        digits=(16, 4),
        compute="_compute_ev_results",
        store=True,
    )

    ev2_a2 = fields.Float(
        string="EV2 A2",
        digits=(16, 4),
        compute="_compute_ev_results",
        store=True,
    )

    sigma_max_ev1 = fields.Float(
        string="σ Max EV1",
        digits=(16, 2),
        compute="_compute_ev_results",
        store=True,
    )

    sigma_max_ev2 = fields.Float(
        string="σ Max EV2",
        digits=(16, 2),
        compute="_compute_ev_results",
        store=True,
    )
    # =====================================================
    # GENERATED GRAPHS
    # =====================================================

    main_graph = fields.Image(
        string="Main Load Settlement Graph",
        readonly=True,
        attachment=True,
    )

    ev1_graph = fields.Image(
        string="EV1 Graph",
        readonly=True,
        attachment=True,
    )

    ev2_graph = fields.Image(
        string="EV2 Graph",
        readonly=True,
        attachment=True,
    )

    content_ids = fields.One2many('ev2.report.content', 'test_id',string="Table of Contents")
    # =====================================================
    # REPORT TEXT
    # =====================================================

    introduction = fields.Html(string="Introduction")
    scope = fields.Html(string="Scope")
    setup_equipment = fields.Html(string="Setup & Equipments Used")
    test_procedure = fields.Html(string="Test Procedure")
    result_discussion = fields.Html(string="Results & Discussion")
    conclusion = fields.Html(string="Conclusion")

    def _get_plate_size_key(self):
        self.ensure_one()

        size = (self.plate_size or "").lower()

        if "300" in size:
            return 300

        if "600" in size:
            return 600

        if "762" in size:
            return 762

        return 300

    PLATE_DATA = {
        300: {
            "loading_1": [
                (1, 0.71, 0.010),
                (2, 5.65, 0.080),
                (3, 11.31, 0.160),
                (4, 16.96, 0.240),
                (5, 22.62, 0.320),
                (6, 28.27, 0.400),
                (7, 31.81, 0.450),
                (8, 35.34, 0.500),
            ],
            "rebound": [
                (9, 35.34, 0.500),
                (10, 17.67, 0.250),
                (11, 8.84, 0.125),
                (12, 0.71, 0.010),
            ],
            "loading_2": [
                (13, 0.71, 0.010),
                (14, 5.65, 0.080),
                (15, 11.31, 0.160),
                (16, 16.96, 0.240),
                (17, 22.62, 0.320),
                (18, 28.27, 0.400),
                (19, 31.81, 0.450),
            ]
        },

        600: {
            "loading_1": [
                (1, 0.28, 0.001),
                (2, 5.65, 0.020),
                (3, 11.31, 0.040),
                (4, 22.62, 0.080),
                (5, 33.93, 0.120),
                (6, 45.24, 0.160),
                (7, 56.55, 0.200),
                (8, 70.69, 0.250),
            ],
            "rebound": [
                (9, 70.69, 0.250),
                (10, 17.67, 0.120),
                (11, 8.84, 0.060),
                (12, 0.71, 0.020),
            ],
            "loading_2": [
                (13, 5.65, 0.020),
                (14, 11.31, 0.040),
                (15, 22.62, 0.080),
                (16, 33.93, 0.120),
                (17, 45.24, 0.160),
                (18, 56.55, 0.200),
            ]
        },

        762: {
            "loading_1": [
                (1, 0.46, 0.001),
                (2, 4.56, 0.010),
                (3, 9.12, 0.020),
                (4, 18.24, 0.040),
                (5, 36.48, 0.080),
                (6, 54.72, 0.120),
                (7, 72.96, 0.160),
                (8, 91.21, 0.200),
            ],
            "rebound": [
                (9, 91.21, 0.200),
                (10, 17.67, 0.160),
                (11, 8.84, 0.120),
                (12, 0.71, 0.010),
            ],
            "loading_2": [
                (13, 4.56, 0.010),
                (14, 9.12, 0.020),
                (15, 18.24, 0.040),
                (16, 36.48, 0.080),
                (17, 54.72, 0.120),
                (18, 72.96, 0.160),
            ]
        },
    }

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if not record.line_ids:

            plate_key = record._get_plate_size_key()
            table = self.PLATE_DATA.get(plate_key, {})

            line_vals = []
            sequence = 1
            for phase_seq, cycle_type in enumerate(
                ["loading_1", "rebound", "loading_2"],
                start=1
            ):

                for stage_no, load_kn, stress in table.get(cycle_type, []):

                    line_vals.append((0, 0, {
                        "sequence": sequence,
                        "cycle_type": cycle_type,
                        "stage_no": stage_no,
                        "load_kn": load_kn,
                        "nominal_stress": stress,
                        "phase_sequence": phase_seq,
                    }))

                    sequence += 1

            record.write({
                "line_ids": line_vals
            })
        record.write({
            'content_ids': [
                (0, 0, {'sequence': 1, 'title': 'INTRODUCTION'}),
                (0, 0, {'sequence': 2, 'title': 'SCOPE'}),
                (0, 0, {'sequence': 3, 'title': 'SETUP & EQUIPMENTS USED'}),
                (0, 0, {'sequence': 4, 'title': 'TEST PROCEDURE'}),
                (0, 0, {'sequence': 5, 'title': 'RESULTS AND DISCUSSION'}),
                (0, 0, {'sequence': 6, 'title': 'NATURE LOAD vs SETTLEMENT CURVE'}),
                (0, 0, {'sequence': 7, 'title': 'POLYNOMIAL LOAD vs SETTLEMENT CURVE'}),
                (0, 0, {'sequence': 8, 'title': 'EV-2 INSTRUMENT SETUP'}),
                (0, 0, {'sequence': 8, 'title': 'MEASURED VALUE FOR FIRST LOADING CYCLE AND UNLOADING CYCLE'}),
                (0, 0, {'sequence': 8, 'title': 'MEASURED VALUE FOR SECOND LOADING CYCLE'}),
                (0, 0, {'sequence': 8, 'title': 'COMPUTATION OF RESULT'}),
            ]
            })
        record.write({
                'introduction': f'''
                    <p style="line-height:1.8;">
                        The EV-2 Plate Load test was conducted for {record.srf_id.customer.name},
                        as per instructions from project proponents and Design Consultants.
                        This report of EV-2 Plate Load Test is as per DIN 18134:2012-04.
                    </p>
                ''',

                'scope': '''
                    <ul style="line-height:1.8;">
                        <li>Mobilization of load test set-up</li>
                        <li>Erection of test setup</li>
                        <li>Carry out load test</li>
                        <li>Recording load versus settlement data</li>
                        <li>Analysis and interpretation of data and preparation of technical report.</li>
                    </ul>
                ''',

                'setup_equipment': f'''
                    <ul style="line-height:1.8;">
                        <li>Plate Loading Apparatus consisting {record.plate_size} mm Loading Plate, Dial Gauge and Settlement Measuring Bridge.</li>
                        <li>Loading System comprising hydraulic Jack 100 MT, Hydraulic Hand Pump and flexible hose pipe.</li>
                        <li>Extension pieces 150 mm × 2 and 50 mm × 2 as spacers.</li>
                        <li>Tripod settlement measuring unit with dial gauge range 25 mm × 0.01 mm.</li>
                    </ul>
                ''',

                'test_procedure': '''
                    <ul style="line-height:1.8;">
                        <li>An area sufficiently large to receive the loading plate shall be levelled using suitable tools (e.g. steel straightedge or trowel) or by turning or working the loading plate back and forth. Any loose material shall be removed.</li>

                        <li>The loading plate shall lie on, and be in full contact with the test surface. If necessary, a thin bed (only a few millimetres thick) of dry medium-grained sand shall be used.</li>

                        <li>The hydraulic jack shall be placed onto the middle of and at right angles to the loading plate beneath the reaction loading system and secured against tilting.</li>

                        <li>Care shall be taken to ensure that the loading system remains stable throughout the test.</li>

                        <li>Measurement of settlement shall be carried out using a dial gauge.</li>

                        <li>The stylus shall be placed at the centre of the loading plate and the dial gauge shall be set vertically.</li>

                        <li>Ensure the stylus can pass freely into the measuring tunnel and is positioned centrally on the plate.</li>

                        <li>The gauge shall not be reset to zero until at least 30 seconds after the preload has been applied.</li>

                        <li>To determine the strain modulus EV, the load shall be applied in eight stages with approximately equal increments until the required maximum stress is reached. The load shall then be released in three stages (50%, 25%, and approximately 2%), followed by the second loading cycle up to the penultimate stage.</li>

                        <li>Each loading stage shall be maintained for 120 seconds before proceeding to the next stage, and the settlement reading shall be recorded at the end of each stage.</li>

                        <li>If a higher load than intended is inadvertently applied, it shall be maintained and noted in the test report.</li>
                    </ul>
                ''',
            })
        if record.eln_ref:
            record.eln_ref.write({'model_id': record.id})

        return record

    def _fig_to_base64(self, fig):
        buffer = io.BytesIO()

        fig.savefig(
            buffer,
            format='png',
            bbox_inches='tight',
            dpi=150
        )

        plt.close(fig)

        buffer.seek(0)

        return base64.b64encode(
            buffer.read()
        )

    def _generate_ev_graph(
        self,
        stress,
        settlement,
        a0,
        a1,
        a2,
        title,
    ):
        fig, ax = plt.subplots(
            figsize=(6, 4),
            facecolor='white'
        )

        ax.set_facecolor('white')

        ax.scatter(
            stress,
            settlement,
            s=50,
            color='blue',
            zorder=3
        )

        x_fit = np.linspace(
            min(stress),
            max(stress),
            200
        )

        y_fit = (
            a2 * x_fit**2
            + a1 * x_fit
            + a0
        )

        ax.plot(
            x_fit,
            y_fit,
            color='blue',
            linewidth=2
        )

        ax.set_title(title)

        ax.set_xlabel(
            "Nominal Stress (N/mm²)"
        )

        ax.set_ylabel(
            "Settlement (mm)"
        )

        ax.grid(True)

        return self._fig_to_base64(fig)

    def _generate_main_graph(self):
        self.ensure_one()

        loading1 = self.line_ids.filtered(
            lambda l: l.cycle_type == 'loading_1'
        ).sorted('stage_no')

        rebound = self.line_ids.filtered(
            lambda l: l.cycle_type == 'rebound'
        ).sorted('stage_no')

        loading2 = self.line_ids.filtered(
            lambda l: l.cycle_type == 'loading_2'
        ).sorted('stage_no')

        fig, ax = plt.subplots(
            figsize=(7, 5)
        )

        # -------------------------
        # First Stage Loading
        # -------------------------
        if loading1:

            x1 = [
                l.nominal_stress
                for l in loading1
            ]

            y1 = [
                l.settlement
                for l in loading1
            ]

            ax.plot(
                x1,
                y1,
                marker='D',
                linewidth=1.5,
                label='1st stage loading'
            )

        # -------------------------
        # Unloading
        # -------------------------
        if rebound:

            xr = [
                l.nominal_stress
                for l in rebound
            ]

            yr = [
                l.settlement
                for l in rebound
            ]

            ax.plot(
                xr,
                yr,
                marker='s',
                linewidth=1.5,
                label='unloading'
            )

        # -------------------------
        # Second Stage Loading
        # -------------------------
        if loading2:

            x2 = [
                l.nominal_stress
                for l in loading2
            ]

            y2 = [
                l.settlement
                for l in loading2
            ]

            ax.plot(
                x2,
                y2,
                marker='o',
                linewidth=1.5,
                label='2nd stage loading'
            )

        _logger.info("LOADING 1 POINTS: %s", list(zip(x1, y1)))
        _logger.info("REBOUND POINTS: %s", list(zip(xr, yr)))
        _logger.info("LOADING 2 POINTS: %s", list(zip(x2, y2)))

        # -------------------------
        # Excel-style formatting
        # -------------------------
        ax.set_title(
            'Normal Stress (MN/m²)',
            fontsize=10,
            pad=12
        )

        ax.set_ylabel(
            'Displacement (mm)'
        )

        # Move X axis to top like Excel
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')

        # Settlement increases downward
        ax.invert_yaxis()

        ax.grid(
            True,
            linestyle='-',
            linewidth=0.5
        )

        ax.legend(
            loc='upper right'
        )

        fig.tight_layout()

        return self._fig_to_base64(fig)



    @api.depends('line_ids.nominal_stress','line_ids.settlement','plate_diameter_mm')
    def _compute_ev_results(self):
        for rec in self:

            # -------------------------
            # EV1 DATA
            # -------------------------
            loading1 = rec.line_ids.filtered(
                lambda l:
                    l.cycle_type == 'loading_1'
                    and l.settlement
            ).sorted('stage_no')
            
            loading1 = loading1[1:]

            if len(loading1) >= 3:

                stress = np.array([
                    l.nominal_stress for l in loading1
                ])

                settlement = np.array([
                    l.settlement for l in loading1
                ])

                # import wdb; wdb.set_trace()
                a2, a1, a0 = np.polyfit(
                    stress,
                    settlement,
                    2
                )

                rec.ev1_a0 = a0
                rec.ev1_a1 = a1
                rec.ev1_a2 = a2

                sigma_max = max(stress)

                rec.sigma_max_ev1 = sigma_max

                radius = rec.plate_diameter_mm

                denominator = a1 + (a2 * sigma_max)

                if denominator:
                    rec.ev1 = (0.75 * radius) / denominator
                
                rec.ev1_graph = rec._generate_ev_graph(stress,settlement,a0,a1,a2,"EV1 Polynomial Fit")

            # -------------------------
            # EV2 DATA
            # -------------------------
            loading2 = rec.line_ids.filtered(
                lambda l:
                    l.cycle_type == 'loading_2'
                    and l.settlement
                ).sorted('stage_no')

            loading2 = loading2[1:]

            if len(loading2) >= 3:

                stress = np.array([
                    l.nominal_stress for l in loading2
                ])

                settlement = np.array([
                    l.settlement for l in loading2
                ])

                a2, a1, a0 = np.polyfit(
                    stress,
                    settlement,
                    2
                )

                rec.ev2_a0 = a0
                rec.ev2_a1 = a1
                rec.ev2_a2 = a2

                sigma_max = max(stress)

                rec.sigma_max_ev2 = sigma_max

                radius = rec.plate_diameter_mm

                denominator = a1 + (a2 * sigma_max)

                if denominator:
                    rec.ev2 = (0.75 * radius) / denominator

                rec.ev2_graph = rec._generate_ev_graph(stress,settlement,a0,a1,a2,"EV2 Polynomial Fit")

            if rec.ev1:
                rec.ev_ratio = rec.ev2 / rec.ev1
                rec.main_graph = rec._generate_main_graph()
            
 

class EV2PlateLoadTestLine(models.Model):
    _name = "ev2.plate.load.test.line"
    _description = "EV2 Plate Load Test Line"
    _order = "sequence"

    test_id = fields.Many2one(
        "ev2.plate.load.test",
        string="EV2 Test",
        required=True,
        ondelete="cascade",
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )

    cycle_type = fields.Selection(
        [
            ("loading_1", "1st Loading"),
            ("rebound", "Rebound"),
            ("loading_2", "2nd Loading"),
        ],
        string="Cycle",
        required=True,
    )

    nominal_stress = fields.Float(
        string="Nominal Stress (MN/m²)",
        digits=(16, 3),
        required=True,
    )

    pressure_gauge_reading = fields.Float(
        string="Pressure Gauge Reading",
        digits=(16, 2),
    )

    dial_gauge_reading = fields.Float(
        string="Dial Gauge Reading",
        digits=(16, 2),
    )

    settlement = fields.Float(
        string="Settlement (mm)",
        digits=(16, 2),
        compute="_compute_settlement",
        store=True,
        readonly=True,
    )

    @api.depends("dial_gauge_reading","test_id.initial_reading")
    def _compute_settlement(self):
        for rec in self:
            if rec.dial_gauge_reading:
                rec.settlement = (rec.test_id.initial_reading - rec.dial_gauge_reading)
            else:
                rec.settlement = 0.0
    
    phase_sequence = fields.Integer(string="Phase Sequence")

    stage_no = fields.Integer(
        string="Stage No",
    )

    load_kn = fields.Float(
        string="Load (kN)",
        digits=(16, 2),
    )


class Ev2ReportContent(models.Model):
    _name = "ev2.report.content"

    sequence = fields.Integer()
    title = fields.Char()
    page_no = fields.Integer()
    test_id = fields.Many2one("ev2.plate.load.test")


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, docids, data=None):
        content, content_type = super()._render_qweb_pdf(report_ref, docids, data=data)
        if report_ref == 'ev2.ev2_plate_load_test_report':
            content = self._append_ev2_report_uploads(docids, content, data=data)
        return content, content_type

    def _append_ev2_report_uploads(self, docids, content, data=None):
        if isinstance(docids, int):
            docids = [docids]

        eln_model = self.env['lerm.eln'].sudo()
        sample_model = self.env['lerm.srf.sample'].sudo()
        eln_ids = set()

        # data['sample'] / context['active_id'] are SAMPLE ids (same as _get_report_values)
        sample_candidates = []
        if data:
            if data.get('sample'):
                sample_candidates.append(data['sample'])
            ctx = data.get('context') or {}
            if ctx.get('active_id'):
                sample_candidates.append(ctx['active_id'])
        for cid in sample_candidates:
            sample = sample_model.browse(cid)
            if sample.exists() and sample.eln_id:
                eln_ids.add(sample.eln_id.id)

        # docids are ELN ids (report bound to lerm.eln)
        for eln_id in docids or []:
            eln = eln_model.browse(eln_id)
            if eln.exists():
                eln_ids.add(eln_id)

        uploads = self.env['ir.attachment'].sudo()
        for eln_id in eln_ids:
            eln = eln_model.browse(eln_id)
            ev2 = self.env['ev2.plate.load.test'].sudo().search(
                [('eln_ref', '=', eln_id)], limit=1
            )
            if ev2:
                uploads |= ev2.ev2_report_upload
            if eln:
                uploads |= eln.file_upload
                if eln.sample_id:
                    uploads |= eln.sample_id.file_upload | eln.sample_id.report_upload

        pdfs = []
        for att in uploads.sorted('id'):
            if att.datas and (att.mimetype or '').startswith('application/pdf'):
                pdfs.append(b64decode(att.datas))
        if not pdfs:
            return content

        # Prefer Odoo's merge_pdf: it picks the most capable PDF backend available.
        try:
            from odoo.tools.pdf import merge_pdf
            return merge_pdf([content] + pdfs)
        except Exception:
            pass

        if not PdfFileMerger:
            return content

        try:
            merger = PdfFileMerger()
            merger.append(BytesIO(content), import_bookmarks=False)
            for pdf in pdfs:
                try:
                    merger.append(BytesIO(pdf), import_bookmarks=False)
                except Exception:
                    continue
            output = BytesIO()
            merger.write(output)
            merger.close()
            return output.getvalue()
        except Exception:
            return content



class Ev2PlateLoadTestReport(models.AbstractModel):
    _name = 'report.ev2.ev2_plate_load_test_report'
    _description = 'Ev2 Plate Load Test Report'
    
    @api.model
    def _get_report_values(self, docids, data):
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['sample'])])
        elif 'active_id' in data['context']:
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)
        
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(eln.kes_no)
        qr.make(fit=True)
        qr_image = qr.make_image()

        # Convert the QR code image to base64 string
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300)
        buf.seek(0)
        graph_image_base64 = base64.b64encode(buf.read()).decode()
        buf.close()
        plt.close()
        

        model_id = eln.model_id
        model_name = eln.material.product_based_calculation[0].ir_model.model if eln.material.product_based_calculation else None
        # import wdb;wdb.set_trace()
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)

        # import wdb;wdb.set_trace()
        return {
            'eln': eln,
            'data': general_data,
            'qrcode': qr_image_base64,
            # 'graph': graph_image_base64,
            'stamp': inreport_value,
            'nabl': nabl,
        }