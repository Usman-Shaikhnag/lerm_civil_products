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
                    p = float(row.get("t/m2", 0) or 0)
                    s = float(row.get("mm", 0) or 0)

                    # 🔥 CRITICAL FIX
                    if p == 0 and s == 0:
                        continue

                    x_vals.append(p)
                    y_vals.append(s)

                except:
                    continue

            if force_zero_start:
                if x_vals and (x_vals[0] != 0 or y_vals[0] != 0):
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

        # -------- Plot --------
        plt.figure(figsize=(7, 4))

        # Loading curve
        plt.plot(x_up_s, y_up_s, color="#1e3a5f", linewidth=2.5)
        plt.scatter(x_loading, y_loading, color='black', s=25, marker='D')

        # Unloading curve
        if x_unloading:
            plt.plot(x_down_s, y_down_s, color="#1e3a5f", linewidth=2.5)
            plt.scatter(x_unloading, y_unloading, color='gray', s=25, marker='D')

        plt.gca().invert_yaxis()
        ax = plt.gca()

        # Move x-axis to top
        ax.xaxis.set_label_position('top')
        ax.xaxis.tick_top()

        # ax.set_xlim(left=0)
        # ax.margins(x=0)

        ax.tick_params(bottom=False)
        plt.xlabel('Pressure under Plate (T/m²)', fontsize=10)
        plt.ylabel('Cumulative Settlement (mm)', fontsize=10)
        plt.title('LOAD SETTLEMENT CURVE', fontsize=14, fontweight='bold')

        plt.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=200)
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')
    # ---------------- PDF GENERATION ---------------- #

    def generate_pdf_report(self):
        import os
        buffer = io.BytesIO()

        # Adjust margins to allow header/footer space
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=1.6 * inch,
            bottomMargin=1.2 * inch,
            leftMargin=0.8 * inch,
            rightMargin=0.8 * inch,
        )

        elements = []
        styles = getSampleStyleSheet()

        # ---------- STYLES ----------
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#1e3a5f'),
            alignment=1,
            spaceAfter=12,
        )

        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#1e3a5f'),
            spaceBefore=12,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
        )

        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            alignment=1,
            fontName='Helvetica-Bold',
        )

        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=9,
            alignment=1,
        )

        # ---------- HEADER + FOOTER ----------
        def add_header_footer(canvas, doc):
            width, height = A4

            # --- HEADER IMAGE ---
            module_path = os.path.dirname(os.path.abspath(__file__))
            header_path = os.path.join(module_path, 'static', 'src', 'img', 'Knack_Header.png')

            if os.path.exists(header_path):
                canvas.drawImage(
                    header_path,
                    x=0.6 * inch,
                    y=height - 1.2 * inch,
                    width=7 * inch,
                    height=0.9 * inch,
                    preserveAspectRatio=True,
                    mask='auto'
                )

            # --- FOOTER TEXT ---
            footer_text_1 = "Testing Location: Taloja Laboratory [Shop No 11, Skyline Sapphire, Sector 7, Taloja Phase 1, Navi Mumbai- 410208]"
            footer_text_2 = "Regd. Office: Shop no. 3 & 105 Bldg. B1, Wadala Truck Terminal, MMRDA Compound, Antop Hill, Mumbai- 400037"
            footer_text_3 = "Tel.: +91 22 2401 0040 | Email: sales@knackengineeringservices.com | Website: www.knackengineeringservices.com | CIN: U45209MH2017PTC291168"

            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(width / 2, 0.9 * inch, footer_text_1)
            canvas.drawCentredString(width / 2, 0.7 * inch, footer_text_2)
            canvas.drawCentredString(width / 2, 0.5 * inch, footer_text_3)

            # --- PAGE NUMBER ---
            page_number_text = f"Page {doc.page}"
            canvas.drawRightString(width - 0.6 * inch, 0.3 * inch, page_number_text)

        # ---------- TITLE ----------
        elements.append(Paragraph("<b>PLATE LOAD TEST REPORT</b>", title_style))
        elements.append(Spacer(1, 12))

        # ---------- SECTIONS ----------
        sections = self.sections_data or {}

        for key in ["objective", "introduction", "procedure"]:
            text = sections.get(key)
            if text:
                elements.append(Paragraph(f"<b>{key.title()}</b>", heading_style))
                elements.append(Paragraph(text, body_style))

        # ---------- TABLE FUNCTION ----------
        def add_table(data, cols_data, title):
            if not data:
                return

            elements.append(Paragraph(f"<b>{title}</b>", heading_style))
            elements.append(Spacer(1, 6))

            if cols_data:
                headers = [col.get('headerName', '') for col in cols_data]
                fields = [col.get('field', '') for col in cols_data]
            else:
                fields = list(data[0].keys())
                headers = fields

            header_row = [Paragraph(h, table_header_style) for h in headers]

            body_rows = []
            for row in data:
                body_rows.append([
                    Paragraph(str(row.get(f, "")), table_cell_style)
                    for f in fields
                ])

            table_data = [header_row] + body_rows

            table = Table(table_data, repeatRows=1)

            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 16))

        # ---------- TABLES ----------
        add_table(self.loading_table_data, self.loading_columns_data, "Loading Test Data")
        add_table(self.unloading_table_data, self.unloading_columns_data, "Unloading Test Data")

        # ---------- GRAPH ----------
        if self.graph:
            elements.append(Paragraph("<b>Load Settlement Curve</b>", heading_style))
            elements.append(Spacer(1, 6))
            img_data = base64.b64decode(self.graph)
            image = Image(io.BytesIO(img_data), width=5.5 * inch, height=3.2 * inch)
            elements.append(image)
            elements.append(Spacer(1, 16))

        # ---------- IMAGE SECTIONS ----------
        for section in self.image_sections or []:
            title = section.get('title', 'Images')
            elements.append(Paragraph(f"<b>{title}</b>", heading_style))
            elements.append(Spacer(1, 6))

            for img in section.get("images", []):
                img_data = base64.b64decode(img)
                image = Image(io.BytesIO(img_data), width=4.5 * inch, height=3 * inch)
                elements.append(image)
                elements.append(Spacer(1, 10))

        # ---------- BUILD DOCUMENT ----------
        doc.build(
            elements,
            onFirstPage=add_header_footer,
            onLaterPages=add_header_footer
        )

        buffer.seek(0)
        return base64.b64encode(buffer.read())

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
                if (load is not None and str(load).strip() != "") or (settlement is not None and str(settlement).strip() != ""):
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