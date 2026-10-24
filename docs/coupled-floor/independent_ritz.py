"""Reproduce the independent plate-energy calculation without native shell data."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'backend'))
from app.services.design.coupled_ritz import solve
if __name__=='__main__':
 results=[solve(p) for p in [4,6,8]]
 (Path(__file__).parent/'independent-ritz.json').write_text(json.dumps(results,indent=2))
 print([(r['order'],r['center_uz_m']) for r in results])
