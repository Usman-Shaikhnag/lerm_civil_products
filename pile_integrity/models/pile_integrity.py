import base64
import qrcode
from base64 import b64decode
from datetime import datetime
from io import BytesIO

from odoo import api, fields, models
from odoo.modules.module import get_module_resource

try:
    from PyPDF2 import PdfFileMerger
except ImportError:
    PdfFileMerger = None



class PileIntegrity(models.Model):
    _name = "pile.integrity"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Pile Integrity")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

  


    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(PileIntegrity, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        record._generate_default_contents()
        record._populate_default_report_text()
        return record

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['pile.integrity'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

          

            if result.parameter.internal_id == '2ab20108-d96d-4acf-bda5-6b71762ae4bb':
                # result.result_char = round(self.average,2)
                result.calculated = True
               
                continue

           

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

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
        if self.eln_ref:
            date_testing = self.eln_ref.date_testing or self.eln_ref.start_date
            if date_testing:
                test_date = date_testing.strftime("%d %B, %Y")

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
        return self.env.ref('lerm_civil.pile_integrity_report_action').report_action(self.eln_ref)

    def action_generate_demo_data(self):
        self.ensure_one()

        demo_lines = [
            ("P-95-PL1", "03/06/2026", 1200, 13.48, 3869.00, "Fairly Uniform Pile Shaft."),
            ("P-95-PL2", "02/07/2026", 1200, 13.48, 4158.00, "Fairly Uniform Pile Shaft."),
            ("P-95-PL3", "05/07/2026", 1200, 13.48, 3664.00, "Fairly Uniform Pile Shaft."),
            ("P-95-PL4", "13/06/2026", 1200, 13.48, 4000.00, "Fairly Uniform Pile Shaft."),
            ("P-95-PL5", "19/06/2026", 1200, 13.48, 3664.00, "Fairly Uniform Pile Shaft."),
            ("P-95-PL6", "17/07/2026", 1200, 13.48, 3880.00, "Fairly Uniform Pile Shaft."),
        ]

        line_vals = []
        for pile_id, doc, dia, cut_off, wave_speed, shaft_cross in demo_lines:
            line_vals.append((0, 0, {
                "pile_id": pile_id,
                "doc": fields.Date.to_date(datetime.strptime(doc, "%d/%m/%Y")),
                "pile_dia": dia,
                "cut_off": cut_off,
                "wave_speed": wave_speed,
                "shaft_cross": shaft_cross,
            }))

        self.write({
            "pile_integrity_test_table": [(5, 0, 0)] + line_vals,
        })

    customer_name = fields.Char(string="Customer Name", compute="_compute_customer_details")
    customer_address = fields.Text(string="Customer Address", compute="_compute_customer_details")
    client = fields.Char(string="Client", compute="_compute_customer_details")
    principal_client = fields.Char(string="PMC")
    site_name_addr = fields.Text(string="Site Name & Address", compute="_compute_customer_details")

    @api.depends('srf_id', 'sample_id', 'srf_id.customer', 'srf_id.contact_person',
                 'eln_ref.srf_id', 'eln_ref.sample_id.srf_id')
    def _compute_customer_details(self):
        for record in self:
            srf = record.srf_id
            if not srf and record.eln_ref:
                srf = record.eln_ref.srf_id or record.eln_ref.sample_id.srf_id
            if not srf and record.sample_id:
                srf = record.sample_id.srf_id
            if srf:
                partner = srf.customer
                if partner:
                    customer_address = ", ".join(filter(None, [
                        partner.street,
                        partner.street2,
                        partner.city,
                        partner.state_id.name if partner.state_id else False,
                        partner.country_id.name if partner.country_id else False,
                        partner.zip,
                    ]))
                else:
                    customer_address = ""
                record.customer_name = partner.name if partner else ""
                record.customer_address = customer_address
                record.client = srf.client or ""
                record.site_name_addr = srf.site_address or ""
            else:
                record.customer_name = record.customer_name or ""
                record.customer_address = record.customer_address or ""
                record.client = record.client or ""
                record.site_name_addr = record.site_name_addr or ""

    introduction = fields.Text(
        string="Introduction",
        default="""M/s  has engaged us to conduct pile integrity testing (PIT) on cast in situ bored piles.
                            This report presents the results of pile integrity testing using the
                            Low Strain Pile Integrity Test method.
                            The objective of testing is to assess pile integrity for potential
                            defects such as necking, cross-sectional changes, honeycombing,
                            discontinuities and concrete quality variations.""",
    )

    equipment_details = fields.Text(
        string="Equipment Details",
        default="""Pile Integrity Tester (PIT) with accelerometer/transducer, instrumented hammer and data acquisition software.""",
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

    pile_type = fields.Char(
        string="Type of Pile",
        default="Cast In Situ Bored Pile",
    )
    pile_diameter = fields.Integer("Pile Diameter (mm)")
    pile_depth = fields.Char("Pile Depth From Test Level (m)")
    concrete_grade = fields.Char("Concrete Grade")

    content_ids = fields.One2many(
        "pile.integrity.contents",
        "parent_id",
        string="Contents",
    )
    image_ids = fields.One2many(
        "pile.integrity.image",
        "parent_id",
        string="Site Images",
    )

        # PILE INTEGRITY TEST
    pile_integrity_name = fields.Char(default="1) PILE INTEGRITY DESCRIPTIONS")

    code_ref = fields.Char(string="Code of Reference :",default="ASTM D5882-16")
    principle_details = fields.Text(string="Principle ",default="The test is based on wave propagation theory.(Wave propagation is any of the ways in which waves travel.) In the sonic test, the top of the pile is hit is heat with the plastic hammer and the reflected waves are recorded by a suitable computerized equipment. From the resulting signal, or reflectogram, one can determine the continuity of the pile.")
    instrument_image = fields.Binary(string="Instrument Image")
    
 
    # procedure_id = fields.One2many('lerm.procedure.master','parent_id')

    procedure = fields.Text(
        string="Procedure",
        default="1. Take 5 points on pile center, north, south, east, and west side\n"
                "2. A small metal/hard rubber hammer is used to\n"
                "3. The shock reflected is recorded through a transducer in a computer disk.\n"
                "4. More than one recording of signals is done until the repeatability of signals is the average of blows."
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
                "reliable information."
    )

                                                        
    interpretation_result = fields.Text(string="Interpretation Of Test Result",
                                                  default="""This indicates reduction in cross section at a particular area of the pile. If this happens, it means a reduction of the
                                                                        pile load carrying capacity & exposed reinforcements that could get corroded due to ground water and soil
                                                                        chemical attacks. This is indicated by “reduction in impedance” noting in the report. A correlation with the soil
                                                                        investigation report indicated if the reduction in
                                                                        Impedance due to soil strata change or due to change in the diameter of the pile. When a serious reduction is
                                                                        observed, the pile is termed as doubtful.""")

    instrument_description_image = fields.Binary(string="Instrument Description Image")


    pile_integrity_test_name = fields.Char(default=" PILE INTEGRITY TEST")
    pile_integrity_test_table = fields.One2many('pile.integrity.line','parent_id')
    temperature = fields.Float("Temperature °C")
    instrument = fields.Char("Instrument")



    pile_report_upload = fields.Many2many(
        'ir.attachment',
        'temprature_upload_rel1',
        'sample_id',
        'attachment_id',
        string='Report Upload',
        help='Attach multiple reports or PDFs to the sample',
    )



    test_result = fields.Text(string="TEST RESULT:",
     default="""The test results for the 08 Piles tested are attached above. In Annexure- II report is in Tabular form, the detailed
                            test graphs are attached in Annexure- III. Generally following conclusions can be derived from integrity tests which
                            are conducted on the pile shafts.<br></br>
                            1. Total 08 Numbers of piles were tested at site.<br></br>
                            2. This report has been prepared with generally accepted engineering practices and the results of integrity
                            testing as per ASTM- D5882. No other warranty, expressed or implied, is made the findings provided in this
                            report are based on the result of the individual pile tested and information made available to us.""")

    # name = fields.Char(string="Name", default="Default Pile Graph")
    # graph_image = fields.Binary("Graph Image", attachment=True)


    # @api.model
    # def generate_pile_graph(self):
    #     """
    #     Generate an accurate graph with dynamic spacing and proper annotations for each pile.
    #     """
    #     piles = [
    #         {"name": "C2A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.347,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.347, "freq": "566.0 Hz", "time": "15:27:42"},
    #         {"name": "C2B", "x": np.linspace(0, 7, 100), "y": np.sin(np.linspace(0, 7, 100)) * 0.463,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.463, "freq": "943.3 Hz", "time": "15:25:14"},
    #         {"name": "C5", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.351,
    #         "details": "L/D=7.5 (D=60cm)", "peak": 0.351, "freq": "490.3 Hz", "time": "16:09:40"},
    #         {"name": "C6A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.344,
    #         "details": "L/D=6.8 (D=60cm)", "peak": 0.344, "freq": "513.2 Hz", "time": "15:23:19"},
    #         {"name": "C6B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.377,
    #         "details": "L/D=6.9 (D=60cm)", "peak": 0.377, "freq": "515.9 Hz", "time": "15:23:19"},
    #         {"name": "C8", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.669,
    #         "details": "L/D=11 (D=60cm)", "peak": 0.669, "freq": "1010.7 Hz","time": "15:23:19"},
    #         {"name": "C9A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.540,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.540, "freq": "600.3 Hz","time": "15:23:19"},
    #         {"name": "C9B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.453,
    #         "details": "L/D=7.2 (D=60cm)", "peak": 0.453, "freq": "434.4 Hz","time": "15:23:19"},
    #         {"name": "C9D", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.488,
    #         "details": "L/D=7.2 (D=60cm)", "peak": 0.488, "freq": "604.0 Hz","time": "15:23:19"},
    #         {"name": "C10B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.415,
    #         "details": "L/D=7 (D=60cm)", "peak": 0.415, "freq": "1088.5 Hz","time": "15:23:19"},
    #         {"name": "C10C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.346,
    #         "details": "L/D=6.9 (D=60cm)", "peak": 0.346, "freq": "401.0 Hz","time": "15:23:19"},
    #         {"name": "C13A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.287,
    #         "details": "L/D=8.5 (D=60cm)", "peak": 0.287, "freq": "432.5 Hz","time": "15:23:19"},
    #         {"name": "C14A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.664,
    #         "details": "L/D=7 (D=60cm)", "peak": 0.664, "freq": "575.9 Hz","time": "15:23:19"},
    #         {"name": "C14B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.282,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.282, "freq": "467.2 Hz","time": "15:23:19"},
    #         {"name": "C14C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.774,
    #         "details": "L/D=7.2 (D=60cm)", "peak": 0.774, "freq": "589.6 Hz","time": "15:23:19"},
    #         {"name": "C17A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.617,
    #         "details": "L/D=8.5 (D=60cm)", "peak": 0.617, "freq": "467.2 Hz","time": "15:23:19"},
    #         {"name": "C18A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.378,
    #         "details": "L/D=6.8 (D=60cm)", "peak": 0.378, "freq": "448.2 Hz","time": "15:23:19"},
    #         {"name": "C20A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.454,
    #         "details": "L/D=9.7 (D=60cm)", "peak": 0.454, "freq": "385.4 Hz","time": "15:23:19"},
    #         {"name": "C20B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.720,
    #         "details": "L/D=7 (D=60cm)", "peak": 0.720, "freq": "739.2 Hz","time": "15:23:19"},
    #         {"name": "C20C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.528,
    #         "details": "L/D=9.7 (D=60cm)", "peak": 0.528, "freq": "811.9 Hz","time": "15:23:19"},
    #         {"name": "C21B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.330,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.330, "freq": "660.3 Hz","time": "15:23:19"},
    #         {"name": "C21C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.322,
    #         "details": "L/D=6.5 (D=60cm)", "peak": 0.322, "freq": "593.1 Hz","time": "15:23:19"},
    #         # Add more pile data here if needed
    #     ]

    #     # Dynamically adjust figure height based on the number of piles
    #     num_piles = len(piles)
    #     fig_height = num_piles * 1.30  # Adjust height scaling factor as needed

    #     # Set up the figure with subplots
    #     fig, axes = plt.subplots(num_piles, 1, figsize=(8, fig_height), sharex=True)
    #     fig.subplots_adjust(hspace=0.8)  # Increase space between plots

    #     for ax, pile in zip(axes, piles):
    #         # Plot the data
    #         ax.plot(pile["x"], pile["y"], label=pile["name"], color='black')

    #         # Get current y-limits
    #         y_min, y_max = ax.get_ylim()

    #         # Add dashed lines for the limits, within the y-axis limits
    #         ax.axhline(y=min(max(pile["peak"], y_min), y_max), color='red', linestyle='--', linewidth=0.8)
    #         ax.axhline(0, color='red', linestyle='--', linewidth=0.8)

    #         # Extend the blue line to the x limits
    #         ax.set_xlim(0, max(pile["x"]))  # Ensure the blue line spans the x-axis range

    #         # Annotate the graph
    #         ax.set_title(f"Pile: {pile['name']} - {pile['details']}", fontsize=10, weight='bold')
    #         ax.annotate(f"L/D={pile['details']}\n{pile['peak']} cm/s ({pile['freq']})",
    #                     xy=(max(pile["x"]) * 0.7, pile['peak'] - 0.1), xycoords='data',
    #                     fontsize=8, color='black', ha='center')
    #         ax.text(max(pile["x"]) * 0.05, -pile["peak"] * 0.9, f"{pile['time']}", fontsize=8, va='top', ha='left')

    #         # Axis labels and grid
    #         ax.set_ylabel("cm/s")
    #         ax.grid(True, linestyle='--', alpha=0.6)

    #     # Shared X-axis label
    #     axes[-1].set_xlabel("Time (s)")

    #     # Optimize layout
    #     plt.tight_layout()

    #     # Save the graph to a binary field
    #     buf = BytesIO()
    #     plt.savefig(buf, format='png', dpi=300)
    #     buf.seek(0)
    #     graph_image_base64 = base64.b64encode(buf.read()).decode()
    #     buf.close()
    #     plt.close()

    #     # Create a record with the graph
    #     self.write({
    #         'graph_image': graph_image_base64,
    #     })
    
    
  
    
    # def regenerate_graph(self):
    #     """
    #     Regenerate the pile graph manually.
    #     """
    #     self.generate_pile_graph()




# class ProcedureMaster(models.Model):
#     _name = "lerm.procedure.master"
#     _description = "Procedure Master"

#     parent_id = fields.Many2one('pile.integrity', string="Parent Id")

#     name = fields.Char(string="Procedure")
#     serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('serial_no'))
#                 vals['serial_no'] = max_serial_no + 1

#         return super(ProcedureMaster, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.serial_no = index + 1

class PileIntegrityLine(models.Model):
    _name = "pile.integrity.line"
    _description = "Pile Integrity Line"

    parent_id = fields.Many2one('pile.integrity', string="Parent Id")

    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    pile_id = fields.Char(string="Pile ID")
    doc = fields.Date(string="DOC")
    pile_dia = fields.Integer(string="Dia (MM)")
    cut_off  = fields.Float(string="Cut Off Length (M)")
    wave_speed = fields.Float(string="Wave Speed (m/s)")
    shaft_cross  = fields.Char(string="Shaft Cross-Section & soil Changes")

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PileIntegrityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class PileIntegrityContents(models.Model):
    _name = "pile.integrity.contents"
    _description = "Pile Integrity Contents"

    parent_id = fields.Many2one(
        "pile.integrity",
        string="Parent Id",
        ondelete="cascade",
    )
    seq = fields.Text(string="Sequence")
    name = fields.Text(string="Name")
    page_no = fields.Text(string="Page No")


class PileIntegrityImage(models.Model):
    _name = "pile.integrity.image"
    _description = "Pile Integrity Images"

    parent_id = fields.Many2one(
        "pile.integrity",
        string="Report",
        ondelete="cascade",
    )

    name = fields.Char()
    image = fields.Binary(attachment=True)


class PileIntegrityReport(models.AbstractModel):
    _name = 'report.pile_integrity.pile_integrity_report'
    _description = 'Steel TMT Bar'
    
    @api.model
    def _get_report_values(self, docids, data):
        data = data or {}
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        context = data.get('context') or {}

        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['sample'])])
        elif context.get('active_id'):
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', context['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)

        if not eln:
            eln = self.env['lerm.eln'].sudo().search([('id', 'in', docids)], limit=1)

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(eln.kes_no)
        qr.make(fit=True)
        qr_image = qr.make_image()

        # Convert the QR code image to base64 string
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        model_id = eln.model_id
        general_data = self.env['pile.integrity'].sudo().browse(model_id) if model_id else self.env['pile.integrity']
        if not general_data.exists():
            general_data = self.env['pile.integrity'].sudo().search(
                [('eln_ref', '=', eln.id)], limit=1
            )

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

        show_doc_column = any(general_data.pile_integrity_test_table.mapped('doc'))

        return {
            'eln': eln,
            'o': eln,
            'data': general_data,
            'qrcode': qr_image_base64,
            'stamp': inreport_value,
            'nabl': nabl,
            'fromEln': True,
            'show_doc_column': show_doc_column,
            'fig1a': img_to_base64('pile_integrity_Figure1a.png'),
            'fig1b': img_to_base64('pile_integrity_Figure1b.png'),
            'fig1c': img_to_base64('pile_integrity_Figure1c.png'),
            'fig1d': img_to_base64('pile_integrity_Figure1d.png'),
        }


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, docids, data=None):
        content, content_type = super()._render_qweb_pdf(report_ref, docids, data=data)
        if report_ref == 'pile_integrity.pile_integrity_report':
            content = self._append_pile_report_uploads(docids, content, data=data)
        return content, content_type

    def _append_pile_report_uploads(self, docids, content, data=None):
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
            pile = self.env['pile.integrity'].sudo().search(
                [('eln_ref', '=', eln_id)], limit=1
            )
            if pile:
                uploads |= pile.pile_report_upload
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
