"""Bounded current18 public metadata review. No private reads or scientific imports."""
from pathlib import Path
import ast, copy, datetime, hashlib, json, os, stat, subprocess, sys, types
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent
D=F/'real-data-pilot-final18-2026-10-08';O=F/'real-data-pilot-final17-2026-10-08'
C=F/'real-data-pilot-fixed18-metadata-successor01-2026-10-08'
NAME='eth-paper-real-data-end-to-end-resource-20261008-18';OLD='eth-paper-real-data-end-to-end-resource-20261008-17'
cache={};evidence={};opened=set()
def audit(event,args):
    if event=='import' and args[0].split('.')[0] in {'numpy','torch','scipy','pandas'}:raise RuntimeError('numerical import prohibited')
    if event=='open' and isinstance(args[0],(str,bytes)):
        path=os.fsdecode(args[0]);opened.add(path)
        if 'research_artifacts/real_pilot_runtime/' in path:raise RuntimeError('private/runtime body read prohibited')
        if Path(path).suffix in {'.npy','.npz','.parquet','.tar'}:raise RuntimeError('scientific/archive body read prohibited')
sys.addaudithook(audit)
def raw(p):
    p=Path(p)
    if not p.is_absolute():p=R/p
    if p not in cache:
        s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
        data=p.read_bytes();z=p.lstat();assert len(data)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
        cache[p]=data
    return cache[p]
def ref(p):
    p=Path(p);p=p if p.is_absolute() else R/p
    return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw(p)).hexdigest()}
def pin(value):
    assert ref(value['path'])['sha256']==value['sha256']
    if 'bytes' in value:assert len(raw(value['path']))==value['bytes']
    evidence[value['path']]=value['sha256'];return json.loads(raw(value['path'])) if str(value['path']).endswith('.json') else None
def record(p):
    v=ref(p);evidence[v['path']]=v['sha256'];return v
def read(p):record(p);return json.loads(raw(p))
def module(p):
    m=types.ModuleType('metadata_review_'+p.stem);m.__file__=str(p);exec(compile(raw(p),str(p),'exec'),m.__dict__);return m
binding=read(D/'BINDING_DRAFT01.json');assert binding['identity']==NAME and binding['status']=='DRAFT_NOT_RELEASED' and binding['binding_review'] is None
private=binding['transport'];assert private['path']=='research_artifacts/real_pilot_runtime/pilot-transport-20261008-18-01/archive_transport01.json'
for role,value in binding.items():
    if isinstance(value,dict) and 'path' in value:
        if role=='transport': evidence[value['path']]=value['sha256']
        else:pin(value)
gate=read(D/'gate01.json');oldgate=json.loads(raw(O/'gate01.json'));exp=gate['experiments'][NAME];oldexp=oldgate['experiments'][OLD]
assert {k:v for k,v in gate['experiments'].items() if k!=NAME}==oldgate['experiments']
assert gate['families']==oldgate['families'] and gate['datasets']==oldgate['datasets']
assert len(exp['source_files'])==298 and len(exp['inputs'])==59
for path,digest in exp['source_files'].items():pin({'path':path,'sha256':digest})
for role,value in exp['inputs'].items():
    if role=='archive_transport':assert all(value[k]==private[k] for k in ('path','sha256'));evidence[value['path']]=value['sha256']
    else:pin(value)
