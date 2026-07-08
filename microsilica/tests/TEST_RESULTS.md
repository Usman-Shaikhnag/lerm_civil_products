Microsilica Test Results — infra_main
======================================
Date: 2026-07-08
Module: microsilica
Test File: tests/test_microsilica_formulas.py

Summary: 0 failed, 0 error(s) of 23 tests — ALL PASSED
Test Time: 0.39s (406 queries)

Test Log:
---------
PASS  TestMicrosilicaFormulas.test_avg_strength_by_age_14_days
PASS  TestMicrosilicaFormulas.test_avg_strength_by_age_28_days
PASS  TestMicrosilicaFormulas.test_avg_strength_by_age_7_days
PASS  TestMicrosilicaFormulas.test_compressive_strength_density
PASS  TestMicrosilicaFormulas.test_compressive_strength_formula_excel_7days
PASS  TestMicrosilicaFormulas.test_compressive_strength_line_auto_sr_no
PASS  TestMicrosilicaFormulas.test_cs_flow_percent
PASS  TestMicrosilicaFormulas.test_pozzolanic_index
PASS  TestMicrosilicaFormulas.test_pozzolanic_index_zero_when_control_zero
PASS  TestMicrosilicaFormulas.test_specific_gravity_average
PASS  TestMicrosilicaFormulas.test_specific_gravity_equal_vol_water
PASS  TestMicrosilicaFormulas.test_specific_gravity_line_auto_sr_no
PASS  TestMicrosilicaFormulas.test_specific_gravity_value_excel_trial1
PASS  TestMicrosilicaFormulas.test_specific_gravity_value_excel_trial2
PASS  TestMicrosilicaFormulas.test_specific_gravity_value_excel_trial3
PASS  TestMicrosilicaFormulas.test_specific_gravity_volume
PASS  TestMicrosilicaFormulas.test_tm_flow_percent
PASS  TestMicrosilicaFormulas.test_water_weight_formula
PASS  TestMicrosilicaFormulas.test_water_weight_zero_when_p_empty
PASS  TestMicrosilicaFormulas.test_wet_sieving_avg_percent_passing
PASS  TestMicrosilicaFormulas.test_wet_sieving_line_auto_sr_no
PASS  TestMicrosilicaFormulas.test_wet_sieving_percent_passing_excel_values
PASS  TestMicrosilicaFormulas.test_wet_sieving_weight_passing

Formulas Verified:
------------------
1. Wet Sieving (45 Micron):
   - % Passing = (Ws - Wr) / Ws * 100
   - Average of multiple trials
   - Auto SR NO increment

2. Compressive Strength (70.6mm cube):
   - Density (g/cc) = Weight / 7.06^3
   - Comp Strength (N/mm²) = Load(kN) * 1000 / 70.6^2
   - Per-age averages: 7 days, 14 days, 28 days
   - Auto SR NO increment

3. Specific Gravity (Water Displacement):
   - Volume of Silica = V2 - V1
   - Weight of Equal Vol Water = (V2 - V1) * 1.0
   - Sp. Gravity = W1 / Weight of Equal Vol Water
   - Average of 3 trials
   - Auto SR NO increment

4. Pozzolanic Activity Index:
   - Index = (Test Mixture Avg / Control Avg) * 100
   - Returns 0 when control avg is 0

5. Flow %:
   - % Flow = Average Measured - 100
   - Both test mixture and control sample

6. Water Weight:
   - Water Weight = P/4 + 3.0
   - Returns 0 when P is empty
