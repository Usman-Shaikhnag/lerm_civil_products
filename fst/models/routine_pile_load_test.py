from odoo import api, fields, models
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
import base64
import io
import math
import matplotlib.pyplot as plt

# Constants for graph styling
GRAPH_MAJOR_GRID_COLOR = '#d28b5c'
GRAPH_MINOR_GRID_COLOR = '#f0c7a0'


# =========================================================
# ROUTINE PARENT (CLONE OF INITIAL)
# =========================================================
class RoutinePileLoadTest(models.Model):
    _name = "routine.pile.load.test"
    _description = "Routine Vertical Pile Load Test Report"
    _order = "rec_date desc, id desc"


    # ================= SAME FIELDS =================
    work_name = fields.Char("Name of Work")
    contractor = fields.Char("Contractor")
    client = fields.Char("Client")
    cover_image = fields.Binary("Cover Image")

    ulr = fields.Char("ULR No", copy=False, readonly=True)
    report_no = fields.Char("Report No", copy=False, readonly=True)
    pile_no = fields.Char("Pile No")
    name = fields.Char("Project Name", required=True)
    rec_date = fields.Date("Report Date")
    site_location = fields.Char("Site Location")
    test_standard = fields.Char("Test Standard")
    test_equipment = fields.Text("Testing Equipment")
    introduction = fields.Text("Introduction")
    objective = fields.Text("Objective")
    test_procedure = fields.Text("Test Procedure")
    issued_to = fields.Char("Issued To")
    letter_no = fields.Char("Letter No")
    letter_date = fields.Date("Letter Date")
    srf_no = fields.Char("SRF No")
    executed_by = fields.Char("Executed By")

    allowable_capacity = fields.Float("Allowable Capacity")
    interpretation = fields.Text("Interpretation")
    conclusion = fields.Text("Conclusion")

    signatory_name = fields.Char("Authorized Signatory")
    signatory_designation = fields.Char("Designation")

    purpose = fields.Text("Purpose")
    scope = fields.Text("Scope")
    selection_of_piles = fields.Text("Selection of Piles")
    procedure_adopted = fields.Text("Procedure Adopted")
    analysis_safe_load = fields.Text("Analysis of Safe Load")

    pile_diameter = fields.Float("Pile Diameter (mm)")
    pile_type = fields.Char("Pile Type")
    pile_coordinates = fields.Char("Pile Coordinates")
    concrete_grade = fields.Char("Concrete Grade")
    pile_depth = fields.Float("Pile Depth (m)")
    design_load = fields.Float("Design Load (MT)")
    test_load = fields.Float("Test Load (MT)",compute="_compute_test_load",store=True)
    kentledge_load = fields.Float("Kentledge Load (MT)",compute="_compute_kentledge_load",store=True)
    date_of_casting = fields.Date("Date of Casting")
    date_of_testing = fields.Date("Date of Testing")

    date_of_casting_str = fields.Char(
        "Date of Casting (Formatted)",
        compute="_compute_formatted_dates",
        store=True)

    date_of_testing_str = fields.Char(
        "Date of Testing (Formatted)",
        compute="_compute_formatted_dates",
        store=True)

    incremental_load = fields.Float("Incremental Load",compute="_compute_incremental_load",store=True)
    jack_capacity = fields.Float("Jack Capacity")
    jack_ram_dia = fields.Float("Jack Ram Diameter")
    jack_ram_area = fields.Float("Jack Ram Area")
    jack_efficiency = fields.Float("Jack Efficiency")
    pressure_gauge_range = fields.Float("Pressure Gauge Range")
    pressure_gauge_least_count = fields.Float("Pressure Gauge Least Count")
    load_per_division = fields.Float("Load Per Division",compute="_compute_load_per_division",store=True)
    division_per_stage = fields.Float("Division Per Stage",compute="_compute_division_per_stage",store=True,digits=(6,3))
    actual_stage_load = fields.Float("Actual Stage Load",compute="_compute_actual_stage_load",store=True)
    test_equipment = fields.Text()

    @api.depends('date_of_casting', 'date_of_testing')
    def _compute_formatted_dates(self):
        for rec in self:
            rec.date_of_casting_str = (
                rec.date_of_casting.strftime('%d.%m.%Y')
                if rec.date_of_casting else False
            )

            rec.date_of_testing_str = (
                rec.date_of_testing.strftime('%d.%m.%Y')
                if rec.date_of_testing else False
            )

    @api.depends('design_load')
    def _compute_test_load(self):
        for rec in self:
            if rec.design_load > 0:
                rec.test_load = rec.design_load * 1.5
            else:
                rec.test_load = 0

    @api.depends('test_load')
    def _compute_kentledge_load(self):
        for rec in self:
            if rec.test_load > 0:
                rec.kentledge_load = round(rec.test_load * 1.25,1)
            else:
                rec.kentledge_load = 0

    @api.depends('design_load')
    def _compute_incremental_load(self):
        for rec in self:
            if rec.design_load > 0:
                rec.incremental_load = rec.design_load * 0.20
            else:
                rec.incremental_load = 0

    @api.depends('jack_ram_area', 'jack_efficiency', 'pressure_gauge_least_count')
    def _compute_load_per_division(self):
        for rec in self:
            if (
                rec.jack_ram_area > 0
                and rec.jack_efficiency > 0
                and rec.pressure_gauge_least_count > 0
            ):
                rec.load_per_division = round(
                    (
                        rec.pressure_gauge_least_count
                        * rec.jack_ram_area
                        * (rec.jack_efficiency / 100)
                    ) / 1000,
                    2
                )
            else:
                rec.load_per_division = 0

    @api.depends('load_per_division','incremental_load')
    def _compute_division_per_stage(self):
        for rec in self:
            if rec.load_per_division > 0 and rec.incremental_load > 0:
                rec.division_per_stage = round((rec.incremental_load / rec.load_per_division),3)

    @api.depends('load_per_division', 'division_per_stage')
    def _compute_actual_stage_load(self):
        for rec in self:
            if rec.load_per_division > 0 and rec.division_per_stage > 0:
                rounded_division = round(rec.division_per_stage)
                rec.actual_stage_load = round(
                    rounded_division * rec.load_per_division,
                    2
                )
            else:
                rec.actual_stage_load = 0

    @api.onchange('design_load')
    def _onchange_design_load(self):
        for rec in self:

            # Test Load
            rec.test_load = round(rec.design_load * 1.5 if rec.design_load > 0 else 0)

            # Kentledge Load
            rec.kentledge_load = round(rec.test_load * 1.25 if rec.test_load > 0 else 0,1)

            # Incremental Load
            rec.incremental_load = rec.design_load * 0.20 if rec.design_load > 0 else 0

            # Division Per Stage
            if rec.load_per_division > 0 and rec.incremental_load > 0:
                rec.division_per_stage = round((rec.incremental_load / rec.load_per_division),3)
            else:
                rec.division_per_stage = 0

            # Actual Stage Load
            if rec.load_per_division > 0 and rec.division_per_stage > 0:
                rounded_division = round(rec.division_per_stage)
                rec.actual_stage_load = round(rounded_division * rec.load_per_division,2)
            else:
                rec.actual_stage_load = 0


    @api.onchange('jack_ram_area','jack_efficiency','pressure_gauge_least_count')
    def _onchange_load_calculations(self):
        for rec in self:

            # Load Per Division
            if (rec.jack_ram_area > 0 and rec.jack_efficiency > 0 and rec.pressure_gauge_least_count > 0):
                rec.load_per_division = round((
                    rec.pressure_gauge_least_count
                    * rec.jack_ram_area
                    * (rec.jack_efficiency / 100)
                    ) / 1000,2)
            else:
                rec.load_per_division = 0

            # Division Per Stage
            if rec.load_per_division > 0 and rec.incremental_load > 0:
                rec.division_per_stage = round((rec.incremental_load / rec.load_per_division),3)
            else:
                rec.division_per_stage = 0

            # Actual Stage Load
            if rec.load_per_division > 0 and rec.division_per_stage > 0:
                rounded_division = round(rec.division_per_stage)
                rec.actual_stage_load = round(rounded_division * rec.load_per_division,2)
            else:
                rec.actual_stage_load = 0

    equipment_ids = fields.One2many(
        "routine.pile.load.equipment",
        "parent_id",
        string="Equipments"
    )
    # ================= SAME RELATIONS =================
    loading_reading_ids = fields.One2many(
        "routine.pile.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    unloading_reading_ids = fields.One2many(
        "routine.pile.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )

    content_ids = fields.One2many(
        "routine.pile.report.content",
        "parent_id",
        string="Contents",
        copy=False
    )

    basic_data_ids = fields.One2many(
        "routine.pile.basic.data",
        "parent_id",
        string="Basic Data",
        copy=False
    )

    site_image_ids = fields.One2many(
        "routine.pile.test.image",
        "parent_id",
        string="Site Photographs",
        copy=False
    )

    graph_image = fields.Binary("Load Settlement Graph")


    # ================= SAME COMPUTES =================
    gross_settlement = fields.Float(compute="_compute_settlement_values", store=True)
    net_settlement = fields.Float(compute="_compute_settlement_values", store=True)
    rebound = fields.Float(compute="_compute_settlement_values", store=True)

    # Settlement Summary
    ed = fields.Float(
        "Elastic Deformation (ED)",
        compute="_compute_settlement_values",
        store=True,
        digits=(16,3)
    )

    rd = fields.Float(
        "Residual Deformation (RD)",
        compute="_compute_settlement_values",
        store=True,
        digits=(16,3)
    )

    elastic_rebound = fields.Float(
        "Elastic Rebound",
        compute="_compute_settlement_values",
        store=True
    )

    max_settlement = fields.Float(
        "Maximum Settlement",
        compute="_compute_max_settlement",
        store=True,
        readonly=True,
        digits=(16,3)
    )

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

            cert = lab.lab_certificate_no or ''
            loc = lab.lab_location_line[:1].location_code or ''

            seq = self.env['ir.sequence'].next_by_code(
                lab.ulr_sequence.code
            )

            rec.ulr = f"{cert}{year}{loc}{seq}"

    # =========================================================
    # 🔥 EXACT SAME FUNCTIONS (copied 1:1)
    # =========================================================
    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_max_settlement(self):
        for rec in self:
            values = (
                rec.loading_reading_ids.mapped('mean_mm') +
                rec.unloading_reading_ids.mapped('mean_mm')
            )
            load_values = (
                rec.loading_reading_ids.mapped('load_tonne') +
                rec.unloading_reading_ids.mapped('load_tonne')
            )

            rec.max_settlement = max(values) if values else 0.0
            rec.elastic_rebound = max(load_values) if load_values else 0.0

    @api.depends('loading_reading_ids.mean_mm', 'unloading_reading_ids.mean_mm')
    def _compute_settlement_values(self):
        for rec in self:

            loading_map = {}

            for r in rec.loading_reading_ids:
                loading_map[r.load_tonne] = r.mean_mm

            if loading_map:

                # maximum applied load
                gross = max(loading_map.keys())

                # maximum settlement
                total_settlement = max(loading_map.values())

            else:
                gross = 0.0
                total_settlement = 0.0

            # RD = settlement when load returns to 0 after unloading
            rebound_lines = rec.unloading_reading_ids.filtered(
                lambda r: r.load_tonne == 0
            ).sorted('reading_datetime')

            # residual settlement after unloading
            rd = rebound_lines[-1].mean_mm if rebound_lines else 0.0

            # elastic rebound
            ed = total_settlement - rd

            rec.ed = round(ed, 3)
            rec.rd = round(rd, 3)
            # rec.elastic_rebound = round(gross, 2)

            # optional if you have field for max load
            # rec.max_load = round(gross, 2)

    def action_generate_graph(self):
        """Generate Load-Settlement graph exactly like PDF"""
        self.ensure_one()

        def loading_points(readings):
            result = []

            prev_load = None
            last_mean = None

            for r in readings.sorted('reading_datetime'):

                if prev_load is None:
                    prev_load = r.load_tonne
                    last_mean = r.mean_mm
                    continue

                # same step if:
                #   same load OR zero (continuation)
                if r.load_tonne == prev_load or r.load_tonne == 0:
                    last_mean = r.mean_mm
                else:
                    result.append((prev_load, last_mean))
                    prev_load = r.load_tonne
                    last_mean = r.mean_mm

            if prev_load is not None:
                result.append((prev_load, last_mean))

            return result


        def unloading_points(readings):
            return [
                (r.load_tonne, r.mean_mm)
                for r in readings.sorted('reading_datetime')
            ]
        # loading_all = self.loading_reading_ids.sorted('reading_datetime')
        # unloading_all = self.unloading_reading_ids.sorted('reading_datetime')

        loading = loading_points(self.loading_reading_ids)
        unloading = unloading_points(self.unloading_reading_ids)
        # import wdb;wdb.set_trace()
        if not loading and not unloading:
            raise UserError("No reading data found to generate the graph. Please add loading/unloading readings first.")

        fig, ax = plt.subplots(figsize=(7.5, 5.5))

        # =====================================================
        # LOADING CURVE
        # =====================================================

        if loading:

            load_vals = [0] + [l for l, m in loading]
            settle_vals = [0] + [m for l, m in loading]

            ax.plot(
                load_vals,
                settle_vals,
                marker='o',
                markersize=6,
                markeredgewidth=1.2,
                linewidth=1.8,
                label='Loading',
                zorder=3,
                clip_on=False
            )

        # =====================================================
        # UNLOADING CURVE
        # =====================================================

        if unloading:

            load_vals = [l for l, m in unloading]
            settle_vals = [m for l, m in unloading]

            ax.plot(
                load_vals,
                settle_vals,
                marker='o',
                markersize=6,
                markeredgewidth=1.2,
                linestyle='--',
                linewidth=1.8,
                label='Unloading',
                zorder=3,
                clip_on=False
            )

        # =====================================================
        # LABELS
        # =====================================================

        ax.set_ylabel(
            "SETTLEMENT (MM)",
            fontsize=10,
            fontweight='bold',
            labelpad=8
        )
        ax.xaxis.set_label_position('top')
        ax.tick_params(axis='x', which='both', top=True, bottom=False, labeltop=True, labelbottom=False)

        ax.set_xlabel(
            "LOAD (TONNE)",
            fontsize=10,
            fontweight='bold'
        )

        ax.set_title(
            "LOAD - SETTLEMENT GRAPH",
            fontsize=12,
            fontweight='bold',
            pad=12
        )

        # =====================================================
        # Y AXIS STEP CALCULATION
        # =====================================================

        def load_major_step(x_max):

            if x_max < 20:
                return 2

            elif x_max <= 25:
                return 5

            elif x_max <= 80:
                return 10

            elif x_max <= 150:
                return 20

            elif x_max <= 400:
                return 50

            elif x_max <= 1000:
                return 100

            else:
                return 200

        all_loads = [l for l, m in (loading + unloading) if l > 0]
        all_means = [m for l, m in (loading + unloading) if m > 0]

        x_max = max(all_loads) if all_loads else 20
        y_max = max(all_means) if all_means else 1

        x_major = load_major_step(x_max)

        if x_major < 5:
            x_minor = x_major / 2
        else:
            x_minor = x_major / 5

        # =====================================================
        # X AXIS STEP CALCULATION
        # =====================================================

        def settlement_major_step(y_max):

            if y_max <= 2:
                return 0.2

            elif y_max <= 5:
                return 0.5

            elif y_max <= 15:
                return 1

            elif y_max <= 30:
                return 2

            else:
                return 5

        all_means = [m for l, m in (loading + unloading)]

        # y_max = max(all_means) if all_means else 1

        y_major = settlement_major_step(y_max)
        y_minor = y_major / 5

        # =====================================================
        # AXIS LIMITS
        # =====================================================

        # X: tight to data, rounded up to next major tick
        x_limit = math.ceil(x_max / x_major) * x_major
        ax.set_xlim(0, x_limit)

        # Y: tight to data, rounded up to next major tick  
        y_limit = math.ceil(y_max / y_major) * y_major
        ax.set_ylim(0, y_limit)
        ax.invert_yaxis()
        # =====================================================
        # REMOVE EXTRA PADDING
        # =====================================================

        ax.margins(x=0, y=0)

        ax.set_xmargin(0)
        ax.set_ymargin(0)

        # =====================================================
        # TICKS
        # =====================================================

        ax.xaxis.set_major_locator(
            plt.MultipleLocator(x_major)
        )

        ax.xaxis.set_minor_locator(
            plt.MultipleLocator(x_minor)
        )

        ax.yaxis.set_major_locator(
            plt.MultipleLocator(y_major)
        )

        ax.yaxis.set_minor_locator(
            plt.MultipleLocator(y_minor)
        )

        # =====================================================
        # GRID
        # =====================================================

        ax.grid(
            which='major',
            linestyle='-',
            linewidth=0.8,
            color='#d28b5c'
        )

        ax.grid(
            which='minor',
            linestyle='-',
            linewidth=0.4,
            color='#f0c7a0'
        )

        # =====================================================
        # ENGINEERING STYLE AXES
        # =====================================================

        ax.tick_params(
            axis='both',
            which='major',
            direction='inout',
            length=6
        )

        ax.tick_params(
            axis='both',
            which='minor',
            direction='inout',
            length=3
        )

        # =====================================================
        # LEGEND
        # =====================================================

        # ax.legend(
        #     loc='lower right',
        #     frameon=False
        # )

        # =====================================================
        # SAVE IMAGE
        # =====================================================

        fig.subplots_adjust(
            left=0.08,
            right=0.98,
            bottom=0.08,
            top=0.92
        )

        buffer = io.BytesIO()

        fig.savefig(
            buffer,
            format='png',
            dpi=150,
            bbox_inches='tight',
            pad_inches=0
        )

        plt.close(fig)

        # self.graph_image = base64.b64encode(buffer.getvalue())
        self.graph_image = base64.b64encode(buffer.getvalue())

    # ================= SAME RECOMPUTE =================
    def action_recompute_all(self):
        for rec in self:
            for line in rec.loading_reading_ids:
                line._compute_mean()
                line._compute_split_dt()
            for line in rec.unloading_reading_ids:
                line._compute_mean()
                line._compute_split_dt()

            rec._compute_settlement_values()
            rec._compute_max_settlement()

    def print_report(self):
        self.ensure_one()
        report = self.env.ref('fst.routine_pile_load_test_report_py3o')
        filename = f"{self.name or 'Routine Pile Load Test Report'}"
        return report.report_action(self, config={'report_name': filename})

    # ================= SAME DUPLICATE =================
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



    def action_delete_line(self):
        self.unlink()


# =========================================================
# CHILD MODELS (CLONES)
# =========================================================
class RoutinePileReadingLoading(models.Model):
    _name = "routine.pile.reading.loading"
    _description = "Pile Load Reading - Loading"
    _order = "id"

    parent_id = fields.Many2one("routine.pile.load.test", ondelete="cascade", required=True)

    reading_datetime = fields.Datetime(
        "Date & Time",
        required=True,
    )

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
    load_tonne = fields.Float()

    dial_a = fields.Float()
    dial_b = fields.Float()
    dial_c = fields.Float()
    dial_d = fields.Float()

    mean_mm = fields.Float(
        string="Mean (mm)",
        compute="_compute_mean",
        store=True,
        readonly=True,
        digits=(16,3)
    )
    @api.model
    def default_get(self, fields_list):
        """Minimal default - just set current time as fallback"""
        res = super().default_get(fields_list)
        
        # Don't set reading_datetime here - let onchange handle it
        # This is just a safety fallback
        if 'reading_datetime' in fields_list and 'reading_datetime' not in res:
            res['reading_datetime'] = fields.Datetime.now()
        
        return res

    @api.onchange('parent_id')
    def _onchange_set_datetime(self):
        """Auto-fill datetime when adding new line in tree"""
        # Always run for new records
        if self.parent_id:
            latest_datetime = None
            
            # First, check unsaved lines in the current form (these have priority)
            unsaved_lines = [
                r for r in self.parent_id.loading_reading_ids 
                if r.reading_datetime and r != self  # Exclude current line
            ]
            
            if unsaved_lines:
                # Get the one with the latest datetime from unsaved lines
                latest = max(unsaved_lines, key=lambda x: x.reading_datetime)
                latest_datetime = latest.reading_datetime
            else:
                # No unsaved lines, check saved lines from database
                saved_lines = self.search(
                    [('parent_id', '=', self.parent_id.id)],
                    order='id desc',
                    limit=1
                )
                if saved_lines and saved_lines.reading_datetime:
                    latest_datetime = saved_lines.reading_datetime
            
            # Set the datetime
            if latest_datetime:
                self.reading_datetime = latest_datetime + timedelta(minutes=15)
            else:
                self.reading_datetime = fields.Datetime.now()

    @api.model 
    def create(self, vals):
        """Ensure datetime is set on create (when form is saved)"""
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
        
        return super().create(vals)

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

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_mean(self):
        for rec in self:
            values = [rec.dial_a, rec.dial_b, rec.dial_c, rec.dial_d]
            valid = [v for v in values if v is not False]
            rec.mean_mm = round(sum(valid) / len(valid), 3) if valid else 0.0


class RoutinePileReadingUnloading(models.Model):
    _name = "routine.pile.reading.unloading"
    _description = "Pile Load Reading - Unloading"
    _order = "id"

    parent_id = fields.Many2one(
        "routine.pile.load.test",
        ondelete="cascade",
        required=True,
        index=True
    )

    reading_datetime = fields.Datetime(
        "Date & Time",
        required=True,
    )

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
    load_tonne = fields.Float("Load (Tonne)")

    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    dial_c = fields.Float("Dial C (mm)")
    dial_d = fields.Float("Dial D (mm)")

    mean_mm = fields.Float(
        string="Mean (mm)",
        compute="_compute_mean",
        store=True,
        readonly=True,
        digits=(16,3)
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

        return super().create(vals)


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

    @api.depends('dial_a', 'dial_b', 'dial_c', 'dial_d')
    def _compute_mean(self):
        for rec in self:
            values = [rec.dial_a, rec.dial_b, rec.dial_c, rec.dial_d]
            valid = [v for v in values if v is not False]
            rec.mean_mm = round(sum(valid) / len(valid), 3) if valid else 0.0




class RoutinePileReportContent(models.Model):
    _name = "routine.pile.report.content"
    parent_id = fields.Many2one("routine.pile.load.test", ondelete="cascade")
    sequence = fields.Float()
    description = fields.Char(required=True)
    page_no = fields.Char()


class RoutinePileBasicData(models.Model):
    _name = "routine.pile.basic.data"
    parent_id = fields.Many2one("routine.pile.load.test", ondelete="cascade")
    sr_no = fields.Integer()
    parameter = fields.Char(required=True)
    value = fields.Char()


class RoutinePileImage(models.Model):
    _name = "routine.pile.test.image"
    parent_id = fields.Many2one("routine.pile.load.test", ondelete="cascade")
    sequence = fields.Integer(default=1)
    image = fields.Binary(required=True)
    caption = fields.Char()


class RoutinePileLoadEquipment(models.Model):
    _name = "routine.pile.load.equipment"
    parent_id = fields.Many2one("routine.pile.load.test")
    equipment_name = fields.Char("Equipment")
    quantity = fields.Char("Quantity")
    details = fields.Text("Details")