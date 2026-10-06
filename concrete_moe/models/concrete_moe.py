from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from datetime import datetime , timedelta


# Internal Id of the "Modulus of Elasticity of Concrete" parameter master record.
# Fill this in from Settings > Lerm > Parameter Master before using the module.
MOE_PARAMETER_INTERNAL_ID = '0d84a152-37e6-4423-85a9-df33ef387f44'

# Internal Id of the "Poisson's Ratio" parameter master record. This is a second,
# independent parameter that shares the same form: its result is the average
# Poisson's ratio and it is judged against its own lab limits and grade table.
# Fill this in from Settings > Lerm > Parameter Master before using the module.
POISSON_PARAMETER_INTERNAL_ID = '6ba2bb5e-dfd0-4e97-98a5-b2f708e0231f'

# Reference stress divisors (28 day cube compressive strength)
BASIC_STRESS_DIVISOR = 9.0
UPPER_STRESS_DIVISOR = 3.0

# Static modulus of elasticity factors (second table)
CIRCLE_AREA_DIVISOR = 4.0      # V = (pi / 4) * D^2 * L
MM3_TO_M3 = 1e-9               # 1 m3 = 1e9 mm3
MICRO = 1e-6                   # strain entered as micro strain (x10^-6)
GPA_DIVISOR = 1000.0           # Ec (GPa) = Ec (MPa) / 1000

