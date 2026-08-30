import base64

from odoo import api, fields, models
from odoo.modules.module import get_module_resource


class PileIntegrityTest(models.Model):
    _name = "pile.integrity.test"
    _description = "Low Strain Pile Integrity Test Report"
    _order = "rec_date desc, id desc"
    _rec_name = "name"

    name = fields.Char("Name", default="Pile Integrity")

    report_no = fields.Char("Report No", copy=False)
    ulr_no = fields.Char("ULR No", copy=False)
    rec_date = fields.Date("Report Date")
    test_date = fields.Date("Date of Testing")

    customer_name = fields.Char(string="Customer Name")
    customer_address = fields.Text(string="Customer Address")
    client = fields.Char(string="Client")
    principal_client = fields.Char(string="PMC")
    site_name_addr = fields.Text(string="Site Name & Address")

    code_ref = fields.Char(
        string="Code of Reference",
        default="ASTM D5882-16",
    )

    pile_integrity_name = fields.Char(default="1) PILE INTEGRITY DESCRIPTIONS")

    introduction = fields.Text(
        string="Introduction",
        default="""M/s  has engaged us to conduct pile integrity testing (PIT) on cast in situ bored piles.
                            This report presents the results of pile integrity testing using the
                            Low Strain Pile Integrity Test method.
                            The objective of testing is to assess pile integrity for potential
                            defects such as necking, cross-sectional changes, honeycombing,
                            discontinuities and concrete quality variations.""",
    )

    principle_details = fields.Text(
        string="Principle",
        default="The test is based on wave propagation theory.(Wave propagation is any of the ways in which waves travel.) In the sonic test, the top of the pile is hit is heat with the plastic hammer and the reflected waves are recorded by a suitable computerized equipment. From the resulting signal, or reflectogram, one can determine the continuity of the pile.",
    )

    equipment_details = fields.Text(
        string="Equipment Details",
        default="""Pile Integrity Tester (PIT) with accelerometer/transducer, instrumented hammer and data acquisition software.""",
    )

    procedure = fields.Text(
        string="Procedure",
        default="1. Take 5 points on pile center, north, south, east, and west side\n"
                "2. A small metal/hard rubber hammer is used to\n"
                "3. The shock reflected is recorded through a transducer in a computer disk.\n"
                "4. More than one recording of signals is done until the repeatability of signals is the average of blows.",
    )

    influences_result = fields.Text(
        string="Influences Of Test Result",
        default="The top of the pile should consist of clean concrete and free of debris, laitance and bentonite.\n"
                "The test requires the surface preparation to be done properly. For the test to be effective, the top of the pile should\n"
                "consist of clean concrete and free of debris, laitance and bentonite. Testing a pile with a head which was not\n"
                "properly prepared may yield misleading results.\n"
                "For larger diameter piles, it is recommended that the test be carried out at multiple locations on the pile head to\n"
                "accurately determine the results.\n"
                "If pile records are available like bore-logs, cut length, then the results can be fine tuned for greater & more\n"
                "reliable information.",
    )

    interpretation_result = fields.Text(
        string="Interpretation Of Test Result",
        default="""This indicates reduction in cross section at a particular area of the pile. If this happens, it means a reduction of the
                                                    pile load carrying capacity & exposed reinforcements that could get corroded due to ground water and soil
                                                    chemical attacks. This is indicated by "reduction in impedance" noting in the report. A correlation with the soil
                                                    investigation report indicated if the reduction in
                                                    Impedance due to soil strata change or due to change in the diameter of the pile. When a serious reduction is
                                                    observed, the pile is termed as doubtful.""",
    )

    limitations = fields.Text(
        string="Limitations",
        default="""The test results are based on Low Strain Pile Integrity Testing and should be interpreted in conjunction with pile construction records and soil investigation data.
                                        The method is primarily intended to identify major defects, changes in cross section, necking, bulging, discontinuities and significant impedance variations.
                                        The test does not directly measure pile load carrying capacity and may not detect minor defects located deep within the pile shaft.
                                        Results may be influenced by pile head condition, surrounding soil characteristics and testing conditions.""",
    )

    conclusion = fields.Text(
        string="Conclusion",
        default="""Based on the Low Strain Pile Integrity Test results, the tested pile(s) exhibited the characteristics presented in the attached reflectograms and result tables.
                                        The observations and interpretations presented in this report are based on the recorded wave responses obtained during testing and should be considered together with available construction and geotechnical information.""",
    )

    test_result = fields.Text(
        string="DISCUSSION OF TEST RESULTS:",
        default="""The test results for the tested piles are attached in Appendix I of the report.
                                        Pile Integrity Testing was conducted on 1200 mm diameter bored cast in situ piles.
                                        The test results for the pile tested have been attached in the report.
                                        Wave speed for the piles varied from 3904 m/s to 4307 m/sec and can be termed as concrete of consistent quality.
                                        The input data such as pile diameter, length, and grade are made available by the agency.
                                        This report has been prepared with generally accepted engineering practices and the results of integrity testing as per ASTM D5882.
                                        No other warranty, expressed or implied, is made.
                                        The findings provided in this report are based on the result of the individual pile tested and information made available to us.""",
    )

    pile_integrity_test_name = fields.Char(default=" PILE INTEGRITY TEST")

    pile_type = fields.Char(
        string="Type of Pile",
        default="Cast In Situ Bored Pile",
    )
    pile_diameter = fields.Integer("Pile Diameter (mm)")
    pile_depth = fields.Char("Pile Depth From Test Level (m)")
    concrete_grade = fields.Char("Concrete Grade")

    temperature = fields.Float("Temperature °C")
    instrument = fields.Char("Instrument")

    content_ids = fields.One2many(
        "pile.integrity.test.contents",
        "parent_id",
        string="Contents",
    )
    pile_integrity_test_table = fields.One2many(
        "pile.integrity.test.line",
        "parent_id",
    )
    image_ids = fields.One2many(
        "pile.integrity.test.image",
        "parent_id",
        string="Site Images",
    )

    signatory_name = fields.Char("Authorized Signatory")
    signatory_designation = fields.Char("Designation")

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._generate_default_contents()
        record._populate_default_report_text()
        return record

    def _generate_default_contents(self):
        self.ensure_one()

        contents = [
            ("1.", "INTRODUCTION"),
            ("2.", "PILE DETAIL"),
            ("3.", "OVERVIEW"),
            ("4.", "EQUIPMENT DETAILS"),
            ("5.", "METHODOLOGY"),
            ("6.", "INTERPRETATION OF RESULTS"),
            ("7.", "LIMITATIONS OF PILE INTEGRITY TEST"),
            ("8.", "DISCUSSION OF TEST RESULTS"),
            ("9.", "CONCLUSION"),
            ("10.", "APPENDIX I - PILE INTEGRITY TEST RESULTS"),
            ("11.", "APPENDIX II - REFLECTOGRAM OF PILES"),
        ]

        self.write({
            "content_ids": [(5, 0, 0)] + [
                (0, 0, {
                    "seq": seq,
                    "name": name,
                    "page_no": "",
                })
                for seq, name in contents
            ],
        })

    def action_prefill_contents(self):
        self.ensure_one()
        self._generate_default_contents()
        self._populate_default_report_text()

    def _populate_default_report_text(self):
        """Populate standard report text from report details."""

        self.ensure_one()

        test_date = ""
        if self.test_date:
            test_date = self.test_date.strftime("%d %B, %Y") or "-"

        customer = self.customer_name or ""

        self.write({
            "introduction": (
                f"{customer} has engaged us to conduct pile integrity testing (PIT) on cast in situ bored piles. "
                "This report presents the results of pile integrity testing using the Pile Integrity Tester (PIT), "
                "based on the details provided by the client and the site conditions at the time of testing. "
                "The aim of testing was to assess the pile integrity for potential problems like cross-sectional "
                "changes, honeycombing, concrete quality, continuity etc. "
                "The tests were conducted by Low Strain Pile Integrity Tester in accordance with ASTM D5882 & "
                "IS 14893. "
                f"Tests were conducted on {test_date}."
            ),
            "equipment_details": (
                "Integrity tests were performed using the most advanced state of art data collection system available to estimate pile integrity by surface impact methods."
                "In this system the PIT Collector allows for detection of wave reflections from changes in pile impedance."
                "The Collector can acquire, enhance, display and plot data."
                "The conclusion and interpretation of the results are based on the pile top velocity against time curve.\n\n"
                "The testing involves attachment of accelerometer on the pile top."
                "After attachment, the impact device (a nylon tipped hammer) generates a low strain compressive wave, which travels down the pile."
                "The acceleration and velocity records of the impact, along with subsequent reflections from either pile toe and/or discontinuity are graphically displayed.\n\n"
                "The integrity testing method separates the effect of impact and surface reflections from other relevant reflections (i.e. Piles toe or other discontinuities) by averaging records of several impacts."
                "This averaging technique tends to cancel random signals in any particular blow while amplifying the effect of the relevant repetitive response.\n\n"
                "The signal records obtained are also exponentially amplified with time. This enhances the identification of relevant reflections in records, which have low energy due to signals being dampened out by skin friction."
            ),
            "procedure": (
                "Pile head preparation is important in order to impart a clear impulse in the pile and allow the "
                "detection of the returning reflected signals. The sensor (usually accelerometer) is fixed to the "
                "pile head while the pile is struck with the hand-held hammer preferably at or near the pile "
                "centre. The induced pile head velocity records and the subsequent reflections from either pile "
                "toe and/or discontinuities are graphically displayed on the screen of the PIT collector. "
                "Several hammer blows are usually recorded on each pile for averaging the signals and to confirm "
                "that a consistent repeatable response is being obtained. In case of large diameter piles, the "
                "tests shall be conducted at 5-6 places to cover the entire section of the pile."
            ),
            "interpretation_result": (
                "The interpretation of results consists of evaluation of data based on the reflections recorded "
                "during testing. Reflections are produced by variations in shape, material, soil resistance "
                "changes, joints etc. The deepest reflector is the pile toe and its reflection is last observed. "
                "All such reflections are numerically integrated to velocity before being displayed. The integrity "
                "of the pile is evaluated based on detected changes in impedance (EA/c) along the pile length. "
                "Impedance variation usually refers to cross-sectional change.\n\n"
                "The typical data sets for uniform pile, defective pile, minor defective pile and bulge pile shall "
                "generally be as shown in Figure 1a, 1b, 1c and 1d respectively and are also defined in IS 14893 :2021.\n"
                "Refer to the typical trace for a defective pile in Figure 1b. The method cannot identify nature of defect "
                "as the wave reflect from a reduction in either elastic modulus or cross-section. "
                "Thus, whether the defect is necking, honeycombs, voids, soil inclusions, tremie choke etc. "
                "They are all classified as defects.\n\n"
                "However, all the scenarios are not acceptable and hence such piles are still classified as doubtful and may "
                "need further testing / remedial action / replacement / re-design based on its actual load carrying capacity etc. "
                "Bulbs are not classified as defects.\n\n"
                "The curve after the toe response is basically a second cycle of the wave moving through the pile. "
                "If the energy of impact is sufficient or for shorter pile lengths, it is possible that the wave moves a few times along the pile before "
                "it dies down whereas in some cases, it only completes a partial second cycle. Generally, the waveform after the first cycle is inconsequential for interpretation. \n\n"
                "The length is an important input into the test system which is used to compute wave speed. "
                "Typical range of wave speed for good and consistent concrete is 3500 m/sec to 4500 m/sec and wave speed lesser than 3500m/sec but up to 3200 m/sec "
                "is many times likely for large jobs with lesser quality control or very low percentage reinforcement. Piles with permanent liners may have "
                "consistently higher speeds from 3800 m/sec to 4500 m/sec.\n\n"
                "Piles with a major bulb may show a reflection from bulb and a secondary "
                "reflection similar to a defect. Such a secondary reflection should not be considered as a defect. "
                "The method is intended to detect major defect and minor defects like localized loss of cover may not be detected by this method. "
                "It is sometimes difficult to evaluate the magnitude of defect when pile defects are at half the pile length. \n\n"
                "Where minor decrease in impedance observed in piles and toe response is apparent, the piles with minor defect can be accepted as per "
                "Cl. 6.3.2, IS 14893:2021 & Cl. 6.6.6, ASTM D5882-16. However, engineer in charge of project should use judgement as to the acceptability "
                "of these piles considering other factors such as load redistribution to adjacent piles, load transfer to soil above the defect, applied safety factors and structural load requirements."
            ),
            "limitations": (
                "1. The test method can generally evaluate piles up to an L/D ratio of 45 to 50, depending on "
                "soil resistance.\n"
                "2. For piles with greatly varying cross-sectional area, especially in layered soils, it may be "
                "difficult to distinguish construction effects from localized discontinuities.\n"
                "3. The method cannot evaluate multiple defects inside the pile and is generally not suitable for "
                "jointed precast piles, steel piles, micropiles, etc.\n"
                "4. Although the test system can be used to evaluate length of piles, the determination of pile length "
                "is approximate within a range of ± 5 – 10% due to variation in concrete density. "
                "This implies that the method cannot evaluate defects that could be present in the bottom 5%- 10% of the pile shaft."
            ),
            "test_result": (
                "The test results for the tested piles are attached in Appendix I of the report. "
                f"Pile Integrity Testing was conducted on {self.pile_diameter} mm diameter bored cast in situ piles. "
                "The test results for the tested piles have been attached in the report. "
                "Wave speed for the piles varied from 3904 m/s to 4307 m/s and can be termed as concrete of "
                "consistent quality. The input data such as pile diameter, length and grade were made available "
                "by the agency.\n\n"
                "This report has been prepared in accordance with generally accepted engineering practices and "
                "the requirements of ASTM D5882. No other warranty, expressed or implied, is made. The findings "
                "presented are based solely on the individual piles tested and the information made available "
                "during testing."
            ),
            "influences_result": (
                "The top of the pile should consist of clean concrete and be free of debris, laitance and "
                "bentonite. Proper surface preparation is essential for obtaining reliable results. Testing on "
                "poorly prepared pile heads may produce misleading reflections.\n\n"
                "For larger diameter piles, testing should be carried out at multiple locations on the pile head "
                "to obtain representative results. Where construction records such as bore logs, pile lengths and "
                "casting details are available, they should be considered during interpretation to improve the "
                "reliability of the assessment."
            ),
        })

    def print_report(self):
        self.ensure_one()
        return self.env.ref('pile_integrity.pile_integrity_report_py3o').report_action(self)


