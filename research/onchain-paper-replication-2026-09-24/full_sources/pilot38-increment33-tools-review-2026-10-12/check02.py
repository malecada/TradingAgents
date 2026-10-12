"""Independent bounded static review; never executes candidate helper code."""
import ast,difflib,hashlib,json,stat
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources'
D=Path(__file__).resolve().parent;C=F/'pilot38-increment33-tools-candidate-2026-10-12';B=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full36increment32'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope=json.loads((C/'TOOL_SCOPE01.json').read_text());checks={};snap={p.name:sha(p) for p in C.iterdir() if p.is_file()}
for relative,pin in json.loads((C/'HELPERS_MANIFEST01.json').read_text()).items():assert sha(C/Path(relative).name)==pin
checks['helper_manifest']=True
forward=[];inverse=[]
for name in ('capture','recover','select'):
 old=(B/(name+'32.py')).read_text();new=(C/(name+'33.py')).read_text();ast.parse(new)
 oldpath=str((B/(name+'32.py')).relative_to(R));newpath=scope['deployment_directory']+'/'+name+'33.py'
 forward.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=oldpath,tofile=newpath))
 inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=newpath,tofile=oldpath))
 if name in ('capture','recover'):
  restored=new
  for before,after in reversed(scope['capture_recover_string_aliases'][name]):restored=restored.replace(after,before)
  assert restored==old;assert ast.dump(ast.parse(restored))==ast.dump(ast.parse(old))
  checks[name+'_literal_ast_inverse']=True
assert ''.join(forward)==(C/'LITERAL_PATCH01.diff').read_text()
assert ''.join(inverse)==(C/'LITERAL_INVERSE01.diff').read_text();checks['published_diffs_exact']=True
for field in ('baseline_actual32_return','baseline_actual32_review','closed36_outcome_review'):
 v=scope[field];p=R/v['path'];assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
for relative,pin in scope['main_source_pins'].items():assert sha(R/relative)==pin
checks['eight_current_source_pins']=True
for relative,v in scope['closed36_owner_receipt_pins_from_original_review'].items():
 p=R/relative;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
checks['closed_owner_receipt_pins']=True
v=scope['opaque38'];p=R/v['path'];s=p.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==v['bytes'] and sha(p)==v['sha256']
opaque={'path':v['path'],'bytes':s.st_size,'sha256':sha(p),'mode':format(stat.S_IMODE(s.st_mode),'04o'),'decoded':False}
# Evaluate literal assignments and the actual pure scope predicate only.
tree=ast.parse((C/'select33.py').read_text());values={}
for node in tree.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
  try:values[node.targets[0].id]=ast.literal_eval(node.value)
  except (ValueError,TypeError):pass
assert values['owned']==scope['mandatory_public_roots'] and len(values['owned'])==19
assert values['main_source_pins']==scope['main_source_pins']
assert values['prior_generated_names']==scope['prior32_exact_postcapture_names']
closed_node=next(n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='closed_scopes')
assert ast.literal_eval(closed_node.value.generators[0].iter)==scope['closed36_owned_roots']
closed=[R/p for p in scope['closed36_owned_roots']];allowed=[F/n for n in values['owned']]+closed
pred=next(n.test.args[0].elt for n in tree.body if isinstance(n,ast.Assert) and isinstance(n.msg,ast.Constant) and n.msg.value=='Git delta outside declared full38increment33 scope')
code=compile(ast.Expression(pred),'<actual finite scope predicate>','eval')
private=v['path'];allowed_files={private}|set(values['fixed_public_names']+values['main_source_names'])|{str((B/n).relative_to(R)) for n in values['prior_generated_names']}
def admit(path):return eval(code,{'relative':path,'allowed_files':allowed_files,'excluded':set(),'ROOT':R,'allowed_roots':allowed})
controls={private:True,str(Path(private).parent/'sibling.json'):False,str(Path(private).parent/'connection.json'):False,
'research_runs/eth-paper-real-data-end-to-end-resource-20261011-35/claim.json':False,
'research_artifacts/onchain_representations/unrelated/a.npy':False,
str(Path(scope['closed36_owned_roots'][3]).parent/'unrelated'/'claim.json'):False}
for root in scope['closed36_owned_roots']:controls[root+'/synthetic-child']=True
assert all(admit(k)==expected for k,expected in controls.items());checks['scope_controls']=controls
# Metadata-only bounded roster inside exact four roots, never reading arrays.
rosters={}
for root in closed:
 assert root.is_dir() and not root.is_symlink();rows=[]
 for p in sorted(root.rglob('*')):
  s=p.lstat();rows.append({'path':str(p.relative_to(R)),'mode':format(stat.S_IMODE(s.st_mode),'04o'),'bytes':s.st_size,'type':'directory' if stat.S_ISDIR(s.st_mode) else 'symlink' if stat.S_ISLNK(s.st_mode) else 'regular' if stat.S_ISREG(s.st_mode) else 'other'})
 assert len(rows)<1000 and all(row['type']!='other' for row in rows)
 assert all(row['bytes']<=64*1024**2 for row in rows if row['type']=='regular')
 rosters[str(root.relative_to(R))]=rows
checks['closed36_metadata_roster']=rosters
outcome=json.loads((R/scope['closed36_outcome_review']['path']).read_text())
critical=[path for path in outcome['evidence'] if path.startswith(('research_runs/','research_artifacts/')) and '/eth-paper-real-data-end-to-end-resource-20261011-36/' in path]
assert critical and all(admit(path) for path in critical);checks['original36_outcome_paths_covered']=critical
for name in scope['prior32_exact_postcapture_names']:assert (B/name).is_file() and not (B/name).is_symlink()
receipt=json.loads((B/'FRESH_GIT_RECOVERY32.json').read_text());capture=json.loads((B/'CAPTURE32.json').read_text())
assert sha(B/'CAPTURE32.json')==receipt['capture']['sha256'];assert sha(B/'SELECTION32.json')==capture['selection']['sha256']
checks['actual32_receipt_selection_chain']=True
checks['fresh_names_absent']={name:not (R/scope['deployment_directory']/name).exists() for name in ('SELECTION33.json','CAPTURE33.json','FRESH_GIT_RECOVERY33.json','pilot38-preparation-increment33.tar','fresh-git-recovered-full38increment33.tar')}
assert all(checks['fresh_names_absent'].values())
assert all(sha(C/name)==pin for name,pin in snap.items())
(D/'CHECK02.json').write_text(json.dumps({'status':'SOURCE_ONLY_ACCEPTED','candidate_snapshot':snap,'checks':checks,'opaque':opaque,'helpers_executed':False,'numerical_imports':False},indent=2)+'\n')
print('SOURCE_ONLY_ACCEPTED; candidate tools never executed; exact current snapshot and scope predicates pass')
