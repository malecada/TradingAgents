"""Retained JSON/source-only count audit. No binary payload reads or subprocess."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];I=P.with_name('original-import-post-canonical-timeout-investigation-2026-10-03');F=P.with_name('original-import-native-successor-preparation06-2026-10-03');C=F/'capsule04';PK=C/'tradingagents/research/onchain_replication'
def h(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_bytes())
m=j(I/'MANIFEST01.json');assert h((I/'MANIFEST01.json').read_bytes())=='659b6756fc1a2f93864f39aa0a03934558dbe2035ec3d9f7438a307fa61b2de3'
for row in m['files']:
 b=(I/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
for row in j(I/'receipt-pins01.json')['files']:
 b=(R/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
ex=j(F/'EXECUTION_PRIMARY01.json');ret=j(F/'RETAINED_PRIMARY01.json');assert h((F/'RETAINED_PRIMARY01.json').read_bytes())==ex['retention_sha256'];rows={x['path']:x for x in ret['members']}
census=j(I/'census01.json')
for row in census['selected_source_rows']:
 b=(C/row['path']).read_bytes();assert h(b)==row['sha256'] and len(b)==row['bytes']
claim=j(C/'research_runs/original-import-native-success-20261003-04/claim.json')
for row in census['selected_source_rows']:assert claim['experiment']['source_files'][row['path']]==row['sha256']
def fn(mod,cls,name):
 t=ast.parse((PK/(mod+'.py')).read_bytes())
 if cls:t=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==cls)
 return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
def calls(node,target):return sum(isinstance(n,ast.Call) and ast.unparse(n.func)==target for n in ast.walk(node))
a=calls(fn('compact_matcher','CompactMatcher','_check'),'self.lease')+calls(fn('compact_pair_log','PairLog','_check'),'self.lease');assert a==2
assert calls(fn('compact_matcher','CompactMatcher','_check'),'self.log._check')==1
assert calls(fn('imported_mcm_identity','Target','lease'),'self.execution.check')==1
assert calls(fn('original_import_stage','ImportedExecution','check'),'stage.lease')==1
assert calls(fn('original_import_stage','ImportedExecution','check'),'stage.prepared.execution_contract')==1
b=calls(fn('original_import_stage','ImportStage','lease'),'self.prepared._check')+calls(fn('original_import_preparation','PreparedImport','execution_contract'),'self._check')+calls(fn('original_import_preparation','PreparedImport','stage_contract'),'self._check');assert b==4
assert calls(fn('original_import_preparation','PreparedImport','execution_contract'),'self.stage_contract')==1
assert calls(fn('original_import_preparation','PreparedImport','_check'),'self._bound.check')==1
assert calls(fn('matching_owner','Binding','check'),'run._check_source')==1
f=next(n for n in ast.parse((C/'tradingagents/research/verify.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='verify_claim')
loop=next(n for n in f.body if isinstance(n,ast.For) and ast.unparse(n.target)=='(path, expected)');code=compile(ast.Module(body=[loop],type_ignores=[]),'retained-pinned-loop','exec')
body=b'synthetic-only';pin=h(body);counts=[]
for n in range(1,5):
 name=f'original-import-native-success-20261003-0{n}';p=C/'research_runs'/name/'claim.json';raw=p.read_bytes();assert h(raw)==rows[str(p.relative_to(C))]['sha256'];c=json.loads(raw)
 terminal=j(p.with_name('failed.json'));assert terminal['claim_sha256']==h(raw) and terminal['status']=='failed' and not p.with_name('complete.json').exists()
 pinned=dict(c['experiment']['source_files'])
 for key in ['charter','selection']:
  if c['experiment'].get(key):pinned[c['experiment'][key]['path']]=c['experiment'][key]['sha256']
 log=[]
 def blob(root,commit,path):log.append((commit,path));return body
 ns={'pinned':dict.fromkeys(pinned,pin),'claim':c,'root':None,'_blob':blob,'hashlib':hashlib};exec(code,ns)
 assert c['source']==c['design_source'] and len(log)==len(pinned)
 counts.append({'identity':name,'claim_sha256':h(raw),'source_charter_count':len(pinned),'one_loop_calls':len(log)})
assert [x['source_charter_count'] for x in counts]==[154,157,160,163]
assert ex['native_elapsed_seconds']==1802.3540939379964 and ex['native_sampled_peak_bytes']==395300864 and all(v==0 for v in ex['memory_events'].values()) and ex['complete_mcm_stage_markers']==0
absence=j(F/'ROOT_PROCESS_ABSENCE04.json');assert len(absence['original_pids_absent'])==10 and absence['source_commit']==claim['source']==ex['source_commit']
structural=[]
for row in census['observed_metadata']:
 if row['kind']=='file' and row['path'].endswith('.bin'):
  path=C/row['path'];assert path.stat().st_size==row['bytes']==rows[row['path']]['bytes'];structural.append({'path':row['path'],'bytes':row['bytes']})
print(json.dumps({'manifest_bodies':len(m['files']),'authenticated_selected_sources':len(census['selected_source_rows']),'claims':counts,'one_claims_scan_source_loop_calls':sum(x['one_loop_calls'] for x in counts),'minimum_Target_leases':a,'prepared_checks_per_Target':b,'Binding_checks_per_matchercheck':a*b,'eight_claim_scans_source_loop_calls':a*b*sum(x['one_loop_calls'] for x in counts),'native_elapsed_seconds':ex['native_elapsed_seconds'],'peak':ex['native_sampled_peak_bytes'],'all_memory_events_zero':True,'coordinator_absence_pid_count':10,'binary_members_STAT_ONLY':structural,'binary_bodies_read':0,'actual_wall_share_or_runtime_Git_count':None},indent=2))
