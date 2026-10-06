"""Independent read-only source/accounting review, with owned synthetic metadata."""
import ast,hashlib,json,tempfile
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
FS=HERE.parent
W=FS/'real-data-pilot-archive-namespace-fix01-2026-10-06'
D4=FS/'real-data-pilot-final04-2026-10-06'
D5=FS/'real-data-pilot-final05-2026-10-06'
REG=FS/'real-data-pilot-retry05-registration01-2026-10-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
manifest=load(W/'MANIFEST01.json')
for p,h in manifest.items():assert sha(W/p)==h,p
old=load(FS/'real-data-pilot-retry04-registration01-2026-10-06/CUMULATIVE_ALLOCATION_PROPOSED75_02.json')
a=load(REG/'CUMULATIVE_ALLOCATION_PROPOSED76_01.json');ext=load(REG/'EXTENSION_PROPOSED76_01.json')
assert a['closed_claims'][:-1]==old['closed_claims'] and len(a['closed_claims'])==29
assert ext['claims']==a['closed_claims'] and ext['allocation']==ref(REG/'CUMULATIVE_ALLOCATION_PROPOSED76_01.json')
assert a['base_family']==old['base_family']==ext['base_family'] and a['base_family']['prior_attempts']==17
assert a['consumed_before']==ext['consumed_before']==46
assert a['unchanged_pending_allocation']==old['unchanged_pending_allocation'] and sum(a['unchanged_pending_allocation'].values())==28
assert a['preserved_reserved_preclaim_allowances']==old['preserved_reserved_preclaim_allowances']
assert a['preserved_reserved_preclaim_allowances'][0]['research_claim'] is None
assert a['proposed_cumulative_ceiling']==ext['cumulative_ceiling']==46+28+1+1==76
assert a['prior_adopted_cumulative_ceiling']==75 and a['prior_reviewed_reserved_ceiling']==74
assert a['identities']==[ext['initial_experiment']]==['eth-paper-real-data-end-to-end-resource-20261006-05']
assert all(a[k]==0 for k in ['refunds','category_transfers','historical_claims_reopened','new_financial_fits'])
assert a['maximum_unique_financial_fits_unchanged']==old['maximum_unique_financial_fits_unchanged']==1420
for row in a['closed_claims']:
 d=ROOT/'research_runs'/row['experiment']
 assert sha(d/'claim.json')==row['claim_sha256'] and sha(d/(row['terminal_status']+'.json'))==row['terminal_sha256']
actual=[]
for p in (ROOT/'research_runs').glob('*/claim.json'):
 c=load(p)
 if c.get('program_id')==a['program_id']:actual.append(p.parent.name)
assert set(actual)=={r['experiment'] for r in a['closed_claims']}
for x in a['preserved_reserved_preclaim_allowances']:
 for key in ['outcome_review','recovery_review','terminal_root']:
  assert sha(ROOT/x[key]['path'])==x[key]['sha256']
