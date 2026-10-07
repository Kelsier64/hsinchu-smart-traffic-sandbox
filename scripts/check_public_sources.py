"""New read-only public snapshots, separate from existing research manifests."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission/evidence/public-recheck'
SOURCES = {
    'competition.html': 'https://smartsandbox.hsinchu.gov.tw/home/pagesmartsand.html',
    'how-to-play.html': 'https://smartsandbox.hsinchu.gov.tw/home/pagehowtoplay.html',
    'news.html': 'https://smartsandbox.hsinchu.gov.tw/home/pagenews.html',
    'news-7.html': 'https://smartsandbox.hsinchu.gov.tw/home/pagenewscontent.html?NewsSN=7',
    'proposal-173.html': 'https://smartsandbox.hsinchu.gov.tw/home/pageproposalcontent.html?ProposalSN=173',
    'tdx-oas.json': 'https://tdx.transportdata.tw/webapi/File/Swagger/V3/7f07d940-91a4-495d-9465-1c9df89d709c',
    'vehicle-codes.html': 'https://traffic-api-documentation.gitbook.io/traffic/xiang-dai-zhao-biao',
}


def fetch(item):
    name, url = item
    r = dict(file=name, url=url, retrieved_at=datetime.now(timezone.utc).isoformat())
    try:
        with urlopen(Request(url, headers={'User-Agent': 'SandboxResearch/1.0'}), timeout=25) as response:
            payload = response.read(5_000_001)
            if len(payload) > 5_000_000:
                raise ValueError('size limit')
            r.update(status=response.status, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        (OUT / name).write_bytes(payload)
    except Exception as error:
        r['error'] = type(error).__name__ + ': ' + str(error)
    return r


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    # Never silently overwrite an earlier recheck.
    if (OUT / 'manifest.json').exists():
        raise SystemExit('Existing recheck; preserve it and use a new output directory.')
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, SOURCES.items()))
    (OUT / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    for r in records:
        print(r['file'], r.get('status', r.get('error')))
