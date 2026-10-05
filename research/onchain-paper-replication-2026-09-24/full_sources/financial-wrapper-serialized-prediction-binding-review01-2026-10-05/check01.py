from pathlib import Path
import ast,difflib,hashlib,json,stat
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent
sha=lambda b:hashlib.sha256(b).hexdigest()
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def load(p,pin=None):
 b=p.read_bytes()
 if pin:assert sha(b)==pin,(str(p),'pin')
 return json.loads(b)
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':sha(b),'bytes':len(b)}
A=F/'financial-wrapper-serialized-prediction-preparation01-2026-10-05';R=F/'financial-wrapper-serialized-prediction-review01-2026-10-05';O=F/'financial-wrapper-serialized-continuation-outcome-review01-2026-10-05';P=F/'financial-wrapper-serialized-prediction-parent-preparation01-2026-10-05'
# Authenticate sealed source/review manifests and selected source members, reuse prior unchanged tests.
for directory,pin in [(A,'b7e5adfac87e0774f70c3b8181b06fceb77b59a65c0f6ebf937a20a871726017'),(R,'08fcfaf4a47be74447cddbc4dbee220f25cec15dcaa97135b053ba3a5dd39df7')]:
 manifest=load(directory/'MANIFEST01.json',pin)
 for name in (['operational_source_compatibility.py','financial_wrapper_fixture.py','evaluation.py','preclaim01.py'] if directory==A else ['SOURCE_DRAFT_REVIEW01.json','CHECK01.json','REPORT01.md']):
  row=next(x for x in manifest['members'] if x['path']==name);b=(directory/name).read_bytes();assert sha(b)==row['sha256'] and len(b)==row['bytes'];assert stat.S_IMODE((directory/name).stat().st_mode)==0o444
load(O/'MANIFEST01.json','269a52860c823ef83c776581b40fd7e2727dad9eab74e9719f773c34b35a6ffd')
outcome=load(O/'FULL_OUTCOME_RECOVERY_PROOF01.json','6bbe9790775c716a0657a895382d0d3860fe13e42784b5c66abb711bdfae6861')
assert outcome['scope']['new_checkpoint_states']==99 and outcome['scope']['fresh_flat_bodies']==400 and outcome['original_parent_exit'] is None and outcome['native_PID_history_complete'] is False
qpath=F/'heartbeat-root-checkpoint10-2026-10-04/SERIALIZED_PREDICTION_BOUND_PARENT_DRAFT01.json';q=load(qpath,'301d1b891e4f8807516a2cd6163cbbc6f4d51c61bf0121e54899715770447bf3')
gatepath=Path(q['gate_base']['path']);base=load(gatepath,q['gate_base']['sha256']);cap=gatepath.parents[2];gate=json.loads(q['gate_candidate_text']);identity=q['identity'];e=gate['experiments'][identity]
assert e==q['gate_literal_insert'][identity] and len(base['experiments'])==6 and len(gate['experiments'])==7
inverse=json.loads(q['gate_candidate_text']);del inverse['experiments'][identity];assert inverse==base
text=q['gate_candidate_text'];start=text.index(json.dumps(identity)+':');_,end=json.JSONDecoder().raw_decode(text,start+len(json.dumps(identity))+1);inverse_text=text[:start-1]+text[end:];assert inverse_text==gatepath.read_text()
assert q['role_count']==len(e['inputs'])==29 and sorted(e['inputs'])==q['required_roles']==q['parent_binding']['input_roles']
assert sum(v['path'].endswith('/state.pt') for v in e['inputs'].values())==1
continued=load(cap/e['inputs']['continuation_source_successor']['path'],e['inputs']['continuation_source_successor']['sha256']);before=continued['installed'];bodies=q['new_input_bodies'];edgepath=e['inputs']['prediction_source_successor']['path'];edge=json.loads(bodies[edgepath]);after=edge['installed'];assert len(before)==len(after)==195 and set(before)==set(after)
delta=[{'path':k,'old_sha256':before[k],'new_sha256':after[k]} for k in sorted(before) if before[k]!=after[k]]
assert delta==edge['allowed_delta']==q['source_adoption']['allowed_delta'] and {Path(x['path']).name for x in delta}=={'evaluation.py','financial_wrapper_fixture.py','operational_source_compatibility.py'}
for row in delta:
 assert sha((A/Path(row['path']).name).read_bytes())==row['new_sha256'] and sha((cap/row['path']).read_bytes())==row['old_sha256']
assert after==q['source_adoption']['installed'] and all(e['source_files'][k]==v for k,v in after.items())
assert set(edge)=={'schema_version','kind','continuation_policy_sha256','consumer','installed','allowed_delta','continuation_closure_input','parent_recovery_input'}
assert edge['schema_version']==1 and edge['kind']=='same-family-prediction-source-successor-v1' and edge['continuation_policy_sha256']==e['inputs']['continuation_source_successor']['sha256']
assert edge['consumer']=={'experiment':identity,'cell_id':e['cells'][0]} and edge['continuation_closure_input']=='prediction_continuation_closure' and edge['parent_recovery_input']=='prediction_parent_recovery'
for path,body in bodies.items():
 refs=[v for v in e['inputs'].values() if v['path']==path];assert len(refs)==1
 assert (refs[0]['sha256'] is None) if body is None else sha(body.encode())==refs[0]['sha256']