for name,digest in exp['runtime_hashes'].items():pin({'path':'tradingagents/research/'+name,'sha256':digest})
pin(exp['charter']);extension=pin(exp['cumulative_budget_extension']['extension']);budgetreview=pin(exp['cumulative_budget_extension']['review']);pin(extension['allocation'])
assert budgetreview['decision']=='accepted' and budgetreview['extension_sha256']==exp['cumulative_budget_extension']['extension']['sha256'] and extension['cumulative_ceiling']==89
record(F/'real-data-pilot-seventeenth-resource-failed-review01-2026-10-08/budget89-review01/BUDGET89_MACHINE_REVIEW01.json')
readonly=read(D/'ACTUAL_READONLY_ADMISSION01.json');assert readonly['ready'] and readonly['effective_attempt_budget']==89 and readonly['source_pins']==298 and readonly['input_roles']==59 and readonly['experiment']==NAME
SOURCE=readonly['source'];assert SOURCE=='9c54eb2e029b69f0546d30636e9a964e3a460c3d'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==SOURCE
reanchor=read(D/'NUMERICAL_CONTEXT_REANCHOR01.json');pair=read(D/'templates/pair_policy01.json');oldpair=json.loads(raw(R/oldexp['inputs']['pair_policy']['path']))
context=pair['numerical_source'];assert context['commit']==reanchor['source']=='8bf085d83836fd1f1afb7fa8e17cc31c86a98d2e' and len(context['files'])==179
assert set(context['files'])==set(oldpair['numerical_source']['files'])
changes={p:{'before':oldpair['numerical_source']['files'][p],'after':h} for p,h in context['files'].items() if h!=oldpair['numerical_source']['files'][p]}
assert changes==reanchor['changed'] and len(changes)==2 and reanchor['unchanged']==177
assert {k:v for k,v in pair.items() if k!='numerical_source'}=={k:v for k,v in oldpair.items() if k!='numerical_source'}
for p,h in context['files'].items():assert evidence[p]==h
tree=subprocess.check_output(['git','ls-tree','-r','--full-tree',context['commit'],'--',*context['files']],cwd=R,text=True)
tree_map={line.split('\t',1)[1]:line.split('\t',1)[0].split()[2] for line in tree.splitlines()};assert set(tree_map)==set(context['files'])
assert all(hashlib.sha1(b'blob '+str(len(raw(p))).encode()+b'\0'+raw(p)).hexdigest()==oid for p,oid in tree_map.items())
job=read(D/'inputs01/execution_job.json');producer=read(D/'inputs01/producer_plan.json');selected=job['payload']['representation_jobs']['original32'];item=producer['producers'][selected['producer']]
assert selected['descriptor']==item['descriptor'] and selected['descriptor']['pair_execution']['policy_sha256']==exp['inputs']['pair_policy']['sha256']==ref(D/'templates/pair_policy01.json')['sha256']
archive=read(D/'inputs01/archive_policy.json');assert archive['remote_namespace']=='ethpilot-20261008-18'
assert selected['descriptor']['compact_archive_execution']['policy_sha256']==exp['inputs']['archive_policy']['sha256']
# Exact narrow inverse across all eight actual public generated documents.
old_pair_hash=oldexp['inputs']['pair_policy']['sha256'];new_pair_hash=exp['inputs']['pair_policy']['sha256'];old_archive_hash=oldexp['inputs']['archive_policy']['sha256'];new_archive_hash=exp['inputs']['archive_policy']['sha256']
def inverse(v):
    if isinstance(v,dict):return {k:inverse(x) for k,x in v.items()}
    if isinstance(v,list):return [inverse(x) for x in v]
    if isinstance(v,str):return v.replace(NAME,OLD).replace('ethpilot-20261008-18','ethpilot-20261008-17').replace(new_pair_hash,old_pair_hash).replace(new_archive_hash,old_archive_hash)
    return v
for p in sorted((D/'inputs01').iterdir()):assert inverse(read(p))==json.loads(raw(O/'inputs01'/p.name))
# Entry delta is a literal identity/budget change only; no full preflight or launcher execution.
for n in ['preflight01.py','root_io.py']:
    before=raw(O/n).decode();after=raw(D/n).decode();expected=before.replace(OLD,NAME)
    if n=='preflight01.py':
        expected=expected.replace('real-data-pilot-fixed17-metadata-successor01-2026-10-08','real-data-pilot-fixed18-metadata-successor01-2026-10-08').replace('pilot17_index_capacity','pilot18_index_capacity').replace('effective_attempt_budget!=88','effective_attempt_budget!=89').replace("'effective_attempt_budget':88","'effective_attempt_budget':89")
    assert after==expected;compile(after,str(D/n),'exec');record(D/n)
