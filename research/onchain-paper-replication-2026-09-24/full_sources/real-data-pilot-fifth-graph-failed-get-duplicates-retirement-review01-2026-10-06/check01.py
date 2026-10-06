"""Independent metadata/source predicate checks; never calls execute/inactive/unlink."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os
M=Path.cwd().resolve();D=Path(__file__).resolve().parent;F=D.parent
A=F/'real-data-pilot-fifth-graph-failed-get-duplicates-retirement-preparation01-2026-10-06'
T=F/'real-data-pilot-fifth-graph-failed-get-duplicates-retirement01-2026-10-06'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((A/'MANIFEST01.json').read_bytes())
for name,row in manifest.get('members',manifest.get('files')).items():assert h(A/name)==(row['sha256'] if isinstance(row,dict) else row)
inv=json.loads((A/'INVERSE01.json').read_bytes());old=(M/inv['baseline']).read_text();assert h(M/inv['baseline'])==inv['baseline_sha256'];text=old
for edit in inv['edits']:
 assert text.count(edit['before'])==1; text=text.replace(edit['before'],edit['after'])
assert text==(A/'retire01.py').read_text() and h(A/'retire01.py')==inv['candidate_sha256']
for name in ('retire01.py','prepare01.py'):
 assert (T/name).read_bytes()==(A/name).read_bytes();ast.parse((T/name).read_bytes())
assert h(T/'selection01.json')=='cf4f97fc9e0cef896d52e5404d50af228971034f5afff745c16f10c8c6cd7869'
c=json.loads((T/'selection01.json').read_bytes());assert c['status']=='FROZEN_FOR_REVIEW'
sp=importlib.util.spec_from_file_location('reviewed_failed_get_retirement',T/'retire01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
# Only metadata and current lstat joins; entry and inactive/native methods are not invoked.
m.recovery(M,c);originals,gets=m.selected(M,c)
assert len(originals)==len(gets)==3 and sum(r['recovered']['bytes'] for r in c['rows'])==3278655680
refusals=[]
for kind in ('original-as-delete','wrong-index','null-outcome','wrong-identity','wrong-content','wrong-stat'):
 bad=copy.deepcopy(c)
 if kind=='original-as-delete':bad['rows'][0]['recovered']['path']=bad['rows'][0]['original']['path']
 elif kind=='wrong-index':bad['rows'][0]['index']=14
 elif kind=='null-outcome':bad['recovery_basis']['outcome_review']=None
 elif kind=='wrong-identity':bad['identity']='different-retirement'
 elif kind=='wrong-content':bad['rows'][0]['recovered']['sha256']='0'*64
 else:bad['rows'][0]['recovered']['stat_identity'][1]+=1
 try:
  if kind=='null-outcome':m.recovery(M,bad)
  else:m.selected(M,bad)
 except ValueError as e:refusals.append({'case':kind,'reason':str(e)})
 else:raise AssertionError(kind+' accepted')
for n in ('attempt01.json','complete01.json','failed01.json'):assert not os.path.lexists(T/n)
review=json.loads((M/c['recovery_basis']['outcome_review']['path']).read_bytes())
assert all(not Path('/proc',str(pid)).exists() for pid in review['known_recorded_pids_absent'])
E=dict(c['evidence'])
for p in [A/'MANIFEST01.json',A/'INVERSE01.json',T/'retire01.py',T/'prepare01.py',T/'selection01.json',M/m.COLD]:E[str(p.relative_to(M))]=h(p)
assert E[m.COLD]==m.COLD_SHA
for p,pin in E.items():assert hashlib.sha256(m.metadata(M,p,pin)).hexdigest()==pin
result={'decision':'pass','manifest_sha256':h(A/'MANIFEST01.json'),'literal_inverse_edits':len(inv['edits']),'installed_sources_byte_exact':True,'actual_full30_and_recovered_three_metadata_joins':True,'current_original_get_stat_mode_joins':6,'refusals':refusals,'recorded_pids_absent':len(review['known_recorded_pids_absent']),'payload_reads':0,'inactive_or_execute_invoked':False,'network_native_git_or_deletion':False}
(D/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');E[str((D/'CHECK01.json').relative_to(M))]=h(D/'CHECK01.json')
release={'decision':'accepted','retirement_identity':m.ID,'entry_sha256':h(T/'retire01.py'),'retire_only_three_verified_failed_payload_get_duplicates':True,'selection':{'path':str((T/'selection01.json').relative_to(M)),'sha256':h(T/'selection01.json')},'retire_bytes':3278655680,'remove_only':[str(p.relative_to(M)) for p in gets],'preserve_originals':[str(p.relative_to(M)) for p in originals],'evidence':dict(sorted(E.items())),'preconditions':['Root commits source/selection/release and verifies actual pushed readback before one invocation','Unchanged execute must repeat fresh inactive-consumer/native checks, exact metadata/stats, descriptor locks and one-use reservation'],'scope':'Ordinary redundant recovered-body cache retirement only. Old May30 FAILED/source COMPLETE/graph UNAVAILABLE unchanged. Historical full BYTE recovery is accepted; current remote availability and writer exclusion are not asserted. No original payload, scientific evidence metadata, other recovery or numerical authority is removed or granted.','historical_source':'Backup/source/runtime acceptance pertains to completed3e4736; subsequent package integration is distinct and is not numerical admission.'}
(D/'RELEASE_REVIEW01.json').write_text(json.dumps(release,sort_keys=True,indent=2)+'\n')
print(json.dumps({'decision':'accepted','release_sha256':h(D/'RELEASE_REVIEW01.json'),'source_sha256':h(T/'retire01.py'),'retire_bytes':release['retire_bytes'],'refusals':len(refusals),'evidence_count':len(E)}))
