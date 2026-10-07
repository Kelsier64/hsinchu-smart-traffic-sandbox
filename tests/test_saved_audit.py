"""Mutation tests prove that the independent audit rejects key evidence defects."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_baseline import verify


class SavedAuditTests(unittest.TestCase):
    def reject(self, filename, change):
        (ROOT / 'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp', prefix='audit-test-') as td:
            target = Path(td)
            for p in (ROOT / 'data/baseline').iterdir():
                shutil.copy2(p, target / p.name)
            frame = pd.read_csv(target / filename)
            change(frame)
            frame.to_csv(target / filename, index=False)
            with self.assertRaises(AssertionError):
                verify(target)

    def test_historical_mean_corruption(self):
        self.reject('selected-observations.csv', lambda d: d.__setitem__('historical_now', d.historical_now + 1))

    def test_future_label_misalignment(self):
        self.reject('predictions-15min.csv', lambda d: d.__setitem__('actual', d.actual.shift(1).fillna(1)))

    def test_missing_evaluation_row(self):
        self.reject('predictions-30min.csv', lambda d: d.drop(index=d.index[-1], inplace=True))

    def test_midnight_rollover_corruption(self):
        self.reject('predictions-30min.csv', lambda d: d.__setitem__('target_interval_end', d.target_interval_end.str.replace('2026-09-03', '2026-09-02')))

    def test_wrong_coefficient(self):
        self.reject('metrics.csv', lambda d: d.loc.__setitem__((d.model.eq('residual_baseline'), 'alpha'), 1))
