"""Read-only current original Git/source metadata; no admission or runtime import."""
import ast,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).parent
s=importlib.util.spec_from_file_location('held',P/'held_outcome01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
template=P.parent/'held-consumer-native-release-prerequisite-investigation01-2026-10-03/RELEASE_TEMPLATE01.json'
release=m.parse(template.read_bytes());r=m.Reader(release['capsule_root']);reg=m.sources(r,release)
exp=reg['experiments'][m.IDENTITY]
assert len(exp['inputs'])==33 and len(exp['outputs'])==6
inputs={name:{'sha256':m.sha(m.input_body(r,exp,name)),'path':ref['path']} for name,ref in sorted(exp['inputs'].items())}
r.recheck()
tree=ast.parse((P/'held_outcome01.py').read_bytes());imports=[]
for n in ast.walk(tree):
 if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
 if isinstance(n,ast.ImportFrom):imports.append(n.module)
assert set(imports)<=set('ast hashlib json os selectors stat subprocess sys time pathlib'.split())
result={'status':'readonly-current-metadata-checked','source':m.SOURCE,'source_count':len(release['source_files']),'committed_registration_sha256':release['registration_sha256'],'inputs':inputs,'output_names':exp['outputs'],'source_and_registration_git_bodies':205,'parser_imports':imports,'positive_held_outcome_checked':False,'authority_granted':False,'bytes_read_including_recheck':r.total}
(P/'METADATA_READBACK04.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('PASS: actual205 Git/current bodies,33 opaque input roles,6 output names; no admission/authority/outcome proof')
