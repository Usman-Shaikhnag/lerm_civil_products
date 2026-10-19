from odoo import api, fields, models
from odoo.tools.misc import file_open
from datetime import datetime, date, timedelta
import base64
import json
import re

import pytz

from . import uplift_calc
from . import uplift_graph
from . import uplift_test_data

# Pile load test arrangement (Section A-A and plan) of report KES260901159.
ARRANGEMENT_DRAWING = "fst_upload_lift_test/static/src/img/uplift_test_arrangement.png"

PROJECT_TITLE = (
    "WORK OF DESIGN, BUILD, OPERATION AND MAINTENANCE OF 418 MLD DHARAVI "
    "WASTEWATER TREATMENT FACILITY UNDER MUMBAI SEWAGE DISPOSAL PROJECT, "
    "STAGE II (PRIORITY WORKS)"
)


class FstUpliftLoadTest(models.Model):
    _name = "fst.uplift.load.test"
    _description = "Uplift Pile Load Test Report"
    _order = "rec_date desc, id desc"

    name = fields.Char("Project Name", compute="_compute_eln_fields", store=True, readonly=False)
    rec_date = fields.Date("Report Date")
    work_name = fields.Char("Name of Work", compute="_compute_eln_fields", store=True, readonly=False)
    client = fields.Char(string="Client", compute="_compute_eln_fields", store=True, readonly=False)
    contractor = fields.Char(string="Contractor", compute="_compute_eln_fields", store=True, readonly=False)
    lab_id = fields.Many2one('lerm.lab.master', string="Lab Name")

    ulr = fields.Char("ULR No", copy=False, compute="_compute_eln_fields", store=True)
    report_no = fields.Char("Report No", copy=False, compute="_compute_eln_fields", store=True)
    pile_no = fields.Char("Pile No / Location")
    site_location = fields.Char("Site Location", compute="_compute_eln_fields", store=True, readonly=False)
    test_standard = fields.Char("Test Standard", compute="_compute_eln_fields", store=True, readonly=False)

    srf_id = fields.Many2one('lerm.civil.srf', string="SRF", readonly=True)
    sample_id = fields.Many2one('lerm.srf.sample', string="Sample", readonly=True)
    eln_ref = fields.Many2one('lerm.eln', string="ELN", readonly=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter", readonly=True)

    discipline = fields.Char("Discipline", compute="_compute_srf_data", store=True)
    group = fields.Char("Group", compute="_compute_srf_data", store=True)

    # ================= TEST PARAMETERS =================
    pile_diameter = fields.Float("Pile Diameter (mm)")
    max_test_load = fields.Float("Maximum Test Load (MT)")
    design_load = fields.Float("Design Load (MT)", compute="_compute_design_load", store=True)
    effective_area_jack = fields.Float("Effective Area of Jack (cm²)", default=2001.9)
    dial_gauge_least_count = fields.Char("Dial Gauge Least Count", default="0.01 mm")
    test_start_date = fields.Date("Test Start Date")
    test_end_date = fields.Date("End Date")

    # ================= COVER PAGE =================
    grade = fields.Char("Grade", compute="_compute_eln_fields", store=True, readonly=False)
    consultant = fields.Char("Consultant Name", compute="_compute_eln_fields", store=True, readonly=False)
    main_client = fields.Char("Main Client", compute="_compute_eln_fields", store=True, readonly=False)
    pile_coordinates = fields.Char("Pile Co-ordinates", help="e.g. E-275091.386 N-2107665.345")
    test_name = fields.Char("Test Name", default="Uplift Load Test")

    # ================= REPORT SECTIONS =================
    general_philosophy = fields.Text("1. General Philosophy")
    scope_of_works = fields.Text("2. Scope of Works")
    reference = fields.Text("3. References")
    pile_details = fields.Text("4. Pile Details")
    setup_apparatus = fields.Text("5. Setting up of Testing Apparatus")
    arrangement_drawing = fields.Binary("Test Arrangement Drawing")
    measuring_system = fields.Text("6. Measuring System")
    test_procedure = fields.Text("7. Method of Conducting Test")
    pile_test_observations = fields.Text("8. Test Report & Observations")
    conclusion = fields.Html("9. Conclusions", sanitize_style=True)

    checked_by_name = fields.Char("Checked By")
    checked_by_designation = fields.Char("Checked By Designation", default="Sr. Site Engineer")
    signatory_name = fields.Char("Approved By")
    signatory_designation = fields.Char("Approved By Designation", default="Technical Manager")

    loading_reading_ids = fields.One2many(
        "fst.uplift.load.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    unloading_reading_ids = fields.One2many(
        "fst.uplift.load.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )

    summary_ids = fields.One2many(
        "fst.uplift.load.summary",
        "parent_id",
        string="Uplift Summary",
        copy=False,
        readonly=True
    )

    content_ids = fields.One2many(
        "fst.uplift.load.report.content",
        "parent_id",
        string="Contents",
        copy=False
    )

    site_image_ids = fields.One2many(
        "fst.uplift.load.test.image",
        "parent_id",
        string="Site Photographs",
        domain=[('image_type', '=', 'site')],
        context={'default_image_type': 'site'},
        copy=False
    )

    datasheet_image_ids = fields.One2many(
        "fst.uplift.load.test.image",
        "parent_id",
        string="Field Data Sheets",
        domain=[('image_type', '=', 'datasheet')],
        context={'default_image_type': 'datasheet'},
        copy=False,
        help="Scanned site reading sheets, printed in Annexure I after the readings."
    )

    graph_image = fields.Binary("Load vs Uplift Graph")
    graph_image_log = fields.Binary("Load vs Uplift Log Graph")

    graph_break_loads = fields.Char(
        "Break Loading Graph At Load (MT)",
        help="Comma separated load values. The loading curve is not drawn "
             "between a matching point and the next point, e.g. '80' leaves a "
             "gap between 80 and 120 MT.",
        copy=False
    )

    graph_break_unload_loads = fields.Char(
        "Break Unloading Graph At Load (MT)",
        help="Comma separated load values. The unloading curve is not drawn "
             "between a matching point and the next point, e.g. '80' leaves a "
             "gap between 80 and 40 MT.",
        copy=False
    )

    total_uplift = fields.Float(
        "Total Uplift (mm)",
        digits=(16, 2),
        compute="_compute_uplift_values",
        store=True,
        help="Cumulative uplift at the end of loading (test load held)."
    )

    net_uplift = fields.Float(
        "Net Uplift (mm)",
        digits=(16, 2),
        compute="_compute_uplift_values",
        store=True,
        help="Cumulative uplift remaining after the load is released."
    )

    rebound = fields.Float(
        "Rebound (mm)",
        digits=(16, 2),
        compute="_compute_uplift_values",
        store=True,
        help="Total uplift - Net uplift."
    )

    rec_date_str = fields.Char(
        "Report Date (Text)",
        compute="_compute_rec_date_str",
        store=True
    )

    last_reading_datetime = fields.Datetime(
        compute="_compute_last_reading_datetime",
        store=False,
        copy=False
    )

    @api.depends('rec_date')
    def _compute_rec_date_str(self):
        for rec in self:
            if rec.rec_date:
                rec.rec_date_str = rec.rec_date.strftime("%d/%m/%Y")
            else:
                rec.rec_date_str = False

    @api.depends('max_test_load')
    def _compute_design_load(self):
        for rec in self:
            rec.design_load = round(rec.max_test_load / 2.5, 2) if rec.max_test_load else 0.0

    @api.depends('sample_id.discipline_id.discipline', 'sample_id.group_id.group')
    def _compute_srf_data(self):
        for rec in self:
            rec.discipline = rec.sample_id.discipline_id.discipline if rec.sample_id and rec.sample_id.discipline_id else False
            rec.group = rec.sample_id.group_id.group if rec.sample_id and rec.sample_id.group_id else False

    @api.depends('eln_ref', 'srf_id', 'srf_id.customer.name',
                 'srf_id.name_work.project_name',
                 'srf_id.site_address', 'srf_id.contractor.name',
                 'sample_id.kes_no', 'sample_id.ulr_no', 'parameter_id.test_method.test_method',
                 'eln_ref.parameters_result.test_method', 'srf_id.consultant_name1',
                 'srf_id.client', 'sample_id.grade_id.grade')
    def _compute_eln_fields(self):
        for rec in self:
            # Opened from a parameter row the parameter is known; opened through
            # the product based "Open Form" only the ELN is.
            tm = rec.parameter_id.test_method or rec.eln_ref.parameters_result[:1].test_method
            tm_name = tm.test_method if tm else False
            rec.grade = rec.sample_id.grade_id.grade or rec.grade or False

            if rec.eln_ref:
                kes_no = rec.sample_id.kes_no if rec.sample_id else False
                ulr_no = rec.sample_id.ulr_no if rec.sample_id else False
                rec.report_no = kes_no if kes_no and kes_no != 'New' else (rec.eln_ref.eln_id or rec.report_no or False)
                rec.ulr = ulr_no if ulr_no and ulr_no != 'New' else (rec.ulr or False)
                rec.test_standard = tm_name or rec.test_standard or False
            else:
                if not rec.report_no:
                    rec.report_no = False
                if not rec.ulr:
                    rec.ulr = False
                if not rec.test_standard:
                    rec.test_standard = tm_name or False

            if rec.srf_id:
                rec.client = rec.srf_id.customer.name if rec.srf_id.customer else (rec.client or False)
                project = rec.srf_id.name_work.project_name if rec.srf_id.name_work else False
                rec.name = project or rec.name or False
                rec.work_name = project or rec.work_name or False
                site_address = rec.srf_id.site_address or ''
                valid_parts = [p.strip() for p in site_address.split(',') if p.strip() and p.strip() not in ('False', 'None')]
                rec.site_location = site_address if valid_parts else False
                rec.contractor = rec.srf_id.contractor.name if rec.srf_id.contractor else (rec.contractor or False)
                rec.consultant = rec.srf_id.consultant_name1 or rec.consultant or False
                rec.main_client = rec.srf_id.client or rec.main_client or False
            else:
                for field_name in ('client', 'name', 'work_name', 'site_location', 'contractor',
                                   'consultant', 'main_client'):
                    if not rec[field_name]:
                        rec[field_name] = False

    @api.depends('summary_ids.cumulative_uplift_raw', 'summary_ids.load_type')
    def _compute_uplift_values(self):
        for rec in self:
            rows = [
                {'load_type': s.load_type, 'cumulative_raw': s.cumulative_uplift_raw}
                for s in rec.summary_ids.sorted('sequence')
            ]
            rec.total_uplift, rec.net_uplift, rec.rebound = uplift_calc.uplift_totals(rows)

    @api.depends('loading_reading_ids.reading_datetime')
    def _compute_last_reading_datetime(self):
        for rec in self:
            dates = [d for d in rec.loading_reading_ids.mapped('reading_datetime') if d]
            rec.last_reading_datetime = max(dates) if dates else False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record.with_context(_fst_no_recompute=True)._compute_srf_data()
            record.with_context(_fst_no_recompute=True)._compute_eln_fields()
            if record.eln_ref:
                record.eln_ref.write({'model_id': record.id})
            if record.parameter_id:
                record.parameter_id.write({'model_id': record.id})
        return records

    def write(self, vals):
        if not self.env.context.get('_fst_no_recompute'):
            old_report_no = {rec.id: rec.report_no for rec in self}
            old_ulr = {rec.id: rec.ulr for rec in self}
        res = super().write(vals)
        if not self.env.context.get('_fst_no_recompute'):
            for rec in self:
                rec = rec.with_context(_fst_no_recompute=True)
                if rec.eln_ref or rec.srf_id:
                    rec._compute_srf_data()
                    rec._compute_eln_fields()
                else:
                    if not rec.report_no and old_report_no.get(rec.id):
                        rec.report_no = old_report_no[rec.id]
                    if not rec.ulr and old_ulr.get(rec.id):
                        rec.ulr = old_ulr[rec.id]
            if 'effective_area_jack' in vals:
                # Loads are derived from the jack area, so the stage loads change.
                self.sudo()._refresh_results()
        return res

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

            match = re.search(r'(\d+F?)$', seq_raw)
            seq = match.group(1) if match else ''

            rec.ulr = f"{cert}{year}{loc}{seq}"

    def format_2dp(self, value):
        """Two decimals, rounded as Excel shows the sheet's values."""
        return f"{uplift_calc.excel_round(value):.2f}"

    @staticmethod
    def _fmt_num(value):
        return f"{value:g}" if value else "0"

    @staticmethod
    def _ordinal_date(value):
        if not value:
            return ""
        day = value.day
        suffix = 'th' if 11 <= day % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        return f"{day}{suffix} {value.strftime('%B %Y')}"

    def action_prefill_contents(self):
        """Fill the report sections with the text of report KES260901159."""
        self.ensure_one()

        dia = self._fmt_num(self.pile_diameter or 600.0)
        design = self._fmt_num(self.design_load)
        test_load = self._fmt_num(self.max_test_load)
        project = self.site_location or self.work_name or self.name or ""
        start = self._ordinal_date(self.test_start_date)
        end = self._ordinal_date(self.test_end_date)
        dates = f"{start} – {end}" if start and end else (start or end)
        least_count = self.dial_gauge_least_count or "0.01 mm"

        self.general_philosophy = (
            f"M/s Knack Engineering Services Pvt. Ltd. has been commissioned for the work of "
            f"conducting INITIAL pile Uplift Load Test for “{project}.”\n"
            f"One No. of Uplift Load Test to be conducted to reconfirm the Load Carrying "
            f"Capacity of the Piles ({dia}mm Dia) to support the design load of "
            f"{self.max_test_load:.2f} MT (Uplift / Tension). In order to Load the pile in "
            f"Uplift / Tension we propose to use 2 adjacent Test Piles as Reaction Piles. These "
            f"two reaction piles contribute the reaction load & in turn these piles will be "
            f"under Compression."
        )
        self.scope_of_works = (
            "• Mobilization of Load test set-up.\n"
            "• Erection of test setup.\n"
            "• Carrying out load test.\n"
            "• Analysis and Interpretation of data and preparation & submission of technical report."
        )
        self.reference = (
            "• IS 2911 (Part 4) - 2013 - Code of practice for design and construction of pile "
            "foundation’s part 4 Load Test on Piles.\n"
            "• IS 10270 (1982): Design and Construction of Pre stressed Rock Anchors"
        )
        self.pile_details = (
            f"• Test Pile No. - Uplift Test Pile – 1 Nos. - {dia}mm Dia\n"
            f"• Date of Testing – {dates}.\n"
            f"• Working Load – {design} MT.\n"
            f"• Test Load – 2.5 x Working Load = 2.5 x {design} = {test_load} MT."
        )
        self.setup_apparatus = (
            "1) The test Apparatus consist of the following:\n"
            "     i. Main beams – 1 Nos\n"
            "     ii. 1500 MT Jacks (1 Nos) with pump\n"
            "     iii. Dial Gauges (2 Nos)\n"
            "2) The Test beam will be placed on the top of reaction support (2 Nos one on either "
            "side) after preparation of reaction pile heads with GP2 / micro-concrete and placing "
            "the plate of sufficient thickness on top of it (if Reqd).\n"
            "3) The Jack will be then placed on the top of Test beam while taking care to keep the "
            "surface of the jack in plumb.\n"
            "4) Then the bars projecting above the Test Pile (in middle) will then be bent above the "
            "confinement Spiral Reinforcement provided so that all the bars will be projecting "
            "beyond the test beam placed on top of Test pile.\n"
            "5) Reaction Frame (fabricated as per drawing in Enclosure 3) will be then welded at top "
            "with 6 Nos of 25 mm Dia L shaped bars (smaller leg portion of L Bars will be welded "
            "with reaction beam top) and the longer Leg of L Bars will be welded to the "
            "reinforcement bent bars projecting above the test pile. This will transfer the Tension "
            "Load applied through the Jack to the pile concentrically."
        )
        if not self.arrangement_drawing:
            with file_open(ARRANGEMENT_DRAWING, 'rb') as drawing:
                self.arrangement_drawing = base64.b64encode(drawing.read())
        self.measuring_system = (
            f"1) Load applied by jack shall be measured by a calibrated pressure gauge with a least "
            f"count of {least_count}.\n"
            f"2) Movement of the pile shall be measured by dial gauges, fixed to datum bar and "
            f"having a least count of {least_count}. A minimum of two dial gauges, placed "
            f"diametrically opposite shall be used. Datum bars shall be provided with rigid "
            f"supports as the datum bars shall have rigid supports preferably of concrete pillars "
            f"or steel sections, embedded well into the ground. The supports shall be located more "
            f"than three times the pile diameter, subject to a minimum of 1.5 m, clear away from "
            f"the pile face and also sufficiently away from the supports of the loaded platform to "
            f"avoid any disturbance on these accounts. Movements near the supports of the datum bar "
            f"shall be avoided while the test is in progress."
        )
        self.test_procedure = (
            "The test shall be conducted as outlined below:\n"
            "1) Loading shall be applied to the pile top in increments of one fifth the rated "
            "capacity of pile.\n"
            "2) Each stage shall be maintained for a period till the rate of movement of the pile "
            "head is not more than 0.2 mm/hr or one hour, whichever is greater.\n"
            "3) Loading shall be continued till one of the following occurs:\n"
            "     i. Yield of soil pile system occurs causing progressive movement of the pile "
            "exceeding 12 mm.\n"
            "     ii. The loading on the pile top equals twice the estimated safe load or as specified."
        )
        pile = self.pile_no or "Test Pile"
        self.pile_test_observations = (
            f"8.1. Pile – {pile}:\n"
            "1) A chart was plotted to depict Load on Pile Top in Tons vs. Settlement (Elastic "
            "Compression of sub-grade) in mm and same is attached in Annexure II.\n"
            f"2) Settlement of pile at test load = {self.format_2dp(self.total_uplift)} mm.\n"
            f"3) Net settlement of Pile = {self.format_2dp(self.net_uplift)} mm."
        )
        self.conclusion = (
            "<p>According to Cl. 7.1.5 IS 2911 part IV: 2013 safe load on single pile shall be "
            "taken as the least of the following:</p>"
            "<p><b>The safe capacity of the pile shall be the least of the following:</b></p>"
            "<p><b>A) For piles up to and including 600 mm diameter:</b></p>"
            "<p>1) Two-thirds of the load at which the total displacement is 12 mm or the load "
            "corresponding to a specified permissible uplift.<br/>"
            "2) Half of the load at which the load displacement curve shows a clear break "
            "(downward trend).</p>"
            "<p><b>B) For piles more than 600 mm diameter:</b></p>"
            "<p>1) Two-thirds of the load at which the total displacement is 18 mm or maximum of "
            "2 percent of pile diameter whichever is less or the load corresponding to a specified "
            "permissible uplift; and<br/>"
            "2) Half of the load at which the load displacement curve shows a clear break "
            "(downward trend).</p>"
            f"<p style=\"font-size:15pt;\"><b>Hence, Safe load can be considered as {design} MT "
            f"for Test Pile-01.</b></p>"
        )

        self.content_ids.unlink()
        sp = "  "
        contents = [
            # (section_number, description, page_no)
            ("01.", "General Philosophy", "03"),
            ("02.", "Scope of Works", "03"),
            ("03.", "References", "03"),
            ("04.", "Pile Details", "03"),
            ("05.", "Setting up of Testing Apparatus", "04"),
            ("06.", "Measuring System", "05"),
            ("07.", "Method of Conducting Test", "05"),
            ("08.", "Test Report & Observations", "06"),
            ("09.", "Conclusions", "06"),
            ("", f"Annexure I{sp}Test Readings", "07"),
            ("", f"Annexure II{sp}Load vs. Displacement Plot", "10"),
            ("", f"Annexure III{sp}Site Photographs", "12"),
        ]
        self.env['fst.uplift.load.report.content'].create([{
            'parent_id': self.id,
            'sequence': seq,
            'section_number': number,
            'description': name,
            'page_no': page,
        } for seq, (number, name, page) in enumerate(contents, start=1)])

    def report_reading_blocks(self):
        """Loading / unloading blocks for Annexure I, one entry per load stage.

        Each stage carries its readings plus the stage values of the summary,
        so the report can merge the Sr. No, pressure, load and uplift cells.
        """
        self.ensure_one()
        summaries = self.summary_ids.sorted('sequence')
        blocks = []
        index = 0
        for load_type, label, lines in (
                ('loading', 'LOADING', self.loading_reading_ids),
                ('unloading', 'UNLOADING', self.unloading_reading_ids)):
            lines = lines.sorted(lambda l: (l.reading_datetime, l.id))
            if not lines:
                continue
            dicts = [dict(reading, line=line) for reading, line
                     in zip(self._reading_dicts(lines), lines)]
            stages = []
            for number, stage in enumerate(uplift_calc.group_stages(dicts), start=1):
                summary = summaries[index] if index < len(summaries) else summaries.browse()
                index += 1
                stages.append({
                    'number': number,
                    'lines': [r['line'] for r in stage],
                    'pressure': stage[0]['pressure'],
                    'load': stage[0]['load'],
                    'avg': summary.avg_uplift,
                    'cumulative': summary.cumulative_uplift,
                })
            first = fields.Datetime.context_timestamp(self, lines[0].reading_datetime)
            blocks.append({
                'type': load_type,
                'title': f"{label} ({first.strftime('%d-%m-%Y')})",
                'stages': stages,
            })
        return blocks

    def report_date(self, value, padded=True):
        """Dates as the report prints them: 01/09/2026 (cover) or 1/9/2026 (readings)."""
        if not value:
            return ""
        return value.strftime("%d/%m/%Y") if padded else f"{value.day}/{value.month}/{value.year}"

    def _local_to_utc(self, value):
        """'YYYY-MM-DD HH:MM' in the user's timezone -> naive UTC datetime."""
        tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'Asia/Kolkata')
        local = tz.localize(datetime.strptime(value, '%Y-%m-%d %H:%M'))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def action_generate_test_data(self):
        self.ensure_one()

        # Defaults taken from the "Welspun Uplift Load Test" sheet.
        if not self.effective_area_jack:
            self.effective_area_jack = 2001.9
        if not self.max_test_load:
            self.max_test_load = 140.0
        if not self.pile_diameter:
            self.pile_diameter = 600.0
        if not self.test_start_date:
            self.test_start_date = date(2026, 9, 1)
        if not self.test_end_date:
            self.test_end_date = date(2026, 9, 2)
        if not self.dial_gauge_least_count:
            self.dial_gauge_least_count = "0.01 mm"
        if not self.name:
            self.name = "418 MLD WASTE WATER TREATMENT FACILITIES AT DHARAVI"
        if not self.work_name:
            self.work_name = self.name
        if not self.pile_no:
            self.pile_no = "Gas Building Test Pile Uplift Load Test"
        if not self.test_standard:
            self.test_standard = "IS 2911 Part 4: 2013"
        # Cover page of report KES260901159.
        if not self.report_no:
            self.report_no = "KES260901159"
        if not self.ulr:
            self.ulr = "TC682826000033455F"
        if not self.rec_date:
            self.rec_date = date(2026, 9, 7)
        if not self.client:
            self.client = "Welspun Enterprises Limited"
        if not self.contractor:
            self.contractor = "Welspun Enterprises Limited"
        if not self.site_location:
            self.site_location = PROJECT_TITLE
        if not self.grade:
            self.grade = "M-50"
        if not self.consultant:
            self.consultant = "TATA Consulting Engineers"
        if not self.main_client:
            self.main_client = "Brihanmumbai Municipal Corporation"
        if not self.pile_coordinates:
            self.pile_coordinates = "E-275091.386 N-2107665.345"
        if not self.test_name:
            self.test_name = "Uplift Load Test"
        if not self.checked_by_name:
            self.checked_by_name = "Sohel Rasul Shaikh"
        if not self.checked_by_designation:
            self.checked_by_designation = "Sr. Site Engineer"
        if not self.signatory_name:
            self.signatory_name = "Waqar Adeeb Tungekar"
        if not self.signatory_designation:
            self.signatory_designation = "Technical Manager"

        # Clear any previously generated readings before regenerating.
        self.loading_reading_ids.unlink()
        self.unloading_reading_ids.unlink()

        for model, rows in (
            ('fst.uplift.load.reading.loading', uplift_test_data.LOADING),
            ('fst.uplift.load.reading.unloading', uplift_test_data.UNLOADING),
        ):
            self.env[model].create([{
                'parent_id': self.id,
                'reading_datetime': self._local_to_utc(when),
                'reading_interval': interval,
                'pressure_gauge': pressure,
                'dial_a': dial_a,
                'dial_b': dial_b,
            } for pressure, interval, dial_a, dial_b, when in rows])

        self.action_recompute_all()
        self.action_prefill_contents()
        self.action_generate_graph()
        self.action_generate_log_graph()

    def _graph_points(self):
        summaries = self.summary_ids.sorted('sequence')
        # Plot the unrounded values, as the sheet's chart does.
        loading = [(s.load_tonne, s.cumulative_uplift_raw)
                   for s in summaries if s.load_type == 'loading']
        unloading = [(s.load_tonne, s.cumulative_uplift_raw)
                     for s in summaries if s.load_type == 'unloading']
        return summaries, loading, unloading

    def action_generate_graph(self):
        self.ensure_one()
        self._refresh_results()
        summaries, loading, unloading = self._graph_points()
        if not summaries:
            self.graph_image = False
            return
        png = uplift_graph.render_load_uplift_graph(
            loading, unloading,
            uplift_graph.parse_loads(self.graph_break_loads),
            uplift_graph.parse_loads(self.graph_break_unload_loads),
        )
        self.graph_image = base64.b64encode(png)

    def action_generate_log_graph(self):
        """Log-log Load vs Uplift curve."""
        self.ensure_one()
        self._refresh_results()
        points = [(s.cumulative_uplift_raw, s.load_tonne, s.load_type)
                  for s in self.summary_ids.sorted('sequence')]
        png = uplift_graph.render_log_graph(
            points,
            uplift_graph.parse_loads(self.graph_break_loads),
            uplift_graph.parse_loads(self.graph_break_unload_loads),
        )
        self.graph_image_log = base64.b64encode(png) if png else False

    def action_recompute_all(self):
        for rec in self:
            rec.loading_reading_ids._compute_split_dt()
            rec.unloading_reading_ids._compute_split_dt()
            rec.sudo()._refresh_results()

    def _refresh_results(self):
        self._recompute_summary()
        self._compute_uplift_values()

    @staticmethod
    def _reading_dicts(lines):
        return [{
            'interval': line.reading_interval,
            'pressure': line.pressure_gauge,
            'load': line.load_tonne,
            'dial_a': line.dial_a,
            'dial_b': line.dial_b,
        } for line in lines.sorted(lambda l: (l.reading_datetime, l.id))]

    def _recompute_summary(self):
        Summary = self.env['fst.uplift.load.summary'].sudo()
        for rec in self:
            Summary.search([('parent_id', '=', rec.id)]).unlink()
            rows = uplift_calc.stage_summary(
                self._reading_dicts(rec.loading_reading_ids),
                self._reading_dicts(rec.unloading_reading_ids),
            )
            Summary.create([{
                'parent_id': rec.id,
                'sequence': seq,
                'load_type': row['load_type'],
                'load_tonne': row['load'],
                'avg_uplift': row['avg'],
                'cumulative_uplift': row['cumulative'],
                'cumulative_uplift_raw': row['cumulative_raw'],
            } for seq, row in enumerate(rows, start=1)])

    def print_report(self):
        self.ensure_one()
        return self.env.ref(
            'fst_upload_lift_test.uplift_load_report'
        ).report_action(self)

    def action_duplicate_parent(self):
        for record in self:
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'graph_image': False,
                'graph_image_log': False,
            })
            for lines in (record.loading_reading_ids, record.unloading_reading_ids,
                          record.content_ids, record.site_image_ids,
                          record.datasheet_image_ids):
                for line in lines:
                    line.copy({'parent_id': new_parent.id})
            new_parent.action_recompute_all()
        return True

    def action_delete_line(self):
        for rec in self:
            rec.unlink()