# Thirteen documented metadata edits; no execution of the mutating preparer.
oldprep=raw(O/'prepare17.py').decode();newprep=raw(D/'prepare18.py').decode()
replacements=[("OLD = F/'real-data-pilot-final16-2026-10-07'", "OLD = F/'real-data-pilot-final17-2026-10-08'"),
("HELP = F/'real-data-pilot-fixed17-metadata-successor01-2026-10-08'", "HELP = F/'real-data-pilot-fixed18-metadata-successor01-2026-10-08'"),
("N0 = 'eth-paper-real-data-end-to-end-resource-20261007-16'", "N0 = 'eth-paper-real-data-end-to-end-resource-20261008-17'"),
("NAME = 'eth-paper-real-data-end-to-end-resource-20261008-17'", "NAME = 'eth-paper-real-data-end-to-end-resource-20261008-18'"),
("NS0 = 'ethpilot-20261007-16'", "NS0 = 'ethpilot-20261008-17'"),("NS = 'ethpilot-20261008-17'", "NS = 'ethpilot-20261008-18'"),
('strict17 storage and the lock fix.', 'strict18 storage and the bounded live-guard fix.'),
('templates/job_template03.json','templates/job_template01.json'),('INPUT_DRAFT02.json','INPUT_DRAFT01.json'),
('sampled fresh17 writable union','sampled fresh18 writable union'),('TRANSPORT_REQUEST02.json','TRANSPORT_REQUEST01.json'),
('pilot-transport-20261008-17-01','pilot-transport-20261008-18-01'),
('Reviewed lock correction and literal strict17 identity only','Reviewed bounded live-guard correction and literal strict18 identity only')]
for before,after in replacements:assert oldprep.count(before)==1;oldprep=oldprep.replace(before,after)
assert oldprep==newprep;compile(newprep,str(D/'prepare18.py'),'exec');record(D/'prepare18.py')
for k in exp:
    if k not in {'charter','cumulative_budget_extension','question','source_files','inputs'}:assert exp[k]==oldexp[k],k
def successor_path(p):
    return p.replace('real-data-pilot-final17-','real-data-pilot-final18-').replace('real-data-pilot-fixed17-','real-data-pilot-fixed18-').replace('real-data-pilot-retry17-','real-data-pilot-retry18-').replace('PROPOSED88_01','PROPOSED89_01').replace('real-data-pilot-sixteenth-resource-failed-review01-2026-10-08/EXTENSION88_REVIEW01.json','real-data-pilot-seventeenth-resource-failed-review01-2026-10-08/budget89-review01/EXTENSION89_REVIEW01.json')
assert {successor_path(p) for p in oldexp['source_files']}==set(exp['source_files'])
assert len(set(exp['source_files'])-set(oldexp['source_files']))==10
assert {p for p in set(exp['source_files'])&set(oldexp['source_files']) if exp['source_files'][p]!=oldexp['source_files'][p]}==set(changes)
assert exp['inputs']['execution_workspace']==oldexp['inputs']['execution_workspace']
assert set(exp['inputs'])==set(oldexp['inputs'])
# Recompute only pure stdlib metadata; no originals, private transport or arrays.

