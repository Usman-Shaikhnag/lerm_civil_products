from odoo import api, fields, models
from datetime import timedelta
import base64
import io
import math
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import (
    FuncFormatter,
    LogLocator,
    MultipleLocator,
    NullFormatter,
)
from scipy.interpolate import PchipInterpolator


class FstInitialVerticalLoadTest(models.Model):
    _name = "fst.initial.vertical.load.test"
    _description = "Initial Vertical Pile Load Test Report"
    _order = "rec_date desc, id desc"

    name = fields.Char("Project Name", compute="_compute_eln_fields", store=True, readonly=False)
    rec_date = fields.Date("Report Date")
    work_name = fields.Char("Name of Work", compute="_compute_eln_fields", store=True, readonly=False)
    client = fields.Char(string="Client", compute="_compute_eln_fields", store=True, readonly=False)
    contractor = fields.Char(string="Contractor", compute="_compute_eln_fields", store=True, readonly=False)
    lab_id = fields.Many2one('lerm.lab.master', string="Lab Name")

    ulr = fields.Char("ULR No", copy=False, compute="_compute_eln_fields", store=True)
    report_no = fields.Char("Report No", copy=False, compute="_compute_eln_fields", store=True)
    pile_no = fields.Char("Pile No")
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
    effective_area_jack = fields.Float("Effective Area of Jack", default=2001.9)
    dial_gauge_least_count = fields.Char("Dial Gauge Least Count", default="0.01 mm")
    test_start_date = fields.Date("Test Start Date")
    test_end_date = fields.Date("End Date")

    # ================= NARRATIVE =================
    general_philosophy = fields.Text("General Philosophy")
    scope_of_works = fields.Text("Scope of Works")
    reference = fields.Text("Reference")
    pile_details = fields.Text("Pile Details")
    test_arrangement = fields.Text("Test Arrangement")
    installation_test_pile = fields.Text("Installation of Test Pile")
    installation_rock_anchors = fields.Text("Installation of Vertical Rock Anchors")
    preparation_pile_head = fields.Text("Preparation of Pile Head for Test Pile")
    erection_test_beam = fields.Text("Erection of Test Beam & Assembly & Testing")
    test_equipment = fields.Text("Equipment Used")
    setup_apparatus = fields.Text("Setting up of Testing Apparatus")
    test_procedure = fields.Text("Load Test Procedure")
    test_report_observations = fields.Text("Test Report & Observations")
    pile_initial_test_pile = fields.Text("Pile - Initial Test Pile")
    preparation_report = fields.Text("Preparation of Test Report")
    conclusion = fields.Text("Conclusion")

    allowable_capacity = fields.Float("Allowable Vertical Capacity")

    signatory_name = fields.Char("Authorized Signatory")
    signatory_designation = fields.Char("Designation")

    loading_reading_ids = fields.One2many(
        "fst.initial.vertical.load.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    loading_summary_ids = fields.One2many(
        "fst.initial.vertical.load.loading.summary",
        "parent_id",
        string="Settlement Summary",
        copy=False,
        readonly=True
    )

    unloading_reading_ids = fields.One2many(
        "fst.initial.vertical.load.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )

    content_ids = fields.One2many(
        "fst.initial.vertical.load.report.content",
        "parent_id",
        string="Contents",
        copy=False
    )

    basic_data_ids = fields.One2many(
        "fst.initial.vertical.load.basic.data",
        "parent_id",
        string="Basic Data",
        copy=False
    )

    site_image_ids = fields.One2many(
        "fst.initial.vertical.load.test.image",
        "parent_id",
        string="Site Photographs",
        copy=False
    )

    graph_image = fields.Binary("Load Settlement Graph")

    graph_image_log = fields.Binary("Load vs Uplift Log Graph")

    graph_break_loads = fields.Char(
        "Break Loading Graph At Load (MT)",
        help="Comma separated load values. The loading curve is not drawn "
             "between a matching point and the next point, e.g. '90' leaves a "
             "gap between 90 and 120 MT.",
        copy=False
    )

    graph_break_unload_loads = fields.Char(
        "Break Unloading Graph At Load (MT)",
        help="Comma separated load values. The unloading curve is not drawn "
             "between a matching point and the next point, e.g. '90' leaves a "
             "gap between 90 and 120 MT.",
        copy=False
    )

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

    max_settlement = fields.Float(
        "Maximum Settlement",
        compute="_compute_max_settlement",
        store=True,
        readonly=True
    )

    target_settlement = fields.Float("Target Settlement (mm)", default=0.0, store=True)
    allowable_load = fields.Float("Allowable Load (t)", default=0.0, store=True)

    analysis_text = fields.Text("Analysis of Test Results")

    rec_date_str = fields.Char(
        "Report Date (Text)",
        compute="_compute_rec_date_str",
        store=True
    )

    @api.depends('rec_date')
    def _compute_rec_date_str(self):
        for rec in self:
            if rec.rec_date:
                rec.rec_date_str = rec.rec_date.strftime("%d-%m-%Y")
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
                 'sample_id.kes_no', 'sample_id.ulr_no', 'parameter_id.test_method.test_method')
    def _compute_eln_fields(self):
        for rec in self:
            tm = rec.parameter_id.test_method if rec.parameter_id else False
            tm_name = tm.test_method if tm else False

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
            else:
                for field_name in ('client', 'name', 'work_name', 'site_location', 'contractor'):
                    if not rec[field_name]:
                        rec[field_name] = False

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.with_context(_fst_no_recompute=True)._compute_srf_data()
        record.with_context(_fst_no_recompute=True)._compute_eln_fields()
        if record.eln_ref:
            record.eln_ref.write({'model_id': record.id})
        if record.parameter_id:
            record.parameter_id.write({'model_id': record.id})
        return record

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

    def action_prefill_contents(self):
        self.ensure_one()

        self.general_philosophy = (
            "Initial Pile Static Load Test on 1 no of pile was carried out to confirm the "
            "vertical load carrying capacity of 600 mm dia. Static pile load test is the most "
            "direct method for studying behaviour of pile under actual loading conditions and "
            "for determining the settlement."
        )
        self.scope_of_works = (
            "\u2022 Mobilization of Load test set-up.\n"
            "\u2022 Erection of test setup.\n"
            "\u2022 Carrying out load test.\n"
            "\u2022 Analysis and Interpretation of data and preparation & submission of technical report."
        )
        self.reference = (
            "\u2022 IS 2911 (Part 4) - 2013 -Code of practice for design and construction of pile "
            "foundations Part 4 Load Test on Piles.\n"
            "\u2022 IS 10270 (1982): Design and Construction of Pre stressed Rock Anchors."
        )
        self.pile_details = (
            "\u2022 Test Pile No. \u2013 Initial Test - 600mm Dia\n"
            "\u2022 Date of Testing \u2013 04th September 2026 \u2013 06th September 2026.\n"
            "\u2022 Working Load \u2013 127.2 MT.\n"
            "\u2022 Test Load \u2013 2.5 x Working Load = 2.5 x 127.2= 318 MT.\n"
            "\u2022 Reaction System Used = Reaction Anchors Method.\n"
            "\u2022 Nos. of Anchors Proposed = 02 Nos."
        )
        self.test_arrangement = (
            "A hydraulic jack along with power pack pump was used to apply the load on the pile. "
            "The reaction was obtained from 08 Nos. of anchors drilled. The pile head movement / "
            "settlement was measured by means of four dial gauges having least count of 0.01mm. "
            "The dial gauges were attached to the datum bar by means of magnetic stands."
        )
        self.installation_test_pile = (
            "The installation of (bored Cast in situ) INITIAL Test Pile 600 mm Dia was done as "
            "per approved methodology."
        )
        self.installation_rock_anchors = (
            "The reaction system proposed consists of 08 nos. of Pre-stressed Rock Anchors "
            "drilled at stipulated location. The general steps involved were as follows:\n"
            "1. Boring of 200mm Dia rock anchor.\n"
            "2. Lowering of MS/PVC casing of 200m diameter till rock level.\n"
            "3. After drilling, the hole was washed thoroughly to remove all loose material (if "
            "any) with air i.e. air flushing.\n"
            "4. Preparation of cable: The cable was made up of 11 NOS of 15.2 mm Dia HTstrands. "
            "Strands were grouped together into a circular cable with spacer at 1.50 m c/c. The "
            "top of the cable was so arranged that strands should pass from the circular bunch to "
            "stressing plate configuration.\n"
            "5. The cable was then lowered into the hole. After lowering the cable, GP2 grout was "
            "injected (0.18 water: GP2 ratio) under gravity through central 20 mm diameter HDPE/ "
            "equivalent pipe. The cables were tensioned after a minimum period of 07 days.\n"
            "6. Details of the Anchors used:\n"
            "\u2022 Anchor Dia \u2013 200mm\n"
            "\u2022 Free length \u2013 9 m\n"
            "\u2022 Fixed Length \u2013 12.00 m\n"
            "\u2022 Total length of anchors \u2013 21.00 m\n"
            "\u2022 Nos of Strands \u2013 11 Nos 15.2 mm Dia"
        )
        self.preparation_pile_head = (
            "The pile head at the cut off level / ground level of the test pile was prepared for "
            "the Jack to rest on the top surface of the pile. The excess concrete at the pile top "
            "was chipped up to sound concrete to prepare a rough horizontal surface. A layer of "
            "cement sand mortar was applied on the rough concrete surface shall be to form a plain "
            "and levelled surface. A bearing plate of 25mm thickness was then be placed on the "
            "pile top to provide a solid base for the testing Jack to be seated."
        )
        self.erection_test_beam = (
            "Hydraulic Jacks, Datum Bar and Test Beam / girder assembly was then erected as shown "
            "in drawing as per approved Method Statement."
        )
        self.test_equipment = (
            "\u2022 Hydraulic Jack\n"
            "\u2022 Pressure Gauge\n"
            "\u2022 Dial Gauges - 4 Nos of Dial Gauges with LC of 0.01 mm\n"
            "\u2022 Datum Bars\n"
            "\u2022 Reaction arrangement / Kentledge"
        )
        self.setup_apparatus = (
            "1) The test Apparatus consist of the following:\n"
            "i. Main reaction beam \u2013 1 Nos.\n"
            "ii. 1500 MT Jacks (1 Nos.) with pump\n"
            "iii. Dial Gauges (4 Nos)\n"
            "2) The Jack was first placed on the top of finished concrete surface of the Test Pile "
            "while taking care to keep the surface of the jack in plumb.\n"
            "3) Specific Bearing Plates were placed on the top of Girder Assembly at anchor "
            "location.\n"
            "4) Single wire wedges were placed over each strand and stressing was carried out by "
            "single pull stressing Jack. Strands were locked initially with 1.0 MT (Approx. 5 % of "
            "its capacity) so as to remove any slag in strands. Minimum ten strands of each anchor "
            "were stressed alternately to avoid the lifting of girder from another end."
        )
        self.test_procedure = (
            "1) The test was carried out by applying a series of vertical downward incremental "
            "load each increment being of about 20 percent of safe load on the pile as per cl. "
            "7.1.2 of IS 2911 (IV) 2013. This increment was carried out up to 250% of the safe "
            "working load as per cl. 7.2.1.1 of IS 2911 (IV) 2013.\n"
            "2) Settlement was recorded with minimum 4 dial gauges of 0.01 mm sensitivity. The "
            "dial gauges were placed symmetrically and at equal distances from the pile and "
            "normally held by datum bars resting on immovable supports at a distance of 3D "
            "(subject to minimum of 2.0 m) from the edge of the piles, where D is the pile stem "
            "diameter of circular piles. The settlement was recorded in the format as per as per "
            "Cl. 7.1.4.1 of IS 2911 (IV) 2013.\n"
            "3) Continuous monitoring during the application of increment of test load and taking "
            "of measurement or displacement in each stage of loading was carried out at every "
            "15 min. Next loading increment shall be applied after satisfying following criteria:\n"
            "\u2022 0.2 mm or less in first hour OR\n"
            "\u2022 2 hour whichever occur first.\n"
            "4) The above process was continued as per Cl. 7.2.1.1 of IS 2911 (IV) 2013 till\n"
            "\u2022 The test load was reached i.e. 250% of the safe working load, maintained for "
            "24 Hrs.\n"
            "\u2022 Maximum settlement of pile exceeds a value of 10 percent of pile diameter.\n"
            "5) The unloading in increments was done in a similar manner (after maintaining the "
            "Test Load for 24 Hrs.) as mentioned in above steps 1 & 2 with each incremental "
            "unloading being maintained for 30minutes and the subsequent elastic rebound in the "
            "pile was measured accurately as in step 3 above and recorded in format as per "
            "\u201cEnclosure 2\u201d.\n"
            "6) All of the above activities were carried out in presence of Engineers "
            "Representative.\n"
            "7) Once the test load was reached, the safe vertical load on single pile for the test "
            "was ascertained considering the following criteria:\n"
            "\u2022 Two-thirds of the final load at which the total displacement attains a value "
            "of 12 mm or maximum of 2 percent pile diameter whichever is less\n"
            "\u2022 50 percent of the final load at which the total displacement equal to 10 "
            "percent of the pile diameter."
        )
        self.pile_initial_test_pile = (
            "1) A chart was plotted to depict Load on Pile Top in Tons vs. Settlement (Elastic "
            "Compression of sub-grade) in mm and same is attached in Enclosure 2.\n"
            "2) Settlement of pile at test load of 318 MT = 8.32 mm.\n"
            "3) Net settlement of Pile = 7.04 mm.\n"
            "4) Elastic Rebound of Pile = 1.28 mm."
        )
        self.preparation_report = (
            "A chart was plotted to depict Vertical Load on Pile in Tons vs. Pile Settlement "
            "in mm and same is attached with the test report."
        )
        self.conclusion = (
            "The pile is acceptable as per the acceptance criteria mentioned in Cl. 7.1.5 "
            "IS 2911 part IV: 2013. Hence, Safe load can be considered as 127.2 MT for Test "
            "Pile at Gas Building."
        )

        existing = self.env['fst.initial.vertical.load.report.content'].search(
            [('parent_id', '=', self.id)]
        )
        existing.unlink()

        contents = [
            # (sequence, section_number, name, parent_section, is_subsection, page_no)
            (1, "1", "GENERAL PHILOSOPHY", "", False, "2"),
            (2, "2", "SCOPE OF WORKS", "", False, "2"),
            (3, "3", "REFERENCES", "", False, "2"),
            (4, "4", "PILE DETAILS", "", False, "2"),
            (5, "5", "TEST ARRANGEMENT", "", False, "3"),
            (6, "5.1", "Installation of Test Pile", "TEST ARRANGEMENT", True, "3"),
            (7, "5.2", "Installation of Vertical Rock Anchors", "TEST ARRANGEMENT", True, "3"),
            (8, "5.3", "Preparation of Pile Head for Test Pile", "TEST ARRANGEMENT", True, "4"),
            (9, "5.4", "Erection of Test Beam & Assembly & Testing", "TEST ARRANGEMENT", True, "4"),
            (10, "5.4.1", "Setting up of Testing Apparatus", "Erection of Test Beam & Assembly & Testing", True, "4"),
            (11, "5.4.2", "Load Test Procedure", "Erection of Test Beam & Assembly & Testing", True, "5"),
            (12, "6", "TEST REPORT & OBSERVATIONS", "", False, "6"),
            (13, "", "CONCLUSIONS", "", False, "6"),
            (14, "", "Annexure I (TEST READINGS)", "", False, "7"),
            (15, "", "Annexure II (Load vs. Deflection Plot)", "", False, "9"),
            (16, "", "Annexure III (Site Photographs)", "", False, "16"),
        ]
        for seq, section_number, name, parent_section, is_subsection, page in contents:
            self.env['fst.initial.vertical.load.report.content'].create({
                'parent_id': self.id,
                'sequence': seq,
                'section_number': section_number,
                'description': name,
                'parent_section': parent_section,
                'is_subsection': is_subsection,
                'page_no': page,
            })

    def action_generate_test_data(self):
        self.ensure_one()
        from datetime import datetime, date

        # Defaults taken from the "Welspun Initial Vertical Load test" sheet.
        if not self.effective_area_jack:
            self.effective_area_jack = 2001.9
        if not self.max_test_load:
            self.max_test_load = 318.0
        if not self.pile_diameter:
            self.pile_diameter = 600.0
        if not self.test_start_date:
            self.test_start_date = date(2026, 4, 9)
        if not self.test_end_date:
            self.test_end_date = date(2026, 6, 9)
        if not self.dial_gauge_least_count:
            self.dial_gauge_least_count = "0.01 mm"
        if not self.name:
            self.name = "418 MLD WASTE WATER TREATMENT FACILITIES AT DHARAVI"
        if not self.work_name:
            self.work_name = self.name
        if not self.pile_no:
            self.pile_no = "Gas Building Test Pile-Static Load Test"
        if not self.test_standard:
            self.test_standard = "IS 2911 (Part 4)"

        self.action_prefill_contents()

        self.env['fst.initial.vertical.load.basic.data'].search(
            [('parent_id', '=', self.id)]).unlink()

        basic_data = [
            ("1", "Project Name", self.name),
            ("2", "Pile No", self.pile_no or ""),
            ("3", "Pile Diameter", f"{self.pile_diameter:.0f} mm" if self.pile_diameter else ""),
            ("4", "Type of Pile", "Bored Initial Test Pile"),
            ("5", "Type of Test", "Initial Vertical Pile Load Test"),
            ("6", "Maximum Test Load", f"{self.max_test_load:.2f} MT" if self.max_test_load else ""),
            ("7", "Design Load", f"{self.design_load:.2f} MT" if self.design_load else ""),
            ("8", "Test Standard", self.test_standard or "IS 2911 (Part 4)"),
        ]
        for sr, param, value in basic_data:
            self.env['fst.initial.vertical.load.basic.data'].create({
                'parent_id': self.id,
                'sr_no': int(sr),
                'parameter': param,
                'value': value,
            })

        # Clear any previously generated readings before regenerating.
        self.loading_reading_ids.unlink()
        self.unloading_reading_ids.unlink()

        # (pressure gauge, reading interval, dial_a, dial_b, dial_c, dial_d)
        loading_data = [
            (15.0, 0, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 0.5, 0.72, 0.4, 0.23),
            (0.0, 30, 0.53, 0.73, 0.42, 0.25),
            (0.0, 30, 0.56, 0.75, 0.45, 0.28),
            (0.0, 60, 0.59, 0.79, 0.47, 0.3),
            (30.0, 0, 0.59, 0.79, 0.47, 0.3),
            (0.0, 15, 1.01, 1.12, 0.91, 0.82),
            (0.0, 30, 1.04, 1.16, 0.95, 0.86),
            (0.0, 30, 1.06, 1.18, 0.97, 0.88),
            (0.0, 60, 1.08, 1.19, 0.98, 0.89),
            (45.0, 0, 1.08, 1.19, 0.98, 0.89),
            (0.0, 15, 1.78, 1.82, 1.6, 1.52),
            (0.0, 30, 1.83, 1.87, 1.65, 1.54),
            (0.0, 30, 1.86, 1.9, 1.67, 1.56),
            (0.0, 60, 1.87, 1.91, 1.68, 1.57),
            (60.0, 0, 1.87, 1.91, 1.68, 1.57),
            (0.0, 15, 2.2, 2.32, 2.05, 1.97),
            (0.0, 30, 2.25, 2.37, 2.09, 2.01),
            (0.0, 30, 2.28, 2.41, 2.12, 2.04),
            (0.0, 60, 2.29, 2.43, 2.15, 2.05),
            (75.0, 0, 2.29, 2.43, 2.15, 2.05),
            (0.0, 15, 2.83, 2.92, 2.72, 2.62),
            (0.0, 30, 2.86, 2.93, 2.73, 2.63),
            (0.0, 30, 2.89, 2.95, 2.74, 2.65),
            (0.0, 60, 2.9, 2.96, 2.75, 2.66),
            (90.0, 0, 2.9, 2.96, 2.75, 2.66),
            (0.0, 15, 3.45, 3.65, 3.39, 3.27),
            (0.0, 30, 3.45, 3.67, 3.41, 3.27),
            (0.0, 30, 3.48, 3.66, 3.41, 3.29),
            (0.0, 60, 3.49, 3.66, 3.43, 3.31),
            (105.0, 0, 3.49, 3.66, 3.43, 3.31),
            (0.0, 15, 4.7, 4.89, 4.6, 4.45),
            (0.0, 30, 4.75, 4.93, 4.63, 4.48),
            (0.0, 30, 4.78, 4.95, 4.65, 4.5),
            (0.0, 60, 4.8, 4.97, 4.66, 4.52),
            (120.0, 0, 4.8, 4.97, 4.66, 4.52),
            (0.0, 15, 5.62, 5.75, 5.15, 5.02),
            (0.0, 30, 5.63, 5.76, 5.16, 5.02),
            (0.0, 30, 5.64, 5.77, 5.17, 5.04),
            (0.0, 60, 5.66, 5.78, 5.18, 5.05),
            (135.0, 0, 5.66, 5.78, 5.18, 5.05),
            (0.0, 15, 6.35, 6.49, 6.02, 5.91),
            (0.0, 30, 6.38, 6.53, 6.03, 5.93),
            (0.0, 30, 6.39, 6.54, 6.03, 5.96),
            (0.0, 60, 6.4, 6.54, 6.03, 5.96),
            (150.0, 0, 6.4, 6.54, 6.03, 5.96),
            (0.0, 15, 7.12, 7.25, 7.01, 6.9),
            (0.0, 30, 7.15, 7.28, 7.02, 6.93),
            (0.0, 30, 7.18, 7.29, 7.04, 6.95),
            (0.0, 60, 7.2, 7.29, 7.06, 6.98),
            (160.0, 0, 7.2, 7.29, 7.06, 6.98),
            (0.0, 15, 8.08, 8.29, 8.01, 7.91),
            (0.0, 30, 8.12, 8.32, 8.05, 7.94),
            (0.0, 30, 8.14, 8.35, 8.1, 7.98),
            (0.0, 60, 8.16, 8.35, 8.1, 7.98),
            (160.0, 0, 8.3, 8.53, 8.27, 8.19),
        ]

        unloading_data = [
            (150.0, 0, 8.3, 8.53, 8.27, 8.19),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 8.26, 8.52, 8.24, 8.16),
            (135.0, 0, 8.26, 8.52, 8.24, 8.16),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 8.23, 8.5, 8.21, 8.13),
            (120.0, 0, 8.23, 8.5, 8.21, 8.13),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 8.2, 8.48, 8.19, 8.11),
            (105.0, 0, 8.2, 8.48, 8.19, 8.11),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 8.17, 8.46, 8.17, 8.09),
            (90.0, 0, 8.17, 8.46, 8.17, 8.09),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 8.12, 8.4, 8.12, 8.04),
            (75.0, 0, 8.12, 8.4, 8.12, 8.04),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 8.06, 8.31, 8.05, 8.01),
            (60.0, 0, 8.06, 8.31, 8.05, 8.01),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 8.01, 8.22, 7.95, 7.91),
            (45.0, 0, 8.01, 8.22, 7.95, 7.91),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 7.92, 8.1, 7.8, 7.78),
            (30.0, 0, 7.92, 8.1, 7.8, 7.78),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 7.7, 7.92, 7.61, 7.65),
            (15.0, 0, 7.7, 7.92, 7.61, 7.65),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 7.6, 7.81, 7.52, 7.54),
            (0.0, 0, 7.6, 7.81, 7.52, 7.54),
            (0.0, 15, 0.0, 0.0, 0.0, 0.0),
            (0.0, 30, 0.0, 0.0, 0.0, 0.0),
            (0.0, 45, 0.0, 0.0, 0.0, 0.0),
            (0.0, 15, 7.02, 7.1, 7.05, 6.99),
        ]

        base = datetime(2026, 4, 9, 8, 0, 0)
        for idx, (pressure, interval, a, b, c, d) in enumerate(loading_data):
            self.env['fst.initial.vertical.load.reading.loading'].create({
                'parent_id': self.id,
                'reading_datetime': base + timedelta(minutes=15 * idx),
                'reading_interval': interval,
                'pressure_gauge': pressure,
                'dial_a': a,
                'dial_b': b,
                'dial_c': c,
                'dial_d': d,
            })

        for idx, (pressure, interval, a, b, c, d) in enumerate(unloading_data):
            self.env['fst.initial.vertical.load.reading.unloading'].create({
                'parent_id': self.id,
                'reading_datetime': base + timedelta(minutes=15 * (len(loading_data) + idx)),
                'reading_interval': interval,
                'pressure_gauge': pressure,
                'dial_a': a,
                'dial_b': b,
                'dial_c': c,
                'dial_d': d,
            })

        self.action_recompute_all()

    @api.depends('loading_summary_ids.cumulative_settlement')
    def _compute_max_settlement(self):
        for rec in self:
            values = rec.loading_summary_ids.mapped('cumulative_settlement')
            rec.max_settlement = max(values) if values else 0.0

    @api.depends('loading_summary_ids.cumulative_settlement')
    def _compute_settlement_values(self):
        for rec in self:
            summaries = rec.loading_summary_ids.sorted('sequence')
            if summaries:
                peak = max(summaries, key=lambda s: s.cumulative_settlement)
                gross = peak.cumulative_settlement
                final = summaries[-1].cumulative_settlement if len(summaries) > 1 else gross
                rebound = gross - final
            else:
                gross = 0.0
                rebound = 0.0

            net = gross - rebound

            rec.gross_settlement = round(gross, 2)
            rec.rebound = round(rebound, 2)
            rec.net_settlement = round(net, 2)

    def action_generate_graph(self):
        self.ensure_one()
        self._recompute_loading_summary()
        self.env.cr.execute(
            "SELECT target_settlement, allowable_load FROM fst_initial_vertical_load_test WHERE id = %s",
            (self.id,)
        )
        row = self.env.cr.dictfetchone()

        summaries = self.loading_summary_ids.sorted('sequence')
        if not summaries:
            self.graph_image = False
            return

        loading = [(s.load_tonne, s.cumulative_settlement)
                   for s in summaries if s.load_type == 'loading']
        unloading = [(s.load_tonne, s.cumulative_settlement)
                     for s in summaries if s.load_type == 'unloading']

        if not unloading:
            for i in range(1, len(summaries)):
                if summaries[i].load_tonne < summaries[i-1].load_tonne:
                    loading = [(s.load_tonne, s.cumulative_settlement)
                               for s in summaries[:i]]
                    unloading = [(s.load_tonne, s.cumulative_settlement)
                                 for s in summaries[i:]]
                    break

        # Full test path, kept in testing sequence. The (0, 0) origin starts the
        # loading branch; the unloading branch starts at the peak of loading.
        load_x = [0.0] + [p[0] for p in loading]
        load_y = [0.0] + [p[1] for p in loading]

        if unloading:
            unload_x = [load_x[-1]] + [p[0] for p in unloading]
            unload_y = [load_y[-1]] + [p[1] for p in unloading]
        else:
            unload_x, unload_y = [], []

        def _smooth_branch(x, y):
            """Shape-preserving smoothing that keeps the measured sequence.

            The points are never sorted by load. A branch is only smoothed when
            its load is monotonic, and the smoothed samples are emitted in the
            same order as the readings (loading low->high, unloading high->low).
            PCHIP passes through every measured point without overshoot, so the
            measured curve is not distorted.
            """
            if len(x) < 3:
                return list(x), list(y)
            x_np = np.asarray(x, dtype=float)
            y_np = np.asarray(y, dtype=float)
            diffs = np.diff(x_np)
            if np.all(diffs > 0):
                sign = 1.0
            elif np.all(diffs < 0):
                sign = -1.0
            else:
                # Non-monotonic branch (e.g. reloading): draw as measured.
                return list(x), list(y)
            # PCHIP needs a strictly increasing abscissa; flip the sign for the
            # unloading branch without reordering the readings.
            t = sign * x_np
            # A vertical hold gives duplicate loads; keep the last reading so the
            # interpolant stays a single-valued function of load.
            keep = np.concatenate((np.diff(t) > 0, [True]))
            t_u, y_u = t[keep], y_np[keep]
            if len(t_u) < 3:
                return list(x), list(y)
            try:
                interp = PchipInterpolator(t_u, y_u)
                t_dense = np.linspace(t_u.min(), t_u.max(), 200)
                return sign * t_dense, interp(t_dense)
            except Exception:
                return list(x), list(y)

        # User-defined gaps. Each branch has its own list of break loads: a load
        # listed there is not connected to the next point, so that branch is
        # drawn as separate segments.
        def _parse_loads(value):
            loads = []
            for token in (value or '').replace('\n', ',').split(','):
                token = token.strip()
                if not token:
                    continue
                try:
                    loads.append(float(token))
                except ValueError:
                    continue
            return loads

        load_breaks = _parse_loads(self.graph_break_loads)
        unload_breaks = _parse_loads(self.graph_break_unload_loads)

        def _segments(x, y, breaks):
            """Split a branch where the load matches a configured break point."""
            if not breaks or len(x) < 2:
                return [(list(x), list(y))]
            cut = set()
            for i, xv in enumerate(x):
                if i < len(x) - 1 and any(abs(xv - b) <= 1.0 for b in breaks):
                    cut.add(i)
            segments = []
            start = 0
            for i in range(len(x)):
                if i in cut:
                    segments.append((list(x[start:i + 1]), list(y[start:i + 1])))
                    start = i + 1
            if start < len(x):
                segments.append((list(x[start:]), list(y[start:])))
            return segments

        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        BLUE = '#1e3a5f'
        for seg_x, seg_y in _segments(load_x, load_y, load_breaks):
            seg_xs, seg_ys = _smooth_branch(seg_x, seg_y)
            ax.plot(seg_xs, seg_ys, color=BLUE, linewidth=2.0, zorder=2)
        ax.scatter(load_x, load_y, color=BLUE, s=32, marker='D',
                   zorder=5, edgecolors='white', linewidths=0.6)
        if unload_x:
            for seg_x, seg_y in _segments(unload_x, unload_y, unload_breaks):
                seg_xs, seg_ys = _smooth_branch(seg_x, seg_y)
                ax.plot(seg_xs, seg_ys, color=BLUE, linewidth=2.0, zorder=2)
            ax.scatter(unload_x, unload_y, color=BLUE, s=32, marker='D',
                       zorder=5, edgecolors='white', linewidths=0.6)

        # Geotechnical convention: load on the top axis, settlement on the left.
        ax.xaxis.set_label_position('top')
        ax.xaxis.tick_top()
        ax.tick_params(axis='x', which='both', bottom=False, top=True,
                       direction='out', length=5)
        ax.tick_params(axis='y', which='both', direction='out', length=5)
        ax.set_xlabel('Load in MT', fontsize=10, fontweight='bold', labelpad=8)
        ax.set_ylabel('Settlement, mm', fontsize=10, fontweight='bold', labelpad=8)
        ax.set_title('LOAD Vs SETTLEMENT CURVE', fontsize=12, fontweight='bold',
                     pad=14)

        for spine in ax.spines.values():
            spine.set_linewidth(0.8)
            spine.set_color('#000000')

        # Numeric (non-categorical) axes with major/minor ticks.
        all_x = list(load_x) + list(unload_x)
        x_peak = max(all_x) if all_x else 30.0
        x_top = int(np.ceil(x_peak / 30.0)) * 30 or 30
        ax.set_xlim(0, x_top)
        ax.xaxis.set_major_locator(MultipleLocator(30))
        ax.xaxis.set_minor_locator(MultipleLocator(10))

        all_y = list(load_y) + list(unload_y)
        y_peak = max(all_y) if all_y else 10.0
        y_top = int(np.ceil(y_peak / 2.0)) * 2 or 2
        ax.set_ylim(0, y_top)
        ax.invert_yaxis()
        ax.yaxis.set_major_locator(MultipleLocator(2))
        ax.yaxis.set_minor_locator(MultipleLocator(1))

        ax.grid(True, which='major', color='#b0b0b0', linestyle='--',
                linewidth=0.5, alpha=0.5)

        y_target = row['target_settlement'] or 0.0
        x_limit = row['allowable_load'] or 0.0
        if y_target and x_limit and y_peak > y_target:
            ax.annotate('', xy=(0, y_target), xytext=(x_limit, y_target),
                        arrowprops=dict(arrowstyle='<->', color='red', lw=1.2))
            ax.text(x_top * 0.01, y_target + y_top * 0.03,
                    f'{y_target} mm Settlement',
                    fontsize=8, color='red', va='bottom')

            ax.annotate('', xy=(x_limit, y_target),
                        xytext=(x_limit, 0),
                        arrowprops=dict(arrowstyle='<->', color='red', lw=1.2))
            ax.text(x_limit + x_top * 0.02, y_target / 2,
                    'Allowable\nLoad', fontsize=8, color='red', ha='left',
                    va='center')

        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, facecolor='white')
        plt.close(fig)
        self.graph_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    def action_generate_log_graph(self):
        """Log-log Load vs Uplift/Settlement engineering curve."""
        self.ensure_one()
        self._recompute_loading_summary()

        summaries = self.loading_summary_ids.sorted('sequence')
        if not summaries:
            self.graph_image_log = False
            return

        # X = uplift / settlement (mm), Y = load (MT), kept in test sequence.
        # A logarithmic axis cannot show zero or negative values, so those
        # readings are skipped.
        points = [
            (s.cumulative_settlement, s.load_tonne, s.load_type)
            for s in summaries
            if s.cumulative_settlement > 0 and s.load_tonne > 0
        ]
        if not points:
            self.graph_image_log = False
            return

        def _parse_loads(value):
            loads = []
            for token in (value or '').replace('\n', ',').split(','):
                token = token.strip()
                if not token:
                    continue
                try:
                    loads.append(float(token))
                except ValueError:
                    continue
            return loads

        load_breaks = _parse_loads(self.graph_break_loads)
        unload_breaks = _parse_loads(self.graph_break_unload_loads)

        # Split the test sequence where a point's load matches a configured
        # break for its stage; the measured order is otherwise preserved.
        segments = []
        start = 0
        for i in range(len(points) - 1):
            _, load_val, stage = points[i]
            breaks = load_breaks if stage == 'loading' else unload_breaks
            if breaks and any(abs(load_val - b) <= 1.0 for b in breaks):
                segments.append(points[start:i + 1])
                start = i + 1
        segments.append(points[start:])

        x_vals = [p[0] for p in points]
        y_vals = [p[1] for p in points]

        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        # XY plot of the measured points in test sequence (never sorted).
        for seg in segments:
            ax.plot(
                [p[0] for p in seg],
                [p[1] for p in seg],
                color='#1f4e9c',
                linewidth=1.8,
                marker='D',
                markersize=6,
                markerfacecolor='#1f4e9c',
                markeredgecolor='#1f4e9c',
                zorder=3,
            )

        ax.set_xscale('log')
        ax.set_yscale('log')

        # Major ticks at powers of ten, logarithmic minor ticks in between.
        ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=15))
        ax.xaxis.set_minor_locator(
            LogLocator(base=10.0, subs=tuple(range(2, 10)), numticks=15))
        ax.yaxis.set_major_locator(LogLocator(base=10.0, numticks=15))
        ax.yaxis.set_minor_locator(
            LogLocator(base=10.0, subs=tuple(range(2, 10)), numticks=15))

        def _plain_log_label(value, _pos):
            return '' if value <= 0 else f'{value:g}'

        ax.xaxis.set_major_formatter(FuncFormatter(_plain_log_label))
        ax.yaxis.set_major_formatter(FuncFormatter(_plain_log_label))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.yaxis.set_minor_formatter(NullFormatter())

        # Engineering defaults (0.1-10 mm, 1-1000 MT), expanded only if the
        # measured data needs a wider logarithmic range.
        def _log_floor(value):
            return 10.0 ** math.floor(math.log10(value))

        def _log_ceil(value):
            return 10.0 ** math.ceil(math.log10(value))

        ax.set_xlim(min(0.1, _log_floor(min(x_vals))),
                    max(10.0, _log_ceil(max(x_vals))))
        ax.set_ylim(min(1.0, _log_floor(min(y_vals))),
                    max(1000.0, _log_ceil(max(y_vals))))

        serif = 'serif'
        ax.set_title('LOAD SETTLEMENT CURVE', fontsize=13, fontweight='bold',
                     fontfamily=serif, pad=14)
        ax.set_xlabel('Uplift in mm', fontsize=11, fontfamily=serif, labelpad=8)
        ax.set_ylabel('Load in MT', fontsize=11, fontfamily=serif, labelpad=8)

        ax.tick_params(axis='both', which='major', length=6, width=0.9,
                       color='black', labelcolor='black')
        ax.tick_params(axis='both', which='minor', length=3, width=0.7,
                       color='black')
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontfamily(serif)
            label.set_fontsize(9)

        for spine in ax.spines.values():
            spine.set_color('black')
            spine.set_linewidth(1.0)

        ax.grid(False)

        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, facecolor='white')
        plt.close(fig)
        self.graph_image_log = base64.b64encode(buf.getvalue()).decode('utf-8')

    def action_recompute_all(self):
        for rec in self:
            for line in rec.loading_reading_ids:
                line._compute_split_dt()
            for line in rec.unloading_reading_ids:
                line._compute_split_dt()

            rec.sudo()._recompute_loading_summary()
            rec._compute_settlement_values()
            rec._compute_max_settlement()

    def _recompute_loading_summary(self):
        Summary = self.env['fst.initial.vertical.load.loading.summary'].sudo()
        for rec in self:
            Summary.search([('parent_id', '=', rec.id)]).unlink()

            def _group_lines(lines):
                # A load step starts at every reading carrying a pressure gauge
                # value (non-zero load) or explicitly marked with a zero reading
                # interval (e.g. the final unloading step held at 0 load).
                # Sub-readings entered without a pressure gauge value (load 0)
                # continue the current step instead of starting a new one.
                # Consecutive steps may share the same load (e.g. test load
                # held), so the load value alone must not be used to merge steps.
                result = []
                cur = None
                for line in lines:
                    load = line.load_tonne
                    if not result or load != 0 or line.reading_interval == 0:
                        cur = load
                        result.append((cur, []))
                    result[-1][1].append(line)
                return result

            def _process(groups, load_type, seq, running_cum, prev_cum):
                for load_val, group in groups:
                    first_cum = None
                    last_cum = None
                    for line in group:
                        cum = line.cumulative_dial
                        if first_cum is None:
                            first_cum = cum
                        last_cum = cum

                    # A single reading per step carries no start reference, so
                    # use the previous step's last cumulative reading.
                    if len(group) == 1 and prev_cum is not None:
                        first_cum = prev_cum

                    if first_cum is None or last_cum is None:
                        continue

                    avg_raw = (last_cum - first_cum) / 4.0
                    avg_settlement = round(avg_raw, 2)

                    prev_cum = last_cum

                    if avg_settlement == 0.0:
                        continue

                    seq += 1
                    running_cum += avg_raw

                    Summary.create({
                        'parent_id': rec.id,
                        'sequence': seq,
                        'load_type': load_type,
                        'load_tonne': load_val,
                        'avg_settlement': avg_settlement,
                        'cumulative_settlement': round(running_cum, 2),
                    })
                return seq, running_cum, prev_cum

            seq = 0
            running_cum = 0.0
            prev_cum = None

            loading_groups = _group_lines(rec.loading_reading_ids.sorted('reading_datetime'))
            seq, running_cum, prev_cum = _process(
                loading_groups, 'loading', seq, running_cum, prev_cum
            )

            unloading_groups = _group_lines(rec.unloading_reading_ids.sorted('reading_datetime'))
            seq, running_cum, prev_cum = _process(
                unloading_groups, 'unloading', seq, running_cum, prev_cum
            )

    def print_report(self):
        self.ensure_one()
        return self.env.ref(
            'fst_initial_vertical_load_test.initial_vertical_load_report'
        ).report_action(self)

    def action_duplicate_parent(self):
        for record in self:
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'loading_reading_ids': False,
                'unloading_reading_ids': False,
                'content_ids': False,
                'basic_data_ids': False,
                'site_image_ids': False,
                'graph_image': False,
            })

            for line in record.loading_reading_ids:
                line.copy({'parent_id': new_parent.id})

            for line in record.unloading_reading_ids:
                line.copy({'parent_id': new_parent.id})

            for line in record.content_ids:
                line.copy({'parent_id': new_parent.id})

            for line in record.basic_data_ids:
                line.copy({'parent_id': new_parent.id})

            for line in record.site_image_ids:
                line.copy({'parent_id': new_parent.id})

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


