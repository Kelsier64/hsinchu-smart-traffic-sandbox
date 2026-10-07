"""Fetch five explicitly verified public archive links, preserving provenance."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1] / 'data' / 'research'
catalog = (root / 'm04a-catalog.html').read_text(encoding='utf-8')
records = []
manifest_path = root / 'baseline-source-manifest.json'
previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else []
by_file = {r['file']: r for r in previous}
for day in ['20260827', '20260828', '20260831', '20260901', '20260902']:
    name = f'M04A_{day}.tar.gz'
    assert f'href="{name}"' in catalog
    url = 'https://tisvcloud.freeway.gov.tw/history/TDCS/M04A/' + name
    target = root / name
    if not target.exists():
        with urlopen(Request(url, headers={'User-Agent': 'SandboxProposalResearch/1.0'}), timeout=30) as response:
            assert response.status == 200
            payload = response.read(25_000_001)
            assert len(payload) <= 25_000_000
        target.write_bytes(payload)
    payload = target.read_bytes()
    record = dict(url=url, file=name, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), checked_at=datetime.now(timezone.utc).isoformat())
    if name in by_file:
        prior = by_file[name]
        if any(record[k] != prior[k] for k in ['url', 'bytes', 'sha256']):
            raise ValueError(f'{name}: differs from preserved manifest; inspect separately, do not overwrite provenance')
        record = prior
    records.append(record)
    print(json.dumps(record), flush=True)
new_records = [r for r in records if r['file'] not in by_file]
if new_records:
    manifest_path.write_text(json.dumps(previous + new_records, indent=2), encoding='utf-8')
