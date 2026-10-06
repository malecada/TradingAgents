"""Exact scalar runtime validators; AST extraction avoids numerical imports."""
import ast,copy,hashlib,importlib.util,json,struct,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];SRC=ROOT/'tradingagents/research/onchain_replication'
PKG='_finite_reservation_proof';package=types.ModuleType(PKG);package.__path__=[];sys.modules[PKG]=package
SOURCES={}
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def cache_key(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def extract(path,name,functions,assignments=(),env=None):
    raw=path.read_bytes();SOURCES[str(path.relative_to(ROOT))]=sha(raw);tree=ast.parse(raw)
    nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in functions) or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in n.targets))]
    assert {n.name for n in nodes if isinstance(n,ast.FunctionDef)}==set(functions)
    m=types.ModuleType(PKG+'.'+name);m.__package__=PKG;m.__dict__.update(env or {});sys.modules[m.__name__]=m
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),m.__dict__);setattr(package,name,m);return m

def full(path,name):
    raw=path.read_bytes();SOURCES[str(path.relative_to(ROOT))]=sha(raw)
    s=importlib.util.spec_from_file_location(PKG+'.'+name,path);m=importlib.util.module_from_spec(s);sys.modules[m.__name__]=m;s.loader.exec_module(m);setattr(package,name,m);return m