class FstInitialVerticalLoadReadingLoading(models.Model):
    _name = "fst.initial.vertical.load.reading.loading"
    _description = "Initial Vertical Load Reading - Loading"
    _order = "id"

    parent_id = fields.Many2one(
        "fst.initial.vertical.load.test",
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

    reading_interval = fields.Integer("Reading Interval (Min)")
    pressure_gauge = fields.Float("Pressure Gauge Reading (kg/cm²)")
    load_tonne = fields.Float("Load (MT)", compute="_compute_load_tonne", store=True, readonly=False)
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    dial_c = fields.Float("Dial C (mm)")
    dial_d = fields.Float("Dial D (mm)")
    cumulative_dial = fields.Float(
        "Cumulative Dial Reading (mm)",
        compute="_compute_cumulative_dial",
        store=True,
        readonly=True
    )

    @api.depends('pressure_gauge', 'parent_id.effective_area_jack')
    def _compute_load_tonne(self):
        for rec in self:
            area = rec.parent_id.effective_area_jack or 0.0
            rec.load_tonne = round(rec.pressure_gauge * area / 1000.0, 4)

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_cumulative_dial(self):
        for rec in self:
            rec.cumulative_dial = round(
                rec.dial_a + rec.dial_b + rec.dial_c + rec.dial_d, 2
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'reading_datetime' in fields_list and 'reading_datetime' not in res:
            res['reading_datetime'] = fields.Datetime.now()
        return res

    @api.onchange('parent_id')
    def _onchange_set_datetime(self):
        if self.parent_id:
            latest_datetime = None
            unsaved_lines = [
                r for r in self.parent_id.loading_reading_ids
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

        res = super().create(vals)
        if res.parent_id:
            parent = res.parent_id.sudo()
            parent._recompute_loading_summary()
            parent._compute_settlement_values()
            parent._compute_max_settlement()
        return res

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('dial_a', 'dial_b', 'dial_c', 'dial_d', 'pressure_gauge')):
            for rec in self:
                if rec.parent_id:
                    parent = rec.parent_id.sudo()
                    parent._recompute_loading_summary()
                    parent._compute_settlement_values()
                    parent._compute_max_settlement()
        return res

    def unlink(self):
        parents = self.mapped('parent_id')
        res = super().unlink()
        for parent in parents:
            if parent:
                parent = parent.sudo()
                parent._recompute_loading_summary()
                parent._compute_settlement_values()
                parent._compute_max_settlement()
        return res

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


class FstInitialVerticalLoadReadingUnloading(models.Model):
    _name = "fst.initial.vertical.load.reading.unloading"
    _description = "Initial Vertical Load Reading - Unloading"
    _order = "id"

    parent_id = fields.Many2one(
        "fst.initial.vertical.load.test",
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

    reading_interval = fields.Integer("Reading Interval (Min)")
    pressure_gauge = fields.Float("Pressure Gauge Reading (kg/cm²)")
    load_tonne = fields.Float("Load (MT)", compute="_compute_load_tonne", store=True, readonly=False)
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    dial_c = fields.Float("Dial C (mm)")
    dial_d = fields.Float("Dial D (mm)")
    cumulative_dial = fields.Float(
        "Cumulative Dial Reading (mm)",
        compute="_compute_cumulative_dial",
        store=True,
        readonly=True
    )

    @api.depends('pressure_gauge', 'parent_id.effective_area_jack')
    def _compute_load_tonne(self):
        for rec in self:
            area = rec.parent_id.effective_area_jack or 0.0
            rec.load_tonne = round(rec.pressure_gauge * area / 1000.0, 4)

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_cumulative_dial(self):
        for rec in self:
            rec.cumulative_dial = round(
                rec.dial_a + rec.dial_b + rec.dial_c + rec.dial_d, 2
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

        res = super().create(vals)
        if res.parent_id:
            parent = res.parent_id.sudo()
            parent._recompute_loading_summary()
            parent._compute_settlement_values()
            parent._compute_max_settlement()
        return res

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('dial_a', 'dial_b', 'dial_c', 'dial_d', 'pressure_gauge')):
            for rec in self:
                if rec.parent_id:
                    parent = rec.parent_id.sudo()
                    parent._recompute_loading_summary()
                    parent._compute_settlement_values()
                    parent._compute_max_settlement()
        return res

    def unlink(self):
        parents = self.mapped('parent_id')
        res = super().unlink()
        for parent in parents:
            if parent:
                parent = parent.sudo()
                parent._recompute_loading_summary()
                parent._compute_settlement_values()
                parent._compute_max_settlement()
        return res

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


class FstInitialVerticalLoadReportContent(models.Model):
    _name = "fst.initial.vertical.load.report.content"
    _description = "Initial Vertical Load Test Report Contents"
    _order = "sequence, id"

    parent_id = fields.Many2one("fst.initial.vertical.load.test", ondelete="cascade")
    sequence = fields.Float("Sl. No")
    section_number = fields.Char("Section Number")
    description = fields.Char("Name")
    parent_section = fields.Char("Parent Section")
    is_subsection = fields.Boolean("Is Subsection")
    page_no = fields.Char("Page No")


class FstInitialVerticalLoadBasicData(models.Model):
    _name = "fst.initial.vertical.load.basic.data"
    _description = "Initial Vertical Load Test Basic Data"

    parent_id = fields.Many2one("fst.initial.vertical.load.test", ondelete="cascade")
    sr_no = fields.Integer("Sl No")
    parameter = fields.Char("Parameter")
    value = fields.Char("Value")


class FstInitialVerticalLoadSummary(models.Model):
    _name = "fst.initial.vertical.load.loading.summary"
    _description = "Initial Vertical Load Test - Settlement Summary"
    _order = "sequence, id"

    parent_id = fields.Many2one(
        "fst.initial.vertical.load.test",
        ondelete="cascade",
        required=True
    )
    sequence = fields.Integer("Sr No")
    load_type = fields.Selection([
        ('loading', 'Loading'),
        ('unloading', 'Unloading'),
    ], string="Stage", default='loading', required=True)
    load_tonne = fields.Float("Load on Plate (MT)")
    avg_settlement = fields.Float("Average Settlement (mm)")
    cumulative_settlement = fields.Float("Cumulative Settlement (mm)")


class FstInitialVerticalLoadTestImage(models.Model):
    _name = "fst.initial.vertical.load.test.image"
    _description = "Initial Vertical Load Test Site Photograph"

    parent_id = fields.Many2one("fst.initial.vertical.load.test", ondelete="cascade")
    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph")
    caption = fields.Char("Caption")
