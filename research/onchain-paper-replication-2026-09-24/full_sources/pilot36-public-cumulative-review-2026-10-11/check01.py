"""Independent public/claim metadata reconstruction. Never binds or claims."""
import ast, collections, copy, hashlib, json, os, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';OUT=pathlib.Path(__file__).resolve().parent
B=F/'real-data-pilot-full36-binding-preparation01-2026-10-11';C=F/'real-data-pilot-full36-cumulative-preparation01-2026-10-11'
OB=F/'real-data-pilot-full35-binding-preparation01-2026-10-11';OC=F/'real-data-pilot-full35-cumulative-preparation01-2026-10-11'
ANCHOR='f450f11cc44f5287d0daf1bcfcaea469d9347613'
sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
    assert p.resolve()==p and not p.is_symlink() and p.is_file()
    s=p.stat();b=p.read_bytes();t=p.stat()
    assert tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))==tuple(getattr(t,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
    return b
load=lambda p:json.loads(raw(p))
def ref(p):
    b=raw(p);return dict(path=str(p.relative_to(ROOT)),sha256=sha(b),bytes=len(b))
def bound(r):
    b=raw(ROOT/r['path']);assert sha(b)==r['sha256'];return b
def save(n,v):
    with (OUT/n).open('x') as h:json.dump(v,h,indent=2,sort_keys=True);h.write('\n')

# Manifest and all205 source bodies authenticated against the actual Git anchor.
manifest=load(B/'MANIFEST01.json')
for n,r in manifest['files'].items():assert ref(B/n)==r
joins=load(B/'CURRENT_NUMERICAL_GIT_JOIN01.json');assert joins['source']==ANCHOR and len(joins['files'])==joins['count']==205
paths=[r['path'] for r in joins['files']];assert len(set(paths))==205
query=''.join(ANCHOR+':'+p+'\n' for p in paths)
stream=subprocess.check_output(['git','cat-file','--batch'],input=query.encode(),cwd=ROOT);offset=0
for r in joins['files']:
    end=stream.index(b'\n',offset);oid,kind,size=stream[offset:end].split();offset=end+1;body=stream[offset:offset+int(size)];offset+=int(size)
    assert stream[offset:offset+1]==b'\n';offset+=1
    assert kind==b'blob' and oid.decode()==r['git_oid'] and len(body)==r['bytes'] and sha(body)==r['sha256'] and body==raw(ROOT/r['path'])
assert offset==len(stream)
job=ROOT/'tradingagents/research/onchain_replication/job.py'
fn=next(n for n in ast.parse(raw(job)).body if isinstance(n,ast.FunctionDef) and n.name=='required_sources')
env={'Path':pathlib.Path,'__file__':str(job)};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(job),'exec'),env)
assert set(env['required_sources']())==set(paths)
docs={p.stem:load(p) for p in (B/'public01').glob('*.json')};old={p.stem:load(p) for p in (OB/'public01').glob('*.json')};assert set(docs)==set(old) and len(docs)==12
expected=copy.deepcopy(old)
expected['mcm_policy']=load(F/'pilot-efficiency-entry-qualification-2026-10-11/QUALIFICATION_MCM_DRAFT01.json')
expected['typed_payload']=load(F/'pilot-efficiency-integration-2026-10-11/SUCCESSOR_TYPED_DRAFT01.json')
expected['pair_policy']['numerical_source']={'commit':ANCHOR,'files':{r['path']:r['sha256'] for r in joins['files']}}
expected['archive_policy']['remote_namespace']='ethpilot-20261011-36';expected['archive_transport']['namespace']='ethpilot-20261011-36'
name='eth-paper-real-data-end-to-end-resource-20261011-36';following=name[:-2]+'37'
for resources in (expected['pilot']['resource_policy'],expected['execution_job']['resources']):
    resources['storage_budget']['experiment']=name;resources['storage_budget']['roots'][1]=str(ROOT/'research_runs'/name)