successor=module(C/'successor02.py');record(C/'successor02.py');deps=read(C/'DEPENDENCIES02.json')
for v in deps.values():pin(v)
draft=read(D/'INPUT_DRAFT01.json');saved=read(D/'PREPARATION_RESULT01.json');actual=successor.prepare(R,draft);assert actual==saved
baseline=read(D/'BASELINE01.json');declared=draft['protocol']['physical_baseline'];observed=baseline['result']['observation'];assert declared['evidence']==binding['baseline']
assert all(declared[k]==observed[v] for k,v in [('logical_bytes','logical_file_bytes'),('allocated_bytes','allocated_bytes'),('entries','entries')])
assert actual['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
assert hashlib.sha256(json.dumps(draft['graphs'],sort_keys=True).encode()).hexdigest()=='73779a7d29bdf98530b3886282339f76edb4feac28b11470a8c147250fe34247'
for mapping in [draft['protocol']['references'],saved['builder03_spec']['references']]:
    for v in mapping.values():pin(v)
# Execute only the unchanged pure inverse function extracted from current preflight.
tree=ast.parse(raw(D/'preflight01.py'));constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['BINDER','INDEX_CAPACITY']}
for v in constants.values():pin(v)
binder=module(R/constants['BINDER']['path'])
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding')
def need(ok,msg):
    if not ok:raise ValueError(msg)
ns={'need':need,'Path':Path,'copy':copy,'OPAQUE_ROLE':'archive_transport'}
exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(D/'preflight01.py'),'exec'),ns)
bound=read(D/'TRANSPORT_BINDING01.json');role=actual['builder03_spec']['template_roles']['archive'];template=pin(actual['builder03_spec']['references'][role])
assert bound['source_request']['prepared']==binding['preparation'] and bound['source_request']['archive_policy']==actual['builder03_spec']['references'][role]
assert {k:bound['source_request']['connection'][k] for k in ('path','sha256')}=={'path':binder.CONNECTION,'sha256':binder.CONNECTION_SHA}
ns['inverse_binding'](actual,template,bound,private,binder.raw,binder.sha)
for role,value in bound['inputs'].items():assert json.loads(raw(exp['inputs'][role]['path']))==value
assert len(bound['inputs'])==8 and bound['private_input']=={'archive_transport':private}
assert draft['protocol']['transport_limits']['namespace']=='ethpilot-20261008-18'
assert exp['inputs']['pair_policy']['path']==str((D/'templates/pair_policy01.json').relative_to(R))
assert all(exp['inputs'][k]==oldexp['inputs'][k] for k in exp['inputs'] if k not in set(bound['inputs'])|{'archive_transport','pair_policy'})
assert job['resources']['start_reserve_bytes']==9126805504 and job['resources']['reserve_bytes']==2684354560
assert job['resources']['memory_max_bytes']==6442450944 and job['resources']['memory_high_bytes']==5368709120
assert job['resources']['disk_floor_bytes']==10737418240 and job['resources']['wall_seconds']==28800
checks=[]
def refuses(label,changed):
    try:ns['inverse_binding'](actual,template,changed,private,binder.raw,binder.sha)
    except ValueError as error:checks.append({'case':label,'refusal':str(error)})
    else:raise AssertionError('counterexample accepted: '+label)
bad=copy.deepcopy(bound);bad['source_request']['private_parent']=bad['source_request']['private_parent'].replace('-18-01','-17-01');refuses('stale private namespace',bad)
bad=copy.deepcopy(bound);bj=bad['inputs']['execution_job'];next(iter(bj['payload']['representation_jobs'].values()))['descriptor']['pair_execution']['policy_sha256']=old_pair_hash;refuses('job alone uses previous pair policy',bad)
bad=copy.deepcopy(bound);bp=bad['inputs']['producer_plan'];bp['producers'][selected['producer']]['descriptor']['pair_execution']['policy_sha256']=old_pair_hash;refuses('producer alone uses previous pair policy',bad)
bad=copy.deepcopy(bound);bad['inputs']['execution_job']['resources']['reserve_bytes']+=1;refuses('host reserve change',bad)
# Gate pair role must resolve to both descriptors, not a stale previous role.
def pair_join(role):
    need(role['sha256']==selected['descriptor']['pair_execution']['policy_sha256']==item['descriptor']['pair_execution']['policy_sha256'],'pair role descriptor join differs')
