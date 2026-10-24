import json,html
from pathlib import Path
out=Path('docs/milestone-12')
rows=[
('Genuine Firebase sign-in and account lifecycle','High','BLOCKED','backend-tests.log: test_firebase_auth.py; synthetic verifier only','Install/configure official SDKs in separately approved staging; qualify linking, revocation, disabled accounts and recovery.',True),
('Secure multi-user project isolation','High','BLOCKED','backend-tests.log: ownership, downloads, conversation isolation; fixes-final.log: protected CAD; security-final.log: concurrent saves','Retain verified server ownership gates; qualify genuine identities and multi-instance isolation before shared access.',True),
('PostgreSQL persistence and restore qualification','High','BLOCKED','security-final.log: production database refuses SQLite and unavailable PostgreSQL; M11 recovery evidence','Provision approved isolated PostgreSQL/PostGIS staging, test migrations/backups and measured restore without original migration.',True),
('Private Cloud Storage and file authorization','High','BLOCKED','backend-tests.log: durability storage failure/ownership; isolation-negative-probes.json','Qualify private bucket IAM, signed access expiry, object/database reconciliation and restore in separate staging.',True),
('Durable engineering jobs and recovery','High','BLOCKED','backend-tests.log: test_durability_readiness.py; coupled-evidence-preservation.json','Implement transactional durable job ownership/leases and atomic evidence publication; test worker crashes. Uncertain jobs require new authorization.',True),
('Distributed AI spending accounting','High','BLOCKED','backend-tests.log: quota and duplicate/concurrency mocks; production shared limiter regression','Qualify multi-instance durable reservations/reconciliation and shared limiter failure. Keep inference disabled.',True),
('Production HTTPS, headers and proxy policy','High','BLOCKED','browser.json; frontend-tests.log; production CORS and secret configuration tests','Qualify TLS/HSTS, full script CSP, explicit trusted proxy allowlist and deployed API/storage headers; current partial CSP is insufficient for full ASVS.',True),
('Monitoring, logging and incident response','Medium','UNVERIFIED','M4 sanitization tests and M11 diagnostics; local browser reports only','Define alert thresholds, access/retention/redaction, incident ownership and recovery drill; test staging failures.',True),
('Dependency and resource-abuse exposure','High','BLOCKED','dependency-review.json; pdf-reproduction-before.json; security-final.log','Review current matching leaf advisories and fresh advisory feed separately; sandbox native parsers, bound multipart ingress/expanded geometry, qualify quotas and bounded staging load.',True),
('Engineering scope and unsupported methods','High','BLOCKED','backend-tests.log: exact revision/results/approval; protected CAD and stale-save tests','Independent engineering validation remains required; do not promote conceptual beams to analytical members or verified quantities. No unsupported method claims.',True),
]
keys=['area','severity','status','evidence','required_remediation','blocks_shared_or_public_access']
matrix=[dict(zip(keys,r)) for r in rows];(out/'release-matrix.json').write_text(json.dumps(matrix,indent=2))
chapter={
'V1':('PDF/CSV escaping and strict native tool schemas tested; SQL uses ORM in reviewed paths.','Complete context-sensitive sink inventory and URL/SSRF egress qualification remain incomplete.'),
'V2':('Allowlisted dimensions, units, revisions and duplicate actions tested.','Global ingress and native parser work budgets, all business-flow abuse paths unqualified.'),
'V3':('React markdown tests and four browser headers verified.','TLS/HSTS, complete script CSP, browser storage/session deployment incomplete.'),
'V4':('Strict tool schemas, ownership and malformed-request tests.','Full API inventory/content-type/body limits and deployed gateway not qualified.'),
'V5':('Owned downloads, bounded survey read, ZIP names/count/expansion checked.','Multipart spooling, malware/native parser sandbox, expanded CAD/3D complexity remain gaps.'),
'V6':('JWT and disabled official-verifier adapter tested with synthetic identities.','Genuine Firebase login/lifecycle, MFA/recovery and credential-strength upgrade not qualified.'),
'V7':('Token expiry and revoked/disabled mocks tested.','Real revocation/session lifecycle, distributed invalidation and stolen-session response unqualified.'),
'V8':('Server-side ownership, protected CAD, history isolation and stale saves tested.','Live identity lifecycle and all deployed services require staging qualification.'),
'V9':('Existing JWT and official Firebase verification boundary fail closed in mocks.','Real provider keys, issuer/audience and clock/revocation integration not qualified.'),
'V10':('Unknown/unlinked Firebase identities rejected; email does not merge identities.','Real OAuth/OIDC sign-in deliberately disabled; full flow not verified.'),
'V11':('Production secret minimum and rejection tests.','Key rotation, storage encryption, backup key custody and full cryptographic inventory incomplete.'),
'V12':('Production origins require explicit HTTPS.','Actual certificates, TLS policy, internal service transport and proxy deployment unverified.'),
'V13':('Production JWT/secret/CORS/shared limiter/database guards tested.','IAM, secrets distribution, private storage and deployed configuration not qualified.'),
'V14':('Exact original row/artifact preservation and scoped ownership tests.','Privacy retention/deletion, backup access and live multi-service data protection unqualified.'),
'V15':('Existing architecture and M4–11 evidence reviewed; recovery never auto-reexecutes.','Durable jobs, distributed accounting and dependency/parser risk prevent shared release.'),
'V16':('Scoped error sanitization tests and local diagnostics retained.','Central monitoring, audit durability, incident drills and production retention unqualified.'),
'V17':('No WebRTC feature identified in reviewed application.','Confirm absence in final deployed feature inventory; do not claim N/A certification.')}
requirements=json.loads((out/'asvs-5.0.0-source.json').read_text())['requirements'];register=[]
for req in requirements:
 if int(req['L'])>2:continue
 evidence,gap=chapter[req['chapter_id']]
 register.append({'requirement':req['req_id'],'level':int(req['L']),'chapter':req['chapter_name'],'section':req['section_name'],'applicability':'Candidate applicable; final inventory pending' if req['chapter_id']!='V17' else 'Not observed; applicability confirmation pending','status':'UNVERIFIED','evidence_scope':evidence,'gap':gap,'test_evidence':'backend-tests.log; fixes-final.log; security-final.log; frontend-tests.log; browser.json; RESULTS.md'})