class PileIntegrityTestContents(models.Model):
    _name = "pile.integrity.test.contents"
    _description = "Pile Integrity Contents"

    parent_id = fields.Many2one(
        "pile.integrity.test",
        string="Parent Id",
        ondelete="cascade",
    )
    seq = fields.Text(string="Sequence")
    name = fields.Text(string="Name")
    page_no = fields.Text(string="Page No")


class PileIntegrityTestImage(models.Model):
    _name = "pile.integrity.test.image"
    _description = "Pile Integrity Images"

    parent_id = fields.Many2one(
        "pile.integrity.test",
        string="Report",
        ondelete="cascade",
    )

    name = fields.Char()
    image = fields.Binary(attachment=True)


class PileIntegrityTestLine(models.Model):
    _name = "pile.integrity.test.line"
    _description = "Pile Integrity Line"

    parent_id = fields.Many2one(
        "pile.integrity.test",
        string="Parent Id",
        ondelete="cascade",
    )

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    pile_id = fields.Char(string="Pile ID")
    doc = fields.Date(string="DOC")
    pile_dia = fields.Integer(string="Dia (MM)", store=True)
    cut_off = fields.Float(string="Cut Off Length (M)")
    wave_speed = fields.Float("Wave Speed (m/s)")
    shaft_cross = fields.Char(string="Shaft Cross-Section & soil Changes")

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super().create(vals)


class PileIntegrityReport(models.AbstractModel):
    _name = 'report.pile_integrity.pile_integrity_report'
    _description = 'Pile Integrity Report'

    @api.model
    def _get_report_values(self, docids, data):
        data = self.env['pile.integrity.test'].sudo().browse(docids)

        def img_to_base64(filename):
            path = get_module_resource(
                'pile_integrity',
                'static',
                'src',
                'img',
                filename,
            )
            with open(path, 'rb') as f:
                return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

        show_doc_column = any(data.pile_integrity_test_table.mapped('doc'))

        return {
            'data': data,
            'show_doc_column': show_doc_column,
            'fig1a': img_to_base64('pile_integrity_Figure1a.png'),
            'fig1b': img_to_base64('pile_integrity_Figure1b.png'),
            'fig1c': img_to_base64('pile_integrity_Figure1c.png'),
            'fig1d': img_to_base64('pile_integrity_Figure1d.png'),
        }
