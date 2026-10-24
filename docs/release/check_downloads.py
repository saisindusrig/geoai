from pathlib import Path
import json,csv,struct,hashlib
from pypdf import PdfReader
root=Path('docs/release');data=json.loads((root/'downloads/api-export.json').read_text());r=PdfReader(root/'downloads/browser-report.pdf');text='\n'.join(p.extract_text() for p in r.pages)
assert len(r.pages)>0 and 'PRELIMINARY' in text.upper()
assert data['project']['name'] in text
rows=list(csv.DictReader((root/'downloads/browser-boq.csv').read_text().splitlines()[1:])); assert len(rows)==6
for row, item in zip(rows,data['quantity_estimate']['line_items']):
    assert row['item_code']==item['item_code']
    for key in ['quantity','rate','amount']:
        assert float(row[key])==item[key]
assert len(rows)==len(data['quantity_estimate']['line_items'])
blob=(root/'downloads/owned-generated-model.glb').read_bytes();magic,version,length=struct.unpack('<4sII',blob[:12]);assert magic==b'glTF' and version==2 and length==len(blob);n=struct.unpack('<I',blob[12:16])[0];model=json.loads(blob[20:20+n]);assert model['asset']['version']=='2.0' and len(model.get('meshes',[]))>0
result={'pdf_pages':len(r.pages),'pdf_contains_project':True,'pdf_contains_disclaimer':True,'csv_rows':len(rows),'csv_matches_saved_estimate':True,'glb_bytes':len(blob),'glb_meshes':len(model['meshes']),'project_id':data['project']['id']}
(root/'download-integrity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
