"""Exploratory offline baselines, finalized M04A; no production performance claim.

Each timestamp is an updated-data interval START; decision_time = start + 5 min.
Publication latency is unknown and assumed zero after interval end for this audit.
Train 3 dates, select residual coefficient on the 4th, evaluate once on the 5th.
"""
import csv
import io
import json
import tarfile
from pathlib import Path
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
source = root / 'data' / 'research'
out = root / 'data' / 'baseline'
out.mkdir(parents=True, exist_ok=True)
rows = []
member_counts = {}
for archive in sorted(source.glob('M04A_*.tar.gz')):
    count = 0
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith('.csv'):
                continue
            assert member.size < 2_000_000
            count += 1
            stream = io.TextIOWrapper(tar.extractfile(member), encoding='utf-8-sig')
            for row in csv.reader(stream):
                if len(row) != 6 or row[3] != '31':
                    continue
                if all(g.startswith('01F') and 850 <= int(g[3:7]) <= 1000 for g in row[1:3]):
                    rows.append(row)
    member_counts[archive.name] = count
df = pd.DataFrame(rows, columns=['timestamp', 'from', 'to', 'vehicle_type', 'seconds', 'volume'])
df['timestamp'] = pd.to_datetime(df.timestamp, format='%Y/%m/%d %H:%M')
for key in ['seconds', 'volume']:
    df[key] = pd.to_numeric(df[key])
df['link'] = df['from'] + '>' + df['to']
df['date'] = df.timestamp.dt.strftime('%Y%m%d')
df['slot'] = df.timestamp.dt.hour * 12 + df.timestamp.dt.minute // 5
assert not df.duplicated(['timestamp', 'link']).any()
df = df.sort_values(['link', 'timestamp']).reset_index(drop=True)
valid = (df.seconds > 0) & (df.volume > 0)
invalid_rows = int((~valid).sum())
df['valid_seconds'] = df.seconds.where(valid)
dates = sorted(df.date.unique())
assert dates == ['20260827','20260828','20260831','20260901','20260902']
train_dates, val_date, test_date = dates[:3], dates[3], dates[4]
train = df[df.date.isin(train_dates)]
hist = train.groupby(['link', 'slot']).valid_seconds.mean()
df['historical_now'] = [hist.get((link, slot), np.nan) for link, slot in zip(df.link, df.slot)]
summary, predictions = [], []
for minutes in [15, 30]:
    steps = minutes // 5
    future = df[['link','date','timestamp','valid_seconds','slot']].rename(columns={'valid_seconds':'actual','slot':'target_slot'})
    future['timestamp'] = future.timestamp - pd.Timedelta(minutes=minutes)
    frame = df.merge(future, on=['link','date','timestamp'], how='inner')
    frame['historical'] = [hist.get((link, slot), np.nan) for link, slot in zip(frame.link, frame.target_slot)]
    frame = frame.dropna(subset=['valid_seconds','actual','historical_now','historical'])
    validation = frame[frame.date == val_date]
    assert len(validation) > 0
    alpha_scores = {}
    for alpha in [0, .25, .5, .75, 1]:
        pred = (validation.historical + alpha * (validation.valid_seconds-validation.historical_now)).clip(lower=1)
        alpha_scores[alpha] = float(np.mean(abs(pred-validation.actual)))
    alpha = min(alpha_scores, key=alpha_scores.get)
    test = frame[frame.date == test_date].copy()
    test['persistence'] = test.valid_seconds
    test['residual_baseline'] = (test.historical + alpha*(test.valid_seconds-test.historical_now)).clip(lower=1)
    test['decision_time'] = test.timestamp + pd.Timedelta(minutes=5)
    test['target_interval_end'] = test.decision_time + pd.Timedelta(minutes=minutes)
    test['horizon_minutes'] = minutes
    for model in ['persistence','historical','residual_baseline']:
        for period, mask in [('all_day', np.ones(len(test),dtype=bool)), ('commute', test.timestamp.dt.hour.isin([7,8,9,16,17,18,19]).to_numpy())]:
            part = test.loc[mask]
            error = part[model]-part.actual
            summary.append(dict(horizon_minutes=minutes, model=model, period=period, n=len(part), mae_seconds=float(abs(error).mean()), rmse_seconds=float(np.sqrt((error**2).mean())), alpha=alpha if model=='residual_baseline' else None))
    test.to_csv(out/f'predictions-{minutes}min.csv', index=False)
    predictions.append(test)
    print(json.dumps(dict(horizon=minutes, selected_alpha=alpha, validation_mae=alpha_scores), ensure_ascii=False))
df.to_csv(out/'selected-observations.csv', index=False)
pd.DataFrame(summary).to_csv(out/'metrics.csv', index=False)
audit = dict(source='交通部高速公路局「交通資料庫」M04A', scope='國道1號門架公里數85.0–100.0之內的相鄰門架配對，小客車31；非市區路網', archive_csv_members=member_counts, rows=len(df), invalid_rows=invalid_rows, links=sorted(df.link.unique()), observed_rows_per_day=df.groupby('date').size().to_dict(), train_dates=train_dates, validation_date=val_date, test_date=test_date, historical_profile='training dates mean per link / five-minute slot; no test fit', timing='finalized interval-start timestamps converted to interval end; publication delay assumed zero; updated data may differ from real-time vintage', caveats=['five weekdays only','one test date; not representative','no city-road transfer claim','no AI/model improvement claim','no intervention/capacity simulation','unweighted paired-observation metrics; links have unequal length'])
(out/'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
print(pd.DataFrame(summary).to_string(index=False))
