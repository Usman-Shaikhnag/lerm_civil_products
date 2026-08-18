from odoo import api, fields, models
from datetime import timedelta
import base64
import io
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline


class FstLateralPileLoadTest(models.Model):
    _name = "fst.lateral.pile.load.test"
    _description = "Initial Lateral Pile Load Test Report"
    _order = "rec_date desc, id desc"

    name = fields.Char("Project Name", required=True)
    rec_date = fields.Date("Report Date")
    work_name = fields.Char("Name of Work")
    client = fields.Char(string="Client")
    contractor = fields.Char(string="Contractor")

    ulr = fields.Char("ULR No", copy=False, readonly=True)
    report_no = fields.Char("Report No", copy=False, readonly=True)
    pile_no = fields.Char("Pile No")
    site_location = fields.Char("Site Location")
    test_standard = fields.Char("Test Standard")

    general_philosophy = fields.Text("General Philosophy")
    methodology = fields.Text("Methodology for Lateral Pile Load Testing")
    scope_of_works = fields.Text("Scope of Works")
    reference = fields.Text("Reference")
    test_equipment = fields.Text("Equipment Used")
    setup_apparatus = fields.Text("Setting up of Testing Apparatus")
    test_procedure = fields.Text("Load Test Procedure")
    preparation_report = fields.Text("Preparation of Test Report")
    conclusion = fields.Text("Conclusion")

    allowable_capacity = fields.Float("Allowable Lateral Capacity")

    signatory_name = fields.Char("Authorized Signatory")
    signatory_designation = fields.Char("Designation")

    loading_reading_ids = fields.One2many(
        "fst.lateral.pile.load.reading.loading",
        "parent_id",
        string="Loading Readings",
        copy=False
    )

    loading_summary_ids = fields.One2many(
        "fst.lateral.pile.load.loading.summary",
        "parent_id",
        string="Settlement Summary",
        copy=False,
        readonly=True
    )

    unloading_reading_ids = fields.One2many(
        "fst.lateral.pile.load.reading.unloading",
        "parent_id",
        string="Unloading Readings",
        copy=False
    )

    content_ids = fields.One2many(
        "fst.lateral.pile.load.report.content",
        "parent_id",
        string="Contents",
        copy=False
    )

    basic_data_ids = fields.One2many(
        "fst.lateral.pile.load.basic.data",
        "parent_id",
        string="Basic Data",
        copy=False
    )

    site_image_ids = fields.One2many(
        "fst.lateral.pile.load.test.image",
        "parent_id",
        string="Site Photographs",
        copy=False
    )

    graph_image = fields.Binary("Load Displacement Graph")

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

    max_displacement = fields.Float(
        "Maximum Displacement",
        compute="_compute_max_displacement",
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
            "One (01) No. of Routine Pile Lateral Load Test was conducted to reconfirm the Lateral "
            "Load Carrying Capacity of the Piles to support the various design lateral loads due to "
            "Wind or Earthquake etc. or any other lateral load on the structure. This report provides "
            "the details for Load \u2013 Displacement behaviour of this Test pile."
        )
        self.scope_of_works = (
            "This procedure was applicable for the testing of 1200mm diameter bored Initial Test pile "
            "for the Lateral Load.\n\n"
            "1. Mobilization of required manpower & machineries.\n"
            "2. Setting up of testing apparatus.\n"
            "3. Incremental loading and unloading & recording of Load Vs Displacement.\n"
            "4. Preparation of test report."
        )
        self.reference = (
            "\u2022 IS 2911 (Part 4) - 2013 - Code of practice for design and construction of pile "
            "foundations - Part 4 Load Test on Piles."
        )
        self.test_equipment = (
            "\u2022 Hydraulic Jack \u2013 100 MT Capacity\n"
            "\u2022 Pressure Gauge \u2013 0-280 kg/cm2 with LC of 5.0 kg/cm2\n"
            "\u2022 Dial Gauges \u2013 2 Nos of Dial Gauges of 25 mm travel with LC of 0.01 mm"
        )
        self.setup_apparatus = (
            "1) The test Apparatus used for the test consisted of the following:\n"
            "   i. Hydraulic Jack \u2013 100 MT Capacity\n"
            "   ii. Pressure Gauge \u2013 0 \u2013 280 kg/cm2 range\n"
            "  iii. Dial Gauges \u2013 2 Nos. with LC of 0.01 mm\n"
            "   iv. Datum Bars \u2013 1 Nos.\n"
            "   v. Suitable Beam with End Plates for Transfer of Load from jack to reaction Pile.\n\n"
            "2) The liner / concrete of test pile was levelled for 100 mm x 100 mm or 100 mm dia. "
            "to fix the hydraulic Jacks. The reaction was taken from nearest Initial Test Pile "
            "(min 2.00m distance apart) The hydraulic jack was resting on steel stool & Datum Bar "
            "was erected."
        )
        self.test_procedure = (
            "1) The test was carried out by applying a series of lateral incremental load as per "
            "cl. 8.1 of IS 2911 (IV) 2013 each increment being of about 20 percent (20%) of ultimate "
            "load on the pile. This increment was carried out up to 1BB50% of the safe working load "
            "as per cl. 8.4.1 of IS 2911 (IV) 2013.\n\n"
            "2) Displacement was recorded with 2 dial gauges spaced at 30 cm and kept horizontally "
            "one above the other on test pile (preferable one dial gauge 15cm above and the other "
            "15cm below the cut off level).\n\n"
            "3) The next increment was applied after the rate of displacement is less than or equal "
            "to 0.1 mm per 30 min subject to minimum of 30 min as per cl. 8.2 of IS 2911 (IV) 2013.\n\n"
            "4) After completion of loading up to final load was decreased, each decrement being "
            "about 20 % of safe load on pile after every 1,10,20 and 30 minutes interval. Readings "
            "were taken immediately after unloading and 15 minutes later, for each stage.\n\n"
            "5) All of the above activities were carried out in presence of Engineer\u2019s "
            "Representative.\n\n"
            "6) Once the Test Load was reached, the safe Lateral load on single pile for the Routine "
            "test would be least of the following:\n"
            "   i) Fifty percent of the final load at which the total displacement increases to 12 mm;\n"
            "  ii) Final load at which the total displacement corresponds to 5 mm."
        )
        self.preparation_report = (
            "A chart was plotted to depict Lateral Load on Pile in Tons vs. Pile Deflection in mm "
            "and same is attached with the test report."
        )
        self.conclusion = (
            "As can be seen from the results of Lateral Load tests on Working Test Pile No. T409-P14, "
            "the Deflection of the piles at the Test Load is 7.87 mm. Moreover, Net Deflection of Pile "
            "is 5.09 & Elastic Rebound is 2.98 mm. Hence, as the total Displacement of the pile is "
            "more than 5mm, the Design Loads can be considered as Safe Design Lateral Loads for the "
            "piles.\n\n"
            "Safe Design Lateral Load for pile T-409-P14 = 5.80 MT"
        )
        self.allowable_capacity = 5.80

        existing = self.env['fst.lateral.pile.load.report.content'].search(
            [('parent_id', '=', self.id)]
        )
        existing.unlink()

        contents = [
            ("01", "General Philosophy", "02"),
            ("02", "Methodology for Lateral Pile Load Testing", "02"),
            ("2.1", "Scope of Works", "02"),
            ("2.2", "Reference", "02"),
            ("2.3", "Equipment Used", "02"),
            ("2.4", "Setting up of Testing Apparatus", "03"),
            ("2.5", "Load Test Procedure", "03"),
            ("2.6", "Preparation of Test Report", "04"),
            ("2.7", "Conclusion", "04"),
        ]
        for seq, desc, page in contents:
            self.env['fst.lateral.pile.load.report.content'].create({
                'parent_id': self.id,
                'sequence': float(seq) if seq.replace('.', '', 1).isdigit() else 0,
                'description': desc,
                'page_no': page,
            })

    def action_generate_test_data(self):
        self.ensure_one()
        from datetime import datetime, timedelta

        now = datetime.now()

        self.general_philosophy = (
            "One (01) No. of Routine Pile Lateral Load Test was conducted to reconfirm the Lateral "
            "Load Carrying Capacity of the Piles to support the various design lateral loads due to "
            "Wind or Earthquake etc. or any other lateral load on the structure. This report provides "
            "the details for Load \u2013 Displacement behaviour of this Test pile."
        )
        self.scope_of_works = (
            "This procedure was applicable for the testing of 1200mm diameter bored Initial Test pile "
            "for the Lateral Load.\n\n"
            "1. Mobilization of required manpower & machineries.\n"
            "2. Setting up of testing apparatus.\n"
            "3. Incremental loading and unloading & recording of Load Vs Displacement.\n"
            "4. Preparation of test report."
        )
        self.reference = (
            "\u2022 IS 2911 (Part 4) - 2013 - Code of practice for design and construction of pile "
            "foundations - Part 4 Load Test on Piles."
        )
        self.test_equipment = (
            "\u2022 Hydraulic Jack \u2013 100 MT Capacity\n"
            "\u2022 Pressure Gauge \u2013 0-280 kg/cm2 with LC of 5.0 kg/cm2\n"
            "\u2022 Dial Gauges \u2013 2 Nos of Dial Gauges of 25 mm travel with LC of 0.01 mm"
        )
        self.setup_apparatus = (
            "1) The test Apparatus used for the test consisted of the following:\n"
            "   i. Hydraulic Jack \u2013 100 MT Capacity\n"
            "   ii. Pressure Gauge \u2013 0 \u2013 280 kg/cm2 range\n"
            "  iii. Dial Gauges \u2013 2 Nos. with LC of 0.01 mm\n"
            "   iv. Datum Bars \u2013 1 Nos.\n"
            "   v. Suitable Beam with End Plates for Transfer of Load from jack to reaction Pile.\n\n"
            "2) The liner / concrete of test pile was levelled for 100 mm x 100 mm or 100 mm dia. "
            "to fix the hydraulic Jacks. The reaction was taken from nearest Initial Test Pile "
            "(min 2.00m distance apart) The hydraulic jack was resting on steel stool & Datum Bar "
            "was erected."
        )
        self.test_procedure = (
            "1) The test was carried out by applying a series of lateral incremental load as per "
            "cl. 8.1 of IS 2911 (IV) 2013 each increment being of about 20 percent (20%) of ultimate "
            "load on the pile. This increment was carried out up to 1BB50% of the safe working load "
            "as per cl. 8.4.1 of IS 2911 (IV) 2013.\n\n"
            "2) Displacement was recorded with 2 dial gauges spaced at 30 cm and kept horizontally "
            "one above the other on test pile (preferable one dial gauge 15cm above and the other "
            "15cm below the cut off level).\n\n"
            "3) The next increment was applied after the rate of displacement is less than or equal "
            "to 0.1 mm per 30 min subject to minimum of 30 min as per cl. 8.2 of IS 2911 (IV) 2013.\n\n"
            "4) After completion of loading up to final load was decreased, each decrement being "
            "about 20 % of safe load on pile after every 1,10,20 and 30 minutes interval. Readings "
            "were taken immediately after unloading and 15 minutes later, for each stage.\n\n"
            "5) All of the above activities were carried out in presence of Engineer\u2019s "
            "Representative.\n\n"
            "6) Once the Test Load was reached, the safe Lateral load on single pile for the Routine "
            "test would be least of the following:\n"
            "   i) Fifty percent of the final load at which the total displacement increases to 12 mm;\n"
            "  ii) Final load at which the total displacement corresponds to 5 mm."
        )
        self.preparation_report = (
            "A chart was plotted to depict Lateral Load on Pile in Tons vs. Pile Deflection in mm "
            "and same is attached with the test report."
        )
        self.conclusion = (
            "As can be seen from the results of Lateral Load tests on Working Test Pile No. T409-P14, "
            "the Deflection of the piles at the Test Load is 7.87 mm. Moreover, Net Deflection of Pile "
            "is 5.09 & Elastic Rebound is 2.98 mm. Hence, as the total Displacement of the pile is "
            "more than 5mm, the Design Loads can be considered as Safe Design Lateral Loads for the "
            "piles.\n\n"
            "Safe Design Lateral Load for pile T-409-P14 = 5.80 MT"
        )
        self.allowable_capacity = 5.80

        basic_data = [
            ("1", "Project Name", self.name),
            ("2", "Pile No", self.pile_no or "T409-P14"),
            ("3", "Pile Diameter", "1200 mm"),
            ("4", "Type of Pile", "Bored Initial Test Pile"),
            ("5", "Type of Test", "Routine Lateral Load Test"),
            ("6", "Test Load (Max)", "5.80 MT"),
            ("7", "Test Standard", self.test_standard or "IS 2911 (Part 4)"),
        ]
        for sr, param, value in basic_data:
            self.env['fst.lateral.pile.load.basic.data'].create({
                'parent_id': self.id,
                'sr_no': int(sr),
                'parameter': param,
                'value': value,
            })

        loading_readings = [
            # (dt, load_tonne, applied_pressure, pressure_under_plate, dial_a, dial_b, dial_c)
            (now, 0.0, 0.0, 0.0, 0.00, 0.00, 0.00),
            (now + timedelta(minutes=15), 1.16, 0.0, 0.0, 0.52, 0.48, 0.50),
            (now + timedelta(minutes=30), 1.16, 0.0, 0.0, 0.85, 0.80, 0.82),
            (now + timedelta(minutes=45), 1.16, 0.0, 0.0, 1.05, 1.00, 1.02),
            (now + timedelta(hours=1), 2.32, 0.0, 0.0, 1.40, 1.35, 1.38),
            (now + timedelta(hours=1, minutes=15), 2.32, 0.0, 0.0, 1.70, 1.65, 1.68),
            (now + timedelta(hours=1, minutes=30), 2.32, 0.0, 0.0, 1.90, 1.85, 1.88),
            (now + timedelta(hours=1, minutes=45), 3.48, 0.0, 0.0, 2.25, 2.20, 2.22),
            (now + timedelta(hours=2), 3.48, 0.0, 0.0, 2.55, 2.50, 2.52),
            (now + timedelta(hours=2, minutes=15), 3.48, 0.0, 0.0, 2.75, 2.70, 2.72),
            (now + timedelta(hours=2, minutes=30), 4.64, 0.0, 0.0, 3.10, 3.05, 3.08),
            (now + timedelta(hours=2, minutes=45), 4.64, 0.0, 0.0, 3.40, 3.35, 3.38),
            (now + timedelta(hours=3), 4.64, 0.0, 0.0, 3.60, 3.55, 3.58),
            (now + timedelta(hours=3, minutes=15), 5.80, 0.0, 0.0, 4.00, 3.95, 3.98),
            (now + timedelta(hours=3, minutes=30), 5.80, 0.0, 0.0, 4.30, 4.25, 4.28),
            (now + timedelta(hours=3, minutes=45), 5.80, 0.0, 0.0, 4.50, 4.45, 4.48),
            (now + timedelta(hours=4), 5.80, 0.0, 0.0, 4.90, 4.85, 4.88),
            (now + timedelta(hours=4, minutes=15), 5.80, 0.0, 0.0, 5.20, 5.15, 5.18),
            (now + timedelta(hours=4, minutes=30), 5.80, 0.0, 0.0, 5.40, 5.35, 5.38),
            (now + timedelta(hours=4, minutes=45), 5.80, 0.0, 0.0, 5.80, 5.75, 5.78),
            (now + timedelta(hours=5), 5.80, 0.0, 0.0, 6.10, 6.05, 6.08),
            (now + timedelta(hours=5, minutes=15), 5.80, 0.0, 0.0, 6.30, 6.25, 6.28),
            (now + timedelta(hours=5, minutes=30), 5.80, 0.0, 0.0, 6.70, 6.65, 6.68),
            (now + timedelta(hours=5, minutes=45), 5.80, 0.0, 0.0, 7.00, 6.95, 6.98),
            (now + timedelta(hours=6), 5.80, 0.0, 0.0, 7.20, 7.15, 7.18),
        ]
        for dt, load, press, under, a, b, c in loading_readings:
            self.env['fst.lateral.pile.load.reading.loading'].create({
                'parent_id': self.id,
                'reading_datetime': dt,
                'load_tonne': load,
                'applied_pressure': press,
                'pressure_under_plate': under,
                'dial_a': a,
                'dial_b': b,
                'dial_c': c,
            })

        unloading_readings = [
            (now + timedelta(hours=6, minutes=15), 4.64, 6.20, 6.15, 6.18),
            (now + timedelta(hours=6, minutes=30), 4.64, 5.80, 5.75, 5.78),
            (now + timedelta(hours=6, minutes=45), 4.64, 5.50, 5.45, 5.48),
            (now + timedelta(hours=7), 3.48, 4.60, 4.55, 4.58),
            (now + timedelta(hours=7, minutes=15), 3.48, 4.20, 4.15, 4.18),
            (now + timedelta(hours=7, minutes=30), 3.48, 3.90, 3.85, 3.88),
            (now + timedelta(hours=7, minutes=45), 2.32, 2.80, 2.75, 2.78),
            (now + timedelta(hours=8), 2.32, 2.40, 2.35, 2.38),
            (now + timedelta(hours=8, minutes=15), 2.32, 2.10, 2.05, 2.08),
            (now + timedelta(hours=8, minutes=30), 1.16, 0.80, 0.75, 0.78),
            (now + timedelta(hours=8, minutes=45), 1.16, 0.65, 0.60, 0.62),
            (now + timedelta(hours=9), 0.0, 0.80, 0.75, 0.78),
            (now + timedelta(hours=9, minutes=15), 0.0, 0.65, 0.60, 0.62),
        ]
        for dt, load, a, b, c in unloading_readings:
            self.env['fst.lateral.pile.load.reading.unloading'].create({
                'parent_id': self.id,
                'reading_datetime': dt,
                'load_tonne': load,
                'dial_a': a,
                'dial_b': b,
                'dial_c': c,
            })
    @api.depends('loading_summary_ids.cumulative_settlement')
    def _compute_max_displacement(self):
        for rec in self:
            values = rec.loading_summary_ids.mapped('cumulative_settlement')
            rec.max_displacement = max(values) if values else 0.0

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
            "SELECT target_settlement, allowable_load FROM fst_lateral_pile_load_test WHERE id = %s",
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

        # Fallback for old data: all summaries have load_type='loading'.
        # Detect the transition where load_tonne stops increasing.
        if not unloading:
            for i in range(1, len(summaries)):
                if summaries[i].load_tonne < summaries[i-1].load_tonne:
                    loading = [(s.load_tonne, s.cumulative_settlement)
                               for s in summaries[:i]]
                    unloading = [(s.load_tonne, s.cumulative_settlement)
                                 for s in summaries[i:]]
                    break

        load_x = [0] + [p[0] for p in loading]
        load_y = [0] + [p[1] for p in loading]

        if unloading:
            unload_x = [load_x[-1]] + [p[0] for p in unloading]
            unload_y = [load_y[-1]] + [p[1] for p in unloading]
        else:
            unload_x, unload_y = [], []

        def smooth(x, y):
            if len(x) < 3:
                return x, y
            x_np = np.array(x, dtype=float)
            y_np = np.array(y, dtype=float)
            if not np.all(np.diff(x_np) >= 0):
                x_np = x_np[::-1]
                y_np = y_np[::-1]
                if not np.all(np.diff(x_np) >= 0):
                    return x, y
            try:
                spline = make_interp_spline(x_np, y_np, k=2)
                x_s = np.linspace(x_np.min(), x_np.max(), 200)
                y_s = spline(x_s)
                return x_s, y_s
            except Exception:
                return x, y

        load_xs, load_ys = smooth(load_x, load_y)
        unload_xs, unload_ys = smooth(unload_x, unload_y)

        fig, ax = plt.subplots(figsize=(7.5, 5.5))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        BLUE = '#1e3a5f'
        ax.plot(load_xs, load_ys, color=BLUE, linewidth=2.2, label='Loading')
        ax.scatter(load_x, load_y, color=BLUE, s=30, marker='D',
                   zorder=5, edgecolors='none')
        if unload_x:
            ax.plot(unload_xs, unload_ys, color=BLUE, linewidth=2.2,
                    label='Unloading')
            ax.scatter(unload_x, unload_y, color=BLUE, s=30, marker='D',
                       zorder=5, edgecolors='none')

        ax.xaxis.set_label_position('top')
        ax.xaxis.tick_top()
        ax.tick_params(bottom=False)
        ax.set_xlabel('Load (t/m\u00B2)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Cumulative Settlement (mm)', fontsize=10, fontweight='bold')
        ax.set_title('LOAD SETTLEMENT CURVE', fontsize=12, fontweight='bold', pad=12)

        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.4)
        ax.set_xlim(left=0)

        y_target = row['target_settlement'] or 0.0
        x_limit = row['allowable_load'] or 0.0
        y_max = max(load_y) if load_y else 10
        x_max = max(load_x) if load_x else 10

        y_pad = y_max * 0.1 or 1.0
        ax.set_ylim(y_max + y_pad, 0)
        if y_target and x_limit and y_max > y_target:
            ax.annotate('', xy=(0, y_target), xytext=(x_limit, y_target),
                        arrowprops=dict(arrowstyle='<->', color='red', lw=1.2))
            ax.text(x_max * 0.01, y_target + y_max * 0.03,
                    f'{y_target} mm Settlement',
                    fontsize=8, color='red', va='bottom')

            ax.annotate('', xy=(x_limit, y_target),
                        xytext=(x_limit, 0),
                        arrowprops=dict(arrowstyle='<->', color='red', lw=1.2))
            ax.text(x_limit + x_max * 0.02, y_target / 2,
                    'Allowable\nLoad', fontsize=8, color='red', ha='left',
                    va='center')

        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, facecolor='white')
        plt.close(fig)
        self.graph_image = base64.b64encode(buf.getvalue()).decode('utf-8')

    def action_recompute_all(self):
        for rec in self:

            for line in rec.loading_reading_ids:
                line._compute_split_dt()

            for line in rec.unloading_reading_ids:
                line._compute_split_dt()

            rec.sudo()._recompute_loading_summary()
            rec._compute_settlement_values()
            rec._compute_max_displacement()

    def _recompute_loading_summary(self):
        Summary = self.env['fst.lateral.pile.load.loading.summary'].sudo()
        for rec in self:
            Summary.search([('parent_id', '=', rec.id)]).unlink()

            def _group_lines(lines):
                result = []
                cur = None
                for line in lines:
                    if line.load_tonne != cur:
                        cur = line.load_tonne
                        result.append((cur, []))
                    result[-1][1].append(line)
                return result

            loading_groups = _group_lines(rec.loading_reading_ids.sorted('reading_datetime'))
            unloading_groups = _group_lines(rec.unloading_reading_ids.sorted('reading_datetime'))

            seq = 0
            running_cum = 0.0
            prev_vals = None
            for load_val, group in loading_groups:
                first_vals = None
                last_vals = None
                for line in group:
                    vals = [line.dial_a, line.dial_b, line.dial_c]
                    if all(v is not None and v is not False for v in vals):
                        if first_vals is None:
                            first_vals = vals
                        last_vals = vals

                if first_vals and last_vals:
                    d1d2_avg = ((last_vals[0] - first_vals[0]) + (last_vals[1] - first_vals[1])) / 2.0
                    d3_diff = last_vals[2] - first_vals[2]
                    avg_raw = d1d2_avg + d3_diff
                    avg_settlement = round(avg_raw, 2)
                else:
                    avg_raw = 0.0
                    avg_settlement = 0.0

                if last_vals:
                    prev_vals = last_vals

                if avg_settlement == 0.0:
                    continue

                seq += 1
                running_cum += avg_raw

                Summary.create({
                    'parent_id': rec.id,
                    'sequence': seq,
                    'load_type': 'loading',
                    'load_tonne': load_val,
                    'avg_settlement': avg_settlement,
                    'cumulative_settlement': round(running_cum, 2),
                })

            for load_val, group in unloading_groups:
                first_vals = None
                last_vals = None
                for line in group:
                    vals = [line.dial_a, line.dial_b, line.dial_c]
                    if all(v is not None and v is not False for v in vals):
                        if first_vals is None:
                            first_vals = vals
                        last_vals = vals

                if first_vals and last_vals and prev_vals:
                    d1d2_avg = ((last_vals[0] - prev_vals[0]) + (last_vals[1] - prev_vals[1])) / 2.0
                    d3_diff = last_vals[2] - prev_vals[2]
                    avg_raw = d1d2_avg + d3_diff
                    avg_settlement = round(avg_raw, 2)
                else:
                    avg_raw = 0.0
                    avg_settlement = 0.0

                if last_vals:
                    prev_vals = last_vals

                if avg_settlement == 0.0:
                    continue

                seq += 1
                running_cum += avg_raw

                Summary.create({
                    'parent_id': rec.id,
                    'sequence': seq,
                    'load_type': 'unloading',
                    'load_tonne': load_val,
                    'avg_settlement': avg_settlement,
                    'cumulative_settlement': round(running_cum, 2),
                })

    def print_report(self):
        self.ensure_one()
        return self.env.ref('fst_lateral_pile_load.lateral_pile_load_report_py3o').report_action(self)

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
                line.copy({
                    'parent_id': new_parent.id,
                })

            for line in record.unloading_reading_ids:
                line.copy({
                    'parent_id': new_parent.id,
                })

            for line in record.content_ids:
                line.copy({
                    'parent_id': new_parent.id,
                })

            for line in record.basic_data_ids:
                line.copy({
                    'parent_id': new_parent.id,
                })

            for line in record.site_image_ids:
                line.copy({
                    'parent_id': new_parent.id,
                })

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


