"""Offline plan/lexical path tests only; not live ACL or resource isolation proof."""
import json
import ntpath
from pathlib import Path
import unittest

PLAN=json.loads((Path(__file__).parent/'fresh-environment-plan.json').read_text())
def inside(candidate,root):
 if not ntpath.isabs(candidate) or candidate.startswith('\\\\'):return False
 a=ntpath.normcase(ntpath.normpath(candidate));b=ntpath.normcase(ntpath.normpath(root))
 try:return ntpath.commonpath([a,b])==b
 except ValueError:return False
def approved_data_path(candidate,reparse=False,inherited_access=False):
 return inside(candidate,PLAN['root']) and not inside(candidate,PLAN['existing_data_root']) and not reparse and not inherited_access

class IsolationPlanTests(unittest.TestCase):
 def test_all_initial_application_data_is_empty(self):self.assertTrue(all(value==0 for value in PLAN['initial_counts'].values()))
 def test_new_paths_do_not_overlap_original(self):
  self.assertFalse(inside(PLAN['root'],PLAN['existing_data_root']))
  self.assertFalse(inside(PLAN['existing_data_root'],PLAN['root']))
  for path in PLAN['data_paths'].values():self.assertTrue(approved_data_path(path))
 def test_original_database_and_backup_are_rejected(self):
  for path in [r'D:\layout project\backend\dev.db',r'D:\layout project\backend\assistant-history.db',r'D:\layout project\.cleanup-backups']:
   self.assertFalse(approved_data_path(path))
 def test_traversal_and_prefix_lookalike_are_rejected(self):
  self.assertFalse(approved_data_path(PLAN['root']+r'\..\..\layout project\backend\dev.db'))
  self.assertFalse(approved_data_path(PLAN['root']+'-other\\data'))
 def test_relative_unc_and_other_drive_are_rejected(self):
  for path in [r'backend\dev.db',r'\\server\share\db',r'C:\StruvoCivil-Staging\data']:self.assertFalse(approved_data_path(path))
 def test_reparse_and_inherited_developer_access_are_rejected(self):
  path=PLAN['data_paths']['private_files'];self.assertFalse(approved_data_path(path,reparse=True));self.assertFalse(approved_data_path(path,inherited_access=True))
 def test_no_legacy_seed_copy_or_fallback(self):
  for key in ['seeding','copy_development_data','legacy_authentication_allowed','database_fallback_allowed','firebase_enabled_now','nebius_inference_enabled','solver_execution_authorized']:self.assertFalse(PLAN[key])
 def test_no_runtime_or_creation_claim(self):
  self.assertFalse(PLAN['root_created']);self.assertFalse(PLAN['runtime_isolation_verified']);self.assertIn('BLOCKED',PLAN['runtime_admission'])

if __name__=='__main__':unittest.main(verbosity=2)
