"""Independent recomputation from saved outputs, including boundary checks."""
from pathlib import Path
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1] / 'data' / 'baseline'
observations = pd.read_csv(root / 'selected-observations.csv')
metrics = pd.read_csv(root / 'metrics.csv')
assert len(observations) == 8640
assert observations.groupby(['link','date']).size().eq(288).all()
for horizon in [15,30]:
    p = pd.read_csv(root / f'predictions-{horizon}min.csv')
    decision = pd.to_datetime(p.decision_time)
    target = pd.to_datetime(p.target_interval_end)
    assert (target-decision).eq(pd.Timedelta(minutes=horizon)).all()
    assert decision.dt.date.eq(target.dt.date).all() or target.dt.hour.eq(0).any()
    # Interval starts, rather than ends at midnight, determine the split.
    origin = pd.to_datetime(p.timestamp)
    target_start = target-pd.Timedelta(minutes=5)
    assert origin.dt.strftime('%Y%m%d').eq('20260902').all()
    assert target_start.dt.strftime('%Y%m%d').eq('20260902').all()
    joined = p.merge(observations[['timestamp','link','valid_seconds']], left_on=['link','timestamp'], right_on=['link','timestamp'], suffixes=('','_source'))
    assert len(joined) == len(p)
    assert np.allclose(joined.persistence, joined.valid_seconds_source)
    actual = observations.assign(target_time=pd.to_datetime(observations.timestamp)).set_index(['link','target_time']).valid_seconds
    recovered = [actual.loc[(link,t)] for link,t in zip(p.link,target_start)]
    assert np.allclose(p.actual, recovered)
    for row in metrics[metrics.horizon_minutes==horizon].itertuples():
        q = p if row.period=='all_day' else p[origin.dt.hour.isin([7,8,9,16,17,18,19])]
        err = q[row.model]-q.actual
        assert len(q)==row.n
        assert np.isclose(abs(err).mean(),row.mae_seconds)
        assert np.isclose(np.sqrt((err**2).mean()),row.rmse_seconds)
print('Verified: complete selected five-minute grid; test-date boundaries; horizon alignment; labels recovered from observations; persistence inputs; all MAE/RMSE/sample counts.')