class FstUpliftLoadReadingMixin(models.AbstractModel):
    _name = "fst.uplift.load.reading.mixin"
    _description = "Uplift Load Test Reading"
    _order = "reading_datetime, id"
    # One2many on the parent that holds the lines of the concrete model.
    _parent_lines_field = None

    parent_id = fields.Many2one(
        "fst.uplift.load.test",
        ondelete="cascade",
        required=True
    )

    reading_datetime = fields.Datetime("Date & Time", required=True)

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

    reading_interval = fields.Integer(
        "Reading Interval (Min)",
        help="0 marks the first reading of a load stage. Use 1440 for a 24 hour reading."
    )
    interval_display = fields.Char("Interval", compute="_compute_interval_display")
    pressure_gauge = fields.Float("Pressure Gauge Reading (kg/cm²)")
    load_tonne = fields.Float("Load (MT)", compute="_compute_load_tonne", store=True, readonly=False)
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    cumulative_dial = fields.Float(
        "Cumulative Dial Reading (mm)",
        compute="_compute_cumulative_dial",
        store=True,
        readonly=True
    )
    is_recorded = fields.Boolean(compute="_compute_is_recorded")

    @api.depends('pressure_gauge', 'parent_id.effective_area_jack')
    def _compute_load_tonne(self):
        for rec in self:
            rec.load_tonne = uplift_calc.load_from_pressure(
                rec.pressure_gauge, rec.parent_id.effective_area_jack)

    @api.depends('dial_a', 'dial_b')
    def _compute_cumulative_dial(self):
        for rec in self:
            rec.cumulative_dial = uplift_calc.cumulative_dial(rec.dial_a, rec.dial_b)

    @api.depends('dial_a', 'dial_b', 'reading_interval')
    def _compute_is_recorded(self):
        for rec in self:
            rec.is_recorded = bool(rec.dial_a or rec.dial_b or rec.reading_interval == 0)

    @api.depends('reading_interval')
    def _compute_interval_display(self):
        for rec in self:
            minutes = rec.reading_interval
            if minutes > 60 and minutes % 60 == 0:
                rec.interval_display = f"{minutes // 60} Hours"
            else:
                rec.interval_display = str(minutes)

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

    @api.onchange('parent_id')
    def _onchange_set_datetime(self):
        if self.parent_id:
            latest_datetime = None
            unsaved_lines = [
                r for r in self.parent_id[self._parent_lines_field]
                if r.reading_datetime and r != self
            ]
            if unsaved_lines:
                latest = max(unsaved_lines, key=lambda x: x.reading_datetime)
                latest_datetime = latest.reading_datetime
            else:
                saved_lines = self.search(
                    [('parent_id', '=', self.parent_id.id)],
                    order='reading_datetime desc, id desc',
                    limit=1
                )
                if saved_lines and saved_lines.reading_datetime:
                    latest_datetime = saved_lines.reading_datetime

            if latest_datetime:
                self.reading_datetime = latest_datetime + timedelta(minutes=15)
            else:
                self.reading_datetime = fields.Datetime.now()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reading_datetime'):
                continue
            parent_id = vals.get('parent_id') or self.env.context.get('default_parent_id')
            last_line = self.search(
                [('parent_id', '=', parent_id)],
                order='reading_datetime desc, id desc',
                limit=1
            ) if parent_id else False
            if last_line and last_line.reading_datetime:
                vals['reading_datetime'] = last_line.reading_datetime + timedelta(minutes=15)
            else:
                vals['reading_datetime'] = fields.Datetime.now()

        records = super().create(vals_list)
        records.mapped('parent_id').sudo()._refresh_results()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('dial_a', 'dial_b', 'pressure_gauge', 'load_tonne',
                                   'reading_interval', 'reading_datetime')):
            self.mapped('parent_id').sudo()._refresh_results()
        return res

    def unlink(self):
        parents = self.mapped('parent_id')
        res = super().unlink()
        parents.exists().sudo()._refresh_results()
        return res