assert not (ROOT/'research_runs/eth-paper-real-data-end-to-end-resource-20261006-03/claim.json').exists()
package=ROOT/'tradingagents/research/onchain_replication'
for f in ['job.py','real_pilot_import_caller.py']:assert (W/'baseline'/f).read_bytes()==(package/f).read_bytes()
oldstore=(package/'real_pilot_storage.py').read_bytes();newstore=(D5/'candidate/real_pilot_storage.py').read_bytes()
oldid=b'eth-paper-real-data-end-to-end-resource-20261006-04';newid=oldid[:-2]+b'05'
assert oldstore.count(oldid)==newstore.count(newid)==1 and newstore.replace(newid,oldid)==oldstore
jobold=(W/'baseline/job.py').read_text();jobnew=(W/'candidate/job.py').read_text()
assert jobold.count('        route.admitted(admitted,job)\n')==1
assert jobnew==jobold.replace('        route.admitted(admitted,job)\n','        if route is real_pilot_import_caller:\n            route.admitted(admitted,job,fresh_archive=True)\n        else:\n            route.admitted(admitted,job)\n')
source=(W/'candidate/real_pilot_import_caller.py').read_text();tree=ast.parse(source)
oldsource=(W/'baseline/real_pilot_import_caller.py').read_text()
helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_archive_namespace')
helpertext=ast.get_source_segment(source,helper)
reverse=source.replace(helpertext+'\n\n\n','').replace('def admitted(ad, job, *, fresh_archive=False):','def admitted(ad, job):').replace('        _archive_namespace(ad,s,p,fresh=fresh_archive)\n','')
assert reverse==oldsource
closure=load(D4/'gate01.json')['experiments']['eth-paper-real-data-end-to-end-resource-20261006-04']['source_files']
packagepins={p:h for p,h in closure.items() if p.startswith('tradingagents/')}
assert len(packagepins)==179
for p,h in packagepins.items():assert sha(ROOT/p)==h,p
# Independently execute only three actual helper functions against authenticated fake bytes.
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'require','_read','_archive_namespace'}]
scope={'__package__':'tradingagents.research.onchain_replication','hashlib':hashlib,'json':json,'FILE_MAX':4*1024**2}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'review-selected-helper','exec'),scope)
with tempfile.TemporaryDirectory(dir=HERE,prefix='metadata-') as t:
 root=Path(t);(root/'research_artifacts').mkdir();ad=SimpleNamespace(root=root,experiment_id=newid.decode(),inputs={})
 selected={'compact_archive_transport_input':'transport','compact_archive_input':'archive'};plan={'schema_version':2,'archive_inputs':{}}
 def put(role,value):
  p=root/(role+'.json');p.write_text(json.dumps(value));ad.inputs[role]={'path':p.name,'sha256':sha(p)}
 def call(fresh=True):scope['_archive_namespace'](ad,selected,plan,fresh=fresh)
 def refuse():
  try:call()
  except ValueError:return
  raise AssertionError('unexpected namespace acceptance')
 put('transport',{'namespace':'ethpilot-20261006-02'});put('archive',{'remote_namespace':'ethpilot-20261006-05'});refuse()
 put('transport',{'namespace':'ethpilot-20261006-05'});call()
 p=root/'research_artifacts/archive-dispatch-ethpilot-20261006-05';p.write_bytes(b'preserved evidence');before=sha(p);refuse();call(False);assert sha(p)==before
 put('archive',{'remote_namespace':'ethpilot-20261006-04'});refuse()
# Worker entry call is before ResearchRun.start, and execute/population remains unchanged.
jobtree=ast.parse(jobnew);worker=next(n for n in jobtree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
assert ast.unparse(worker.body[0]).startswith('admitted, job = _admitted(args)')
assert 'require(not os.path.lexists(self.root)' in (package/'archive_dispatch.py').read_text()
result={'decision':'accepted','extension':ref(REG/'EXTENSION_PROPOSED76_01.json'),'allocation':ref(REG/'CUMULATIVE_ALLOCATION_PROPOSED76_01.json'),'candidate_refs':[ref(W/'candidate/job.py'),ref(W/'candidate/real_pilot_import_caller.py'),ref(D5/'candidate/real_pilot_storage.py')],'package_pins_unchanged_before_integration':len(packagepins),'direct_claim_terminal_pairs':len(actual),'prior_claims':17,'equation':'76 = 46 + 28 + 1 reserved closed preclaim03 + 1 new05','synthetic_checks':['authenticated stale02 transport rejected','fresh05 accepted','reserved file refused without mutation','later admission accepts own context','remote04 mismatch refused'],'not_tested':['financial returns/timing/cashflows/fees/funding','real graph/model execution','capacity or throughput','actual private dispatch body','D5 final binding and entry','D4 external recoverability']}
(HERE/'CHECK_STAGE1.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2))
