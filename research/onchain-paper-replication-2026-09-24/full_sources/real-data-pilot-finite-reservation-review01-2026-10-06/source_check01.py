"""Independent scalar reconstruction and targeted runtime-contract review only."""
import ast,copy,difflib,hashlib,importlib.util,json,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FS=HERE.parent
C=FS/'real-data-pilot-finite-reservation-correction01-2026-10-06'
SRC=ROOT/'tradingagents/research/onchain_replication'
evidence={}
def readbody(p):
    b=p.read_bytes();assert len(b)<4*1024**2;evidence[str(p.relative_to(ROOT))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(readbody(p))
manifest=read(C/'MANIFEST01.json')
for name,ref in manifest['files'].items():
    b=readbody(C/name);assert len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256']
changes=read(C/'SOURCE_CHANGES01.json')
for c in changes:
    if c.get('before_sha256') is None:
        new=readbody(C/Path(c['target']).name)
        assert hashlib.sha256(new).hexdigest()==c['candidate_sha256']
        assert not (ROOT/c['target']).exists()
        continue
    old=readbody(ROOT/c['target']);new=readbody(C/Path(c['target']).name)
    assert hashlib.sha256(old).hexdigest()==c['before_sha256'] and hashlib.sha256(new).hexdigest()==c['candidate_sha256']
    assert ''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile=c['target'],tofile=c['target']))==readbody(C/(Path(c['target']).name+'.patch')).decode()
    assert ''.join(difflib.unified_diff(new.decode().splitlines(True),old.decode().splitlines(True),fromfile=c['target'],tofile=c['target']))==readbody(C/(Path(c['target']).name+'.inverse.patch')).decode()
