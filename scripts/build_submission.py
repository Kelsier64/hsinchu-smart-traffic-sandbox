"""Build traceable figures and PDF from the ONE canonical Markdown proposal."""
import html
import hashlib
import importlib.metadata
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Optional local dependencies; normal installations need not use this directory.
sys.path.insert(0, str(ROOT / 'tmp/pdf-deps'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'tmp/matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from pypdf import PdfReader

OUT = ROOT / 'submission'
ASSETS = OUT / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)
font_path = os.environ.get('PROPOSAL_CJK_FONT', 'C:/Windows/Fonts/msjh.ttc')
if not Path(font_path).is_file():
    raise SystemExit('Set PROPOSAL_CJK_FONT to an embeddable Traditional Chinese TTF/TTC.')
font_manager.fontManager.addfont(font_path)
plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
plt.rcParams['axes.unicode_minus'] = False
models = ['persistence', 'historical', 'residual_baseline']
model_labels = dict(zip(models, ['維持目前值', '歷史同時段', '殘差校正']))
palette = ['#00857c', '#cf8535', '#8050b3']
metrics = pd.read_csv(ROOT / 'data/baseline/metrics.csv')
fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.4), constrained_layout=True)
for ax, horizon in zip(axes, [15, 30]):
    for i, model in enumerate(models):
        g = metrics[(metrics.horizon_minutes == horizon) & (metrics.model == model)].set_index('period')
        ax.bar([i * .24, 1 + i * .24], g.loc[['all_day', 'commute'], 'mae_seconds'], width=.22, color=palette[i], label=model_labels[model])
    ax.set_xticks([.24, 1.24], ['全日', '通勤時段'])
    ax.set_ylabel('平均絕對誤差（秒）')
    ax.set_title(f'{horizon}分鐘預測 | 2026-09-02 | 六個有向路段')
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis='y', alpha=.18)
axes[1].legend(fontsize=8)
fig.savefig(ASSETS / 'baseline-errors.png', dpi=180)
plt.close(fig)
p = pd.read_csv(ROOT / 'data/baseline/predictions-15min.csv')
p = p[p.link == '01F0880S>01F0928S']
x = pd.to_datetime(p.target_interval_end)
fig, ax = plt.subplots(figsize=(10.5, 3.7), constrained_layout=True)
ax.plot(x, p.actual, color='#18334c', label='實際觀測', linewidth=1.8)
for model, color in zip(models, palette):
    ax.plot(x, p[model], color=color, label=model_labels[model], linewidth=1.1)
import matplotlib.dates as mdates
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.set_ylabel('旅行時間（秒）')
ax.set_xlabel('目標區間結束時間（臺灣時間；末端00:00為9月3日）')
ax.set_title('01F0880S > 01F0928S | 2026-09-02 | 15分鐘預測')
ax.spines[['top', 'right']].set_visible(False)
ax.grid(alpha=.18)
ax.legend(fontsize=8, ncol=2)
fig.savefig(ASSETS / 'baseline-curve.png', dpi=180)
plt.close(fig)

pdfmetrics.registerFont(TTFont('CJK', font_path, subfontIndex=0))
pdfmetrics.registerFont(TTFont('Symbols', str(Path(matplotlib.get_data_path()) / 'fonts/ttf/DejaVuSans.ttf')))
pdfmetrics.registerFontFamily('CJK', normal='CJK', bold='CJK', italic='CJK', boldItalic='CJK')
styles = {
    'title': ParagraphStyle('title', fontName='CJK', fontSize=22, leading=31, textColor=colors.HexColor('#006b70'), spaceAfter=18, wordWrap='CJK'),
    'h1': ParagraphStyle('h1', fontName='CJK', fontSize=16, leading=24, textColor=colors.HexColor('#006b70'), spaceAfter=16, wordWrap='CJK'),
    'h2': ParagraphStyle('h2', fontName='CJK', fontSize=12, leading=19, spaceBefore=13, spaceAfter=8, keepWithNext=True, wordWrap='CJK'),
    'body': ParagraphStyle('body', fontName='CJK', fontSize=10, leading=16.5, spaceAfter=9, wordWrap='CJK'),
    'cell': ParagraphStyle('cell', fontName='CJK', fontSize=8.4, leading=13, wordWrap='CJK'),
    'caption': ParagraphStyle('caption', fontName='CJK', fontSize=8.5, leading=13, spaceAfter=10, textColor=colors.HexColor('#526676'), wordWrap='CJK'),
}


