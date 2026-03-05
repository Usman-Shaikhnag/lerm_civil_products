from odoo import models, fields, api
import json
import hmac
import hashlib
import base64
import io
import numpy as np
import matplotlib
matplotlib.use('Agg')
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


class PlateLoadTest(models.Model):
    _name = "lerm.plate.load.test"
    _rec_name = "project_name"

    # --- Meta / Cover Block ---
    project_name = fields.Char("Project Name")
    site_address = fields.Char("Site Address")
    test_start_date = fields.Date("Test Start Date")
    test_end_date = fields.Date("Test End Date")
    location = fields.Char("Location")
    strata = fields.Char("Strata")
    plate_size = fields.Char("Size of Plate", default="300 x 300 mm")
    concessionaire = fields.Char("Concessionaire")
    pmc_name = fields.Char("PMC Name")
    epc_contractor = fields.Char("EPC Contractor")
    letter_dated = fields.Date("Letter Dated On")
    discipline = fields.Char("Discipline")
    group = fields.Char("Group")
    references = fields.Char("References", default="IS 1888: 1982")
    test_name = fields.Char("Test Name", default="Plate Load Test")
    report_no = fields.Char("Report No")
    ulr_no = fields.Char("ULR No")

    # --- Sections (text blocks) ---
    sections_data = fields.Json(default=dict)
    # Keys: 'introduction', 'objective', 'apparatus', 'procedure', 'conclusion'

    # --- Loading Table ---
    loading_columns_data = fields.Json(string="Loading Columns", default=list)
    loading_table_data = fields.Json(string="Loading Table", default=list)

    # --- Unloading Table (Annexure - combined load/unload) ---
    unloading_columns_data = fields.Json(string="Unloading Columns", default=list)
    unloading_table_data = fields.Json(string="Unloading Table", default=list)

    # --- Summary / Safe Bearing Capacity ---
    safe_bearing_capacity = fields.Float("Safe Bearing Capacity (t/m²)")
    factor_of_safety = fields.Float("Factor of Safety")
    ultimate_bearing_capacity = fields.Float("Ultimate Bearing Capacity (t/m²)")
    max_load_intensity = fields.Float("Maximum Load Intensity (t/m²)")
    allowable_bearing_capacity = fields.Float("Allowable Bearing Capacity (t/m²)")
    total_settlement = fields.Float("Total Settlement (mm)")

    # --- Signature Block ---
    checked_by_name = fields.Char("Checked By - Name")
    checked_by_title = fields.Char("Checked By - Title")
    approved_by_name = fields.Char("Approved By - Name")
    approved_by_title = fields.Char("Approved By - Title")

    # --- Annexures ---
    graph = fields.Binary("Load Settlement Graph")
    image_sections = fields.Json(default=list)
    # Each item: { 'title': 'Site Photographs', 'images': [base64, ...] }
    # Add a 'Site Datasheet' section the same way

    pdf_report = fields.Binary("PDF Report")
    pdf_filename = fields.Char(default="Plate_Load_Test_Report.pdf")
    contents_ids = fields.One2many(
        "lerm.plate.load.test.contents",
        "plate_load_test_id",
        string="Table of Contents"
    )
    # ---------------- TOKEN LOGIC ---------------- #
    def _get_secret_key(self):
        key = self.env['ir.config_parameter'].sudo().get_param('plate_load_secret_key')
        if not key:
            raise ValueError("Set 'plate_load_secret_key' in system parameters.")
        return key

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if not record.contents_ids:
            default_lines = [
                {"sr_no": "1", "item": "Introduction", "page": "3"},
                {"sr_no": "2", "item": "Objective", "page": "3"},
                {"sr_no": "3", "item": "Apparatus", "page": "3"},
                {"sr_no": "4", "item": "Setup & Test Procedure", "page": "3"},
                {"sr_no": "5", "item": "Load vs Settlement Data & Safe Bearing Capacity", "page": "4"},
                {"sr_no": "6", "item": "ANNEXURES", "page": "5"},
                {"sr_no": "", "item": "I. Calculation", "page": "5"},
                {"sr_no": "", "item": "II. Load Intensity vs Settlement Graph", "page": "6"},
                {"sr_no": "", "item": "III. Site Datasheet", "page": "7"},
                {"sr_no": "", "item": "IV. Site Photographs", "page": "8"},
            ]

            for line in default_lines:
                self.env["lerm.plate.load.test.contents"].create({
                    "plate_load_test_id": record.id,
                    "sr_no": line["sr_no"],
                    "item": line["item"],
                    "page": line["page"],
                })

        return record

    def open_form(self):
        self.ensure_one()
        secret_key = self._get_secret_key()

        data = {
            "form_id": self.id,
            "uid": self.env.user.id,
        }

        payload = json.dumps(data, separators=(',', ':'))
        signature = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        token = base64.urlsafe_b64encode(
            json.dumps({"data": data, "sig": signature}).encode()
        ).decode()

        react_url = f"http://147.93.154.53:5173/plate_load_test?token={token}"

        return {
            'type': 'ir.actions.act_url',
            'url': react_url,
            'target': 'new'
        }

    # ---------------- CHART GENERATION ---------------- #

    def generate_pressure_line_chart(self, loading_data, unloading_data):
        # -------- Extract Pressure & Settlement --------
        def extract_vals(data, force_zero_start=False):
            x_vals = []
            y_vals = []

            for row in data:
                try:
                    # Robust key picking
                    p = row.get("t/m2") or row.get("t/m\u00B2") or row.get("load") or row.get("Load") or row.get("applied_pressure")
                    s = row.get("mm") or row.get("settlement") or row.get("Settlement") or row.get("cumulative_settlement")

                    if p is None or s is None:
                        continue

                    p = float(p)
                    s = float(s)

                    x_vals.append(p)
                    y_vals.append(s)

                except:
                    continue

            # Sort by pressure just in case
            if x_vals:
                combined = sorted(zip(x_vals, y_vals))
                x_vals, y_vals = zip(*combined)
                x_vals = list(x_vals)
                y_vals = list(y_vals)

            if force_zero_start:
                if not x_vals or (x_vals[0] != 0 or y_vals[0] != 0):
                    x_vals.insert(0, 0)
                    y_vals.insert(0, 0)

            return x_vals, y_vals


        x_loading, y_loading = extract_vals(loading_data, force_zero_start=True)
        x_unloading, y_unloading = extract_vals(unloading_data, force_zero_start=False)
        # import wdb;wdb.set_trace()
        if not x_loading:
            return ""

        # -------- Safe Spline --------
        def smooth(x, y):
            try:
                if len(x) < 3:
                    return x, y

                x_np = np.array(x)
                y_np = np.array(y)

                # If pressure not monotonic, skip smoothing
                if not np.all(np.diff(x_np) >= 0) and not np.all(np.diff(x_np) <= 0):
                    return x, y

                spline = make_interp_spline(x_np, y_np, k=2)
                x_s = np.linspace(min(x_np), max(x_np), 200)
                y_s = spline(x_s)

                return x_s, y_s

            except:
                return x, y


        x_up_s, y_up_s = smooth(x_loading, y_loading)
        x_down_s, y_down_s = smooth(x_unloading, y_unloading)

        # -------- Plot (Thread-Safe OO API) --------
        fig = Figure(figsize=(8, 5))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Loading curve
        ax.plot(x_up_s, y_up_s, color="#1e3a5f", linewidth=2.5, label="Loading")
        ax.scatter(x_loading, y_loading, color='black', s=25, marker='D', zorder=5)

        # Unloading curve
        if x_unloading:
            ax.plot(x_down_s, y_down_s, color="#1e3a5f", linewidth=2.5, label="Unloading")
            ax.scatter(x_unloading, y_unloading, color='black', s=25, marker='D', zorder=5)

        ax.invert_yaxis()

        # Move x-axis to top
        ax.xaxis.set_label_position('top')
        ax.xaxis.tick_top()
        ax.tick_params(bottom=False)

        ax.set_xlabel('Load Intensity (T/m\u00B2)', fontsize=10, fontweight='bold', labelpad=10)
        ax.set_ylabel('Cumulative Settlement (mm)', fontsize=10, fontweight='bold')
        
        fig.suptitle('LOAD SETTLEMENT CURVE', fontsize=14, fontweight='bold', y=0.05)

        ax.grid(True, linestyle='--', alpha=0.4)
        fig.tight_layout(rect=[0, 0.08, 1, 0.95])

        buffer = io.BytesIO()
        canvas.print_png(buffer)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    # ---------------- PDF GENERATION ---------------- #

    def print_report(self):
        return self.env.ref('fst.plate_load_test_pdf').report_action(self)
        