class FstLateralPileLoadReadingLoading(models.Model):
    _name = "fst.lateral.pile.load.reading.loading"
    _description = "Lateral Pile Load Reading - Loading"
    _order = "id"

    parent_id = fields.Many2one(
        "fst.lateral.pile.load.test",
        ondelete="cascade",
        required=True
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
    applied_pressure = fields.Float("Applied Pressure (kg/cm²)")
    pressure_under_plate = fields.Float("Pressure under plate (t/m²)")

    @api.onchange('applied_pressure')
    def _onchange_applied_pressure(self):
        for rec in self:
            if rec.applied_pressure:
                rec.load_tonne = round(rec.applied_pressure * 154.0 / 1000.0, 2)
                rec.pressure_under_plate = round(rec.load_tonne / 0.07, 2)

    @api.onchange('load_tonne')
    def _onchange_load_tonne(self):
        for rec in self:
            if rec.load_tonne:
                rec.applied_pressure = round(rec.load_tonne * 1000.0 / 154.0, 2)
                rec.pressure_under_plate = round(rec.load_tonne / 0.07, 2)

    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    dial_c = fields.Float("Dial C (mm)")

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
            parent._compute_max_displacement()
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'dial_a' in vals or 'dial_b' in vals or 'dial_c' in vals:
            for rec in self:
                if rec.parent_id:
                    parent = rec.parent_id.sudo()
                    parent._recompute_loading_summary()
                    parent._compute_settlement_values()
                    parent._compute_max_displacement()
        return res

    def unlink(self):
        parents = self.mapped('parent_id')
        res = super().unlink()
        for parent in parents:
            if parent:
                parent = parent.sudo()
                parent._recompute_loading_summary()
                parent._compute_settlement_values()
                parent._compute_max_displacement()
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


class FstLateralPileLoadReadingUnloading(models.Model):
    _name = "fst.lateral.pile.load.reading.unloading"
    _description = "Lateral Pile Load Reading - Unloading"
    _order = "id"

    parent_id = fields.Many2one(
        "fst.lateral.pile.load.test",
        ondelete="cascade",
        required=True
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
    applied_pressure = fields.Float("Applied Pressure (kg/cm²)")
    pressure_under_plate = fields.Float("Pressure under plate (t/m²)")
    dial_a = fields.Float("Dial A (mm)")
    dial_b = fields.Float("Dial B (mm)")
    dial_c = fields.Float("Dial C (mm)")

    @api.onchange('applied_pressure')
    def _onchange_applied_pressure(self):
        for rec in self:
            if rec.applied_pressure:
                rec.load_tonne = round(rec.applied_pressure * 154.0 / 1000.0, 2)
                rec.pressure_under_plate = round(rec.load_tonne / 0.07, 2)

    @api.onchange('load_tonne')
    def _onchange_load_tonne(self):
        for rec in self:
            if rec.load_tonne:
                rec.applied_pressure = round(rec.load_tonne * 1000.0 / 154.0, 2)
                rec.pressure_under_plate = round(rec.load_tonne / 0.07, 2)

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
            parent._compute_max_displacement()
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'dial_a' in vals or 'dial_b' in vals or 'dial_c' in vals:
            for rec in self:
                if rec.parent_id:
                    parent = rec.parent_id.sudo()
                    parent._recompute_loading_summary()
                    parent._compute_settlement_values()
                    parent._compute_max_displacement()
        return res

    def unlink(self):
        parents = self.mapped('parent_id')
        res = super().unlink()
        for parent in parents:
            if parent:
                parent = parent.sudo()
                parent._recompute_loading_summary()
                parent._compute_settlement_values()
                parent._compute_max_displacement()
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


class FstLateralPileLoadReportContent(models.Model):
    _name = "fst.lateral.pile.load.report.content"
    _description = "Report Contents"

    parent_id = fields.Many2one("fst.lateral.pile.load.test", ondelete="cascade")
    sequence = fields.Float("Sl. No")
    description = fields.Char("Description")
    page_no = fields.Char("Page No")


class FstLateralPileLoadBasicData(models.Model):
    _name = "fst.lateral.pile.load.basic.data"
    _description = "Lateral Pile Load Test Basic Data"

    parent_id = fields.Many2one("fst.lateral.pile.load.test", ondelete="cascade")
    sr_no = fields.Integer("Sl No")
    parameter = fields.Char("Parameter")
    value = fields.Char("Value")


class FstLateralPileLoadLoadingSummary(models.Model):
    _name = "fst.lateral.pile.load.loading.summary"
    _description = "Lateral Pile Load Test - Loading Summary"
    _order = "sequence, id"

    parent_id = fields.Many2one(
        "fst.lateral.pile.load.test",
        ondelete="cascade",
        required=True
    )
    sequence = fields.Integer("Sr No")
    load_type = fields.Selection([
        ('loading', 'Loading'),
        ('unloading', 'Unloading'),
    ], string="Stage", default='loading', required=True)
    load_tonne = fields.Float("Load on Plate (t)")
    avg_settlement = fields.Float("Average Settlement (mm)")
    cumulative_settlement = fields.Float("Cumulative Settlement (mm)")


class FstLateralPileLoadTestImage(models.Model):
    _name = "fst.lateral.pile.load.test.image"
    _description = "Lateral Pile Load Test Site Photograph"

    parent_id = fields.Many2one("fst.lateral.pile.load.test", ondelete="cascade")
    sequence = fields.Integer("Sr No", default=1)
    image = fields.Binary("Site Photograph")
    caption = fields.Char("Caption")