class MechanicalConcretemoe(models.Model):
    _name = "mechanical.concrete.moe"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name", default="Concrete MOE")
    compressive_visible = fields.Boolean("concrete moe",compute="_compute_visible")
    poisson_visible = fields.Boolean("poisson's ratio",compute="_compute_visible")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    notes_id = fields.One2many('mechanical.concrete.moe.notes', 'parent_id', string="Notes",ondelete='cascade')

    @api.model
    def default_get(self, fields):
        res = super(MechanicalConcretemoe, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The Test Report(s) is/are valid only to the sample submitted to the laboratory.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sample(s) was/were not drawn by laboratory.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'This Report may not be reproduced in except full/ part without the permission of the Lab Head of the Laboratory.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': '# - Information provided by the customer.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    child_lines = fields.One2many('mechanical.concrete.moe.line','parent_id',string="Parameter")
    # Same specimen rows, exposed under their own relation so that the second
    # table can be rendered as its own table (a one2many may only appear once
    # per form view).
    specimen_lines = fields.One2many('mechanical.concrete.moe.line','parent_id',string="Specimen")

    # Third table (optional Poisson's ratio) has its own lines: the strains it
    # needs are transverse ones that the second table does not hold.
    poisson_lines = fields.One2many('mechanical.concrete.moe.poisson.line','parent_id',string="Poisson's Ratio",copy=False)

    # Cube specimens of the first table. Any number of lines can be entered, the
    # average Fc and both reference stresses follow from what is filled in.
    cube_lines = fields.One2many('mechanical.concrete.moe.cube.line','parent_id',string="Cube Specimen",copy=False)

    # Average Fc. This is the value the first parameter reports to the ELN result,
    # so the field name is kept as average_strength.
    average_strength = fields.Float(string="Average Fc in N/mm2", compute="_compute_average_strength",store=True,digits=(12,2))

    basic_stress = fields.Float(string="Basic Stress (Fc/9) in MPa", compute="_compute_reference_stress",store=True,digits=(12,2))
    upper_stress = fields.Float(string="Upper Stress (Fc/3) in MPa", compute="_compute_reference_stress",store=True,digits=(12,2))

    average_ec_mpa = fields.Float(string="Average Ec (MPa)", compute="_compute_average_ec", digits=(12,2))
    average_ec_gpa = fields.Float(string="Average Ec (GPa)", compute="_compute_average_ec", digits=(12,2))

    average_poisson_ratio = fields.Float(string="Average Poisson's Ratio", compute="_compute_average_poisson_ratio", digits=(12,2))

    nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),

    ], string='NABL', default='fail',compute="_compute_nabl")

    confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--'),
    ], string='Confirmity', default='fail',compute="_compute_confirmity")

    poisson_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),

    ], string="Poisson's NABL", default='fail',compute="_compute_poisson_nabl")

    poisson_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--'),
    ], string="Poisson's Confirmity", default='fail',compute="_compute_poisson_confirmity")


    def _get_parameter(self):
        """Parameter master record holding the lab limits, mu value and the grade table."""
        return self.env['lerm.parameter.master'].sudo().search(
            [('internal_id','=','%s' % MOE_PARAMETER_INTERNAL_ID)], limit=1)


    def _get_requirement(self):
        """Return the (parameter master, grade row) pair for this record.

        Both are empty recordsets when the parameter master is not configured or
        when it holds no row for the grade of the current test.
        """
        line = self._get_parameter()
        if not line or not self.grade:
            return line, self.env['lerm.parameter.master.table']
        material = line.parameter_table.filtered(
            lambda row: row.grade == self.grade
        )[:1]
        return line, material


    def _get_poisson_parameter(self):
        """Parameter master record of the second (Poisson's Ratio) parameter.

        It is a separate record from the MOE one, with its own lab limits, mu value
        and grade table. limit=1 keeps this a singleton even if the id was copied.
        """
        return self.env['lerm.parameter.master'].sudo().search(
            [('internal_id','=','%s' % POISSON_PARAMETER_INTERNAL_ID)], limit=1)


    def _get_poisson_requirement(self):
        """Return the (Poisson parameter master, grade row) pair for this record.

        Mirrors _get_requirement: both are empty recordsets when the parameter
        master is not configured or holds no row for the current grade.
        """
        line = self._get_poisson_parameter()
        if not line or not self.grade:
            return line, self.env['lerm.parameter.master.table']
        material = line.parameter_table.filtered(
            lambda row: row.grade == self.grade
        )[:1]
        return line, material


    @api.depends('cube_lines', 'cube_lines.compressive_strength')
    def _compute_average_strength(self):
        """Average Fc over the cube specimens that were actually filled in.

        Adding, editing or removing a cube line retriggers this, so the average
        and both reference stresses always follow the entered values.
        """
        for record in self:
            strengths = [
                line.compressive_strength
                for line in record.cube_lines
                if line.compressive_strength
            ]
            if strengths:
                # Only the final result is rounded, the average itself is not.
                average = sum(strengths) / len(strengths)
            else:
                average = 0.0
            record.average_strength = round(average, 2)


    @api.depends('average_strength')
    def _compute_reference_stress(self):
        """Basic stress = Fc/9 and Upper stress = Fc/3, both readonly."""
        for record in self:
            record.basic_stress = round(record.average_strength / BASIC_STRESS_DIVISOR, 2)
            record.upper_stress = round(record.average_strength / UPPER_STRESS_DIVISOR, 2)


    @api.depends('child_lines.ec_mpa')
    def _compute_average_ec(self):
        """Average modulus of elasticity of the three specimens."""
        for record in self:
            moduli = [line.ec_mpa for line in record.child_lines if line.ec_mpa]
            if moduli:
                average = sum(moduli) / len(moduli)
            else:
                average = 0.0
            record.average_ec_mpa = round(average, 2)
            record.average_ec_gpa = round(average / GPA_DIVISOR, 2)


    @api.depends(
        'poisson_lines',
        'poisson_lines.poisson_ratio',
        'poisson_lines.long_strain_b',
        'poisson_lines.long_strain_a',
        'poisson_lines.trans_strain_b',
        'poisson_lines.trans_strain_a',
    )
    def _compute_average_poisson_ratio(self):
        """Average of the Poisson's ratios that could be calculated.

        Specimens left blank (ratio 0 because no strain was entered) are skipped,
        exactly like the Ec average above.
        """
        for record in self:
            ratios = [line.poisson_ratio for line in record.poisson_lines if line.poisson_ratio]
            if ratios:
                average = sum(ratios) / len(ratios)
            else:
                average = 0.0
            record.average_poisson_ratio = round(average, 2)


    @api.depends('average_strength','eln_ref','grade')
    def _compute_nabl(self):

        for record in self:
            record.nabl = 'fail'
            line = record._get_parameter()
            if not line:
                continue

            # No cube strength entered (or an entered value of zero) cannot pass.
            if not record.average_strength:
                continue

            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value

            lower = record.average_strength - record.average_strength * mu_value
            upper = record.average_strength + record.average_strength * mu_value
            if lower >= lab_min and upper <= lab_max:
                record.nabl = 'pass'
            else:
                record.nabl = 'fail'


    @api.depends('average_strength', 'eln_ref', 'grade')
    def _compute_confirmity(self):
        # Conformity is judged on the 28 day cube compressive strength, i.e. the
        # Average Fc over the entered cube specimens, against the grade wise
        # requirement of the MOE parameter master.  The Basic stress (Fc/9), the
        # Upper stress (Fc/3) and the Ec of the specimen table are results of this
        # stage, not acceptance values for it.
        for record in self:
            # Default to 'fail' and only upgrade to 'pass' once the test value and
            # every requirement are available and satisfied.
            record.confirmity = 'fail'

            line, material = record._get_requirement()
            if not material:
                continue

            # The parameter master explicitly marks this grade as having no
            # requirement defined.
            if material.permissable_limit == '--' or not material.permissable_limit:
                record.confirmity = '--'
                continue

            req_min = material.req_min
            req_max = material.req_max
            # No requirement configured on the grade row.
            if not req_min and not req_max:
                continue

            # No cube strength entered (or an entered value of zero) cannot conform.
            if not record.average_strength:
                continue

            mu_value = line.mu_value
            lower = record.average_strength - record.average_strength * mu_value
            upper = record.average_strength + record.average_strength * mu_value

            if lower >= req_min and upper <= req_max:
                record.confirmity = 'pass'


    @api.depends('average_poisson_ratio', 'eln_ref', 'grade')
    def _compute_poisson_nabl(self):
        """NABL of the second parameter, judged on the average Poisson's ratio.

        Independent of the cube strength NABL above: the limits and the mu value
        come from the Poisson's Ratio parameter master, not the MOE one.
        """
        for record in self:
            record.poisson_nabl = 'fail'
            line = record._get_poisson_parameter()
            if not line:
                continue

            # No ratio could be calculated (all specimens left blank).
            if not record.average_poisson_ratio:
                continue

            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value

            ratio = record.average_poisson_ratio
            lower = ratio - ratio * mu_value
            upper = ratio + ratio * mu_value
            if lower >= lab_min and upper <= lab_max:
                record.poisson_nabl = 'pass'
            else:
                record.poisson_nabl = 'fail'


    @api.depends('average_poisson_ratio', 'eln_ref', 'grade')
    def _compute_poisson_confirmity(self):
        """Conformity of the second parameter against its own grade requirement.

        No age scaling is applied here: the age factors of the cube strength table
        do not apply to Poisson's ratio.
        """
        for record in self:
            record.poisson_confirmity = 'fail'

            line, material = record._get_poisson_requirement()
            if not material:
                continue

            if material.permissable_limit == '--' or not material.permissable_limit:
                record.poisson_confirmity = '--'
                continue

            req_min = material.req_min
            req_max = material.req_max
            if not req_min and not req_max:
                continue

            if not record.average_poisson_ratio:
                continue

            mu_value = line.mu_value
            ratio = record.average_poisson_ratio
            lower = ratio - ratio * mu_value
            upper = ratio + ratio * mu_value

            if lower >= req_min and upper <= req_max:
                record.poisson_confirmity = 'pass'


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            if result.parameter.internal_id == MOE_PARAMETER_INTERNAL_ID:
                result.result_char = round(self.average_strength,2)
                result.calculated = True
                continue

            # Second parameter: the average Poisson's ratio, against its own limits.
            if result.parameter.internal_id == POISSON_PARAMETER_INTERNAL_ID:
                result.result_char = round(self.average_poisson_ratio,2)
                result.calculated = True
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
        record = super(MechanicalConcretemoe, self).create(vals)
        record.eln_ref.write({'model_id':record.id})
        return record


    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            record.sample_parameters = record.eln_ref.parameters_result.parameter.ids


    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):

        for record in self:
            record.compressive_visible = False
            record.poisson_visible = False

            for sample in record.sample_parameters:
                if sample.internal_id == MOE_PARAMETER_INTERNAL_ID:
                    record.compressive_visible = True

                if sample.internal_id == POISSON_PARAMETER_INTERNAL_ID:
                    record.poisson_visible = True


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    def get_all_fields(self):
        record = self.env['mechanical.concrete.moe'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class MechanicalConcreteMoeCubeLine(models.Model):
    """One 28 day cube specimen of the first table.

    The cube number is the line's own position in the parent's sequence, so it is
    always 1, 2, 3 ... and renumbers by itself when a line is removed. Only the
    compressive strength is ever typed.
    """
    _name = "mechanical.concrete.moe.cube.line"
    _description = "Concrete MOE Cube Specimen Line"
    _order = "id"

    parent_id = fields.Many2one('mechanical.concrete.moe',string="Parent Id",ondelete='cascade',index=True)

    specimen = fields.Integer(string="Cube Specimen",compute="_compute_specimen",store=True,readonly=True)

    compressive_strength = fields.Float(string="Compressive Strength (MPa)",digits=(12,2))

    # The remaining three columns of the first table are calculated on the parent
    # (Average Fc, then Basic stress = Fc/9 and Upper stress = Fc/3). They are
    # exposed here as related fields purely so that the whole first table can be
    # rendered as a single one2many tree: a column inside an embedded tree is
    # always resolved against the line model, so the values must exist here.
    # No calculation is duplicated here, this only mirrors the parent's fields.
    average_fc = fields.Float(string="Average Fc (MPa)",related='parent_id.average_strength',readonly=True,digits=(12,2))
    basic_stress_fc = fields.Float(string="Basic Stress, σb = Fc/9 (MPa)",related='parent_id.basic_stress',readonly=True,digits=(12,2))
    upper_stress_fc = fields.Float(string="Upper Stress, σa = Fc/3 (MPa)",related='parent_id.upper_stress',readonly=True,digits=(12,2))

    # Display-only mirrors of the parent's calculated values. A column inside the
    # cube_lines tree is always resolved against this line model, so the parent's
    # average_strength / basic_stress cannot be used directly there. These are
    # plain related fields: no calculation is duplicated or recalculated here.
    average_fc_display = fields.Float(string="Average Fc (MPa)",related='parent_id.average_strength',readonly=True,digits=(12,2))
    basic_stress_display = fields.Float(string="Basic Stress, σb = Fc/9 (MPa)",related='parent_id.basic_stress',readonly=True,digits=(12,2))


    @api.depends('parent_id', 'parent_id.cube_lines')
    def _compute_specimen(self):
        """Cube Specimen number = position within the parent (1, 2, 3 ...).

        Taken from the one2many sequence, so a deleted line shifts the remaining
        ones back into 1, 2, 3 ... order. The lines are never sorted on `id`:
        unsaved lines coming from an onchange carry a NewId, which is not
        orderable.
        """
        for record in self:
            sibling_ids = record.parent_id.cube_lines.ids
            record.specimen = (
                sibling_ids.index(record.id) + 1 if record.id in sibling_ids else 0
            )


class MechanicalConcreteMoeLine(models.Model):
    _name = "mechanical.concrete.moe.line"

    parent_id = fields.Many2one('mechanical.concrete.moe',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
    length = fields.Float(string="Length (mm)")
    width = fields.Float(string="Width (mm)")
    area = fields.Float(string="Area (mm²)",compute="_compute_area" ,digits=(12,2))
    id_mark = fields.Char(string="ID Mark/Location")
    wt_sample = fields.Float(string="Weight of Sample in kgs",digits=(16,3))
    crushing_load = fields.Float(string="Crushing Load in kN")
    compressive_strength = fields.Float(string="Compressive Strength N/mm²",compute="_compute_compressive_strength" ,digits=(12,2))

    # Modulus of Elasticity fields (second table)
    # Specimen number is the line's own position in the parent's sequence, so it
    # is always 1, 2, 3 ... and renumbers by itself when a line is removed.
    specimen = fields.Integer(string="Specimen",compute="_compute_specimen",store=True,readonly=True)
    diameter = fields.Float(string="Diameter D (mm)", digits=(12,3))
    specimen_length = fields.Float(string="Length L (mm)", digits=(12,3))
    mass = fields.Float(string="Mass (kg)", digits=(16,3))
    strain_b = fields.Float(string="εb (×10⁻⁶)", digits=(12,3))
    strain_a = fields.Float(string="εa (×10⁻⁶)", digits=(12,3))

    l_d_ratio = fields.Float(string="L/D", compute="_compute_moe_dimensions", digits=(12,3), store=True)
    density = fields.Float(string="Density (kg/m³)", compute="_compute_moe_dimensions", digits=(12,3), store=True)
    # Neither stress is entered per specimen: they are the reference stresses of
    # the first table (Fc/9 and Fc/3), identical for every row, and both feed
    # the Ec calculation below.
    stress_b = fields.Float(string="Stress σb (MPa)", compute="_compute_reference_stresses", digits=(12,3))
    stress_a = fields.Float(string="Stress σa (MPa)", compute="_compute_reference_stresses", digits=(12,3))
    ec_mpa = fields.Float(string="Ec (MPa)", compute="_compute_moe_modulus", digits=(12,2), store=True)
    ec_gpa = fields.Float(string="Ec (GPa)", compute="_compute_moe_modulus_gpa", digits=(12,2), store=True)


    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for record in self:
            parent = record.parent_id.sudo()
            sample_id = parent.eln_ref.sample_id.client_sample_id
            if sample_id:
                record.id_mark = sample_id
            else:
                record.id_mark = ""


    @api.onchange('id_mark')
    def _onchange_id_mark(self):
        for record in self:
            if record.id_mark and not record.parent_id.eln_ref.sample_id.client_sample_id:
                record.parent_id.eln_ref.sample_id.client_sample_id = record.id_mark


    @api.depends('length', 'width')
    def _compute_area(self):
        for record in self:
            record.area = round((record.length * record.width) , 4)


    @api.depends('crushing_load', 'area')
    def _compute_compressive_strength(self):
        for record in self:
            if record.area != 0:
                record.compressive_strength = record.crushing_load / record.area * 1000
            else:
                record.compressive_strength = 0.0


    @api.depends('parent_id', 'parent_id.child_lines', 'sr_no')
    def _compute_specimen(self):
        """Specimen number = position of the line within its parent (1, 2, 3 ...).

        Derived from the one2many sequence instead of a stored counter, so a
        deleted line shifts the remaining ones back into 1, 2, 3 ... order.
        """
        for record in self:
            if not record.parent_id:
                record.specimen = 0
                continue
            siblings = record.parent_id.child_lines
            # Sort on the position in the one2many, not on `id`: unsaved lines coming
            # from an onchange carry a NewId, which is not orderable.
            ordered_ids = [
                line.id
                for _, line in sorted(
                    enumerate(siblings), key=lambda pair: (pair[1].sr_no or 0, pair[0])
                )
            ]
            record.specimen = (
                ordered_ids.index(record.id) + 1 if record.id in ordered_ids else 0
            )


    @api.depends('diameter', 'specimen_length', 'mass')
    def _compute_moe_dimensions(self):
        """L/D ratio and density of the specimen (second table)."""
        for record in self:
            # L/D
            if record.diameter > 0 and record.specimen_length > 0:
                record.l_d_ratio = round(record.specimen_length / record.diameter, 3)
            else:
                record.l_d_ratio = 0.0

            # Density = mass / volume, volume = (pi / 4) * D^2 * L
            volume = (
                math.pi / CIRCLE_AREA_DIVISOR
                * record.diameter ** 2
                * record.specimen_length
                * MM3_TO_M3
            )
            if record.mass > 0 and volume > 0:
                record.density = round(record.mass / volume, 3)
            else:
                record.density = 0.0


    @api.depends('parent_id', 'parent_id.basic_stress', 'parent_id.upper_stress')
    def _compute_reference_stresses(self):
        """σb = Fc/9 and σa = Fc/3 from the first table, never typed per specimen."""
        for record in self:
            record.stress_b = record.parent_id.basic_stress
            record.stress_a = record.parent_id.upper_stress


    @api.depends('stress_b', 'stress_a', 'strain_b', 'strain_a')
    def _compute_moe_modulus(self):
        """Static modulus of elasticity, Ec = (σa - σb) / (εa - εb).

        Both stresses come from the first table's reference stresses, so Ec
        follows the entered cube strengths without any manual stress entry.
        """
        for record in self:
            strain_difference = (record.strain_a - record.strain_b) * MICRO
            stress_difference = record.stress_a - record.stress_b
            if strain_difference > 0 and stress_difference > 0:
                record.ec_mpa = round(
                    stress_difference / strain_difference, 2
                )
            else:
                record.ec_mpa = 0.0


    @api.depends('ec_mpa')
    def _compute_moe_modulus_gpa(self):
        for record in self:
            record.ec_gpa = round(record.ec_mpa / GPA_DIVISOR, 2)


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalConcreteMoeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted(lambda r: r.id if isinstance(r.id, int) else 0)
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ConcreteMoeNotes(models.Model):
    _name = "mechanical.concrete.moe.notes"

    parent_id = fields.Many2one('mechanical.concrete.moe',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


class MechanicalConcreteMoePoissonLine(models.Model):
    _name = "mechanical.concrete.moe.poisson.line"
    _description = "Concrete MOE Poisson's Ratio Line"
    _order = "id"

    parent_id = fields.Many2one('mechanical.concrete.moe',string="Parent Id",ondelete='cascade',index=True)

    # Specimen number is the line's own position in the parent's sequence, so it
    # is always 1, 2, 3 ... and renumbers by itself when a line is removed.
    specimen = fields.Integer(string="Specimen",compute="_compute_specimen",store=True,readonly=True)

    # Strains are typed by the technician as micro strain (x10^-6) and are never
    # recomputed, so nothing overwrites an entered value.
    long_strain_b = fields.Float(string="Long. εb (×10⁻⁶)", digits=(12,3))
    long_strain_a = fields.Float(string="Long. εa (×10⁻⁶)", digits=(12,3))
    trans_strain_b = fields.Float(string="Trans. εb (×10⁻⁶)", digits=(12,3))
    trans_strain_a = fields.Float(string="Trans. εa (×10⁻⁶)", digits=(12,3))

    poisson_ratio = fields.Float(string="Poisson's Ratio μ", compute="_compute_poisson_ratio", digits=(12,2))


    @api.depends('parent_id', 'parent_id.poisson_lines')
    def _compute_specimen(self):
        """Specimen number = position of the line within its parent (1, 2, 3 ...).

        Taken from the one2many sequence, so a deleted line shifts the remaining
        ones back into 1, 2, 3 ... order. The lines are never sorted on `id`:
        unsaved lines coming from an onchange carry a NewId, which is not
        orderable.
        """
        for record in self:
            sibling_ids = record.parent_id.poisson_lines.ids
            record.specimen = (
                sibling_ids.index(record.id) + 1 if record.id in sibling_ids else 0
            )


    @api.depends(
        'long_strain_b',
        'long_strain_a',
        'trans_strain_b',
        'trans_strain_a',
    )
    def _compute_poisson_ratio(self):
        """μ = (Trans. εa - Trans. εb) / (Long. εa - Long. εb)."""
        for record in self:
            strain_difference = record.long_strain_a - record.long_strain_b
            if strain_difference > 0:
                record.poisson_ratio = round(
                    (record.trans_strain_a - record.trans_strain_b) / strain_difference, 2
                )
            else:
                # Strains not entered (or Long. εa not above Long. εb) yet.
                record.poisson_ratio = 0.0