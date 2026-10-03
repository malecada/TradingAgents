"""Only exact readonly source fragments. Never execute remote/helper main."""
import ast,copy,hashlib,json,stat,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE.parent/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03';PRIOR=HERE.parent/'neural-cold-feature-handoff-comparison-outcome-local-review01-2026-10-03'
source=OUT/'recover_comparison_outcome02.py';raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='ed851881af69b0055ffd3f0c4e0aa15fc272742be1de3985ac9615375eb830dc';tree=ast.parse(raw)
retained=json.loads((OUT/'OUTCOME_RETENTION01.json').read_bytes());expected={x['path']:x for x in retained['members']};binding=json.loads((OUT/'COLLECTION_ROOT_MODE_BINDING01.json').read_bytes());info=(OUT/'collection01').lstat();assert stat.S_ISDIR(info.st_mode) and binding['original_root']==str(OUT/'collection01') and binding['mode']==509 and binding['device']==info.st_dev and binding['inode']==info.st_ino and stat.S_IMODE(info.st_mode)==509
assert binding['archive_directories_exclude_root']==549 and binding['whole_tree_directories_including_root']==550
start=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='root_binding' for x in n.targets));end=next(i for i,n in enumerate(tree.body[start:],start) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='owned' for x in n.targets));code=compile(ast.Module(body=tree.body[start:end],type_ignores=[]),str(source),'exec')
mutations=['valid','source','collection_sha256','archive_sha256','count','rootcount','inode','mode','boolmode']
results=[]
with tempfile.TemporaryDirectory(dir=HERE,prefix='synthetic-binding-') as tmp:
 out=Path(tmp);p=out/'selected'/str((OUT/'COLLECTION_ROOT_MODE_BINDING01.json').relative_to(ROOT));p.parent.mkdir(parents=True)
 for case in mutations:
  x=copy.deepcopy(binding)
  if case in ('source','collection_sha256','archive_sha256'):x[case]='0'*len(x[case])
  elif case=='count':x['archive_member_count_excludes_root']=2314
  elif case=='rootcount':x['whole_tree_members_including_root']=2313
  elif case=='inode':x['inode']+=1
  elif case=='mode':x['mode']=448
  elif case=='boolmode':x['mode']=True
  p.write_text(json.dumps(x));ns={'json':json,'out':out,'HERE':OUT,'ROOT':ROOT,'retained':retained,'expected':expected,'stat':stat}
  try:exec(code,ns)
  except AssertionError:
   assert case!='valid';results.append({'case':case,'result':'refused'})
  else:assert case=='valid';results.append({'case':case,'result':'accepted_actual_bound_root'})
loop=next(n for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='path');ns={'owned':PRIOR/'restored-collection01','expected':expected,'actual':set(),'stat':stat,'digest':lambda b:hashlib.sha256(b).hexdigest()};exec(compile(ast.Module(body=[loop],type_ignores=[]),str(source),'exec'),ns);assert ns['actual']==set(expected) and len(ns['actual'])==2313
old=ast.parse((OUT/'recover_comparison_outcome01.py').read_bytes())
for name in ('call','digest','put'):
 one=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name);two=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name);assert ast.dump(one,include_attributes=False)==ast.dump(two,include_attributes=False)
# Existing actual tar loop remains byte/AST-identical.
one=next(n for n in old.body if isinstance(n,ast.With) and 'tarfile.open' in ast.unparse(n.items[0].context_expr));two=next(n for n in tree.body if isinstance(n,ast.With) and 'tarfile.open' in ast.unparse(n.items[0].context_expr));assert ast.dump(one,include_attributes=False)==ast.dump(two,include_attributes=False)
r={'schema_version':1,'status':'SOURCE_ONLY_ACCEPTED_RCO1_CLOSED','source_sha256':hashlib.sha256(raw).hexdigest(),'root_binding_sha256':hashlib.sha256((OUT/'COLLECTION_ROOT_MODE_BINDING01.json').read_bytes()).hexdigest(),'actual_source_binding_cases':results,'actual_source_rewalk_members':2313,'archive_members_exclude_root':True,'whole_tree_includes_root':2314,'git_put_digest_tar_AST_unchanged':True,'network_or_full_helper_invocation':False,'arrays_decoded':False}
(HERE/'READBACK02.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
