"""The forensic reader must not manufacture acceptance from incomplete metrics."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1/inspect_spb_l8random_r2.py'
spec = importlib.util.spec_from_file_location('recovery_inspection', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(step=3, grad='1.2345678901234567', marker='binary64-v1'):
    return (f'step:{step} - metrics_precision:{marker} - actor/grad_norm:{grad} - '
            'timing_s/update_actor:8.5 - policy_credit/invalid_advantage_max:0 - '
            f'episode/valid_action_ratio:1 - episode/success_rate:0.625 - training/global_step:{step}\n')


class InspectionTest(unittest.TestCase):
    def inspect(self, text, lo=3, hi=3):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'console.log'
            p.write_text(text)
            original = p.read_bytes()
            value = m.returned_rows(p, lo, hi)
            self.assertEqual(p.read_bytes(), original)
            self.assertEqual([x.name for x in Path(d).iterdir()], ['console.log'])
            return value

    def test_full_precision_read_only(self):
        result = self.inspect('irrelevant output\n'+row())
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['actor/grad_norm'], float('1.2345678901234567'))
        self.assertEqual(result['selected_bytes'], len(row().encode()))

    def test_missing(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.inspect(row(), hi=4)

    def test_duplicate(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.inspect(row()+row())

    def test_precision(self):
        with self.assertRaisesRegex(ValueError, 'Precision'):
            self.inspect(row(marker='legacy'))

    def test_nonfinite_or_nonpositive(self):
        for grad in ['nan','inf','0','-1']:
            with self.subTest(grad=grad), self.assertRaises(ValueError):
                self.inspect(row(grad=grad))

    def test_unknown_nonfinite_metric_not_filtered_out(self):
        with self.assertRaisesRegex(ValueError, 'Nonfinite'):
            self.inspect(row().strip()+' - other/metric:nan\n')

    def test_line_bound(self):
        with self.assertRaisesRegex(ValueError, 'line exceeds'):
            self.inspect('x'*(256*1024+1)+'\n'+row())

    def test_small_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'state'
            p.write_text('{}')
            link = Path(d)/'link'
            link.symlink_to(p)
            with self.assertRaisesRegex(ValueError, 'regular file'):
                m.small_bytes(link)


if __name__ == '__main__':
    unittest.main()