spec=importlib.util.spec_from_file_location('reviewed_finite_scalar',C/'check01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
worker_check=m.run();assert worker_check['status']=='PASS'
prep=read(C/'metadata01/PREPARATION_RESULT01.json');refs=prep['builder03_spec']['references'];docs=prep['builder03_result']['inputs']
def meta(role):
    if role in docs:return copy.deepcopy(docs[role])
    r=refs[role];b=readbody(ROOT/r['path']);assert hashlib.sha256(b).hexdigest()==r['sha256'];return json.loads(b)
envelope=meta('compact_policy');stage=envelope['stage_policy'];mcm=meta('mcm_policy');typed=meta('typed_payload');imported=meta('original_import_stage')
rows={k:v['rows'] for k,v in typed['graphs'].items()};pairs={k:32*n for k,n in rows.items()};maximum=max(pairs.values());chunk=stage['score_chunk_cells']
# Independent closed-form accounting reconstructed from actual source contracts.
record=struct.calcsize('<QB7xQdQ32s32s32s')+32;assert record==m.log.RECORD_BYTES==168
meta_bytes=m.io.META_LIMIT;assert meta_bytes==8192
log_bytes=record*stage['log']['max_events']+2*meta_bytes
assert stage['log']['max_events']==2*maximum+stage['schedule']['max_total_checkpoints']
score={k:88*n+(4*((n+chunk-1)//chunk)+4)*meta_bytes for k,n in pairs.items()}
stage_bytes={k:log_bytes+stage['restart_retention']['max_live_bytes']+v for k,v in score.items()}
owner=2*65536+imported['max_stage_bytes']+sum(v+2*meta_bytes for v in stage_bytes.values())
expected={'compact.max_workflow_retained_logical_bytes':owner,'compact.stage.max_retained_logical_bytes':max(stage_bytes.values()),'compact.log.max_pairs':maximum,'compact.log.max_logical_bytes':log_bytes,'mcm.max_entries':maximum,'mcm.numeric.max_output_bytes':4*maximum,'mcm.numeric.max_numeric_bytes':4*maximum+mcm['numeric']['max_buffer_bytes']}
assert envelope['max_workflow_retained_logical_bytes']==owner
assert stage['max_retained_logical_bytes']==max(stage_bytes.values()) and stage['log']['max_pairs']==maximum and stage['log']['max_logical_bytes']==log_bytes
assert mcm['max_entries']==maximum and mcm['numeric']['max_output_bytes']==4*maximum and mcm['numeric']['max_numeric_bytes']==4*maximum+mcm['numeric']['max_buffer_bytes']
assert len(pairs)==7 and sum(rows.values())==12999004 and sum(pairs.values())==415968128
assert owner==207708891392 and max(stage_bytes.values())==30829446656
archive=read(FS/'real-data-pilot-final02-2026-10-06/inputs03/archive_policy.json')
args=[envelope,imported,mcm,meta('mcm_output_policy'),archive,typed,meta('pair_policy'),docs['pilot']['graph_inputs']]
actual=m.helper.validate(*args)
assert actual['owner_logical_reservation_bytes']==owner and all(actual['stage_capacities'][k]['logical_reservation_bytes']==stage_bytes[k] for k in pairs)
# The actual imported route's numeric validator is identical to the scalar proof.
kernel_path=FS/'original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py'
tree=ast.parse(readbody(kernel_path));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_policy')
other=ast.parse(readbody(FS/'mcm-array-kernel-2026-10-01/kernel.py'));other=next(n for n in other.body if isinstance(n,ast.FunctionDef) and n.name=='validate_policy')
assert ast.dump(fn,include_attributes=False)==ast.dump(other,include_attributes=False)
ns={'require':m.require};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(kernel_path),'exec'),ns)
for n in pairs.values():ns['validate_policy'](mcm['numeric'],n)
refusals=[]
def mutate(index,path,value,label):
    bad=copy.deepcopy(args);target=bad[index]
    for k in path[:-1]:target=target[k]
    target[path[-1]]=value
    try:m.helper.validate(*bad)
    except (ValueError,TypeError,KeyError):refusals.append(label)
    else:raise AssertionError('underfunded or malformed accepted: '+label)
for index,path in [(0,['max_workflow_retained_logical_bytes']),(0,['stage_policy','max_retained_logical_bytes']),(0,['stage_policy','log','max_pairs']),(0,['stage_policy','log','max_logical_bytes']),(2,['max_entries']),(2,['numeric','max_output_bytes']),(2,['numeric','max_numeric_bytes'])]:
    v=args[index]
    for k in path:v=v[k]
    mutate(index,path,v-1,'one-below '+'.'.join(path));mutate(index,path,True,'bool '+'.'.join(path))
mutate(3,['max_artifact_bytes'],4*maximum+2*meta_bytes-1,'artifact one-below')
mutate(2,['max_workflow_metadata_bytes'],3*meta_bytes*7-1,'MCM metadata one-below')
graph=max(pairs,key=pairs.get)
for kind,width in m.helper.typed_payload_policy.KINDS.items():
    b=typed['graphs'][graph]['kinds'][kind]
    for key in ('max_operations','max_chunks'):
        mutate(5,['graphs',graph,'kinds',kind,key],b[key]-1,kind+' '+key+' one-below')
    mutate(5,['graphs',graph,'kinds',kind,'max_preserved_bytes'],pairs[graph]*width-1,kind+' payload one-below')
    if kind!='mcm-output-f32':mutate(5,['graphs',graph,'kinds',kind,'max_recovered_bytes'],pairs[graph]*width-1,kind+' recovery one-below')
assert not any(k in sys.modules for k in ('numpy','torch','scipy','tradingagents'))
result={'schema_version':1,'status':'PASS','candidate_manifest_sha256':hashlib.sha256((C/'MANIFEST01.json').read_bytes()).hexdigest(),'exact_patch_and_inverse':True,'worker_scalar_proof_reproduced':worker_check,'independent_seven_finite_values':expected,'per_graph_pair_counts':pairs,'independent_stage_reservations':stage_bytes,'additional_refusals':refusals,'actual_imported_kernel_validator_identical':True,'preclaim_owner_or_native_or_numerical_import':False,'evidence':evidence,'qualification':'Full finite scalar stage/Owner/archive/typed contracts only. These logical totals are not physical local store or capacity results; unchanged physical guards remain mandatory.'}
(HERE/'SOURCE_CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'values':expected,'additional_refusals':len(refusals),'manifest':result['candidate_manifest_sha256']},indent=2))
