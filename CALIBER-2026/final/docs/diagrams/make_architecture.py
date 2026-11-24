"""Generate docs/diagrams/architecture.svg (+ .png via headless Chrome).  Run: py docs/diagrams/make_architecture.py"""
import subprocess, shutil
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parent
W, Hh = 1920, 1080
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
INK, MUTED = '#1F2937', '#6B7280'
PAL = {'src': ('#334155', '#F8FAFC'), 'prep': ('#1D4ED8', '#EFF6FF'), 'ml': ('#6D28D9', '#F5F3FF'),
       'dec': ('#0F766E', '#F0FDFA'), 'ta': ('#B45309', '#FFFBEB'), 'xai': ('#334155', '#F1F5F9')}

BOXES = [
    ('src', 'Source data', '6 SAP extracts', [
        '• BoM: stock, Min/Max', '• FuncLoc criticality', '• Goods issues', '• Notification history',
        '• PR / PO', '• Maintenance plans'], '17 months · 7,481 parts'),
    ('prep', '1 · Clean & trust', 'data-quality layer', [
        '• PO amount = unit price', '• Price fallback:', '   PO → category', '• Lead time PR → delivery:',
        '   P50 / P90 / σ', '• Split demand:', '   routine vs shutdown', '• Demand class (SBC)',
        '• Trust score 0–1', '   from 4 quality flags'], '8 data issues logged'),
    ('prep', '2 · Feature store', 'point-in-time, 27 features', [
        '• Installed base:', '   FLs, qty, criticality', '• Failures on its FLs:', '   notifs, emergencies',
        '• PM load on its FLs', '• Consumption history', '   + 90-day momentum', '• Procurement & lead time',
        '• Category, current Min/Max'], 'No look-ahead leakage'),
    ('ml', '3 · Two-part forecaster', 'LightGBM', [
        '• Who moves?', '   classifier → P(use)', '• How much?', '   Tweedie regressor,',
        '   blended with run rate', '• Training: 14 stacked', '   90-day folds,', '   recency-weighted'],
     'AUC 0.92 · cold-start 0.85'),
    ('ml', '4 · Uncertainty', 'Monte Carlo', [
        '• Compound Poisson,', '   2,000 simulations', '• Empirical issue sizes', '• Random lead time',
        '   (gamma)', '→ q50 / q90 / q95', '→ lead-time demand', '   distribution'], 'Ranges, not one number'),
    ('dec', '5 · Cost–risk optimizer', 'per part, per criticality', [
        '• Service level A/B/C/S', '   99 / 97 / 95 / 90%', '• Safety stock, ROP,', '   dynamic Min–Max, EOQ',
        '• Action: reorder / reduce', '   / dispose / monitor', '• Order-by date', '• Budget–risk frontier'],
     'Cost vs downtime risk'),
    ('dec', 'Decision app', 'Next.js · SQLite · Vercel', [
        '• Shutdown readiness', '• Parts & actions', '• Scenario simulator', '• Inventory health',
        '• Data trust', '', '  Planner approves or', '  rejects each action'], 'Web + mobile (PWA)'),
]

X0, BW, GAP = 50, 230, 35
BY, BH, HEAD = 300, 530, 78
xs = [X0 + i * (BW + GAP) for i in range(len(BOXES))]
cx = [x + BW / 2 for x in xs]
s = []
t = lambda x, y, txt, size=15, fill=INK, weight='normal', anchor='start': s.append(
    f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(txt)}</text>')

s.append(f'<rect width="{W}" height="{Hh}" fill="#FFFFFF"/>')
s.append('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker></defs>')
t(X0, 82, 'PartPulse: driver-based spare-part intelligence', 36, INK, 'bold')
t(X0, 122, "Forecast the equipment that consumes the parts, not each part's own sparse history", 19, MUTED)