class FstUpliftLoadReadingLoading(models.Model):
    _name = "fst.uplift.load.reading.loading"
    _inherit = "fst.uplift.load.reading.mixin"
    _description = "Uplift Load Reading - Loading"
    _parent_lines_field = "loading_reading_ids"


class FstUpliftLoadReadingUnloading(models.Model):
    _name = "fst.uplift.load.reading.unloading"
    _inherit = "fst.uplift.load.reading.mixin"
    _description = "Uplift Load Reading - Unloading"
    _parent_lines_field = "unloading_reading_ids"


class FstUpliftLoadReportContent(models.Model):
    _name = "fst.uplift.load.report.content"
    _description = "Uplift Load Test Report Contents"
    _order = "sequence, id"

    parent_id = fields.Many2one("fst.uplift.load.test", ondelete="cascade")
    sequence = fields.Float("Sl. No")
    section_number = fields.Char("Section Number")
    description = fields.Char("Name")
    parent_section = fields.Char("Parent Section")
    is_subsection = fields.Boolean("Is Subsection")
    page_no = fields.Char("Page No")


class FstUpliftLoadSummary(models.Model):
    _name = "fst.uplift.load.summary"
    _description = "Uplift Load Test - Uplift Summary"
    _order = "sequence, id"

    parent_id = fields.Many2one(
        "fst.uplift.load.test",
        ondelete="cascade",
        required=True
    )
    sequence = fields.Integer("Sr No")
    load_type = fields.Selection([
        ('loading', 'Loading'),
        ('unloading', 'Unloading'),
    ], string="Stage", default='loading', required=True)
    load_tonne = fields.Float("Applied Load (MT)")
    # Rounded to 2 decimals as the sheet shows them (uplift_calc.excel_round).
    avg_uplift = fields.Float("Average Uplift (mm)", digits=(16, 2))
    cumulative_uplift = fields.Float("Cumulative Uplift (mm)", digits=(16, 2))
    # Unrounded running total, used for the totals and the graphs.
    cumulative_uplift_raw = fields.Float("Cumulative Uplift, unrounded (mm)")