pair_join(exp['inputs']['pair_policy'])
try:pair_join(oldexp['inputs']['pair_policy'])
except ValueError as error:checks.append({'case':'stale gate pair-policy role','refusal':str(error)})
else:raise AssertionError('stale gate pair role accepted')
record(D/'PAIR_POLICY_ROLE_CORRECTION01.json')
record(D/'PREPARATION_SUCCESSOR_DIFF01.patch')
record(D/'preflight01.py.successor.patch');record(D/'root_io.py.successor.patch')

for p in [D/'REGISTRATION_PREPARATION_FAILURE01.json',D/'PREPARATION_EXIT01.json',D/'TRANSPORT_REQUEST01.json',D/'ALL_INPUT_REFS01.json',D/'INPUT_REFS01.json']:record(p)
# Include actual metadata helper read closure, not recursively accumulated old reviews.
for path in sorted(opened):
    p=Path(path).resolve()
    if p.is_absolute() and p.is_relative_to(F) and p.is_file() and p.suffix in {'.py','.json'}:record(p)
# Gate's current source/input closure must already be committed; readonly/review evidence is later committed by Root.
committed={**exp['source_files'],**{v['path']:v['sha256'] for k,v in exp['inputs'].items() if k!='archive_transport'},exp['charter']['path']:exp['charter']['sha256']}
committed[str((D/'gate01.json').relative_to(R))]=ref(D/'gate01.json')['sha256']
queries=[SOURCE+':'+p for p in committed];output=subprocess.check_output(['git','cat-file','--batch'],cwd=R,input=('\n'.join(queries)+'\n').encode());pos=0
for path in committed:
    end=output.index(b'\n',pos);head=output[pos:end].split();pos=end+1;assert len(head)==3 and head[1]==b'blob';size=int(head[2]);assert output[pos:pos+size]==raw(path) and output[pos+size:pos+size+1]==b'\n';pos+=size+1
assert pos==len(output)
namespaces=[R/'research_runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/NAME,R/'research_artifacts/archive-dispatch-ethpilot-20261008-18',D/'launch-attempt01.json',D/'outer-exit01.json']
assert all(not p.exists() and not p.is_symlink() for p in namespaces)
units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True);assert not units.strip()
result={'focused_counterexamples':checks,'preparer_literal_edits':13,'schema_version':1,'decision':'accepted','identity':NAME,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence':dict(sorted(evidence.items())),'reviewed_draft_binding':ref(D/'BINDING_DRAFT01.json'),'source':SOURCE,'numerical_source_anchor':context['commit'],'source_pins':298,'input_roles':59,'package_pins':179,'package_changed':changes,'metadata_reconstruction_equal':True,'binder_inverse_exact':True,'generated_documents_narrow_inverse_equal':True,'gate_source_and_public_input_committed_closure_count':len(committed),'private_body_reads':0,'private_reference_only':private,'actual_readonly_ready_budget':89,'fresh_namespaces_absent':[str(p.relative_to(R)) for p in namespaces],'native_active_units_empty':True,'status':'DRAFT_COMPOSITION_ACCEPTED_NOT_RELEASED','qualification':'Accept exact current draft composition with binding_review=null. Source179 context/298 source pins/59 roles, pure metadata reconstruction, private-reference binder inverse, source and entry literal deltas checked. Prior17 outcome/recovery and unchanged scientific/resource gates reused; no historical matrix rerun. Root must bind this review, preserve exact inverse, commit/push/readback and obtain separate final release before full original preflight and one unused18 launch. No admission/claim/native launch was performed here.','not_tested':['Private dispatch bytes are excluded; original admission/binder public receipts and final Root opaque validator remain required.','No numerical import/feature/training, raw scientific stores, capacity/throughput/performance, full current installed-runtime inventory or complete preflight.','Namespace/unit observations are instantaneous, not writer exclusion; actual full original launch preflight must repeat checks.']}
record(Path(__file__));result['evidence']=dict(sorted(evidence.items()))
out=H/'BINDING_REVIEW01.json'
with out.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':'accepted','review':ref(out),'evidence_count':len(evidence)},sort_keys=True))
