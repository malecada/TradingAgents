"""Finite Root-only preparation38 corrected-source rebase; no binder, admission or claim."""
import argparse
import ast
import copy
import datetime
import difflib
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT=Path.cwd().resolve();HERE=Path(__file__).resolve().parent;F=HERE.parent
OLD=F/'real-data-pilot-full35-binding-preparation01-2026-10-11'
EFF=F/'pilot-efficiency-integration-2026-10-11'
STOP=F/'pilot-efficiency-entry-qualification-2026-10-11'
NAME='eth-paper-real-data-end-to-end-resource-20261012-38'
PRIOR='eth-paper-real-data-end-to-end-resource-20261011-35'
BASE_MANIFEST='ecf0606d1c2f6197692ebdeec77264d150b18cb13f688ba2c23e2b378b60ed54'
BINDER_SHA='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'

def raw(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
def load(p):return json.loads(p.read_bytes())
def ref(p):
    b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,value):
    with p.open('xb') as h:h.write(raw(value))

def main(anchor):
    assert re.fullmatch('[0-9a-f]{40}',anchor) and subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==anchor
    assert HERE==F/'real-data-pilot-full38-binding-preparation01-2026-10-12'
    assert ref(OLD/'MANIFEST01.json')['sha256']==BASE_MANIFEST
    for name,pin in load(OLD/'MANIFEST01.json')['files'].items():
        p=OLD/name;assert p.resolve().is_relative_to(OLD) and not p.is_symlink() and ref(p)==pin
    routes=[ROOT/'research_runs'/NAME,ROOT/'research_artifacts/archive-dispatch-ethpilot-20261012-38',ROOT/'research_artifacts/real_pilot_runtime/pilot-transport-20261012-38-01']
    assert all(not os.path.lexists(p) for p in routes)
    source=ROOT/'tradingagents/research/onchain_replication/job.py'
    function=next(n for n in ast.parse(source.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='required_sources')
    scope={'Path':Path,'__file__':str(source)}
    exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),scope)
    files={p:ref(ROOT/p)['sha256'] for p in sorted(scope['required_sources']())};assert len(files)==205
    queries='\n'.join(anchor+':'+p for p in files)+'\n'
    output=subprocess.check_output(['git','-c','core.packedGitWindowSize=16m','-c','core.packedGitLimit=64m','cat-file','--batch'],input=queries.encode())
    offset=0;joined=[]
    for path,digest in files.items():
        end=output.index(b'\n',offset);fields=output[offset:end].split();assert len(fields)==3 and fields[1]==b'blob'
        size=int(fields[2]);offset=end+1;body=output[offset:offset+size];offset+=size
        assert output[offset:offset+1]==b'\n';offset+=1
        assert body==(ROOT/path).read_bytes() and hashlib.sha256(body).hexdigest()==digest,path
        joined.append({'path':path,'bytes':size,'sha256':digest,'git_oid':fields[0].decode()})
    assert offset==len(output)
    docs={p.stem:load(p) for p in (OLD/'public01').glob('*.json')};assert len(docs)==12
    baseline=copy.deepcopy(docs)
    selection=load(EFF/'SUCCESSOR_SELECTION_DRAFT01.json')
    assert ref(EFF/'SUCCESSOR_MCM_DRAFT01.json')['sha256']==selection['draft_sha256']
    docs['mcm_policy']=load(STOP/'QUALIFICATION_MCM_DRAFT01.json')
    assert docs['mcm_policy']['entry_qualification']['experiment_id']=='eth-paper-real-data-end-to-end-resource-20261011-36'
    docs['mcm_policy']['entry_qualification']['experiment_id']=NAME
    assert docs['mcm_policy']['entry_qualification']=={'format':'genuine-mcm-entry-preparation-only-v1','experiment_id':NAME,'graph_hash':sorted(docs['pilot']['graph_inputs'])[0]}
    without_stop=copy.deepcopy(docs['mcm_policy']);without_stop.pop('entry_qualification')
    assert without_stop==load(EFF/'SUCCESSOR_MCM_DRAFT01.json')
    docs['typed_payload']=load(EFF/'SUCCESSOR_TYPED_DRAFT01.json')
    docs['pair_policy']['numerical_source']={'commit':anchor,'files':files}
    docs['archive_policy']['remote_namespace']='ethpilot-20261012-38'
    docs['archive_transport']['namespace']='ethpilot-20261012-38'
    assert docs['archive_policy']['transport_identity'] is None and docs['archive_transport']['connection'] is None
    for resources in (docs['execution_job']['resources'],docs['pilot']['resource_policy']):
        assert resources['storage_budget']['experiment']==PRIOR
        assert resources['storage_budget']['roots'][1]==str(ROOT/'research_runs'/PRIOR)
        resources['storage_budget']['experiment']=NAME;resources['storage_budget']['roots'][1]=str(ROOT/'research_runs'/NAME)
    assert docs['execution_job']['resources']==docs['pilot']['resource_policy']
    pilot=docs['pilot'];assert 'expected_code_cache_input' not in pilot and 'phase_timing_policy' not in pilot
    pilot['expected_code_cache_input']='expected_code_cache';pilot['phase_timing_policy']='exclusive-wall-cpu-v1'
    pilot['outputs']['timing']='phase-timing.json';pilot['cell_id']='real-eth-first-graph-entry-preparation-resource38'
    lease=ROOT/'tradingagents/research/onchain_replication/imported_authority_lease.py'
    expected=next(n.value for n in ast.parse(lease.read_bytes()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED_POLICY' for t in n.targets))
    save(HERE/'EXPECTED_CODE_POLICY01.json',ast.literal_eval(expected))
    for value in (docs['execution_job']['payload']['representation_jobs']['original32'],docs['producer_plan']['producers']['original32']):
        for role,key in [('pair_policy','pair_execution'),('archive_policy','compact_archive_execution')]:value['descriptor'][key]['policy_sha256']=hashlib.sha256(raw(docs[role])).hexdigest()
    # Four scientific bodies, all seven whole graphs and original training scope are preserved.
    for role in ('compact_policy','original_import','resource_population_plan','mcm_output_policy'):assert docs[role]==baseline[role]
    for key in ('decisions','graph_inputs','graph_sequences','batch_size','seed','lookback_days','model_execution','model_input','training_input','indices'):assert pilot[key]==baseline['pilot'][key]
    (HERE/'public01').mkdir()
    for role,value in docs.items():save(HERE/'public01'/(role+'.json'),value)
    prepared=load(OLD/'PREPARED01.json');prepared['builder03_result']['inputs']={k:v for k,v in docs.items() if k!='archive_policy'}
    assert len(prepared['builder03_result']['inputs'])==11
    prepared['builder03_spec']['references']['archive_policy']=ref(HERE/'public01/archive_policy.json');save(HERE/'PREPARED01.json',prepared)
    request=load(OLD/'REQUEST01.json');request.update(prepared=ref(HERE/'PREPARED01.json'),archive_policy=ref(HERE/'public01/archive_policy.json'),private_parent='research_artifacts/real_pilot_runtime/pilot-transport-20261012-38-01');save(HERE/'REQUEST01.json',request)
    # Retain the opaque connection reference; never open its body.
    refs=load(OLD/'PUBLIC_INPUT_REFS_DRAFT01.json');assert len(refs)==71 and 'archive_transport' not in refs
    for role in docs:
        if role!='archive_transport':
            pin=ref(HERE/'public01'/(role+'.json'));refs[role].update(path=pin['path'],sha256=pin['sha256'])
    assert 'expected_code_cache' not in refs
    pin=ref(HERE/'EXPECTED_CODE_POLICY01.json');refs['expected_code_cache']={k:pin[k] for k in ('path','sha256')};refs['expected_code_cache']['dataset']='eth'
    assert len(refs)==72;save(HERE/'PUBLIC_INPUT_REFS_DRAFT01.json',refs)
    before=(OLD/'bind_actual01.py').read_text();after=before.replace('20261011-35','20261012-38').replace('len(refs)==72','len(refs)==73');ast.parse(after)
    assert before!=after
    with (HERE/'bind_actual01.py').open('x') as h:h.write(after)
    save(HERE/'CURRENT_NUMERICAL_GIT_JOIN01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':anchor,'files':joined,'count':205,'actual_git_batch_exit':0,'actual_git_batch_stdout_sha256':hashlib.sha256(output).hexdigest(),'claim':False})
    patches=[]
    for role in sorted(docs):patches.extend(difflib.unified_diff(raw(baseline[role]).decode().splitlines(True),raw(docs[role]).decode().splitlines(True),fromfile='full35/public01/'+role,tofile='full38/public01/'+role))
    patches.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='full35/bind_actual01.py',tofile='full38/bind_actual01.py'))
    with (HERE/'LITERAL_PATCH01.diff').open('x') as h:h.write(''.join(patches))
    save(HERE/'ROOT_PREPARATION01.json',{'status':'DRAFT_NOT_RELEASED','source_anchor':anchor,'predecessor_manifest':ref(OLD/'MANIFEST01.json'),'source_bodies':205,'public_documents':12,'draft_input_roles':72,'bound_input_roles':73,'bound_gate_outputs':9,'binder_executed':False,'claim':False,'scientific_method_change':False,'preparation_exception':'EntryPreparationComplete','whole_pilot_unchanged_cells':415968128,'whole_pilot_unchanged_graphs':7,'physical_caps_changed':False,'existing_binder_sha256':BINDER_SHA,'fresh_absent_paths':[str(p.relative_to(ROOT)) for p in routes]})
    save(HERE/'MANIFEST01.json',{'status':'DRAFT_NOT_RELEASED','files':{str(p.relative_to(HERE)):ref(p) for p in sorted(HERE.rglob('*')) if p.is_file()},'scope':'Fixed38 corrected preparation-only public rebinding. Actual205 committed source joins; explicit code-cache/timing/C05/continuation/metadata controls. No binder, admission, claim, physical capacity or release.'})
    print(json.dumps({'status':'DRAFT_NOT_RELEASED','source_bodies':205,'draft_roles':72,'bound_roles':73,'claim':False}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--anchor',required=True);main(parser.parse_args().anchor)
