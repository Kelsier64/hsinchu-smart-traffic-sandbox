"""Inventory saved official sources and distinguish derived text/data."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from fetch_research_sources import SOURCES

root = Path(__file__).resolve().parents[1]
sources = {f'data/research/{name}': url for url, name in SOURCES.values()}
rules_url = 'https://smartsandbox.hsinchu.gov.tw/Document/2026%E6%96%B0%E7%AB%B9%E7%B8%A3%E6%99%BA%E6%85%A7%E6%B2%99%E7%9B%92%E5%89%B5%E6%96%B0%E8%A8%88%E7%95%AB%E7%AB%B6%E8%B3%BD%E7%B0%A1%E7%AB%A0.pdf?v=20260806'
sources['official-rules-20260806.pdf'] = rules_url
sources['freeway-index.html'] = 'https://tisvcloud.freeway.gov.tw/'
derived = {
    'official-rules.txt': 'official-rules-20260806.pdf',
    'data/research/tdcs-manual.txt': 'data/research/tdcs-manual.pdf',
    'data/research/hsinchu-freeway-vd.json': 'data/research/vd-static.xml',
}
archive_manifest = root / 'data/research/baseline-source-manifest.json'
for record in json.loads(archive_manifest.read_text(encoding='utf-8')):
    sources[f"data/research/{record['file']}"] = record['url']
download_records = json.loads((root/'data/research/source-fetch-log.json').read_text(encoding='utf-8'))
by_file = {f"data/research/{r['saved_as']}":r for r in download_records if r.get('saved_as')}
records = []
for rel in sorted(set(sources)|set(derived)):
    path = root / rel
    if not path.is_file():
        continue
    payload = path.read_bytes()
    record = dict(path=rel, kind='derived' if rel in derived else 'official_download', bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    if rel in derived:
        record['derived_from'] = derived[rel]
    else:
        record['source_url'] = sources[rel]
    if rel in by_file:
        record['fetched_at'] = by_file[rel]['fetched_at']
    records.append(record)
output = dict(inventoried_at=datetime.now(timezone.utc).isoformat(), note='File hashes describe local snapshots; source publication dates and download times are not inferred when absent. Third-party sources remain attributed to their publishers.', files=records)
(root/'data/research/official-source-manifest.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Inventoried {len(records)} files, {sum(r["bytes"] for r in records):,} bytes.')
