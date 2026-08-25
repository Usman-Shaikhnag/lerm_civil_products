from odoo.tests.common import TransactionCase
from datetime import datetime


class TestLoadingSummary(TransactionCase):

    def setUp(self):
        super().setUp()
        TestModel = self.env['fst.lateral.pile.load.test']
        LoadingReading = self.env['fst.lateral.pile.load.reading.loading']
        Summary = self.env['fst.lateral.pile.load.loading.summary']

        self.parent = TestModel.create({
            'name': 'Test Project',
            'rec_date': datetime.now(),
        })

        base = datetime(2023, 11, 29, 9, 0)

        # loading phase data matching TP-03 (5) sheet (formula: ((D1+D2)/2)+D3)
        data = [
            # (offset_min, load_tonne, dial_a, dial_b, dial_c)
            # load 3.08
            (0,    3.08,  0.17, 0.21, 0.13),
            (15,   3.08,  None, None, None),
            (30,   3.08,  0.69, 0.71, 0.80),
            # load 6.16
            (0,    6.16,  0.69, 0.71, 0.80),
            (15,   6.16,  None, None, None),
            (30,   6.16,  1.05, 1.17, 1.23),
            # load 9.24
            (0,    9.24,  1.05, 1.17, 1.23),
            (15,   9.24,  None, None, None),
            (30,   9.24,  1.81, 1.79, 1.60),
            # load 12.32
            (0,   12.32,  1.81, 1.79, 1.60),
            (15,  12.32,  None, None, None),
            (30,  12.32,  2.30, 2.34, 2.42),
            # load 14.63
            (0,   14.63,  2.30, 2.34, 2.42),
            (15,  14.63,  None, None, None),
            (30,  14.63,  3.35, 3.40, 3.72),
        ]

        for offset_min, load, a, b, c in data:
            if a is None and b is None and c is None:
                continue
            dt = self._offset_datetime(base, offset_min)
            LoadingReading.create({
                'parent_id': self.parent.id,
                'reading_datetime': dt,
                'load_tonne': load,
                'dial_a': a or 0.0,
                'dial_b': b or 0.0,
                'dial_c': c or 0.0,
            })

        self.parent._recompute_loading_summary()
        self.summaries = Summary.search([('parent_id', '=', self.parent.id)]).sorted('sequence')

    def _offset_datetime(self, base, offset_min):
        if offset_min == 0:
            return base
        if offset_min == 15:
            return base.replace(hour=9, minute=15)
        if offset_min == 30:
            return base.replace(hour=9, minute=30)
        return base.replace(hour=9, minute=int(offset_min))

    def test_summary_row_count(self):
        self.assertEqual(len(self.summaries), 5, "Should have 5 loading steps")

    def test_step1_load_3_08(self):
        s = self.summaries[0]
        self.assertEqual(s.load_tonne, 3.08)
        self.assertEqual(s.avg_settlement, 1.18)
        self.assertEqual(s.cumulative_settlement, 1.18)

    def test_step2_load_6_16(self):
        s = self.summaries[1]
        self.assertEqual(s.load_tonne, 6.16)
        self.assertEqual(s.avg_settlement, 0.84)
        self.assertEqual(s.cumulative_settlement, 2.02)

    def test_step3_load_9_24(self):
        s = self.summaries[2]
        self.assertEqual(s.load_tonne, 9.24)
        self.assertEqual(s.avg_settlement, 1.06)
        self.assertEqual(s.cumulative_settlement, 3.08)

    def test_step4_load_12_32(self):
        s = self.summaries[3]
        self.assertEqual(s.load_tonne, 12.32)
        self.assertEqual(s.avg_settlement, 1.34)
        self.assertEqual(s.cumulative_settlement, 4.42)

    def test_step5_load_14_63(self):
        s = self.summaries[4]
        self.assertEqual(s.load_tonne, 14.63)
        self.assertEqual(s.avg_settlement, 2.36)
        self.assertEqual(s.cumulative_settlement, 6.78)

    def test_loading_summary_auto_recomputes_on_create(self):
        LoadingReading = self.env['fst.lateral.pile.load.reading.loading']
        Summary = self.env['fst.lateral.pile.load.loading.summary']

        base = datetime(2023, 11, 29, 10, 0)
        LoadingReading.create({
            'parent_id': self.parent.id,
            'reading_datetime': base,
            'load_tonne': 25.0,
            'dial_a': 5.0,
            'dial_b': 5.0,
            'dial_c': 5.0,
        })

        summaries = Summary.search([('parent_id', '=', self.parent.id)]).sorted('sequence')
        self.assertEqual(len(summaries), 6)
        last = summaries[-1]
        self.assertEqual(last.load_tonne, 25.0)

    def test_loading_summary_auto_recomputes_on_write(self):
        LoadingReading = self.env['fst.lateral.pile.load.reading.loading']
        Summary = self.env['fst.lateral.pile.load.loading.summary']

        line = LoadingReading.search([
            ('parent_id', '=', self.parent.id),
            ('load_tonne', '=', 3.85),
        ], order='reading_datetime', limit=1)
        line.write({'dial_a': 0.5})

        summaries = Summary.search([('parent_id', '=', self.parent.id)]).sorted('sequence')
        first = summaries[0]
        self.assertNotEqual(first.avg_settlement, 1.18)

    def test_loading_summary_auto_recomputes_on_unlink(self):
        LoadingReading = self.env['fst.lateral.pile.load.reading.loading']
        Summary = self.env['fst.lateral.pile.load.loading.summary']

        line = LoadingReading.search([
            ('parent_id', '=', self.parent.id),
        ], order='id', limit=1)
        line.unlink()

        summaries = Summary.search([('parent_id', '=', self.parent.id)])
        self.assertEqual(len(summaries), 5, "Summary should still exist (no load group was fully removed)")
