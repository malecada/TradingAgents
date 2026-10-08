import ast,hashlib,json,pathlib
ROOT=pathlib.Path.cwd();HERE=pathlib.Path(__file__).resolve().parent
C=HERE.parent/'real-data-pilot-sharded-checkpoint-candidate01-2026-10-08';S=ROOT/'tradingagents/research/onchain_replication'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(C/'MANIFEST02.json')=='90170c393b71c2142ce65fc8b6f44c9763b92367b2a1695aa723e705608b0129'
m=json.loads((C/'MANIFEST02.json').read_text())
for n,v in m['sources'].items():
 assert sha(C/n)==v['sha256']
 if v['main_baseline_sha256'] is not None:assert sha(S/n)==v['main_baseline_sha256']
for n,h in m['evidence'].items():assert sha(C/n)==h
# Compare complete numerical functions independently, and default serialization bodies
# after removing exactly the optional dispatch and new keyword parameter.
def defs(p):return {x.name:x for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef)}
dump=lambda node:ast.dump(node,include_attributes=False)
checked=[]
for name in ('matching_annealing.py','matching_checkpoint.py','matching_hardening.py'):
 old=defs(S/name);new=defs(C/name)
 for n in set(old)-{'save','load'}:
  assert dump(old[n])==dump(new[n]),(name,n);checked.append(name+':'+n)
 for n in ('save','load'):
  node=new[n];assert node.args.kwonlyargs[-1].arg=='checkpoint_layout' and isinstance(node.args.kw_defaults[-1],ast.Constant) and node.args.kw_defaults[-1].value is None
  node.args.kwonlyargs.pop();node.args.kw_defaults.pop();first=node.body.pop(0)
  assert isinstance(first,ast.If) and isinstance(first.test,ast.Compare) and isinstance(first.test.left,ast.Name) and first.test.left.id=='checkpoint_layout'
  assert dump(node)==dump(old[n]),(name,n);checked.append(name+':default '+n)
r=json.loads((HERE/'CHECKS01.json').read_text());assert r['status']=='PASS' and r['count']==43
assert r['selected_io_scratch_bytes']==3*(262144*8+128)+65536==6357376
assert 16384<r['largest_fixture_proof_bytes']<=65536
# Cardinality geometry independent of implementation helper.
assert (350110*24+262144-1)//262144==33
summary={'status':'ACCEPTED_NARROW_SOURCE_ONLY','candidate_manifest_sha256':sha(C/'MANIFEST02.json'),'source_bodies':9,'all_evidence_hashes_match':True,'baseline_sources_match':True,'unchanged_functions_and_legacy_serialization':checked,'focused_checks':43,'largest_pair_chunks_per_array':33,'largest_pair_total_numeric_chunks':132,'largest_proof_bytes':r['largest_fixture_proof_bytes'],'io_scratch_bytes':6357376,'execution_admitted':False,'composition_with_other_candidates_reviewed':False}
(HERE/'REVIEW01.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
