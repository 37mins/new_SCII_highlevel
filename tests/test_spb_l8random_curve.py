"""Small ledger projection must reject missing, duplicate or non-natural games."""
import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'experiments/records/20260921-sc2-policy-credit-v1/collect-spb-l8random-r2-curve.py'
spec=importlib.util.spec_from_file_location('spb_curve',path)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CurveTest(unittest.TestCase):
    def batch(self):
        return [dict(reset_index=0,env_index=i,terminated=True,truncated=False,
                     game_result='Victory' if i<5 else 'Defeat') for i in range(8)]

    def test_natural_batch(self):
        self.assertEqual(m.batch_rows(self.batch(),1,1),[dict(step=1,games=8,wins=5)])

    def test_missing_or_duplicate(self):
        a=self.batch();a[-1]['env_index']=0
        for rows in [a,self.batch()[:-1]]:
            with self.assertRaises(ValueError):m.batch_rows(rows,1,1)

    def test_unfinished_or_truncated(self):
        for key,value in [('terminated',False),('truncated',True),('game_result','unknown')]:
            a=self.batch();a[0][key]=value
            with self.assertRaises(ValueError):m.batch_rows(a,1,1)

    def test_wrong_reset(self):
        a=self.batch();a[0]['reset_index']=1
        with self.assertRaises(ValueError):m.batch_rows(a,1,1)


if __name__=='__main__':unittest.main()
