"""Hash-check saved archives, rerun original pipeline in isolation, compare numerically."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'data/research/baseline-source-manifest.json').read_text(encoding='utf-8'))
for r in records:
    p = ROOT / 'data/research' / r['file']
    assert p.stat().st_size == r['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256'], p.name
(ROOT / 'tmp').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=ROOT / 'tmp', prefix='baseline-rerun-') as td:
    script = (ROOT / 'scripts/traffic_baseline.py').read_text(encoding='utf-8')
    script = script.replace("root = Path(__file__).resolve().parents[1]", 'root = Path(' + repr(str(ROOT)) + ')')
    script = script.replace("out = root / 'data' / 'baseline'", 'out = Path(' + repr(td) + ')')
    generated = Path(td) / 'rerun.py'
    generated.write_text(script, encoding='utf-8')
    run = subprocess.run([sys.executable, '-X', 'utf8', str(generated)], capture_output=True, text=True, encoding='utf-8', check=True)
    for name in ['selected-observations.csv', 'predictions-15min.csv', 'predictions-30min.csv', 'metrics.csv']:
        original = pd.read_csv(ROOT / 'data/baseline' / name)
        fresh = pd.read_csv(Path(td) / name)
        pd.testing.assert_frame_equal(original, fresh, check_exact=False, atol=1e-10, rtol=1e-10)
    assert json.loads((Path(td) / 'audit.json').read_text(encoding='utf-8')) == json.loads((ROOT / 'data/baseline/audit.json').read_text(encoding='utf-8'))
    from verify_baseline import verify
    verify(Path(td))
    (ROOT / 'submission/evidence/raw-rerun.txt').write_text('PASS: five saved archive hashes; original parser rerun; four CSV and audit match; independent audit passed.\nNOT redownloaded.\n' + run.stdout, encoding='utf-8')
print('PASS: 5 saved archive hashes; raw-to-selected-to-predictions-to-metrics reproduction, isolated outputs; no download or manifest overwrite.')
