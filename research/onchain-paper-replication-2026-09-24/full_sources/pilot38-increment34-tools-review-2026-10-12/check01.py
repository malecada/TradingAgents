"""Bounded source review; no candidate helper execution, network or imports."""
import ast,difflib,hashlib,json,stat
from pathlib import Path
R=Path.cwd();D=Path(__file__).resolve().parent;F=D.parent
C=F/'pilot38-corrected-registration-increment34-candidate-2026-10-12';B=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full38increment33'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope=json.loads((C/'TOOL_SCOPE01.json').read_text());snapshot={p.name:sha(p) for p in C.iterdir() if p.is_file()}
expected={'select34.py':'e45cec5f96dfd6cf667661341141be95a057572544948603e7e6c05d0e66ae66','capture34.py':'c88cadaf99f5219f3637723ae0e6370efd6b34f7c226cf755483f0caf8906c5c','recover34.py':'31b4d6e1afa13774fd386f176517743ed09028afbb470fd3a58c6b0d9c5f1bd3','HELPERS_MANIFEST01.json':'05eed51c9ac7affea2263c2976f22f8ff4b730a3522eaef3977d2d6057fb62e2'}
for name,pin in expected.items():assert sha(C/name)==pin
manifest=json.loads((C/'HELPERS_MANIFEST01.json').read_text())
for name,pin in manifest.items():assert sha(C/Path(name).name)==pin
patch=[];inverse=[]
for name in ('capture','recover'):
 old=(B/(name+'33.py')).read_text();new=(C/(name+'34.py')).read_text();restore=new
 for before,after in reversed(scope['capture_recover_aliases'][name]):restore=restore.replace(after,before)
 assert restore==old and ast.dump(ast.parse(restore))==ast.dump(ast.parse(old))
 op=str((B/(name+'33.py')).relative_to(R));np=scope['deployment_directory']+'/'+name+'34.py'
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=op,tofile=np));inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=np,tofile=op))
assert ''.join(patch)==(C/'LITERAL_PATCH01.diff').read_text();assert ''.join(inverse)==(C/'LITERAL_INVERSE01.diff').read_text()
tree=ast.parse((C/'select34.py').read_text());values={}
for n in tree.body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name):
  try:values[n.targets[0].id]=ast.literal_eval(n.value)
  except (ValueError,TypeError):pass
pins=values['selected_pins'];assert pins==scope['selected_pins'] and len(pins)==len({p['path'] for p in pins})==67
assert len(values['helper_names'])==7 and len(manifest)==6
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('rglob','glob','walk','run','check_output','Popen','system') for n in ast.walk(tree))
assert {n.names[0].name for n in tree.body if isinstance(n,ast.Import)}=={'datetime'} # One stdlib combined import statement.
for pin in values['baseline_pins']+pins:
 p=R/pin['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==pin['bytes'] and sha(p)==pin['sha256']
 assert str(p.relative_to(R)).startswith('research/onchain-paper-replication-2026-09-24/full_sources/')
assert sum(p['bytes'] for p in pins)==2114684
prior=json.loads((R/scope['baseline']['path']).read_text());capture=json.loads((B/'CAPTURE33.json').read_text());sel=json.loads((B/'SELECTION33.json').read_text())
assert prior['source']=='d4064aace3d26f33a5708ea4c1665a156644de6f' and prior['capture']['sha256']==sha(B/'CAPTURE33.json') and capture['selection']['sha256']==sha(B/'SELECTION33.json')
assert sha(R/scope['accepted_return_review']['path'])=='ea801acb7276c98409a60b7018a38d7e6fc1e3bd16253bc4e4a501c56608d923'
rows={r['path']:r for r in sel['rows']};names={p['path'] for p in pins}
for name in scope['unchanged33_rows_omitted']:
 row=rows[name];p=R/name;assert name not in names and sha(p)==row['sha256'] and p.stat().st_size==row['bytes'] and stat.S_IMODE(p.stat().st_mode)==int(row['mode'],8)
assert not any(Path(p).name in scope['excluded_duplicate_names'] for p in names)
assert not any('/research_artifacts/' in '/'+p or '/research_runs/' in '/'+p or '/full36' in p for p in names)
entry=F/'real-data-pilot-full38-entry-preparation01-2026-10-12'
fixed={'gate01.json':'cd22da5d2d036b54e9f7d17af64d9d51e331e5e7b503d3123acc7c46e9de1489','prepare_entry01.py':'947b0ca2f511ff6ad1531343b126ac7437f833b9ad13a514708ba784a216865f'}
byname={p['path']:p for p in pins}
for leaf,pin in fixed.items():assert byname[str((entry/leaf).relative_to(R))]['sha256']==pin
cell=F/'pilot38-entry-registration-review-2026-10-12/CELL_CORRECTION_REVIEW01.json';assert byname[str(cell.relative_to(R))]['sha256']=='aeade665a2b41f0dbaf006100ae00fbaa636f4443676a24e86d7663796243a92'
gate_name=str((entry/'gate01.json').relative_to(R));assert rows[gate_name]['sha256']!=byname[gate_name]['sha256']
admission=json.loads((entry/'JOB_METADATA_ADMISSION02.json').read_text());assert admission['claim'] is False and admission['native_launched'] is False and admission['exit_code']==0 and admission['source']=='4cb2d366ca3d210156c1f99d2d7b953355648eb1'
for side,pin in admission['raw'].items():assert sha(R/pin['path'])==pin['sha256'] and (R/pin['path']).stat().st_size==pin['bytes'] and pin['path'] in names
result=json.loads((entry/'JOB_METADATA_ADMISSION02.stdout').read_text());assert result=={'ready':True,'effective_attempt_budget':110,'source_pins':1036,'input_roles':73,'registered_cells':['real-eth-first-graph-entry-preparation-resource38'],'claim':False,'native_launched':False}
for name in ('SELECTION34.json','CAPTURE34.json','FRESH_GIT_RECOVERY34.json','pilot38-preparation-increment34.tar'):
 assert not (R/scope['deployment_directory']/name).exists()
assert all(sha(C/name)==pin for name,pin in snapshot.items())
out={'decision':'accepted','qualification':'Source-only fixed increment34 preservation helper acceptance, not actual capture/return, claim or release.','candidate_snapshot':snapshot,'helpers':expected,'fixed_metadata_count':67,'helper_count':7,'metadata_bytes':2114684,'unchanged33_omitted_count':len(scope['unchanged33_rows_omitted']),'capture_recover_literal_AST_inverse':True,'diffs_exact':True,'baseline_source':prior['source'],'baseline_old_gate_sha256':rows[gate_name]['sha256'],'corrected_gate_sha256':fixed['gate01.json'],'actual_job_metadata02':result,'helper_executed':False,'git_network_numerical_executed':False}
(D/'SOURCE_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print('SOURCE_ONLY_ACCEPTED; 67 fixed metadata + 7 helpers; aliases exact; corrected Gate not yet externally recovered')