class ReportUpliftLoad(models.AbstractModel):
    """Finds the uplift record however the report is printed.

    From the uplift form the docids are uplift records. From the ELN / sample
    (product based calculation) and the bulk print, only the ELN or sample is
    known, so the record is reached through ``eln.model_id`` / ``eln_ref``.
    """
    _name = 'report.fst_upload_lift_test.uplift_load_template'
    _description = 'Uplift Load Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        context = data.get('context') or {}
        if isinstance(context, str):
            context = json.loads(context)
        active_model = context.get('active_model')
        active_id = context.get('active_id')

        Eln = self.env['lerm.eln'].sudo()
        Test = self.env['fst.uplift.load.test'].sudo()

        eln = Eln
        if data.get('report_wizard') and data.get('sample'):
            eln = Eln.search([('sample_id', '=', data['sample'])], limit=1)
        elif data.get('eln_id'):
            eln = Eln.browse(data['eln_id'])
        elif active_model == 'lerm.eln' and active_id:
            eln = Eln.browse(active_id)
        elif active_model == 'lerm.srf.sample' and active_id:
            eln = Eln.search([('sample_id', '=', active_id)], limit=1)

        if eln:
            # model_id is a bare id of whatever model the ELN uses, so only
            # trust it when that record points back to this ELN.
            docs = Test.browse(eln.model_id).exists().filtered(
                lambda r: r.eln_ref == eln) if eln.model_id else Test
            if not docs:
                docs = Test.search([('eln_ref', '=', eln.id)], order='id desc', limit=1)
        else:
            docs = Test.browse(docids or []).exists()

        return {
            'doc_ids': docs.ids,
            'doc_model': 'fst.uplift.load.test',
            'docs': docs,
            'data': data,
        }


class FstUpliftLoadTestImage(models.Model):
    _name = "fst.uplift.load.test.image"
    _description = "Uplift Load Test Photograph / Field Data Sheet"
    _order = "sequence, id"

    parent_id = fields.Many2one("fst.uplift.load.test", ondelete="cascade")
    image_type = fields.Selection([
        ('site', 'Site Photograph'),
        ('datasheet', 'Field Data Sheet'),
    ], string="Type", default='site', required=True)
    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph")
    caption = fields.Char("Caption")
