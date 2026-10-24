import json,re,hashlib,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
class MatrixIntegrity(unittest.TestCase):
 def setUp(self):
  self.report=json.loads((OUT/'40-CONTROL-MATRIX.json').read_text());self.rows=self.report['controls']
 def test_exact_screenshot_wording_and_numbering(self):
  source=Path(self.report['numbering_source']);expected=re.findall(r'^\| ([AB]\d\d) \| (.*?) \|$',source.read_text(encoding='utf-8'),re.M)
  self.assertEqual([(r['id'],r['original_wording']) for r in self.rows],expected)
  self.assertEqual([r['original_number'] for r in self.rows],list(range(1,21))*2)
  self.assertEqual(self.report['source_sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
 def test_complete_unique_evidence_fields(self):
  self.assertEqual(len(self.rows),40);self.assertEqual(len({r['id'] for r in self.rows}),40)
  for r in self.rows:
   self.assertIn(r['status'],['Implemented','Partial','Missing','Not applicable','Unverified'])
   for key in ['applicability','existing_protection','tests_and_evidence','remaining_gap_and_smallest_safe_step','severity','blocks_shared_or_public_launch']:self.assertTrue(r[key],(r['id'],key))
 def test_cropped_wording_and_blocked_disposition(self):
  self.assertIn('[end of screenshot text cropped]',self.rows[-1]['original_wording'])
  self.assertEqual(self.report['decision'],'BLOCKED')
  self.assertNotIn('Implemented',[r['status'] for r in self.rows])
 def test_markdown_contains_exactly_forty_control_rows(self):
  lines=(OUT/'40-CONTROL-MATRIX.md').read_text(encoding='utf-8').splitlines()
  self.assertEqual(len([s for s in lines if re.match(r'^\| [AB]\d\d / ',s)]),40)
if __name__=='__main__':unittest.main()
