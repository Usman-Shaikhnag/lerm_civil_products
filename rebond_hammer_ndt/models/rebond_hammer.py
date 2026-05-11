from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class ReboundHammer(models.Model):
    _name = "rebound.hammer.ndt"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Rebound Hammer")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
    rebond_hammer_visible = fields.Boolean("Rebound Hammer Visible",compute="_compute_visible")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    temperature = fields.Float("Temperature °C")
    child_lines = fields.One2many('rebound.hammer.ndt.line','parent_id',string="Parameter")
    average_mpa = fields.Float(string="Average Mpa",compute="_compute_average",store=True)
    minimum_mpa = fields.Float(string="Minimum Mpa",compute="_compute_average",store=True)
    maximum_mpa = fields.Float(string="Maximum Mpa",compute="_compute_average",store=True)
    structure = fields.Char("Structure")
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    

    abstract = fields.Text(string="Abstract",
                                                  default="The estimation of mechanical properties of concrete can be carried out by several methods; destructive and non-destructive. In this context, the crushing of the samples is the usual destructive test to determine the concrete strength. The rebound hammer test and the ultrasonic device are used in the field of non-destructive tests to determine respectively the compression strength and the ultrasonic pulse velocity (UPV) in the concrete. In this work, eight concrete compositions were used to prepare cylindrical specimens (16 cm x 32 cm) by varying the water/ cement ratio and the cement dosage. An experimental study was conducted to determine the compressive strength of concrete by destructive (compression) and non-destructive (rebound hammer) tests at different ages (7, 14 and 28 days). In addition, the influence of several factors on the modulus of elasticity determined by pulse velocity test was investigated. These factors mainly included the age of concrete and the water/ cement ratio. The results showed that the difference between the resistance values obtained by destructive and non-destructive methods decreases with increasing age of concrete. The dynamic modulus of elasticity increases with the curing time of the concrete until the age of three months. In addition, a simplified expression has been proposed to estimate the rebound number from the value of the dynamic modulus of elasticity determined by pulse velocity test.")
     

    keywords = fields.Text(string="Keywords",
                                                  default="""Rebound Hammer test, Compression test, Pulse velocity test, Destructive test, Non- destructive test, Dynamic modulus of elasticity""")

    introduction = fields.Text(string="Introduction",
                                                  default="""It is often necessary to test concrete structures after the concrete has hardened to determine whether the structure is suitable for its designed use. Ideally, such testing should be done without damaging the concrete. The tests available for testing concrete range from completely non-destructive tests, where there is no damage to the concrete, through those where the concrete surface is slightly damaged, to partially destructive tests, such as core tests and pull-out and pull-off tests, where the surface has to be repaired after the test. The range of properties that can be assessed using non-destructive tests and partially destructive tests is quite large and includes such fundamental parameters as density, elastic modulus and strength as well as surface hardness, surface absorption, reinforcement location, size and distance from the surface.
                                                                        The crushing of the specimens is the usual destructive test to assess the strength of concrete. Non- destructive methods like rebound hammer test and ultrasonic test do not damage buildings and allow to have an inventory of structures and conditions. Non- destructive tests are widely applied to study mechanical properties and integrity of concrete structures. They are simple to use and often economically advantageous. They are suitable for taking measurements on site and taking continuous measurements.
                                                                        These non-destructive methods are usually associated with each other to improve diagnosis and reduce the number of tests .
                                                                        Ultrasound measurements provide a simple non- destructive and inexpensive method to evaluate the elastic modulus of concrete. The formulae proposed by different standards to estimate the dynamic modulus of elasticity from the resistance are very approximate. The dynamic modulus of elasticity is strongly influenced by the aggregates, it cannot be determined accurately based on the strength, which depends mainly on the cement paste and the particle size. For temperatures between - 10° C and + 30° C, there is an increase in the dynamic modulus of elasticity of the concrete with temperature.
                                                                        This paper presents measurements of compressive strength and dynamic modulus of elasticity determined from destructive and non-destructive tests. The results obtained from non-destructive tests were compared with destructive test results. The influences of the age of the concrete, its strength and water/cement ratio on the resistance determined by rebound hammer test and compression test were studied. A simplified expression has been proposed to estimate the rebound number from the value of dynamic modulus of elasticity determined by pulse velocity test.""")
    

    objective = fields.Text(string="Objective",
                                                  default="""The rebound hammer method could be used for:
                                                                        a) Assessing the likely compressive strength of concrete with the help of suitable correlations between rebound index and compressive strength,
                                                                        b) Assessing the uniformity of concrete, 
                                                                        c) Assessing the quality of the concrete in relation to standard requirements, and 
                                                                        d) Assessing the quality of one element of concrete in relation to another.""")

    principle = fields.Text(string="Principle",
                                                  default="""When the plunger of rebound hammer is pressed against the surface of the concrete, the spring- controlled mass rebounds and the extent of such rebound depends upon the surface hardness of concrete. The surface hardness and therefore the rebound is taken to be related to the compressive strength of the concrete. The rebound is read off along a graduated scale and is designated as the rebound number or rebound index.""")


    apparatus = fields.Text(string="Apparatus Required",
                                                  default="""It consists of a spring controlled mass that slides on a plunger within a tubular housing. The impact energy required for rebound hammers for different applications is given in Table""")



    site_image = fields.Binary(string="Site Photograph")


    procedure = fields.Text(string="Procedure",
                                                  default=""" 
                                                                    4.1 Checking of Apparatus: It is necessary that the rebound hammer is checked against the testing anvil before commencement of a test to ensure reliable results. The testing anvil should be of steel having Brinell’s hardness of about 5000 N/mms. The supplier/manufacturer of the rebound hammer should indicate the range of readings on the anvil suitable for different types of rebound hammers.
                                                                    4.2 Procedure of obtaining Correlation between Compressive Strength of Concrete and Rebound Number: The most satisfactory way of establishing a correlation between compressive strength of concrete and its rebound number is to measure both the properties simultaneously on concrete cubes. The concrete cube specimens are held in a compression testing machine under a fixed load, measurements of rebound number taken and then the compressive strength determined as per IS: 516- 1959. The fixed load required is of the order of 7 N/mm2 when the impact energy of the hammer is about 2.2 Nm. The load should be increased for calibrating rebound hammers of greater impact energy and decreased for calibrating rebound hammers of lesser impact energy. The test specimens should be as large a mass as possible in order to minimize the size effect on the test result of a full scale structure. 150 mm cube specimens are preferred for calibrating rebound hammers of lower impact energy (2.2 Nm), whereas for rebound hammers of higher impact energy, for example 30 Nm, the test cubes should not be smaller than 300 mm. If the specimens are wet cured, they should be removed from wet storage and kept in the laboratory atmosphere for about 24 hours before testing. To obtain a correlation between rebound numbers and strength of wet cured and wet tested cubes, it is necessary to establish a correlation between the strength of wet tested cubes and the strength of dry tested cubes on which rebound readings are taken. A direct correlation between rebound numbers on wet cubes and the strength of wet cubes is not recommended. Only the vertical faces of the cube as cast should be tested. At least nine readings should be taken on each of the two vertical faces accessible in the compression testing machine when using the rebound hammers. The points of impact on the specimen must not be nearer an edge than 20 mm and should be not less than 20 mm from each other. The same points must not be impacted more than once. """)


    test_procedure = fields.Text(string="Test Procedure",
                                                  default="""For testing, smooth, clean and dry surface is to be selected. If loosely adhering scale is present, this should be rubbed of with a grinding wheel or stone. Rough surfaces resulting from incomplete compaction, loss of grout, spelled or tooled surfaces do not give reliable results and should be avoided. 
                                                                        1. The point of impact should be at least 20 mm away from any edge or shape discontinuity. 
                                                                        2. For taking a measurement, the rebound hammer should be held at right angles to the surface of the concrete member. 
                                                                        3. The test can thus be conducted horizontally on vertical surfaces or vertically upwards or downwards on horizontal surfaces. If the situation demands, the rebound hammer can be held at intermediate angles also, but in each case, the rebound number will be different for the same concrete. 
                                                                        4. Rebound hammer test is conducted around all the points of observation on all accessible faces of the structural element. Concrete surfaces are thoroughly cleaned before taking any measurement. Around each point of observation, six readings of rebound indices are taken 2nd average of these readings after deleting outliers as per IS:8900-1978 becomes the rebound index for the point of observation. """)

    Influence_condition = fields.Text(string="Influence of Test Conditions",
                                                  default="""The rebound numbers are influenced by a number of factors like types of cement and aggregate, surface condition and moisture content, age of concrete and extent of carbonation of concrete.""")

    Influence_cement = fields.Text(string="Influence of Type of Cement",
                                                  default="""Concretes made with high alumina cement can give strengths 100 percent higher than that with ordinary Portland cement. Concretes made with super sulphated cement can give 50 percent lower strength than that with ordinary Portland cement.""")

    Influence_aggregate = fields.Text(string=" Influence of Type of Aggregate",
                                                  default="""Different types of aggregate used in concrete give different correlations between compressive strength and rebound numbers. Normal aggregates such as gravels and crushed rock aggregates give similar correlations, but concrete made with lightweight aggregates require special calibration. """)



    Influence_concrete = fields.Text(string="Influence of Surface Condition and Moisture Content of Concrete",
                                                  default="""The rebound hammer method is suitable only for close texture concrete. Open texture concrete typical of masonry blocks, honeycombed concrete or no-fines concrete are unsuitable for this test. All correlations assume full compaction, as the strength of partially compacted concrete bears no unique relationship to the rebound numbers. Trowel led and floated surfaces are harder than molded surfaces, and tend to overestimate the strength of concrete. A wet surface will give rise to underestimation of the strength of concrete calibrated under dry conditions. In structural concrete, this can be about 20 percent lower than in an equivalent dry concrete.""")



    Influence_curing_concrete = fields.Text(string="Influence of Curing and Age of Concrete",
                                                  default="""The relationship between hardness and strength varies as a function of time. Variations in initial rate of hardening, subsequent curing and conditions of exposure also influence the relationship. Separate calibration curves are required for different curing regimes but the effect of age can generally be ignored for concrete between 3 days and 3 months old. """)


    Influence_surface = fields.Text(string="Influence of Carbonation of Concrete Surface",
                                                  default="""The influence of carbonation of concrete surface on the rebound number is very significant. Carbonated concrete gives an overestimate of strength which in extreme cases can be up to 50 percent. It is possible to establish correction factors by removing the carbonated layer and testing the concrete with the rebound hammer on the uncarbonated concrete. """)



    interpretation_result = fields.Text(string="Interpretation of Results",
                                                  default="""1. The rebound hammer method provides a convenient and rapid indication of the compressive strength of concrete by means of establishing a suitable correlation between the rebound index and the compressive strength of concrete. The procedure of obtaining such correlation is given in 4.1
                                                                        2. It is also pointed out that rebound indices are indicative of compressive strength of concrete to a limited depth from the surface. If the concrete in a particular member has internal micro-cracking, flaws or heterogeneity across the cross-section, rebound hammer indices will not indicate the same. 
                                                                        3. As such, the estimation of strength of concrete by rebound hammer method cannot be held to be very accurate and probable accuracy of prediction of concrete strength in a structure is ±25 percent. 
                                                                        4. If the relationship between rebound index and compressive strength can be checked by tests on core samples obtained from the structure or standard specimens made with the same concrete materials and mix proportion, then the accuracy of results and confidence thereon are greatly increased.""")

    site_image1 = fields.Binary(string="Site Photograph")

    

    notes_id = fields.One2many('rebound.hammer.ndt.notes', 'parent_id', string="Notes")



    @api.model
    def default_get(self, fields):
        res = super(ReboundHammer, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in fullor partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'ampling is not done by us unless mentioned otherwide.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'without a QR Code and hologram this report is considered invalid.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
            }),
             (0, 0, {
                'sr_no': 'f',
                'notes': 'Alldisputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample willbe destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


   

    @api.depends('child_lines.mpa')
    def _compute_average(self):
        for record in self:
            mpa_values = record.child_lines.mapped('mpa')
            record.average_mpa = sum(mpa_values) / len(mpa_values) if len(mpa_values) > 0 else 0.0
            minimum_mpa = round(min(mpa_values, default=0.0),2)
            record.minimum_mpa = minimum_mpa
            maximum_mpa = round(max(mpa_values, default=0.0),2)
            record.maximum_mpa = maximum_mpa




    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

        

            # if result.parameter.internal_id == '124578874gtre-372f-4775-9bcb-e999987hy':
            #     # result.result_char = self.avg_specific_gravity
            #     result.calculated = True

            if result.parameter.internal_id == 'fe02d1e0-c893-4991-a463-650b73264c1a':
                result.result_char = round(self.average_mpa,2)
                result.calculated = True
                # if self.avg_compaction_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

           

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }



    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(ReboundHammer, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        current_user = self.env.user

        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # Check if user is in Lerm Admin group
            if (
                current_user.has_group('lerm_civil.kes_admin_access_group')
                or current_user.has_group('lerm_civil.lerm_sample_verification')
                or current_user.has_group('lerm_civil.lerm_sample_approval')
            ):
                # Admin sees all parameters
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # Other users only see parameters assigned to them
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]

    def get_all_fields(self):
        record = self.env['rebound.hammer.ndt'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    # added
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


   

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.rebond_hammer_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == 'fe02d1e0-c893-4991-a463-650b73264c1a':
                    record.rebond_hammer_visible = True

                


class CarbonationnLine(models.Model):
    _name = "rebound.hammer.ndt.line"
    parent_id = fields.Many2one('rebound.hammer.ndt',string="Parent Id")
    element = fields.Char(string="Member / Element Type")
    location = fields.Char(string="Location Of Member")
    f1 = fields.Integer(string="1")
    f2 = fields.Integer(string="2")
    f3 = fields.Integer(string="3")
    f4 = fields.Integer(string="4")
    f5 = fields.Integer(string="5")
    f6 = fields.Integer(string="6")
    f7 = fields.Integer(string="7")
    f8 = fields.Integer(string="8")
    f9 = fields.Integer(string="9")
    # f10 = fields.Integer(string="10")
    avg = fields.Float(string="Average" ,compute="_compute_average")
    mpa = fields.Float(string="Mpa")
    direction = fields.Selection([
        ('horizontal', 'Horizontal'),
        ('vertical_up', 'Vertical Up'), 
        ('vertical_down', 'Vertical Down')], string='Direction')
    





    @api.depends('f1', 'f2', 'f3', 'f4', 'f5', 'f6','f7','f8','f9')
    def _compute_average(self):
        for record in self:
            values = [record.f1, record.f2, record.f3, record.f4, record.f5, record.f6,record.f7,record.f8,record.f9]

            sorted_array = sorted(values)
            midpoint = len(sorted_array) // 2
            if len(sorted_array) % 2 == 0:
                median = (sorted_array[midpoint - 1] + sorted_array[midpoint]) / 2.0
            else:
                median = sorted_array[midpoint]

            first_quartile = sorted_array[:midpoint]
            third_quartile = sorted_array[midpoint:]
            midpoint = len(first_quartile) // 2
            if len(first_quartile) % 2 == 0:
                median_first = (first_quartile[midpoint - 1] + first_quartile[midpoint]) / 2.0
            else:
                median_first = first_quartile[midpoint]
            midpoint = len(third_quartile) // 2
            if len(third_quartile) % 2 == 0:
                median_third = (third_quartile[midpoint - 1] + third_quartile[midpoint]) / 2.0
            else:
                median_third = third_quartile[midpoint]
            iqr = median_third - median_first
            lower_bound = median_first - 1.5 * iqr
            upper_bound = median_third + 1.5 * iqr

            filtered_array = [x for x in values if lower_bound <= x <= upper_bound]

            record.avg = sum(filtered_array) / len(filtered_array)
                


class ReboundHammerNotes(models.Model):
    _name = "rebound.hammer.ndt.notes"

    parent_id = fields.Many2one('rebound.hammer.ndt',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")