assert bodies[e['inputs']['prediction_parent_recovery']['path']].encode()==(O/'FULL_OUTCOME_RECOVERY_PROOF01.json').read_bytes()
assert all(bodies[e['inputs'][r]['path']] is None for r in ['prediction_source_successor_review','prediction_source_successor_recovery'])
closure=json.loads(bodies[e['inputs']['source_closure']['path']]);oldclosure=load(cap/e['inputs']['prediction_continuation_closure']['path'],e['inputs']['prediction_continuation_closure']['sha256']);assert closure['installed']==after and oldclosure['installed']==before
assert {k:v for k,v in closure.items() if k!='installed'}=={k:v for k,v in oldclosure.items() if k!='installed'}
prior=json.loads(bodies[e['inputs']['wrapper_prior']['path']]);cp=load(cap/e['inputs']['continued_checkpoint']['path'],outcome['checkpoint_sha256']);claim=load(cap/e['inputs']['continued_claim']['path'],outcome['claim_sha256']);terminal=load(cap/e['inputs']['continued_terminal']['path'],outcome['terminal_sha256']);completion=load(cap/e['inputs']['continued_completion']['path'],e['inputs']['continued_completion']['sha256'])
assert prior['provenance']==cp['provenance'] and prior['parent']==e['parent']==outcome['identity']==claim['experiment_id']==terminal['experiment_id']
assert cp['provenance']['source_commit']==claim['source']==outcome['source'] and cp['provenance']['source_hashes']==sorted(set(before.values()))
assert all(claim['experiment']['source_files'][k]==v for k,v in before.items())
assert cp['members']['state.pt']=={'sha256':e['inputs']['continued_state']['sha256'],'size':497712} and cp['members']['state.pt']['sha256']==outcome['checkpoint_state_sha256']
assert completion['epochs']==100 and completion['sha256']==outcome['checkpoint_sha256']
plan=json.loads(bodies[e['inputs']['wrapper_plan']['path']]);assert plan['phase']=='predict' and plan['experiment']==plan['namespace']==identity and plan['cell_id']==e['cells'][0] and plan['reference_input'] is None
for role in ['model','training','execution_job','runtime_mapping','synthetic_recipe','environment']:
 assert e['inputs'][role]==base['experiments'][outcome['identity']]['inputs'][role]
assert e['cumulative_budget_extension']==base['experiments'][outcome['identity']]['cumulative_budget_extension'] and e['family']==base['experiments'][outcome['identity']]['family'] and e['runtime_hashes']==base['experiments'][outcome['identity']]['runtime_hashes']
assert outcome['accounting']=={'complete':2,'effective':20,'failed':3,'refund':False,'remaining':15,'spent':5}
assert q['accounting_observed']['spent']==5 and q['accounting_observed']['complete']==2 and q['accounting_observed']['failed']==3
for k in ['source','design_source','registration_sha256','gate_sha256','release_refs','proof_reuse_contract']:assert q['parent_binding'][k] is None
assert q['parent_binding']['launch_authority'] is False and q['source_adoption']['source_commit'] is None
oldparent=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-serialized-storage-root-launch-20261005-01/parent01.py');oldraw=oldparent.read_bytes();newraw=(P/'parent01.py').read_bytes();assert sha(oldraw)=='c1ac849e64ec3c49b2154867c645d0d6f00f993757289397b3098a518516519e' and sha(newraw)=='ca52dd65245754cf6ab84f9bea0e94dc7bf791de91124f0ef59d9dec971d512a'
patch=''.join(difflib.unified_diff(oldraw.decode().splitlines(True),newraw.decode().splitlines(True),fromfile='accepted-continuation-caller',tofile='unreleased-prediction-caller'));assert patch==(P/'SOURCE_DELTA01.patch').read_text()
olddefs={n.name:ast.dump(n) for n in ast.parse(oldraw).body if isinstance(n,ast.FunctionDef)};changed=[n.name for n in ast.parse(newraw).body if isinstance(n,ast.FunctionDef) and ast.dump(n)!=olddefs[n.name]];assert changed==['validate_release','preflight']
assert b'SOURCE_BINDING=None' in newraw
proof={'schema_version':1,'kind':'prediction_source_successor_review','decision':'accepted','policy_sha256':sha(bodies[edgepath].encode()),'continuation_policy_sha256':edge['continuation_policy_sha256'],'historical_map_sha256':sha(canonical(before)),'target_map_sha256':sha(canonical(after)),'checker_sha256':after['tradingagents/research/onchain_replication/operational_source_compatibility.py'],'parent_recovery_sha256':e['inputs']['prediction_parent_recovery']['sha256']}
result={'schema_version':1,'decision':'accepted-prospective-source-policy-and-caller-draft-only','draft':ref(qpath),'caller':ref(P/'parent01.py'),'source_review':ref(R/'SOURCE_DRAFT_REVIEW01.json'),'outcome_recovery':ref(O/'FULL_OUTCOME_RECOVERY_PROOF01.json'),'source_delta':delta,'installed_count':195,'old_gate_definitions_preserved':6,'gate_literal_inverse_exact':True,'roles':sorted(e['inputs']),'one_continued_state':True,'caller_changed_functions':changed,'native_cleanup_launch_functions_unchanged':True,'original_parent_exit':None,'native_PID_history_complete':False,'accounting':outcome['accounting'],'source_policy_proof':proof,'prior_focused_tests_reused':True,'numerical_imports':False,'tensor_decoding':False,'admission_or_launch':False,'new_source_recovery':None,'final_release':None}
with (D/'SOURCE_CHECK01.json').open('x') as h:h.write(json.dumps(result,sort_keys=True,indent=2)+'\n')
with (D/'SOURCE_REVIEW_PROOF01.json').open('x') as h:h.write(json.dumps(proof,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps({'check':ref(D/'SOURCE_CHECK01.json'),'proof':ref(D/'SOURCE_REVIEW_PROOF01.json')}))
