"""One concrete metadata successor; no scientific input bodies or run claims."""
import copy
import datetime
import hashlib
import json
import os
import subprocess
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
F = HERE.parent
OLD = F/'real-data-pilot-final18-2026-10-08'
HELP = F/'real-data-pilot-fixed19-metadata-successor01-2026-10-08'
N0 = 'eth-paper-real-data-end-to-end-resource-20261008-18'
NAME = 'eth-paper-real-data-end-to-end-resource-20261008-19'
NS0 = 'ethpilot-20261008-18'
NS = 'ethpilot-20261008-19'

def load(p):
    return json.loads(p.read_bytes())

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def ref(p):
    return dict(path=str(p.relative_to(ROOT)),sha256=digest(p),bytes=p.stat().st_size)

def save(p,v):
    body=(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    if p.exists():
        assert p.read_bytes()==body, 'Existing metadata differs; refuse overwrite'
        return
    with p.open('xb') as stream:stream.write(body)

def module(p):
    m=types.ModuleType(p.stem);m.__file__=str(p)
    if p.name=='real_pilot_storage.py':m.__package__='tradingagents.research.onchain_replication'
    exec(compile(p.read_bytes(),str(p),'exec'),vars(m))
    return m

def renamed(v):
    return json.loads(json.dumps(v).replace(N0,NAME).replace(NS0,NS))

def prepare():
    # Root must first adopt/review/commit strict19 storage and the reviewed import-placement correction.
    anchor=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    oldpair=load(OLD/'templates/pair_policy01.json')
    pins={p:digest(ROOT/p) for p in oldpair['numerical_source']['files']}
    assert len(pins)==179
    changed={p:dict(before=h,after=pins[p]) for p,h in oldpair['numerical_source']['files'].items() if pins[p]!=h}
    assert set(changed)=={'tradingagents/research/onchain_replication/'+n for n in ('matching_pair.py','compact_matcher.py','real_pilot_storage.py','job.py','resources.py','real_pilot_import_caller.py')}
    queries=[anchor+':'+p for p in pins]
    returned=subprocess.check_output(['git','cat-file','--batch'],cwd=ROOT,input=('\n'.join(queries)+'\n').encode())
    pos=0
    for p in pins:
        end=returned.index(b'\n',pos);header=returned[pos:end].split();pos=end+1
        assert len(header)==3 and header[1]==b'blob'
        n=int(header[2]);body=returned[pos:pos+n];pos+=n+1
        assert hashlib.sha256(body).hexdigest()==pins[p] and body==(ROOT/p).read_bytes()
    assert pos==len(returned)
    pair=copy.deepcopy(oldpair);pair['numerical_source']=dict(commit=anchor,files=pins)
    (HERE/'templates').mkdir(exist_ok=True)
    save(HERE/'templates/pair_policy01.json',pair)
    for source,target in [('templates/job_template01.json','job_template01.json'),('templates/pilot.json','pilot.json'),('templates/archive_policy.json','archive_policy.json')]:
        value=renamed(load(OLD/source))
        if target=='job_template01.json':value['resources']['start_reserve_bytes']=2684354560
        if target=='pilot.json':value['resource_policy']['start_reserve_bytes']=2684354560
        if target=='job_template01.json':
            next(iter(value['payload']['representation_jobs'].values()))['descriptor']['pair_execution']['policy_sha256']=digest(HERE/'templates/pair_policy01.json')
        save(HERE/'templates'/target,value)
    draft=load(OLD/'INPUT_DRAFT01.json')
    plan=load(ROOT/draft['protocol']['references']['producer_plan']['path'])
    for p in plan['producers'].values():
        p['descriptor']['pair_execution']['policy_sha256']=digest(HERE/'templates/pair_policy01.json')
    save(HERE/'templates/producer_plan.json',plan)
    refs=draft['protocol']['references']
    for role,name in [('pair_policy','pair_policy01.json'),('execution_job','job_template01.json'),('pilot','pilot.json'),('archive_policy','archive_policy.json'),('producer_plan','producer_plan.json')]:
        refs[role]=ref(HERE/'templates'/name)
    resource=load(HERE/'templates/job_template01.json')['resources']
    storage=module(HELP/'candidate/real_pilot_storage.py')
    observation=storage.WritableUnion(resource['storage_budget'],ROOT).check()
    save(HERE/'BASELINE01.json',dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),result=dict(observation=observation),qualification='Actual sampled fresh18 writable union; no numerical bodies, hard quota, atomicity or future-capacity proof.'))
    draft['protocol']['physical_baseline']=dict(evidence=ref(HERE/'BASELINE01.json'),logical_bytes=observation['logical_file_bytes'],allocated_bytes=observation['allocated_bytes'],entries=observation['entries'])
    draft['protocol']['transport_limits']['namespace']=NS
    save(HERE/'INPUT_DRAFT01.json',draft)
    prepared=module(HELP/'successor02.py').prepare(ROOT,draft)
    save(HERE/'PREPARATION_RESULT01.json',prepared)
    oldrequest=load(OLD/'TRANSPORT_REQUEST01.json')
    parent=ROOT/'research_artifacts/real_pilot_runtime/pilot-transport-20261008-19-01'
    parent.mkdir(mode=0o700)
    request=dict(prepared=ref(HERE/'PREPARATION_RESULT01.json'),archive_policy=refs['archive_policy'],connection=oldrequest['connection'],private_parent=str(parent.relative_to(ROOT)),private_leaf='archive_transport01.json')
    save(HERE/'TRANSPORT_REQUEST01.json',request)
    binder=module(F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py')
    bound=binder.bind(ROOT,request)
    save(HERE/'TRANSPORT_BINDING01.json',bound)
    (HERE/'inputs01').mkdir()
    inputrefs={}
    for role,doc in bound['inputs'].items():
        path=HERE/'inputs01'/f'{role}.json'
        with path.open('xb') as s:s.write(binder.raw(doc))
        inputrefs[role]=ref(path)
    inputrefs.update(bound['private_input'])
    save(HERE/'INPUT_REFS01.json',inputrefs)
    save(HERE/'NUMERICAL_CONTEXT_REANCHOR01.json',dict(source=anchor,previous=oldpair['numerical_source']['commit'],files=179,changed=changed,unchanged=173,qualification='Reviewed matching-engine import placement, user-authorized startup-only policy and literal strict19 identity only; matching, motifs, graphs, model, training and caps unchanged.'))
    save(HERE/'PREPARATION_EXIT01.json',dict(status='DRAFT_NOT_RELEASED',experiment=NAME,numerical_source_anchor=anchor,public_documents=len(bound['inputs']),private_references=len(bound['private_input']),scientific_execution=False,claim=False))
    print(json.dumps(dict(status='prepared',identity=NAME,source_anchor=anchor,inputs=len(inputrefs),growth=prepared['inventory']['new_logical_bytes'])))

if __name__=='__main__':prepare()
