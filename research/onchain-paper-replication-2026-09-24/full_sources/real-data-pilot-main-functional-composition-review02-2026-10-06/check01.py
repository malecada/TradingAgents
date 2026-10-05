"""Independent bounded source composition authentication; no candidate execution."""
import ast,difflib,hashlib,json,subprocess
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[3];F=D.parent
C=F/'real-data-pilot-main-functional-composition02-2026-10-06'
P=Path('tradingagents/research/onchain_replication')
evidence={}
def raw(p):
 p=Path(p);v=p.read_bytes();evidence[str(p.relative_to(ROOT))]=hashlib.sha256(v).hexdigest();return v
def read(p):return json.loads(raw(p))
def sha(v):return hashlib.sha256(v).hexdigest()
def entries(v):
 x=v.get('files',v.get('members'))
 if isinstance(x,list):return {r['path']:r['sha256'] for r in x}
 return {k:(r if isinstance(r,str) else r['sha256']) for k,r in x.items()}
man=read(C/'MANIFEST01.json')
for name,h in entries(man).items():assert sha(raw(C/name))==h,name
mapping=read(C/'SOURCE_MAP01.json');parents={};members={}
for kind,item in mapping['accepted_evidence'].items():
 path=ROOT/item['manifest'];v=read(path);assert evidence[str(path.relative_to(ROOT))]==item['sha256'];parents[kind]=path.parent;members[kind]=entries(v)
def origin(kind,name):return parents[kind]/'candidate'/P/name
def authenticated(kind,name):
 path=parents[kind]/name;v=read(path);assert evidence[str(path.relative_to(ROOT))]==members[kind][name];return v
def parent_body(kind,path):
 b=raw(path);assert sha(b)==members[kind][str(path.relative_to(parents[kind]))];return b
restored=[]
def inverse(kind,name,before,edits):
 path=origin(kind,name);body=parent_body(kind,path).decode();original=raw(before)
 if edits and isinstance(edits[0]['new'],list):
  lines=body.splitlines(True)
  for e in reversed(edits):
   assert lines[e['new_start']:e['new_end']]==e['new'];lines[e['new_start']:e['new_end']]=e['old']
  body=''.join(lines)
 else:
  for e in reversed(edits):assert body.count(e['new'])==1;body=body.replace(e['new'],e['old'],1)
 assert body.encode()==original,(kind,name)
 restored.append({'kind':kind,'name':name,'candidate_sha256':sha(raw(path)),'baseline':str(before.relative_to(ROOT)),'baseline_sha256':sha(original),'literal_inverse':True})
for kind in ('policy','checkpoint'):
 for row in authenticated(kind,'SOURCE_DELTA01.json')['files']:
  assert sha(raw(ROOT/row['path']))==row['baseline_sha256'];inverse(kind,Path(row['path']).name,ROOT/row['path'],row['edits'])
for row in authenticated('composition','COMPOSITION01.json')['baselines']:inverse('composition','real_pilot_import_caller.py',Path(row['origin']),row['edits'])
x=authenticated('throughput','SOURCE_DELTA01.json');inverse('throughput','real_pilot_import_caller.py',Path(x['origin']),x['edits'])
for name,row in authenticated('scope1','SOURCE_DELTA01.json').items():inverse('scope1',name,Path(row['baseline']),row['replacements'])
for name,row in authenticated('scope2','SOURCE_DELTA01.json').items():inverse('scope2',name,origin('scope1',name),row['edits'])
for name,row in authenticated('lease','SOURCE_DELTA01.json').items():inverse('lease',name,Path(row['baseline']),row['edits'])
assert restored==read(C/'INVERSE_PROOF01.json')['edges'] and len(restored)==22
patch=[];new=0
for rel,row in mapping['files'].items():
 candidate=raw(C/'candidate'/rel);source=raw(ROOT/row['source'])
 assert candidate==source and sha(candidate)==row['sha256'] and len(candidate)==row['bytes'];ast.parse(candidate)
 source_parent=(ROOT/row['source_manifest']['manifest']).parent
 source_members=entries(read(ROOT/row['source_manifest']['manifest']))
 assert source_members[str((ROOT/row['source']).relative_to(source_parent))]==sha(candidate)
 old=ROOT/rel
 if row['new_module']:assert not old.exists();previous=b'';new+=1
 else:previous=raw(old);assert sha(previous)==row['baseline_sha256']
 patch.extend(difflib.unified_diff(previous.decode().splitlines(True),candidate.decode().splitlines(True),fromfile='/dev/null' if row['new_module'] else 'a/'+rel,tofile='b/'+rel))
assert len(mapping['files'])==15 and new==5
assert ''.join(patch).encode()==raw(C/'overlay.patch')
assert not subprocess.check_output(['git','diff','--name-only',mapping['baseline_commit'],'--','tradingagents'],cwd=ROOT).strip()
refs=read(C/'REVIEW_REFERENCES01.json')
for path,row in refs['reviews'].items():
 review=read(ROOT/path);assert evidence[path]==row['sha256'] and review['decision']==row['decision']
def tree(name):return ast.parse(raw(C/'candidate'/P/name))
def function(name,fn):return next(n for n in tree(name).body if isinstance(n,ast.FunctionDef) and n.name==fn)
def params(node):return {n.arg for n in [*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs]}
execute=function('real_pilot_import_caller.py','execute')
call=next(n for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='run_one_update')
assert {k.arg for k in call.keywords}<=params(function('real_pilot_training.py','run_one_update'))
model_policy=next(k.value for k in call.keywords if k.arg=='model_execution');assert ast.unparse(model_policy)=="p['model_execution']"
text=ast.unparse(execute)
for expected in ("validate_execution(p['model_execution'])","activate(execution, p['imported_authority_lease_input'])","WritableUnion(budget, run.admission.root)","measurements.completed(key, retained)"):
 assert expected in text,expected
assert not mapping['typed_tail_activation_included'] and 'archive_owner_operations.attach' not in text
result={'decision':'source_composition_checks_passed','candidate_manifest_sha256':evidence[str((C/'MANIFEST01.json').relative_to(ROOT))],'final_modules':15,'new_modules_absent':5,'existing_replacements':10,'literal_inverse_edges':22,'exact_patch_delivery':True,'current_tracked_tradingagents_code_matches':mapping['baseline_commit'],'reused_review_count':len(refs['reviews']),'candidate_imports_executed':False,'numerical_or_native_execution':False,'evidence':evidence}
(D/'CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='evidence'},sort_keys=True))
