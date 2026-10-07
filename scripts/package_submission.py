"""Allowlisted supplemental package, byte limits, provenance and credential-pattern scan."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission'
pdf = OUT / 'proposal.pdf'
assert pdf.is_file(), 'Build and visually inspect proposal.pdf first'
files = []
for path in ['README.md', 'initial-proposal-draft.md', 'data-audit-and-baseline.md',
             'research-proposal-173.md', 'agent-workplan.md', 'OFFICIAL_SOURCES.md',
             'requirements.txt', 'requirements-report.txt']:
    files.append(ROOT / path)
for folder, pattern in [('scripts','*.py'), ('tests','*.py'), ('tests','*.cjs'), ('demo','*'),
                        ('data/baseline','*'), ('submission','*.md'), ('submission/assets','*.png'),
                        ('submission/assets','*.jpg'), ('submission/evidence','*.json'), ('submission/evidence','*.txt')]:
    files.extend(p for p in (ROOT / folder).glob(pattern) if p.is_file())
# Exclude large raw archives. Their hashes and retrieval URLs remain available.
files.extend([ROOT / 'data/research/baseline-source-manifest.json', ROOT / 'data/research/official-source-manifest.json'])
files.extend(p for p in (OUT / 'evidence/public-recheck').glob('*') if p.is_file())
files.extend([ROOT / 'official-rules-20260806.pdf', ROOT / 'official-rules.txt', ROOT / 'data/research/tdcs-manual.pdf'])
# Package-check hashes this ZIP afterwards, so never include a stale/self-referential copy.
files = sorted(set(p for p in files if p.name not in ['package-check.json', 'supplement-smoke.json']))
assert all(p.resolve().is_relative_to(ROOT.resolve()) for p in files)
assert not any(p.suffix in ['.gz', '.env'] or '.git' in p.parts or '__pycache__' in p.parts for p in files)
secret_patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                   r'\b(?:ghp_|github_pat_|sk-proj-)[A-Za-z0-9_-]{20,}',
                   r'\bAKIA[0-9A-Z]{16}\b', r'Bearer\s+[A-Za-z0-9._-]{30,}']
findings = []
for p in files:
    if p.suffix.lower() not in ['.png','.jpg','.zip','.pdf']:
        text = p.read_text(encoding='utf-8')
        if any(re.search(pattern, text) for pattern in secret_patterns):
            findings.append(p.relative_to(ROOT).as_posix())
assert not findings, 'Credential patterns found; inspect privately: ' + ', '.join(findings)
archive = OUT / 'supplement.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, p.relative_to(ROOT).as_posix())
    z.writestr('PACKAGE-NOTE.txt', 'Public offline replay and saved results. Raw national archives are NOT included. Full raw reproduction requires the repository archives listed in data/research/baseline-source-manifest.json. Report source is initial-proposal-draft.md. See submission/human-checklist.md before submission. ZIP acceptance in logged-in portal is unverified.\n')
assert pdf.stat().st_size <= 30_000_000 and archive.stat().st_size <= 30_000_000
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert sum(i.file_size for i in z.infolist()) <= 100_000_000
    assert all(i.file_size <= 30_000_000 for i in z.infolist())
reader = PdfReader(pdf)
text = '\n'.join(p.extract_text() for p in reader.pages)
blockers = ['student eligibility proof', 'portal availability/deadline/fields',
            'AI core-code applicability and human verification', 'formal participant submission']
assert all(s in text for s in ['杜凱朗', '國立臺灣大學', '生物機電工程學系', '一年級'])
assert not any(s in text for s in ['待本人', '待填', '【', '編輯註解'])
import pandas as pd
m = pd.read_csv(ROOT / 'data/baseline/metrics.csv')
source = (ROOT / 'initial-proposal-draft.md').read_text(encoding='utf-8')
for r in m.itertuples():
    assert f'{r.mae_seconds:.2f}／{r.rmse_seconds:.2f}' in source
    assert f'{r.n:,}' in source
local_link_failures = []
for p in [ROOT / 'README.md', ROOT / 'initial-proposal-draft.md'] + list(OUT.glob('*.md')):
    for target in re.findall(r'\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
        if not target.startswith(('http:', 'https:', '#')) and not (p.parent / target.split('#')[0]).exists():
            local_link_failures.append({'file':p.name,'target':target})
assert not local_link_failures, local_link_failures
source_hashes = []
for manifest in [ROOT / 'data/research/official-source-manifest.json']:
    for r in json.loads(manifest.read_text(encoding='utf-8'))['files']:
        p = ROOT / r['path']
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256'], r['path']
        source_hashes.append(r['path'])
report = {'status':'passed within stated scope', 'pdf_pages':len(reader.pages),
          'pdf_bytes':pdf.stat().st_size, 'supplement_bytes':archive.stat().st_size,
          'supplement_file_count':len(files)+1, 'existing_source_hashes_checked':len(source_hashes),
          'canonical_metric_strings':'all 12 MAE/RMSE/n checked against CSV',
          'local_final_document_links':'all resolved',
          'credential_pattern_scan':'no hits in allowlisted text; not a universal secret detector',
          'personal_data_scope':'public aggregate traffic and user-supplied participant name/education; no identity numbers or eligibility proofs',
          'screenshots':'browser tested and displayed, file saving EPERM; no delivered screenshot files',
          'report_prepared':True, 'report_has_editorial_placeholders':False,
          'submission_ready':False, 'remaining_blockers':blockers,
          'artifacts': {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [pdf,archive]}}
(OUT / 'evidence/package-check.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(report, indent=2, ensure_ascii=False))
