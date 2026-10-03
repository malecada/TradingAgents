"""Read only explicit source and claim/registration metadata; no authority API imports."""
import ast, hashlib, json
from pathlib import Path
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source')
OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def body(p):
    assert p.is_file() and not p.is_symlink() and p.stat().st_size<=4*1024**2
    return p.read_bytes()
def ref(p):
    b=body(p);return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def tree(p):return ast.parse(body(p))
paths=['tradingagents/research/'+x+'.py' for x in ('admission','verify','lifecycle')]
paths+=['tradingagents/research/onchain_replication/'+x+'.py' for x in ('matching_owner','compact_owner','compact_terminal','compact_cold_proof','compact_native_producer','compact_cold_features','imported_mcm_identity','compact_mcm','compact_training','compact_publication','compact_closure','compact_denominator','compact_features','compact_sampler','provenance','cache','environment')]
refs=[ref(CAP/p) for p in paths]
assert body(CAP/paths[1])==body(ROOT/paths[1])
assert sha(body(CAP/paths[1]))=='3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'
claims=[]
for name in ('compact-cold-inputs-20261003-01','compact-cold-comparison-20261003-01'):
    cp=CAP/'research_runs'/name/'claim.json'; c=json.loads(body(cp));refs.append(ref(cp))
    rp=CAP/c['registration'];r=json.loads(body(rp));refs.append(ref(rp))
    e=c['experiment'];assert e==r['experiments'][name] and c['source']==c['design_source']
    assert not e.get('selection') and not e.get('cumulative_budget_extension') and c['bindings'] is None
    files=e['source_files'];assert len(files)==195
    for p,h in files.items():assert sha(body(CAP/p))==h
    groups=[];items=list(files)
    for start in range(0,len(items),128):
        names=items[start:start+128];n=sum(len(body(CAP/p)) for p in names)
        assert 2*n<=8*1024**2 and all('\n' not in p and '\r' not in p for p in names)
        groups.append({'files':len(names),'body_bytes_single_source':n,'admission_body_bytes_source_and_design':2*n})
    pinned=dict(files);pinned[e['charter']['path']]=e['charter']['sha256'];assert len(pinned)==196
    requests=[(c['source']+':'+p+'\n').encode() for p in pinned]
    assert max(len(x) for x in requests)<64*1024
    assert all(sum(map(len,requests[i:i+128]))<=64*1024 for i in range(0,len(requests),128))
    claims.append({'identity':name,'claim':ref(cp),'registration':ref(rp),'source':c['source'],'design_source':c['design_source'],'inputs':len(c['inputs']),'source_files':len(files),'source_bytes':sum(len(body(CAP/p)) for p in files),'admission_groups':groups,'verify_sources_requests':len(pinned),'verify_sources_groups':2,'verify_claim_fixed_git_show_calls':2,'verify_claim_total_git_children_normal_success':4,'family':c['family'],'effective_attempt_budget':c['effective_attempt_budget']})
# Extract actual functions only to classify calls, never execute package code.
functions={}
for p in paths:
    for node in ast.walk(tree(CAP/p)):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            if node.name in ('_check_source','_check_inputs','read_input','write_json','verify_claim','claims','check_binding','binding_value','verify_current','sources','verify','live','lease','check','observe','_source','_source_files','_guard'):
                functions[p+':'+str(node.lineno)+':'+node.name]={'line':node.lineno,'end':node.end_lineno,'direct_call_expressions':[ast.unparse(n.func) for n in ast.walk(node) if isinstance(n,ast.Call)]}
result={'scope':'STATIC_SOURCE_AND_METADATA_ONLY_NO_AUTHORITY_API_EXECUTION','source_refs':refs,'claims':claims,'actual_main_verify_equals_CAP':True,'structural_per_current_check_source_normal_success':{'admit_fixed_git_children':7,'admit_source_git_children':4,'claims':2,'claim_verification_git_children':8,'total':19,'input_bytes_read_by_admit':0,'source_body_bytes_from_admit_git':2*claims[1]['source_bytes'],'source_local_read_bytes_admit_two_passes':2*claims[1]['source_bytes'],'verify_sources_body_bytes_both_claims':sum(x['source_bytes']+len(body(CAP/json.loads(body(CAP/'research_runs'/x['identity']/'claim.json'))['experiment']['charter']['path'])) for x in claims)},'terminal_check_structural':{'verify_calls':2,'full_original_calls':1,'source_admission_checks':2,'anchor_git_children':2,'git_children_from_these_paths':40,'all_input_hash_passes':2,'additional_nested_calls':'not counted; full _original and guard/stage routines can add work'},'functions':functions,'os_observation':{'origin':'coordinator message, approximately 08:50; not independently sampled','pid':3483181,'rchar':38497607935,'wchar':12211392884,'syscr':14500424,'syscw':2967998,'read_bytes':27688960,'write_bytes':29941760,'attribution':'unknown; counters aggregate process IO, not proof of authority or numeric hotness'}}
(OUT/'readback01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'PASS','source_refs':len(refs),'claims':len(claims),'source_bytes':claims[1]['source_bytes'],'check_source_git_children':19,'terminal_check_direct_nested_git_children':40,'no_authority_APIs_executed':True}))
