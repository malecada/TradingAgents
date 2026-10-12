import ast,difflib,hashlib,json,subprocess
from pathlib import Path
R=Path.cwd();D=Path(__file__).resolve().parent;F=D.parent;H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full38increment33'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=(H/'select33.py').read_text();new=(H/'select33_02.py').read_text();assert sha(H/'select33_02.py')=='58059f938c185eac57be76b8cc1bd5642c6b8ab67c810446e2966965a42de83d'
assert sha(H/'select33.py')=='9ac94414c8e5269225afd27023fb33e6fc1cafff63f75a78a990d87ebdacac29'
def literals(s):
 out={}
 for n in ast.parse(s).body:
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name):
   try:out[n.targets[0].id]=ast.literal_eval(n.value)
   except (ValueError,TypeError):pass
 return out
ov=literals(old);nv=literals(new);scope=json.loads((H/'TOOL_SCOPE02.json').read_text());pins=nv['extra_git_delta_pins'];assert len(pins)==56 and pins==scope['exact_additional_committed_metadata_pins']
for name,pin in pins.items():
 p=R/name;assert name.startswith(str(F.relative_to(R))+'/') and p.is_file() and not p.is_symlink() and sha(p)==pin
# Independently reverse exactly the stated source changes, leaving every original guard intact.
restored=new.replace('helper_names='+repr(nv['helper_names']),'helper_names='+repr(ov['helper_names']))
block="extra_git_delta_pins="+repr(pins)+"\n# Exact post32 committed metadata bodies only; no additional tree traversal.\nfor relative,expected in extra_git_delta_pins.items():\n    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink() and sha(ROOT/relative)==expected, relative\n    names.add(relative)\n\n"
assert block in restored;restored=restored.replace(block,'')
restored=restored.replace('allowed_files={private_relative}|set(extra_git_delta_pins)|','allowed_files={private_relative}|')
restored=restored.replace("    'exact_additional_committed_metadata_pins':extra_git_delta_pins,\n",'')
assert restored==old and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old))
# Diff payloads must match actual lines; header spelling is only file metadata.
def payload(s):return ''.join(s.splitlines(True)[2:])
a=str((H/'select33.py').relative_to(R));b=str((H/'select33_02.py').relative_to(R))
assert payload(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=a,tofile=b)))==payload((H/'SELECTOR02_PATCH01.diff').read_text())
assert payload(''.join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=b,tofile=a)))==payload((H/'SELECTOR02_INVERSE01.diff').read_text())
base=scope['baseline_source'];head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert head==scope['current_source']
committed=set(subprocess.check_output(['git','diff','--name-only',base,head],text=True).splitlines());working=set(subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).splitlines());s1=json.loads((H/'TOOL_SCOPE01.json').read_text());prior=R/s1['baseline_actual32_return']['path']
roots=[F/n for n in nv['owned']]+[R/n for n in s1['closed36_owned_roots']]
files={s1['opaque38']['path']}|set(nv['fixed_public_names']+nv['main_source_names'])|{str((prior.parent/n).relative_to(R)) for n in nv['prior_generated_names']}|{str((H/n).relative_to(R)) for n in nv['helper_names']}
outside=sorted(n for n in committed|working if n not in files and not any((R/n).is_relative_to(p) for p in roots))
assert set(outside)==set(pins),(set(outside)-set(pins),set(pins)-set(outside))
# Every newly added scope is a file, never its parent directory.
assert nv['owned']==ov['owned'];assert nv['main_source_pins']==ov['main_source_pins']
assert all(str(Path(p).parent/'UNRELATED_SIBLING') not in files|set(pins) and not any((R/Path(p).parent/'UNRELATED_SIBLING').is_relative_to(root) for root in roots) for p in pins)
for name in ('ROOT_CAPTURE_FAILURE33.json','root_select33.stdout','root_select33.stderr'):assert name in nv['helper_names']
failure=json.loads((H/'ROOT_CAPTURE_FAILURE33.json').read_text());assert len(failure['operations'])==1 and failure['operations'][0]['exit_code']==1
for channel in ('stdout','stderr'):
 v=failure['operations'][0][channel];p=R/v['path'];assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
for name,pin in [('capture33.py','bcafc965a1eb0c20fd1062293b36f73458f5cfa057e12c2dfbc685c3c695402f'),('recover33.py','87f4c78eb18b4856d54802eb0f191380f4ba94cbf18aece39d0c6184981a15a2')]:assert sha(H/name)==pin
for name in ('SELECTION33.json','CAPTURE33.json','pilot38-preparation-increment33.tar','FRESH_GIT_RECOVERY33.json'):assert not (H/name).exists()
v={'status':'SOURCE02_ACCEPTED','head':head,'baseline':base,'selector_sha256':sha(H/'select33_02.py'),'exact_extra_pins':pins,'committed_delta_count':len(committed),'working_delta_count':len(working),'outside_old_scope_exactly_pinned':True,'literal_ast_inverse':True,'capture_recover_unchanged':True,'failed_operation_retained':failure,'selection_capture_return_absent':True,'candidate_executed':False,'git_read_only':True}
(D/'SELECTOR02_REVIEW.json').write_text(json.dumps(v,indent=2)+'\n');print('SOURCE02_ACCEPTED; exact56 outside paths; literal/AST inverse; failure evidence and unused capture identity retained')