expected['pilot'].update(expected_code_cache_input='expected_code_cache',phase_timing_policy='exclusive-wall-cpu-v1',cell_id='real-eth-first-graph-entry-preparation-resource36');expected['pilot']['outputs']['timing']='phase-timing.json'
for descriptor in (expected['producer_plan']['producers']['original32']['descriptor'],expected['execution_job']['payload']['representation_jobs']['original32']['descriptor']):
    for role,key in (('pair_policy','pair_execution'),('archive_policy','compact_archive_execution')):descriptor[key]['policy_sha256']=sha(raw(B/'public01'/(role+'.json')))
assert docs==expected,'Unlisted public semantic change'
before=raw(OB/'bind_actual01.py').decode();after=raw(B/'bind_actual01.py').decode()
assert after==before.replace('20261011-35','20261011-36').replace('len(refs)==72','len(refs)==73')
assert ast.dump(ast.parse(after.replace('20261011-36','20261011-35').replace('len(refs)==73','len(refs)==72')))==ast.dump(ast.parse(before))
binder=F/'real-data-pilot-full29-transport-binding01-2026-10-09/binder02/bind01.py';assert sha(raw(binder))=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
refs=load(B/'PUBLIC_INPUT_REFS_DRAFT01.json');oldrefs=load(OB/'PUBLIC_INPUT_REFS_DRAFT01.json');assert len(refs)==72 and set(refs)==set(oldrefs)|{'expected_code_cache'}
for role,r in refs.items():
    if role in docs:assert r['path']==str((B/'public01'/(role+'.json')).relative_to(ROOT)) and r['sha256']==sha(raw(B/'public01'/(role+'.json')))
    elif role=='expected_code_cache':assert r['sha256']==sha(raw(B/'EXPECTED_CODE_POLICY01.json')) and r['path']==str((B/'EXPECTED_CODE_POLICY01.json').relative_to(ROOT))
    else:assert r==oldrefs[role]