def inline(s):
    s = s.replace('\u2212', '-')
    s = html.escape(s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#00777b">\1</link>', s)
    s = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', s)
    for symbol in ['\u2264', '\u2265']:
        s = s.replace(symbol, '<font name="Symbols">' + symbol + '</font>')
    return s.replace('`', '')


lines = (ROOT / 'initial-proposal-draft.md').read_text(encoding='utf-8').splitlines()
story = []
width = A4[0] - 92
i = 0
section = 0
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            cells = [s.strip() for s in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch('[: -]+', s) for s in cells):
                rows.append([Paragraph(inline(s), styles['cell']) for s in cells])
            i += 1
        cols = len(rows[0])
        # Equal widths keep all evidence tables within the live area.
        table = Table(rows, colWidths=[width / cols] * cols, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#dcecee')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#cbdadf')),
        ]))
        table.spaceAfter = 10
        story.append(table)
        continue
    image_match = re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)', line)
    if image_match:
        path = ROOT / image_match[2]
        if not path.is_file():
            raise SystemExit(f'Missing evidence image: {path}')
        im = Image(str(path))
        im.drawHeight *= width / im.drawWidth
        im.drawWidth = width
        story.extend([im, Spacer(1,8)])
    elif line.startswith('# '):
        story.append(Paragraph(inline(line[2:]), styles['title']))
    elif line.startswith('## '):
        if section in [2, 3, 4, 5]:
            story.append(PageBreak())
        section += 1
        story.append(Paragraph(inline(line[3:]), styles['h1']))
    elif line.startswith('### '):
        if line.startswith('### 2. 基準方法與結果'):
            story.append(PageBreak())
        story.append(Paragraph(inline(line[4:]), styles['h2']))
    else:
        story.append(Paragraph(inline(line), styles['caption'] if line.startswith('圖') else styles['body']))
    i += 1


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#cbdadf'))
    canvas.line(46, 40, A4[0]-46, 40)
    canvas.setFont('CJK', 8)
    canvas.setFillColor(colors.HexColor('#526676'))
    canvas.drawString(46, 26, '竹行先知 | 杜凱朗 | 國立臺灣大學 | 初選成果報告書')
    canvas.drawRightString(A4[0]-46, 26, str(doc.page))
    canvas.restoreState()


pdf = OUT / 'proposal.pdf'
SimpleDocTemplate(str(pdf), pagesize=A4, rightMargin=46, leftMargin=46, topMargin=44, bottomMargin=56,
                  title='竹行先知：通勤壅塞預警與容量感知分流', author='杜凱朗').build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(pdf)
text = '\n'.join(page.extract_text() for page in reader.pages)
assert '\x00' not in text, 'Missing/incorrectly mapped PDF text glyphs'
(OUT / 'evidence/proposal-extracted.txt').write_text(text, encoding='utf-8')
assert len(reader.pages) > 0 and pdf.stat().st_size < 30_000_000
assert all(f'{n}、' in text for n in '一二三四五六七')
(OUT / 'evidence/build-environment.json').write_text(json.dumps({
    'python':sys.version, 'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','matplotlib','reportlab','pypdf','Pillow']},
    'font':Path(font_path).name, 'font_sha256':hashlib.sha256(Path(font_path).read_bytes()).hexdigest(),
    'canonical_source_sha256':hashlib.sha256((ROOT / 'initial-proposal-draft.md').read_bytes()).hexdigest(),
    'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(), 'pages':len(reader.pages),
}, indent=2), encoding='utf-8')
print(f'Built {pdf.name}: {len(reader.pages)} pages, {pdf.stat().st_size:,} bytes, embedded CJK font; one canonical Markdown source.')
