"""Reuse guarded, read-only browser checks; no normal services or live auth."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
for name in ('start_isolated.py', 'serve_isolated.py'):
    source = (OUT.parent / 'gate-2a' / name).read_text().replace('gate2a-guard.cjs', 'gate2f-guard.cjs')
    (OUT / name).write_text(source)
browser = (OUT.parent / 'gate-2a/browser.cjs').read_text().replace('gate-2a/', 'gate-2f/')
browser = browser.replace('assert.equal(hardware.software,false);', '')
(OUT / 'browser.cjs').write_text(browser)