assert 'archive_transport' not in refs
lease_tree=ast.parse(raw(ROOT/'tradingagents/research/onchain_replication/imported_authority_lease.py'))
policy=next(n.value for n in lease_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED_POLICY' for t in n.targets))
assert load(B/'EXPECTED_CODE_POLICY01.json')==ast.literal_eval(policy)
prepared=load(B/'PREPARED01.json');op=load(OB/'PREPARED01.json');expected_prepared=copy.deepcopy(op)
expected_prepared['builder03_result']['inputs']={k:v for k,v in docs.items() if k!='archive_policy'};expected_prepared['builder03_spec']['references']['archive_policy']=ref(B/'public01/archive_policy.json');assert prepared==expected_prepared
request=load(B/'REQUEST01.json');er=load(OB/'REQUEST01.json');er.update(prepared=ref(B/'PREPARED01.json'),archive_policy=ref(B/'public01/archive_policy.json'),private_parent='research_artifacts/real_pilot_runtime/pilot-transport-20261011-36-01');assert request==er
# No opaque connection body is opened. Public unbound transport fields stay null.
assert docs['archive_transport']['connection'] is None and docs['archive_policy']['transport_identity'] is None
from tradingagents.research.onchain_replication import compact_mcm_batched, real_pilot_reservations
import_stage=json.loads(bound(refs['original_import_stage']))
# Reservation validation needs the inherited public transport identity, which the unchanged binder supplies.
archive=copy.deepcopy(docs['archive_policy']);archive['transport_identity']=json.loads(bound(load(F/'real-data-pilot-full35-entry-preparation01-2026-10-11/BINDING01.json')['input_refs']['archive_policy']))['transport_identity']
counts={k:v['rows']*32 for k,v in docs['typed_payload']['graphs'].items()}
for n in counts.values():compact_mcm_batched.validate(docs['mcm_policy'],n)
reservation=real_pilot_reservations.validate(docs['compact_policy'],import_stage,docs['mcm_policy'],docs['mcm_output_policy'],archive,docs['typed_payload'],docs['pair_policy'],list(counts))
assert sum(counts.values())==415968128 and len(counts)==7

# Reconstruct accounting from each actual claim and terminal, independent of helper totals.
extension=load(C/'EXTENSION_PROPOSED108_01.json');allocation=load(C/'CUMULATIVE_ALLOCATION_PROPOSED108_01.json')
oldextension=load(OC/'EXTENSION_PROPOSED106_01.json');oldallocation=load(OC/'CUMULATIVE_ALLOCATION_PROPOSED106_01.json')
assert sha(raw(OC/'EXTENSION_PROPOSED106_01.json'))=='e0a1e3f89926094373e6c58022627e5861cda03064657e88a245129756810b9a'
assert sha(raw(OC/'CUMULATIVE_ALLOCATION_PROPOSED106_01.json'))=='0320608cc703f7c8c2e4f1867bfc478a51efcd62ac70d318b409bd49c55815db'
assert extension['claims'][:-1]==oldextension['claims'] and allocation['closed_claims']==extension['claims']
assert extension['claims'][-1]['experiment']==name[:-2]+'35'
assert json.loads(bound(extension['allocation']))==allocation
family=extension['base_family'];assert family==oldextension['base_family']==allocation['base_family']
actual={};status=collections.Counter();terminal_pins=[]
for directory in (ROOT/'research_runs').iterdir():
    p=directory/'claim.json'
    if not p.is_file():continue
    c=load(p)
    if c.get('program_id')==extension['program_id'] and c.get('family')==family:actual[c['experiment_id']]=c
assert set(actual)=={r['experiment'] for r in extension['claims']} and len(actual)==58
for r in extension['claims']:
    directory=ROOT/'research_runs'/r['experiment'];claim=load(directory/'claim.json');terminal=load(directory/(r['terminal_status']+'.json'))
    assert sha(raw(directory/'claim.json'))==r['claim_sha256'] and sha(raw(directory/(r['terminal_status']+'.json')))==r['terminal_sha256']
    assert claim['experiment_id']==terminal['experiment_id']==r['experiment'] and terminal['claim_sha256']==r['claim_sha256'] and terminal['status']==r['terminal_status']
    assert not os.path.lexists(directory/('failed.json' if r['terminal_status']=='complete' else 'complete.json'))
    status[r['terminal_status']]+=1;terminal_pins.append(r)
assert dict(status)=={'complete':20,'failed':38}
assert max(c.get('effective_attempt_budget',family['attempt_budget']) for c in actual.values())==106
history=load(ROOT/'research/onchain-paper-replication-2026-09-24/history.json');assert history['prior_attempts']==family['prior_attempts']==17 and len(history['lineage'])==17
for p,digest in history['metadata_hashes'].items():assert sha(raw(ROOT/p))==digest
hs=collections.Counter();history_pins=[]
for identity in history['lineage']:
    d=ROOT/'research_runs'/identity;available=[s for s in ('complete','failed') if (d/(s+'.json')).is_file()];assert len(available)==1
    s=available[0];c=load(d/'claim.json');t=load(d/(s+'.json'));cp=ref(d/'claim.json');tp=ref(d/(s+'.json'))
    assert c['experiment_id']==t['experiment_id']==identity and t['claim_sha256']==cp['sha256'] and t['status']==s
    hs[s]+=1;history_pins.append(dict(experiment=identity,claim=cp,terminal=tp))
assert dict(hs)=={'complete':13,'failed':4}
changed={'consumed_before','closed_claims','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','identities','new_fixed_allocation','equation','question','qualification'}
assert set(allocation)==set(oldallocation)
assert all(allocation[k]==oldallocation[k] for k in allocation if k not in changed)
assert allocation['unchanged_pending_allocation']=={'financial_fit_batches':15,'missing_body_batches':12,'remaining_graph_matching_mcm_resource':1}
for record in allocation['preserved_reserved_preclaim_allowances']:
    assert record['research_claim'] is None and not (ROOT/'research_runs'/record['identity']/'claim.json').exists()
    for key in ('outcome_review','recovery_review','terminal_root'):bound(record[key])
assert allocation['consumed_before']==extension['consumed_before']==75
assert allocation['proposed_cumulative_ceiling']==extension['cumulative_ceiling']==75+28+3+2==108
assert allocation['identities']==[name,following] and extension['initial_experiment']==name
assert allocation['new_fixed_allocation']=={'first_graph_entry_preparation_qualification_claims':1,'full_seven_graph_joint_update_resource_pilot_claims':1}
assert allocation['refunds']==allocation['category_transfers']==allocation['historical_claims_reopened']==allocation['new_financial_fits']==0 and allocation['maximum_unique_financial_fits_unchanged']==1420
assert all(not os.path.lexists(ROOT/'research_runs'/n) for n in (name,following))
review={'schema_version':1,'decision':'accepted','extension_sha256':sha(raw(C/'EXTENSION_PROPOSED108_01.json')),'reviewer':'Independent pilot36 public and cumulative reviewer','scope':'Exact proposed108 metadata only:75closed(58actual20complete38failed plus17historical13complete4failed; cumulative33complete42failed)+28unchangedpending+3preservedclosedpreclaimreserved+fixed36preparation and37wholegraph resource claims. All106prior allocations preserved; first adoption36 only; no paper allowance, new financial fits, refund, transfer or reopening. Exact current claim/terminal hashes and original historical joins independently authenticated. No adoption, claim, runtime/capacity admission, external recovery or release. Concrete gate and native obligations remain independent.'}
from tradingagents.research.budget_extensions import effective_budget
review_bytes=(json.dumps(review,sort_keys=True,indent=2)+'\n').encode();review_ref={'path':str((OUT/'EXTENSION108_REVIEW01.json').relative_to(ROOT)),'sha256':sha(review_bytes)}
extension_ref={k:v for k,v in ref(C/'EXTENSION_PROPOSED108_01.json').items() if k!='bytes'}
def metadata_bound(r):return review_bytes if r==review_ref else bound(r)
experiment={'cumulative_budget_extension':{'extension':extension_ref,'review':review_ref}}
assert effective_budget(ROOT,extension['program_id'],name,experiment,family,list(actual.values()),metadata_bound)==108
try:effective_budget(ROOT,extension['program_id'],following,experiment,family,list(actual.values()),metadata_bound)
except ValueError as error:assert 'first-adopter' in str(error)
else:raise AssertionError('37 incorrectly accepted as first adopter')
save('EXTENSION108_REVIEW01.json',review)
assert raw(OUT/'EXTENSION108_REVIEW01.json')==review_bytes
save('CHECK01.json',dict(status='PASS_PUBLIC_AND_ACCOUNTING_METADATA_ONLY',source_anchor=ANCHOR,source_bodies=205,public_documents=12,public_roles=72,bound_roles_expected=73,literal_binder_inverse=True,public_semantic_changes_exhaustive=True,ordinary_validators=True,archive_validation_uses_inherited_public_identity_only=True,cells=sum(counts.values()),current_claims=58,current_dispositions=dict(status),historical_dispositions=dict(hs),cumulative_dispositions=dict(status+hs),closed=75,proposed=108,first_adopter36_pass=True,first_adopter37_rejected=True,genuine_claim=False,terminal_pins=terminal_pins,historical_pins=history_pins,manifest=ref(B/'MANIFEST01.json'),extension=ref(C/'EXTENSION_PROPOSED108_01.json'),allocation=ref(C/'CUMULATIVE_ALLOCATION_PROPOSED108_01.json')))
print(json.dumps(dict(status='PASS_METADATA_ONLY',sources=205,public_roles=72,closed=75,dispositions=dict(status+hs),proposed=108,extension_sha256=review['extension_sha256'])))