class PlateLoadTestContents(models.Model):
    _name = "lerm.plate.load.test.contents"
    _description = "Plate Load Test - Table of Contents"

    plate_load_test_id = fields.Many2one(
        "lerm.plate.load.test",
        string="Plate Load Test",
        ondelete="cascade"
    )

    sr_no = fields.Char("Sr. No")
    item = fields.Char("Item")
    page = fields.Char("Page")


class ReportPlateLoadTest(models.AbstractModel):
    _name = 'report.fst.plate_load_test_template'
    _description = 'Plate Load Test Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['lerm.plate.load.test'].browse(docids)

        result = {}

        for doc in docs:

            # --- Average Table (Table 1) ---
            average_table = []
            for row in doc.loading_table_data or []:
                # Try multiple keys for robustness
                load = row.get('t/m2') or row.get('load') or row.get('applied_pressure')
                settlement = row.get('mm') or row.get('settlement') or row.get('cumulative_settlement')
                load_t = row.get('t') or row.get('load_t') or row.get('load_plate')

                # Only include if at least one value is present and not empty
                average_table = []
                seen_first_zero = False

                for row in doc.loading_table_data or []:
                    load = row.get('t/m2') or row.get('load') or row.get('applied_pressure')
                    settlement = row.get('mm') or row.get('settlement') or row.get('cumulative_settlement')
                    load_t = row.get('t') or row.get('load_t') or row.get('load_plate')

                    # Normalize to check if both are effectively zero/empty
                    load_val = str(load).strip() if load is not None else ''
                    settlement_val = str(settlement).strip() if settlement is not None else ''

                    both_zero = (load_val in ('', '0', '0.0')) and (settlement_val in ('', '0', '0.0'))
                    both_empty = load_val == '' and settlement_val == ''

                    if both_empty:
                        continue  # skip fully empty rows always

                    if both_zero and not seen_first_zero:
                        seen_first_zero = True  # keep only the first 0/0 row
                        average_table.append({'load': '0.00', 'settlement': '0.00', 'load_t': load_t})
                        continue

                    if both_zero:
                        continue  # skip subsequent 0/0 rows

                    average_table.append({
                        'load': load,
                        'settlement': settlement,
                        'load_t': load_t,
                    })

            # --- Combined Graph Points ---
            combined_points = []

            # Loading
            for row in doc.loading_table_data or []:
                load = row.get('t/m2') or row.get('load') or row.get('applied_pressure')
                settlement = row.get('mm') or row.get('settlement') or row.get('cumulative_settlement')
                if (load is not None and str(load).strip() != "") or (settlement is not None and str(settlement).strip() != ""):
                    combined_points.append({
                        'load': load,
                        'settlement': settlement,
                    })

            # Unloading
            for row in doc.unloading_table_data or []:
                load = row.get('t/m2') or row.get('load') or row.get('applied_pressure')
                settlement = row.get('mm') or row.get('settlement') or row.get('cumulative_settlement')
                if (load is not None and str(load).strip() != "") or (settlement is not None and str(settlement).strip() != ""):
                    combined_points.append({
                        'load': load,
                        'settlement': settlement,
                    })

            result[doc.id] = {
                'average_table': average_table,
                'combined_graph_points': combined_points,
            }

        # print("result", result)
        return {
            'doc_ids': docids,
            'doc_model': 'lerm.plate.load.test',
            'docs': docs,
            'computed': result,
        }