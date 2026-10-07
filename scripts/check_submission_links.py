"""Read-only URL health check for final Markdown sources; no login or credentials."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parents[1]
files = [ROOT / 'README.md', ROOT / 'initial-proposal-draft.md'] + list((ROOT / 'submission').glob('*.md'))
urls = sorted({u for p in files for u in re.findall(r'\]\((https?://[^)]+)\)', p.read_text(encoding='utf-8'))
               if not u.startswith('http://127.0.0.1')})


def check(url):
    r = {'url':url}
    try:
        with urlopen(Request(url, headers={'User-Agent':'SandboxResearch/1.0'}), timeout=20) as response:
            r.update(status=response.status, final_url=response.url)
    except Exception as e:
        r['error'] = type(e).__name__ + ': ' + str(e)
    return r


with ThreadPoolExecutor(max_workers=4) as pool:
    result = list(pool.map(check, urls))
(ROOT / 'submission/evidence/link-check.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
for r in result:
    print(r.get('status', r.get('error')), r['url'])