io=extract(SRC/'score_batches.py','score_batches',[],['META_LIMIT','MAX_CHUNK_BYTES'])
pair=extract(SRC/'matching_pair.py','matching_pair',[],['LIMIT','ENGINE_FIELDS','POLICY_FIELDS'])
log=extract(SRC/'compact_pair_log.py','compact_pair_log',['_limits'],['FRAME','RECORD_BYTES'],{'struct':struct,'io':io,'require':require})
store=extract(SRC/'restart_retention.py','restart_retention',[],['CONTROL'])
retention=extract(SRC/'stage_retention.py','stage_retention',['validate'],['FORMAT','FIELDS'],{'require':require,'store':store})
compact=extract(SRC/'compact_policy.py','compact_policy',['positive','validate'],['BACKEND','SCHEDULE_FIELDS'],{'require':require,'pair':pair,'io':io,'log':log,'cache_key':cache_key})
full(SRC/'resource_binding.py','resource_binding');full(SRC/'typed_payload_policy.py','typed_payload_policy');full(SRC/'archive_read_control_capacity.py','archive_read_control_capacity');full(SRC/'chunk_durability.py','chunk_durability')
helper=full(HERE/'real_pilot_reservations.py','real_pilot_reservations')
kernel=extract(ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/mcm-array-kernel-2026-10-01/kernel.py','kernel',['validate_policy'],env={'require':require})

def reject(fn):
    try:fn()
    except (ValueError,TypeError,KeyError):return
    raise AssertionError('missing expected refusal')

def run():
    prep=json.loads((HERE/'metadata01/PREPARATION_RESULT01.json').read_bytes())
    final=HERE.parent/'real-data-pilot-final02-2026-10-06'
    refs=prep['builder03_spec']['references'];docs=prep['builder03_result']['inputs']
    def read(role):
        if role in docs:return docs[role]
        ref=refs[role];body=(ROOT/ref['path']).read_bytes();assert len(body)<=4*1024**2 and sha(body)==ref['sha256'];return json.loads(body)
    # The preparer archive intentionally has no bound endpoint. Use the exact
    # final registered public archive metadata, without reading transport secrets.
    docs['archive_policy']=json.loads((final/'inputs03/archive_policy.json').read_bytes())
    selected=next(iter(docs['execution_job']['payload']['representation_jobs'].values()))
    selected['descriptor']['compact_archive_execution']['policy_sha256']=sha((json.dumps(docs['archive_policy'],sort_keys=True,separators=(',',':'))+'\n').encode())
    names=['compact_policy','original_import_stage','mcm_policy','mcm_output_policy','archive_policy','typed_payload','pair_policy']
    args=[read(k) for k in names];keys=docs['pilot']['graph_inputs'];args.append(keys)
    proof=helper.validate(*args)
    for count in proof['pair_occurrences'].values():kernel.validate_policy(args[2]['numeric'],count)
    # Old real metadata fails without any Owner or graph load.
    prior=json.loads((final/'PREPARATION_RESULT05.json').read_bytes())['builder03_spec']['references']
    old=copy.deepcopy(args)
    for index,role in [(0,'compact_policy'),(2,'mcm_policy')]:old[index]=json.loads((ROOT/prior[role]['path']).read_bytes())
    reject(lambda:helper.validate(*old))
    mutations=[(0,['max_workflow_retained_logical_bytes']),(0,['stage_policy','max_retained_logical_bytes']),(0,['stage_policy','log','max_pairs']),(0,['stage_policy','log','max_logical_bytes']),(2,['max_entries']),(2,['numeric','max_output_bytes']),(2,['numeric','max_numeric_bytes'])]
    for index,path in mutations:
        bad=copy.deepcopy(args);target=bad[index]
        for part in path[:-1]:target=target[part]
        target[path[-1]]=None;reject(lambda:helper.validate(*bad))
    for index,path in [(1,['max_stage_bytes']),(3,['max_workflow_output_bytes']),(4,['max_writer_metadata_bytes']),(4,['max_read_metadata_bytes']),(4,['max_stage_bytes']),(4,['max_remote_payload_bytes']),(4,['max_decoded_transfer_bytes']),(4,['max_workflow_metadata_bytes'])]:
        bad=copy.deepcopy(args);bad[index][path[0]]=1;reject(lambda:helper.validate(*bad))
    bad=copy.deepcopy(args);bad[5]['graphs'].pop(next(iter(keys)));reject(lambda:helper.validate(*bad))
    bad=copy.deepcopy(args);bad[6]['limits']['chunk_edges']+=1;reject(lambda:helper.validate(*bad))
    bad=copy.deepcopy(args);bad[0]['stage_policy']['schedule']['max_total_checkpoint_bytes']=1;reject(lambda:helper.validate(*bad))
    # Exact inverse: only seven null fields become finite; no other policy change.
    inverse=copy.deepcopy(args)
    for index,path in mutations:
        target=inverse[index]
        for part in path[:-1]:target=target[part]
        target[path[-1]]=None
    assert inverse[0]==old[0] and inverse[2]==old[2]
    assert docs['execution_job']['resources']==json.loads((final/'PREPARATION_RESULT05.json').read_bytes())['builder03_result']['inputs']['execution_job']['resources']
    # Inspect exact admission placement: helper runs before admitted returns,
    # whereas worker graph import/materialization occurs only downstream.
    original=(SRC/'real_pilot_import_caller.py').read_text();candidate=(HERE/'real_pilot_import_caller.py').read_text()
    start=candidate.index("    if p['schema_version']==2 and 'archive_inputs' in p:\n",candidate.index('def admitted'))
    end=candidate.index('    return name,s,p\n',start)
    assert candidate[:start]+candidate[end:]==original
    block=ast.parse('def early():\n'+candidate[start:end]).body[0].body
    # Actual added code executed with real metadata and helper, not a fabricated Owner.
    ns={'p':docs['pilot'],'s':selected,'d':selected['descriptor'],'ad':types.SimpleNamespace(inputs={**refs,**{k:{'sha256':sha((json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode())} for k,v in docs.items()}}),'_read':lambda ad,name:read(name),'require':require,'__package__':PKG}
    exec(compile(ast.Module(body=block,type_ignores=[]),'actual_added_admission_block','exec'),ns)
    oldread=ns['_read'];ns['_read']=lambda ad,name:old[0] if name=='compact_policy' else oldread(ad,name)
    reject(lambda:exec(compile(ast.Module(body=block,type_ignores=[]),'actual_added_admission_block','exec'),ns))
    storage=(SRC/'real_pilot_storage.py').read_text();updated=(HERE/'real_pilot_storage.py').read_text()
    assert storage.count('eth-paper-real-data-end-to-end-resource-20261006-02')==1 and updated.replace('eth-paper-real-data-end-to-end-resource-20261006-03','eth-paper-real-data-end-to-end-resource-20261006-02')==storage
    assert not any(k in sys.modules for k in ('numpy','torch','scipy','tradingagents'))
    return {'status':'PASS','old_metadata_RED':True,'finite_metadata_GREEN':True,'exact_existing_scalar_validators':SOURCES,'seven_null_refusals':len(mutations),'additional_refusals':11,'policy_inverse_exact':True,'physical_resources_unchanged':True,'actual_added_admission_block_old_RED_new_GREEN':True,'storage_identity_literal_inverse':True,'reservations':proof,'no_numerical_imports_or_graph_bodies_or_claims':True}
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
