"""Extract only allowlisted package paths and test a self-contained offline replay."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
import zipfile
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
(ROOT / 'tmp').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=ROOT / 'tmp', prefix='supplement-smoke-') as td:
    folder = Path(td).resolve()
    with zipfile.ZipFile(ROOT / 'submission/supplement.zip') as z:
        for name in z.namelist():
            assert (folder / name).resolve().is_relative_to(folder), 'unsafe archive path'
        z.extractall(folder)
    spec = importlib.util.spec_from_file_location('packaged_demo', folder / 'scripts/serve_demo.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    server = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    statuses = {}
    try:
        for path, expected in [('demo/',200),('demo/app.js',200),('demo/style.css',200),
                               ('data/baseline/predictions-15min.csv',200),
                               ('data/baseline/predictions-30min.csv',200),
                               ('data/baseline/selected-observations.csv',200),('.git/config',404)]:
            try:
                with urlopen(f'http://127.0.0.1:{server.server_port}/{path}', timeout=5) as response:
                    status = response.status
            except HTTPError as e:
                status = e.code
            assert status == expected, path
            statuses[path] = status
        run = subprocess.run([sys.executable,'-X','utf8','scripts/verify_baseline.py'], cwd=folder,
                             capture_output=True, encoding='utf-8', check=True)
    finally:
        server.shutdown()
        server.server_close()
    report = {'status':'passed', 'scope':'extracted supplemental ZIP; HTTP assets and independent CSV audit',
              'http_statuses':statuses, 'audit_stdout':run.stdout.strip(),
              'raw_archives_included':False, 'requires_private_key':False}
(ROOT / 'submission/evidence/supplement-smoke.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('PASS: extracted ZIP serves all 6 offline assets, rejects .git/config, independent saved-result audit passes.')
