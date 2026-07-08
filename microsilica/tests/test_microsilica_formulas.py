from odoo.tests.common import TransactionCase


class TestMicrosilicaFormulas(TransactionCase):
    """Verify all computed formulas match Silica.xlsx expected values."""

    # === Wet Sieving (45 Micron) ===

    def test_wet_sieving_weight_passing(self):
        """% Passing = (Ws - Wr) / Ws * 100"""
        trial = self.env['microsilica.wet.sieving.line'].create({
            'sample_weight': 100.0,
            'weight_retained': 96.0,
        })
        self.assertAlmostEqual(trial.weight_passing, 4.0, places=2)
        self.assertAlmostEqual(trial.percent_passing, 4.0, places=2)

    def test_wet_sieving_percent_passing_excel_values(self):
        """Excel: Ws=100, Wr=96 => passing=4, %passing=4"""
        trial = self.env['microsilica.wet.sieving.line'].create({
            'sample_weight': 100.0,
            'weight_retained': 96.0,
        })
        self.assertAlmostEqual(trial.weight_passing, 4.0, places=2)
        self.assertAlmostEqual(trial.percent_passing, 4.0, places=2)

    def test_wet_sieving_avg_percent_passing(self):
        """Average of % passing across trials"""
        parent = self._create_main_record()
        self.env['microsilica.wet.sieving.line'].create({
            'parent_id': parent.id,
            'sample_weight': 100.0,
            'weight_retained': 2.0,
        })
        self.env['microsilica.wet.sieving.line'].create({
            'parent_id': parent.id,
            'sample_weight': 100.0,
            'weight_retained': 4.0,
        })
        self.env['microsilica.wet.sieving.line'].create({
            'parent_id': parent.id,
            'sample_weight': 100.0,
            'weight_retained': 3.0,
        })
        parent._compute_avg_percent_passing()
        expected_avg = ((98.0 + 96.0 + 97.0) / 3)
        self.assertAlmostEqual(parent.avg_percent_passing, expected_avg, places=2)

    # === Compressive Strength ===

    def test_compressive_strength_density(self):
        """Density = weight / (7.06^3) per Excel"""
        vol = 7.06 ** 3
        line = self.env['microsilica.compressive.strength.line'].create({
            'weight_g': 185.0,
        })
        expected = 185.0 / vol
        self.assertAlmostEqual(line.density_g_cc, expected, places=4)

    def test_compressive_strength_formula_excel_7days(self):
        """Excel: C12=185, E12=18 => D12=185/7.06^3, F12=18*1000/70.6^2"""
        vol = 7.06 ** 3
        area = 70.6 ** 2
        line = self.env['microsilica.compressive.strength.line'].create({
            'weight_g': 185.0,
            'load_kN': 18.0,
        })
        self.assertAlmostEqual(line.density_g_cc, 185.0 / vol, places=4)
        self.assertAlmostEqual(line.comp_strength, 18.0 * 1000.0 / area, places=2)

    def test_avg_strength_by_age_7_days(self):
        """Average of 3 samples at 7 days"""
        parent = self._create_main_record()
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '7',
            'weight_g': 185.0,
            'load_kN': 18.0,
        })
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '7',
            'weight_g': 188.0,
            'load_kN': 20.0,
        })
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '7',
            'weight_g': 190.0,
            'load_kN': 19.0,
        })
        parent._compute_avg_strength_by_age()
        area = 70.6 ** 2
        s1 = 18.0 * 1000.0 / area
        s2 = 20.0 * 1000.0 / area
        s3 = 19.0 * 1000.0 / area
        expected_avg = (s1 + s2 + s3) / 3
        self.assertAlmostEqual(parent.avg_7_strength, expected_avg, places=2)

    def test_avg_strength_by_age_14_days(self):
        """Average of 3 samples at 14 days"""
        parent = self._create_main_record()
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '14',
            'weight_g': 186.0,
            'load_kN': 24.0,
        })
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '14',
            'weight_g': 189.0,
            'load_kN': 26.0,
        })
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '14',
            'weight_g': 191.0,
            'load_kN': 25.0,
        })
        parent._compute_avg_strength_by_age()
        area = 70.6 ** 2
        s1 = 24.0 * 1000.0 / area
        s2 = 26.0 * 1000.0 / area
        s3 = 25.0 * 1000.0 / area
        expected_avg = (s1 + s2 + s3) / 3
        self.assertAlmostEqual(parent.avg_14_strength, expected_avg, places=2)

    def test_avg_strength_by_age_28_days(self):
        """Average of 3 samples at 28 days"""
        parent = self._create_main_record()
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '28',
            'weight_g': 187.0,
            'load_kN': 30.0,
        })
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '28',
            'weight_g': 190.0,
            'load_kN': 32.0,
        })
        self.env['microsilica.compressive.strength.line'].create({
            'parent_id': parent.id,
            'age_days': '28',
            'weight_g': 192.0,
            'load_kN': 31.0,
        })
        parent._compute_avg_strength_by_age()
        area = 70.6 ** 2
        s1 = 30.0 * 1000.0 / area
        s2 = 32.0 * 1000.0 / area
        s3 = 31.0 * 1000.0 / area
        expected_avg = (s1 + s2 + s3) / 3
        self.assertAlmostEqual(parent.avg_28_strength, expected_avg, places=2)

    def test_water_weight_formula(self):
        """Water weight = P/4 + 3.0 per Excel"""
        parent = self._create_main_record()
        parent.std_consistency_p = 28.0
        parent._compute_water_weight_cs()
        self.assertAlmostEqual(parent.water_weight_cs, 28.0 / 4.0 + 3.0, places=2)

    def test_water_weight_zero_when_p_empty(self):
        parent = self._create_main_record()
        parent.std_consistency_p = 0.0
        parent._compute_water_weight_cs()
        self.assertEqual(parent.water_weight_cs, 0.0)

    # === Specific Gravity ===

    def test_specific_gravity_volume(self):
        """Volume = V2 - V1"""
        line = self.env['microsilica.specific.gravity.line'].create({
            'w1_microsilica': 64.0,
            'v1_initial': 0.0,
            'v2_final': 20.31,
        })
        self.assertAlmostEqual(line.volume_silica, 20.31, places=2)

    def test_specific_gravity_equal_vol_water(self):
        """Weight of equal vol water = (V2-V1) * 1.0"""
        line = self.env['microsilica.specific.gravity.line'].create({
            'w1_microsilica': 64.0,
            'v1_initial': 0.0,
            'v2_final': 20.31,
        })
        self.assertAlmostEqual(line.wt_equal_vol_water, 20.31, places=2)

    def test_specific_gravity_value_excel_trial1(self):
        """Excel Trial 1: W1=64, V1=0, V2=20.31 => SG = 64/20.31"""
        line = self.env['microsilica.specific.gravity.line'].create({
            'w1_microsilica': 64.0,
            'v1_initial': 0.0,
            'v2_final': 20.31,
        })
        expected = 64.0 / 20.31
        self.assertAlmostEqual(line.spe_gravt_microsilica, expected, places=4)

    def test_specific_gravity_value_excel_trial2(self):
        """Excel Trial 2: W1=64, V1=0, V2=20.35 => SG = 64/20.35"""
        line = self.env['microsilica.specific.gravity.line'].create({
            'w1_microsilica': 64.0,
            'v1_initial': 0.0,
            'v2_final': 20.35,
        })
        expected = 64.0 / 20.35
        self.assertAlmostEqual(line.spe_gravt_microsilica, expected, places=4)

    def test_specific_gravity_value_excel_trial3(self):
        """Excel Trial 3: W1=64, V1=0, V2=20.4 => SG = 64/20.4"""
        line = self.env['microsilica.specific.gravity.line'].create({
            'w1_microsilica': 64.0,
            'v1_initial': 0.0,
            'v2_final': 20.4,
        })
        expected = 64.0 / 20.4
        self.assertAlmostEqual(line.spe_gravt_microsilica, expected, places=4)

    def test_specific_gravity_average(self):
        """Average SG of 3 trials"""
        parent = self._create_main_record()
        self.env['microsilica.specific.gravity.line'].create({
            'parent_id': parent.id,
            'w1_microsilica': 64.0,
            'v1_initial': 0.0,
            'v2_final': 20.31,
        })
        self.env['microsilica.specific.gravity.line'].create({
            'parent_id': parent.id,
            'w1_microsilica': 64.0,
            'v1_initial': 0.0,
            'v2_final': 20.35,
        })
        self.env['microsilica.specific.gravity.line'].create({
            'parent_id': parent.id,
            'w1_microsilica': 64.0,
            'v1_initial': 0.0,
            'v2_final': 20.4,
        })
        parent._compute_specific_gravity_avrg()
        expected = ((64.0 / 20.31) + (64.0 / 20.35) + (64.0 / 20.4)) / 3
        self.assertAlmostEqual(parent.specific_gravity_avrg, expected, places=4)

    # === Pozzolanic Activity Index ===

    def test_pozzolanic_index(self):
        """Index = (test_mixture_avg / control_avg) * 100"""
        parent = self._create_main_record()
        parent.tm_avg_7days = 25.50
        parent.cs_avg_7days = 30.00
        parent._compute_pozzolanic_index()
        expected = (25.50 / 30.00) * 100
        self.assertAlmostEqual(parent.pozzolanic_index, expected, places=2)

    def test_pozzolanic_index_zero_when_control_zero(self):
        parent = self._create_main_record()
        parent.tm_avg_7days = 25.50
        parent.cs_avg_7days = 0.0
        parent._compute_pozzolanic_index()
        self.assertEqual(parent.pozzolanic_index, 0.0)

    # === Pozzolanic — Test Mixture Flow ===

    def test_tm_flow_percent(self):
        """% Flow = average_measured - 100"""
        parent = self._create_main_record()
        parent.tm_measured_val1 = 105.0
        parent.tm_measured_val2 = 108.0
        parent.tm_measured_val3 = 107.0
        parent.tm_measured_val4 = 106.0
        parent._compute_tm_avg_measured()
        parent._compute_tm_flow()
        expected_avg = (105.0 + 108.0 + 107.0 + 106.0) / 4
        self.assertAlmostEqual(parent.tm_avg_measured, expected_avg, places=2)
        self.assertAlmostEqual(parent.tm_percent_flow, expected_avg - 100, places=2)

    def test_cs_flow_percent(self):
        """% Flow = average_measured - 100"""
        parent = self._create_main_record()
        parent.cs_measured_val1 = 102.0
        parent.cs_measured_val2 = 104.0
        parent.cs_measured_val3 = 103.0
        parent.cs_measured_val4 = 105.0
        parent._compute_cs_avg_measured()
        parent._compute_cs_flow()
        expected_avg = (102.0 + 104.0 + 103.0 + 105.0) / 4
        self.assertAlmostEqual(parent.cs_avg_measured, expected_avg, places=2)
        self.assertAlmostEqual(parent.cs_percent_flow, expected_avg - 100, places=2)

    # === Line auto-increment SR NO ===

    def test_wet_sieving_line_auto_sr_no(self):
        parent = self._create_main_record()
        a = self.env['microsilica.wet.sieving.line'].create({'parent_id': parent.id})
        b = self.env['microsilica.wet.sieving.line'].create({'parent_id': parent.id})
        c = self.env['microsilica.wet.sieving.line'].create({'parent_id': parent.id})
        self.assertEqual(a.sr_no, 1)
        self.assertEqual(b.sr_no, 2)
        self.assertEqual(c.sr_no, 3)

    def test_compressive_strength_line_auto_sr_no(self):
        parent = self._create_main_record()
        a = self.env['microsilica.compressive.strength.line'].create({'parent_id': parent.id})
        b = self.env['microsilica.compressive.strength.line'].create({'parent_id': parent.id})
        self.assertEqual(a.sr_no, 1)
        self.assertEqual(b.sr_no, 2)

    def test_specific_gravity_line_auto_sr_no(self):
        parent = self._create_main_record()
        a = self.env['microsilica.specific.gravity.line'].create({'parent_id': parent.id})
        b = self.env['microsilica.specific.gravity.line'].create({'parent_id': parent.id})
        self.assertEqual(a.sr_no, 1)
        self.assertEqual(b.sr_no, 2)

    # === Helpers ===

    def _create_main_record(self):
        return self.env['mechanical.microsilica'].create({})
