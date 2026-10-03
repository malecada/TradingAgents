import ast,hashlib,json,pathlib
P=pathlib.Path(__file__).parent;OLD=P.parent/'neural-cold-feature-handoff-outcome-retention-preparation01-2026-10-03'
allowed={'archive01.py':{'safe_components','direct','relative','pages'},'collector01.py':{'source_context','observed_phase','collect','retain_unverified','reservation_paths','unattempted_observation','capsule_authority_paths'}}
counts={}
for name,changes in allowed.items():
 old=ast.parse((OLD/name).read_text());new=ast.parse((P/name).read_text())
 def reduced(tree):
  return [ast.dump(n,include_attributes=False) for n in tree.body if not (isinstance(n,ast.FunctionDef) and n.name in changes) and not (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'AUTHORITY_NAMESPACES','COMPACT_NAMESPACES'})]
 assert reduced(old)==reduced(new),name
 counts[name]=len(reduced(old))
for name in ('closed_comparison01.py','owned_io.py','test_retention01.py','test_archive01.py','closed-context-baseline01.py','closed-auth-baseline01.py'):
 assert (OLD/name).read_bytes()==(P/name).read_bytes(),name
selected=P.parent/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03/source-bodies/tradingagents/research/onchain_replication/compact_native_producer.py'
original=next(ast.literal_eval(n.value) for n in ast.parse(selected.read_text()).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='NAMESPACES')
current=next(ast.literal_eval(n.value) for n in ast.parse((P/'collector01.py').read_text()).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='COMPACT_NAMESPACES')
assert original==current
print(json.dumps({'status':'passed','unchanged_top_level_AST':counts,'byte_exact_files':6,'compact_namespace_origin':str(selected),'origin_sha256':hashlib.sha256(selected.read_bytes()).hexdigest(),'numerical_imports':False},indent=2))
