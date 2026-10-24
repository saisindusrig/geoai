import json,unittest
from pathlib import Path
OUT=Path(__file__).resolve().parent
class AffectedRowsOnly(unittest.TestCase):
 def test_unchanged_rows_and_original_wording(self):
  before=json.loads((OUT/'matrix-before.json').read_text())['controls']
  current=json.loads((OUT.parent/'release-security-40/40-CONTROL-MATRIX.json').read_text())['controls']
  affected=set(json.loads((OUT.parent/'release-security-40/phase-b-matrix-updates.json').read_text()))
  self.assertEqual(len(affected),12)
  self.assertEqual(len(current),40)
  for old,new in zip(before,current):
   for key in ['id','screenshot','original_number','original_wording']:self.assertEqual(old[key],new[key])
   if old['id'] not in affected:self.assertEqual(old,new)
  self.assertEqual(next(r['status'] for r in current if r['id']=='B17'),'Partial')
if __name__=='__main__':unittest.main()