# shutdown event band (top)
c, f = PAL['ta']; by0 = 196
s.append(f'<rect x="{xs[1]}" y="{by0}" width="{xs[6] + BW - xs[1]}" height="60" rx="10" fill="{f}" stroke="{c}" stroke-width="1.5"/>')
t(xs[1] + 18, by0 + 26, 'Shutdown event layer', 17, c, 'bold')
t(xs[1] + 18, by0 + 47, 'Last turnaround kit (2030 orders) replayed × scale → TA gap per part, order-by date before the next shutdown. Planned scope, kept out of daily Min–Max.', 14, INK)
for x, up in [(cx[1], True), (cx[5], False), (cx[6], False)]:
    a, b = (BY, by0 + 60) if up else (by0 + 60, BY)
    s.append(f'<line x1="{x}" y1="{a}" x2="{x}" y2="{b - 2 if not up else b + 2}" stroke="{MUTED}" stroke-width="2" marker-end="url(#ah)"/>')

# main boxes
for i, (k, title, sub, lines, foot) in enumerate(BOXES):
    c, f = PAL[k]; x = xs[i]
    s.append(f'<rect x="{x}" y="{BY}" width="{BW}" height="{BH}" rx="12" fill="{f}" stroke="{c}" stroke-width="1.5"/>')
    s.append(f'<path d="M{x},{BY + 12} a12,12 0 0 1 12,-12 h{BW - 24} a12,12 0 0 1 12,12 v{HEAD - 12} h-{BW} z" fill="{c}"/>')
    t(x + 16, BY + 34, title, 19, '#FFFFFF', 'bold')
    t(x + 16, BY + 59, sub, 14, '#E5E7EB')
    for j, ln in enumerate(lines):
        ind = len(ln) - len(ln.lstrip(' '))
        t(x + 16 + (14 if ind else 0), BY + HEAD + 36 + j * 28, ln.strip(), 15, INK)
    s.append(f'<rect x="{x + 12}" y="{BY + BH - 52}" width="{BW - 24}" height="36" rx="18" fill="#FFFFFF" stroke="{c}" stroke-width="1.2"/>')
    t(x + BW / 2, BY + BH - 28, foot, 13.5, c, 'bold', 'middle')
    if i < len(BOXES) - 1:
        y = BY + BH / 2
        s.append(f'<line x1="{x + BW + 3}" y1="{y}" x2="{x + BW + GAP - 3}" y2="{y}" stroke="{MUTED}" stroke-width="2" marker-end="url(#ah)"/>')

# explainability band (bottom right)
c, f = PAL['xai']; ey = 880
s.append(f'<rect x="{xs[3]}" y="{ey}" width="{xs[6] + BW - xs[3]}" height="60" rx="10" fill="{f}" stroke="{c}" stroke-width="1.5"/>')
t(xs[3] + 18, ey + 26, 'Explainability', 17, c, 'bold')
t(xs[3] + 18, ey + 47, 'TreeSHAP top-3 drivers per part → plain-English reason on every recommendation', 14, INK)
for x, down in [(cx[3], True), (cx[6], False)]:
    a, b = (BY + BH, ey) if down else (ey, BY + BH)
    s.append(f'<line x1="{x}" y1="{a}" x2="{x}" y2="{b - 2 if down else b + 2}" stroke="{MUTED}" stroke-width="2" marker-end="url(#ah)"/>')

# validation callout (bottom left)
c, f = PAL['ml']
s.append(f'<rect x="{xs[0]}" y="{ey}" width="{xs[2] + BW - xs[0]}" height="60" rx="10" fill="{f}" stroke="{c}" stroke-width="1.5" stroke-dasharray="6 4"/>')
t(xs[0] + 18, ey + 26, 'Rolling-origin validation', 17, c, 'bold')
t(xs[0] + 18, ey + 47, 'Retrain monthly on past data only, test next 90 days · AUC 0.92 vs 0.84 run-rate baseline (strict: 0.89)', 14, INK)

t(X0, 1040, 'Dummy dataset: mechanism over absolute values. Downtime cost is a relative index (slider in app). Model settings chosen on the validation origins.', 14, MUTED)

svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}">\n' + '\n'.join(s) + '\n</svg>\n'
(OUT / 'architecture.svg').write_text(svg)

chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
if Path(chrome).exists():
    html = OUT / '_arch.html'
    html.write_text(f'<html><body style="margin:0">{svg}</body></html>')
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={W},{Hh}',
                    '--force-device-scale-factor=2', f'--screenshot={OUT / "architecture.png"}', html.as_uri()],
                   check=True, capture_output=True)
    html.unlink()
print('wrote', OUT / 'architecture.svg')
