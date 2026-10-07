"""Independent saved-result audit; no download or live-availability claim."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/baseline'
MODELS = ['persistence', 'historical', 'residual_baseline']


def verify(folder=FOLDER):
    o = pd.read_csv(folder / 'selected-observations.csv')
    m = pd.read_csv(folder / 'metrics.csv')
    a = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
    dates = ['20260827', '20260828', '20260831', '20260901', '20260902']
    assert a['train_dates'] == dates[:3]
    assert a['validation_date'] == dates[3] and a['test_date'] == dates[4]
    assert not o.isna().any().any(), 'missing observations'
    assert len(o) == 8640 and not o.duplicated(['link', 'timestamp']).any()
    assert sorted(o.link.unique()) == a['links'] and o.vehicle_type.eq(31).all()
    assert np.isfinite(o[['seconds', 'volume', 'valid_seconds']]).all().all()
    assert o.seconds.gt(0).all() and o.volume.gt(0).all()
    assert o.volume.mod(1).eq(0).all()
    assert np.allclose(o.seconds, o.valid_seconds), 'unexpected imputation'
    o['time'] = pd.to_datetime(o.timestamp)
    assert o.time.dt.strftime('%Y%m%d').astype(int).eq(o.date).all()
    assert (o.time.dt.hour * 12 + o.time.dt.minute // 5).eq(o.slot).all()
    for (link, date), g in o.groupby(['link', 'date']):
        expected = pd.date_range(str(date), periods=288, freq='5min')
        assert g.time.sort_values().tolist() == expected.tolist(), 'incomplete time grid'
    assert sorted(o.date.astype(str).unique()) == dates
    profile = o[o.date.astype(str).isin(dates[:3])].groupby(['link', 'slot']).seconds.mean()
    assert np.allclose(o.historical_now, [profile.loc[(l, s)] for l, s in zip(o.link, o.slot)])
    assert o.link.eq(o['from'] + '>' + o['to']).all()
    lookup = o.set_index(['link', 'time'])
    scores = {}
    assert len(m) == 12 and not m.duplicated(['horizon_minutes', 'model', 'period']).any()
    for horizon in [15, 30]:
        p = pd.read_csv(folder / f'predictions-{horizon}min.csv')
        assert not p.drop(columns=['alpha'], errors='ignore').isna().any().any()
        assert not p.duplicated(['link', 'timestamp']).any()
        origin = pd.to_datetime(p.timestamp)
        decision = pd.to_datetime(p.decision_time)
        end = pd.to_datetime(p.target_interval_end)
        target = end - pd.Timedelta(minutes=5)
        assert decision.eq(origin + pd.Timedelta(minutes=5)).all()
        assert end.eq(decision + pd.Timedelta(minutes=horizon)).all()
        assert target.eq(origin + pd.Timedelta(minutes=horizon)).all()
        assert origin.dt.strftime('%Y%m%d').eq(dates[4]).all()
        assert target.dt.strftime('%Y%m%d').eq(dates[4]).all()
        assert p.date.eq(int(dates[4])).all() and p.horizon_minutes.eq(horizon).all()
        assert p.target_slot.eq(target.dt.hour * 12 + target.dt.minute // 5).all()
        expected_keys = {(r.link, r.time) for r in o[o.date.eq(int(dates[4]))].itertuples()
                         if r.time + pd.Timedelta(minutes=horizon) < pd.Timestamp('2026-09-03')}
        assert set(zip(p.link, origin)) == expected_keys, 'unequal evaluation samples'
        now = np.array([lookup.loc[(l, t), 'seconds'] for l, t in zip(p.link, origin)])
        actual = np.array([lookup.loc[(l, t), 'seconds'] for l, t in zip(p.link, target)])
        hnow = np.array([profile.loc[(l, s)] for l, s in zip(p.link, p.slot)])
        hfuture = np.array([profile.loc[(l, s)] for l, s in zip(p.link, p.target_slot)])
        assert np.allclose(p.actual, actual)
        assert np.isfinite(p[MODELS + ['actual']]).all().all()
        assert np.allclose(p.seconds, now)
        assert np.allclose(p.volume, [lookup.loc[(l, t), 'volume'] for l, t in zip(p.link, origin)])
        assert p.slot.eq(origin.dt.hour * 12 + origin.dt.minute // 5).all()
        assert np.allclose(p.persistence, now) and np.allclose(p.valid_seconds, now)
        assert np.allclose(p.historical_now, hnow) and np.allclose(p.historical, hfuture)
        # Select alpha ONLY on validation date, independently of stored metrics.
        vrows = [r for r in o[o.date.eq(int(dates[3]))].itertuples()
                 if r.time + pd.Timedelta(minutes=horizon) < pd.Timestamp('2026-09-02')]
        vnow = np.array([r.seconds for r in vrows])
        vy = np.array([lookup.loc[(r.link, r.time + pd.Timedelta(minutes=horizon)), 'seconds'] for r in vrows])
        vh = np.array([profile.loc[(r.link, r.slot + horizon // 5)] for r in vrows])
        vn = np.array([profile.loc[(r.link, r.slot)] for r in vrows])
        errors = {alpha: float(np.abs(np.maximum(1, vh + alpha * (vnow - vn)) - vy).mean())
                  for alpha in [0, .25, .5, .75, 1]}
        alpha = min(errors, key=errors.get)
        assert np.allclose(p.residual_baseline, np.maximum(1, hfuture + alpha * (now - hnow)))
        scores[str(horizon)] = {'selected_alpha': alpha, 'validation_mae': errors}
        for model in MODELS:
            for period in ['all_day', 'commute']:
                row = m[(m.horizon_minutes == horizon) & (m.model == model) & (m.period == period)]
                assert len(row) == 1
                row = row.iloc[0]
                q = p if period == 'all_day' else p[origin.dt.hour.isin([7, 8, 9, 16, 17, 18, 19])]
                err = q[model] - q.actual
                assert len(q) == row.n
                assert np.isclose(abs(err).mean(), row.mae_seconds)
                assert np.isclose(np.sqrt((err ** 2).mean()), row.rmse_seconds)
                if model == 'residual_baseline':
                    assert row.alpha == alpha
        midnight = end.dt.hour.eq(0) & end.dt.minute.eq(0)
        assert midnight.sum() == 6
        assert target[midnight].dt.hour.eq(23).all()
    return {'status': 'passed', 'scope': 'saved CSV independently recomputed',
            'rows': len(o), 'validation_selection': scores,
            'availability': 'unknown; finalized data, assumed zero delay, no live claim',
            'hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(folder.glob('*')) if p.is_file()}}


if __name__ == '__main__':
    result = verify()
    output = ROOT / 'submission/evidence/saved-audit.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print('PASS: saved results; dates, grid, training-only means, validation-only alpha, all predictions, labels, horizons, midnight, 12 metric rows.')
