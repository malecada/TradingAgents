import ast,hashlib,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry15-review01-2026-10-07';W=F/'real-data-pilot-archive-idle-fix01-2026-10-07';D=F/'real-data-pilot-fixed15-metadata-successor01-2026-10-07';O=F/'real-data-pilot-fixed14-metadata-successor01-2026-10-06';L=F/'real-data-pilot-final15-2026-10-07';P=F/'real-data-pilot-final14-2026-10-06'
def ld(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
a='eth-paper-real-data-end-to-end-resource-20261006-14';b='eth-paper-real-data-end-to-end-resource-20261007-15';storage=R/'tradingagents/research/onchain_replication/real_pilot_storage.py'
assert storage.read_text().count(a)==1 and storage.read_text().replace(a,b)==(D/'candidate/real_pilot_storage.py').read_text()
for name in ['build_inputs03.py','controls01.py']:
 old=(O/'candidate'/name).read_text();assert old.count(a)==1 and old.replace(a,b)==(D/'candidate'/name).read_text()
assert (D/'successor02.py').read_bytes()==(O/'successor02.py').read_bytes()
newdeps=ld(D/'DEPENDENCIES02.json');olddeps=ld(O/'DEPENDENCIES02.json');assert set(newdeps)==set(olddeps)
for key,reference in newdeps.items():
 assert ref(R/reference['path'])['sha256']==reference['sha256']
 if key not in {'builder','controls'}:assert reference==olddeps[key]
expected=(P/'preflight01.py').read_text().replace(a,b).replace('real-data-pilot-fixed14-metadata-successor01-2026-10-06','real-data-pilot-fixed15-metadata-successor01-2026-10-07').replace('!=85','!=86').replace("'effective_attempt_budget':85","'effective_attempt_budget':86")
assert (L/'preflight01.py').read_text()==expected
assert (L/'root_io.py').read_text()==(P/'root_io.py').read_text().replace(a,b)
original=R/'tradingagents/research/onchain_replication/archive_control_history.py';candidate=W/'candidate/archive_control_history.py';old=original.read_text();new=candidate.read_text()
oldtree=ast.parse(old);newtree=ast.parse(new);oldclass=next(n for n in oldtree.body if isinstance(n,ast.ClassDef) and n.name=='Interval');newclass=next(n for n in newtree.body if isinstance(n,ast.ClassDef) and n.name=='Interval')
old_doc=ast.get_source_segment(old,oldclass.body[0]);new_doc=ast.get_source_segment(new,newclass.body[0]);inverse=new.replace(new_doc,old_doc,1).replace('if self.last is not None and not force:','if self.last is not None:',1).replace('(now if force or previous is None else previous)','(now if previous is None else previous)',1);assert inverse==old
assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(oldtree,include_attributes=False)
G=ld(P/'gate01.json');E=next(iter(G['experiments'].values()))
for name in ['archive_dispatch','archive_owner_operations','imported_authority_lease','imported_authority_interval','real_pilot_import_caller','compact_mcm','model','real_pilot_training']:
 p=R/('tradingagents/research/onchain_replication/'+name+'.py');assert ref(p)['sha256']==E['source_files'][str(p.relative_to(R))]
assert ld(R/E['inputs']['imported_authority_lease']['path'])['max_stale_ms']==60000
checks=ld(H/'INTERVAL_CHECK01.json');assert checks['decision']=='passed' and checks['candidate']==ref(candidate) and len(checks['cases'])==12
probe=ld(W/'PROBE_RESULT01.json');v=json.loads(probe['stdout']);assert probe['exit']==0 and probe['killed_reason'] is None and v['status']=='passed' and v['count']==21 and all(x['passed'] for x in v['cases'])
manifest=ld(W/'MANIFEST01.json')
refs=[ref(p) for p in [candidate,W/'INVERSE01.patch',W/'probe01.py',W/'run_probe01.py',W/'PROBE_RESULT01.json',W/'MANIFEST01.json',H/'INTERVAL_CHECK01.json',D/'candidate/real_pilot_storage.py',D/'successor02.py',D/'DEPENDENCIES02.json',L/'preflight01.py',L/'root_io.py']]
o={'schema_version':1,'decision':'accepted','reviewer':'pilot14_review independent retry15 changed-source reviewer','candidates':[ref(candidate),ref(D/'candidate/real_pilot_storage.py')],'references':refs,'findings':[],'checks':['Exact textual and AST inverse: only Interval docstring and two force-related age predicates change.','Both actual callers retain force=not sampled and their complete authenticated audit callbacks; source/object/runtime/claim/native and archive evidence checks unchanged.','Independent12 synthetic actual-Interval cases prove stale sampled use still refuses before audit, forced revalidation only succeeds after complete audit, strict60s duration limit and unchanged sticky clock/policy/error refusal.','Author21-case raw probe independently inspected: actual tiny journal content chain corruption despite metadata repinning, foreign inventory and counter mutation all refused. Extracted actual consumer callsites retain original sampled/forced routing.','Strict identity14→15 only in storage/builder/controls; successor and six dependency refs unchanged; root/preflight exact date/identity/helper/budget86 changes.'], 'semantics_change':'An explicit full archive-history boundary may follow idle time and starts a complete fresh audit, bounded to strictly less than the unchanged60s from that audit entry. It earns a new last timestamp only after success. Sampled use still includes prior age in entry and completion deadlines. This is a prospective boundary revalidation change, not a larger stale cache allowance or a reset after failure.', 'qualification':'Narrow source acceptance; historical14 permanently failed and exact stale age remains unrecorded. Synthetic317s gap is illustrative. Archive-history60s and imported-authority60s are separate controls. No full Context/Owner or actual transport authority was instantiated by the review.', 'not_tested':['No private body, real graph, MCM computation, model fit, Owner/claim/native launch or full end-to-end pipeline.','No measured production audit latency, native memory/throughput/capacity, numerical agreement, financial return/cashflow/fees/funding/exposure or timing-leakage claim.']}
p=H/'SOURCE_REVIEW01.json';p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(ref(p)))
