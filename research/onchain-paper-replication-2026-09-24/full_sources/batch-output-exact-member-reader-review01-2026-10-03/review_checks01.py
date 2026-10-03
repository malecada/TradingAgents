"""Independent exact-source tiny byte checks; no numerical/authority imports."""
import hashlib,json,os,sys
from pathlib import Path
from types import MappingProxyType
P=Path(__file__).resolve().parent;S=P.with_name('batch-output-exact-member-reader-candidate01-2026-10-03');R=P.parents[3]
def h(b):return hashlib.sha256(b).hexdigest()
m=json.loads((S/'MANIFEST01.json').read_bytes());assert h((S/'MANIFEST01.json').read_bytes())=='bcfae3d5f6279ff3c76b34ab486ced45c81901fd9298fe762f4f5f5efaab318a'
for row in m['files']:
 b=(S/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
for row in json.loads((S/'source-origins01.json').read_bytes())['selected_interfaces']:
 b=(R/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
sys.path.insert(0,str(S));import exact_members01 as reader
root=P/'tiny-same-content-replacement01';root.mkdir();data=bytes(128);(root/'matrix.f32').write_bytes(data)
v={'schema_version':1,'kind':'compact-mcm-output','stage_sha256':'ab'*32,'contract_sha256':'cd'*32,'stage_directory':'/original/stage','scope':{k:'12'*32 for k in reader.SCOPES},'owner':'ef'*32,'rows':1,'motifs':32,'dtype':'<f4','order':'row-major','array_bytes':128,'array_sha256':h(data),'execution_admitted':False}
b=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode();(root/'manifest.json').write_bytes(b)
with reader.open_local(root,kind='mcm-output',document_sha256=h(b)) as r:
 old=r._files['matrix.f32'][0];(root/'replacement.tmp').write_bytes(data);os.replace(root/'replacement.tmp',root/'matrix.f32')
 try:r.check()
 except ValueError as e:before=str(e)
 else:raise AssertionError('replacement unexpectedly accepted before rebase')
 del r._frozen
 files=dict(r._files);record,_=r._read('matrix.f32',128,expected=h(data),extent=128);assert record[0]!=old
 files['matrix.f32']=record;r._files=MappingProxyType(files);r._pin=tuple(sorted(files.items()));r._frozen=True
 assert r.read_part('matrix.f32',0,8)==data[:8];r.check()
assert r.closed is True
assert not {'numpy','torch','scipy'}&set(sys.modules)
print(json.dumps({'manifest_files':len(m['files']),'source_refs':11,'before_rebase_refusal':before,'ordinary_delattr_guard_bypass':True,'same_content_new_inode_rebased_with_normal_setattr':True,'successful_context_exit_after_rebase':True,'numerical_imports_or_authority_or_transport':False},indent=2))
