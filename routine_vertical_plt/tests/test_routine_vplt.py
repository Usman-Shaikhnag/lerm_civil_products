from odoo.tests.common import TransactionCase
from datetime import datetime


class TestRoutineVplt(TransactionCase):

    def setUp(self):
        super().setUp()
        self.parent = self.env['routine.vplt.test'].create({
            'name': 'Test Project',
            'pile_no': '240',
            'pile_diameter': 750.0,
            'safe_load': 200.0,
            'test_load': 300.0,
            'rec_date': datetime.now(),
        })

    # === Mean computation (4 dial gauges) ===

    def test_loading_mean_computation(self):
        line = self.env['routine.vplt.reading.loading'].create({
            'parent_id': self.parent.id,
            'load_tonne': 40,
            'dial_a': 0.41,
            'dial_b': 0.37,
            'dial_c': 0.40,
            'dial_d': 0.34,
        })
        expected = round((0.41 + 0.37 + 0.40 + 0.34) / 4, 2)
        self.assertAlmostEqual(line.mean_mm, expected, places=2)

    def test_unloading_mean_computation(self):
        line = self.env['routine.vplt.reading.unloading'].create({
            'parent_id': self.parent.id,
            'load_tonne': 280,
            'dial_a': 4.04,
            'dial_b': 4.10,
            'dial_c': 4.02,
            'dial_d': 4.14,
        })
        expected = round((4.04 + 4.10 + 4.02 + 4.14) / 4, 2)
        self.assertAlmostEqual(line.mean_mm, expected, places=2)

    # === 2% diameter ===

    def test_two_percent_dia(self):
        self.parent._compute_two_percent_dia()
        self.assertAlmostEqual(self.parent.two_percent_dia, 15.0, places=2)

    def test_two_percent_dia_zero_when_no_diameter(self):
        r = self.env['routine.vplt.test'].create({'name': 'No Dia'})
        self.assertEqual(r.two_percent_dia, 0.0)

    # === Criterion (12 or 18 mm) ===

    def test_criterion_18_for_dia_above_600(self):
        r = self.env['routine.vplt.test'].create({
            'name': 'Test',
            'pile_diameter': 750.0,
        })
        self.assertAlmostEqual(r.criterion_18_or_12, 18.0, places=2)

    def test_criterion_12_for_dia_600_or_below(self):
        r = self.env['routine.vplt.test'].create({
            'name': 'Test',
            'pile_diameter': 600.0,
        })
        self.assertAlmostEqual(r.criterion_18_or_12, 12.0, places=2)

        r2 = self.env['routine.vplt.test'].create({
            'name': 'Test2',
            'pile_diameter': 450.0,
        })
        self.assertAlmostEqual(r2.criterion_18_or_12, 12.0, places=2)

    # === Min A,B ===

    def test_min_ab(self):
        self.parent._compute_two_percent_dia()
        self.parent._compute_criterion()
        self.parent._compute_min_ab()
        self.assertAlmostEqual(self.parent.min_a_b, 15.0, places=2)

    # === Settlement values from loading/unloading means ===

    def test_settlement_from_loading_means(self):
        self.env['routine.vplt.loading.mean'].create({
            'parent_id': self.parent.id,
            'seq': 1, 'load_number': 'L1',
            'loading_mean': 0.0, 'load_value_tonne': 0,
        })
        self.env['routine.vplt.loading.mean'].create({
            'parent_id': self.parent.id,
            'seq': 9, 'load_number': 'L9',
            'loading_mean': 4.18, 'load_value_tonne': 300,
        })

        self.env['routine.vplt.unloading.mean'].create({
            'parent_id': self.parent.id,
            'seq': 1, 'unload_number': 'U1',
            'unloading_mean': 3.04, 'load_value_tonne': 0,
        })

        self.parent._compute_settlement_values()

        self.assertAlmostEqual(self.parent.gross_settlement, 4.18, places=2)
        self.assertAlmostEqual(self.parent.rebound, 3.04, places=2)
        self.assertAlmostEqual(self.parent.net_settlement, 1.14, places=2)

    def test_settlement_fallback_to_raw_readings(self):
        self.env['routine.vplt.reading.loading'].create({
            'parent_id': self.parent.id,
            'load_tonne': 0, 'dial_a': 0, 'dial_b': 0,
            'dial_c': 0, 'dial_d': 0,
        })
        self.env['routine.vplt.reading.loading'].create({
            'parent_id': self.parent.id,
            'load_tonne': 300, 'dial_a': 4.15, 'dial_b': 4.20,
            'dial_c': 4.15, 'dial_d': 4.22,
        })
        self.env['routine.vplt.reading.unloading'].create({
            'parent_id': self.parent.id,
            'load_tonne': 0, 'dial_a': 3.09, 'dial_b': 3.11,
            'dial_c': 3.01, 'dial_d': 2.94,
        })

        self.parent._compute_settlement_values()

        self.assertAlmostEqual(self.parent.gross_settlement, 4.18, places=2)
        self.assertAlmostEqual(self.parent.rebound, 3.04, places=2)
        self.assertAlmostEqual(self.parent.net_settlement, 1.14, places=2)

    # === Percent Rebound ===

    def test_percent_rebound(self):
        self.parent.gross_settlement = 4.18
        self.parent.rebound = 1.14
        self.parent._compute_percent_rebound()
        self.assertAlmostEqual(self.parent.percent_rebound, 27.27, places=2)

    def test_percent_rebound_zero_when_no_gross(self):
        r = self.env['routine.vplt.test'].create({'name': 'Test'})
        self.assertEqual(r.percent_rebound, 0.0)

    # === Max settlement ===

    def test_max_settlement(self):
        self.env['routine.vplt.reading.loading'].create({
            'parent_id': self.parent.id,
            'load_tonne': 40, 'dial_a': 1, 'dial_b': 1,
            'dial_c': 1, 'dial_d': 1,
        })
        self.env['routine.vplt.reading.unloading'].create({
            'parent_id': self.parent.id,
            'load_tonne': 0, 'dial_a': 5, 'dial_b': 5,
            'dial_c': 5, 'dial_d': 5,
        })
        self.parent._compute_max_settlement()
        self.assertAlmostEqual(self.parent.max_settlement, 5.0, places=2)

    # === Interpolated loads at 15mm and 18mm ===

    def test_interpolated_load_at_15mm(self):
        self.parent.gross_settlement = 4.18
        self.parent.test_load = 300.0
        self.parent._compute_interpolated_loads()
        # slope = 300/4.18 = 71.77, load at 15mm = 15 * 71.77 = 1076.55
        expected = round(15.0 * (300.0 / 4.18), 2)
        self.assertAlmostEqual(self.parent.settlement_15mm_interpolated, expected, places=2)
        self.assertAlmostEqual(self.parent.settlement_15mm_interpolated, 1076.55, places=2)

    def test_interpolated_load_at_18mm(self):
        self.parent.gross_settlement = 4.18
        self.parent.test_load = 300.0
        self.parent._compute_interpolated_loads()
        expected = round(18.0 * (300.0 / 4.18), 2)
        self.assertAlmostEqual(self.parent.settlement_18mm_interpolated, expected, places=2)
        self.assertAlmostEqual(self.parent.settlement_18mm_interpolated, 1291.86, places=2)

    def test_interpolated_loads_zero_when_no_gross(self):
        r = self.env['routine.vplt.test'].create({'name': 'Test'})
        self.assertEqual(r.settlement_15mm_interpolated, 0.0)
        self.assertEqual(r.settlement_18mm_interpolated, 0.0)

    # === Date string formatting ===

    def test_rec_date_str(self):
        from datetime import date
        r = self.env['routine.vplt.test'].create({
            'name': 'Date Test',
            'rec_date': date(2026, 6, 12),
        })
        self.assertEqual(r.rec_date_str, '12-06-2026')

    def test_rec_date_str_false_when_no_date(self):
        r = self.env['routine.vplt.test'].create({'name': 'No Date'})
        self.assertFalse(r.rec_date_str)

    # === Duplicate ===

    def test_duplicate_creates_new_record(self):
        self.env['routine.vplt.reading.loading'].create({
            'parent_id': self.parent.id,
            'load_tonne': 40, 'dial_a': 0.41, 'dial_b': 0.37,
            'dial_c': 0.40, 'dial_d': 0.34,
        })
        self.parent.action_duplicate_parent()
        copies = self.env['routine.vplt.test'].search([
            ('name', '=', 'Test Project Copy')
        ])
        self.assertEqual(len(copies), 1)
        self.assertEqual(len(copies.loading_reading_ids), 1)
        self.assertFalse(copies.graph_image)

    # === Delete ===

    def test_delete_line(self):
        self.parent.action_delete_line()
        self.assertFalse(self.parent.exists())

    # === Loading mean model ===

    def test_loading_mean_creation(self):
        mean = self.env['routine.vplt.loading.mean'].create({
            'parent_id': self.parent.id,
            'seq': 1,
            'load_number': 'L1',
            'loading_mean': 0.0,
            'load_value_tonne': 0,
        })
        self.assertEqual(mean.seq, 1)
        self.assertEqual(mean.load_number, 'L1')

    # === Unloading mean model ===

    def test_unloading_mean_creation(self):
        mean = self.env['routine.vplt.unloading.mean'].create({
            'parent_id': self.parent.id,
            'seq': 9,
            'unload_number': 'U9',
            'unloading_mean': 4.18,
            'load_value_tonne': 300,
        })
        self.assertEqual(mean.seq, 9)
        self.assertEqual(mean.unload_number, 'U9')

    # === Reading datetime auto-increment ===

    def test_loading_reading_datetime_auto(self):
        d0 = datetime(2026, 5, 20, 16, 0, 0)
        d1 = self.env['routine.vplt.reading.loading'].create({
            'parent_id': self.parent.id,
            'reading_datetime': d0,
        })
        d2 = self.env['routine.vplt.reading.loading'].create({
            'parent_id': self.parent.id,
        })
        expected = d0.replace(minute=15)
        self.assertEqual(d2.reading_datetime, expected)

    # === Full Excel matching test ===

    def test_exact_excel_values(self):
        loading_data = [
            (0, 0, 'L1', 0.0, 0),
            (0.47, 40, 'L2', 0.47, 40),
            (0.95, 80, 'L3', 0.95, 80),
            (1.37, 120, 'L4', 1.37, 120),
            (1.84, 160, 'L5', 1.84, 160),
            (2.20, 200, 'L6', 2.20, 200),
            (2.93, 240, 'L7', 2.93, 240),
            (3.43, 280, 'L8', 3.43, 280),
            (4.18, 300, 'L9', 4.18, 300),
        ]

        for i, (mean, load, num, mval, lval) in enumerate(loading_data, 1):
            self.env['routine.vplt.loading.mean'].create({
                'parent_id': self.parent.id,
                'seq': i,
                'load_number': num,
                'loading_mean': mean,
                'load_value_tonne': load,
            })

        unloading_data = [
            (3.04, 0, 'U1'),
            (3.13, 40, 'U2'),
            (3.23, 80, 'U3'),
            (3.40, 120, 'U4'),
            (3.58, 160, 'U5'),
            (3.77, 200, 'U6'),
            (3.95, 240, 'U7'),
            (4.08, 280, 'U8'),
            (4.18, 300, 'U9'),
        ]

        for i, (mean, load, num) in enumerate(unloading_data, 1):
            self.env['routine.vplt.unloading.mean'].create({
                'parent_id': self.parent.id,
                'seq': i,
                'unload_number': num,
                'unloading_mean': mean,
                'load_value_tonne': load,
            })

        self.parent._compute_settlement_values()
        self.parent._compute_percent_rebound()
        self.parent._compute_interpolated_loads()

        self.assertAlmostEqual(self.parent.gross_settlement, 4.18, places=2)
        self.assertAlmostEqual(self.parent.net_settlement, 1.14, places=2)
        self.assertAlmostEqual(self.parent.rebound, 3.04, places=2)
        self.assertAlmostEqual(self.parent.percent_rebound, 27.27, places=2)
        self.assertAlmostEqual(self.parent.settlement_15mm_interpolated, 1076.55, places=2)
        self.assertAlmostEqual(self.parent.settlement_18mm_interpolated, 1291.86, places=2)