(out/'asvs-register.json').write_text(json.dumps({'standard':'OWASP ASVS 5.0.0','source':'https://github.com/OWASP/ASVS/tree/v5.0.0','requirements':register,'qualification':'Evidence/gap register, not certification. All whole-requirement outcomes remain UNVERIFIED; individual scoped controls may pass tests.'},indent=2))
body=''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in keys)+'</tr>' for r in matrix)
(out/'release-matrix.html').write_text('''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>StruvoCivil M12 qualification</title><style>body{font:15px system-ui;background:#101710;color:#edf2e7;margin:24px}h1{color:#bcdf45}table{border-collapse:collapse;width:100%}td,th{border:1px solid #536047;padding:12px;text-align:left;vertical-align:top}th{background:#263321}button{padding:10px;margin-bottom:15px}input{padding:10px;width:300px}small{color:#c4cdbd}</style><h1>Shared private beta: BLOCKED</h1><p>Local synthetic regression evidence does not establish production readiness. No cloud activation or paid inference.</p><input id="q" placeholder="Filter evidence or area" aria-label="Filter release matrix"><p><small>Ten release areas. True in the final column prevents shared/public access.</small></p><div style="overflow:auto"><table><thead><tr>'''+''.join('<th>'+html.escape(k.replace('_',' '))+'</th>' for k in keys)+'</tr></thead><tbody>'+body+'''</tbody></table></div><p><a href="RESULTS.md">Detailed report</a> · <a href="asvs-register.json">253 ASVS L1/L2 evidence and gap records</a> · <a href="preservation.json">Exact database preservation</a></p><script>document.querySelector('#q').oninput=e=>document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase()))</script>''',encoding='utf-8')
print('Matrix areas',len(matrix),'ASVS records',len(register))
