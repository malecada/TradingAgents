from pathlib import Path
H=Path(__file__).resolve().parent;old=H.parent/'mcm-batched-owner-integration01-2026-10-09'
s=(old/'verify.py').read_text()
s=s.replace("mods=m._modules(R);", "for module in ('batched_journal','batched_driver','batched_pair_executor'):\n load(package+'.'+module,H/(module+'.py'))\nmods=m._modules(R);")
s=s.replace("'schema_version':3,'max_entries'","'schema_version':4,'max_entries'")
s=s.replace("'max_checkpoint_bytes':1000000}","'max_checkpoint_bytes':1000000,'retention':'local-v2','max_spool_bytes':256,'max_offload_metadata_bytes':100000,'max_offload_entries':1000}")
a=s.index("for case in ('bad-token'");b=s.index('# Public producer',a)
s=s[:a]+'''refusals=[]
for directory in ('matching','stream'):
 p=root/directory/'unexpected';p.write_bytes(b'bad')
 try:m.verify_content(root,contract,reference,mods)
 except ValueError:refusals.append(directory+'-extra')
 else:raise AssertionError('extra child accepted')
 p.unlink()
# Exact closed01 witness: adding an empty checkpoint directory was invisible.
old_source=ast.parse((H.parent/'mcm-batched-owner-integration01-2026-10-09/compact_mcm_batched.py').read_text())
fn=next(n for n in old_source.body if isinstance(n,ast.FunctionDef) and n.name=='_checkpoint_inventory')
ns=dict(m.__dict__);exec(compile(ast.Module(body=[fn],type_ignores=[]),'closed01','exec'),ns)
old_before=ns['_checkpoint_inventory'](root/'checkpoints')
(root/'checkpoints/unexpected-empty').mkdir()
assert ns['_checkpoint_inventory'](root/'checkpoints')==old_before
try:m.verify_content(root,contract,reference,mods)
except ValueError:refusals.append('empty-checkpoint-directory')
else:raise AssertionError('closed01 defect remains')
''' + s[b:]
s=s.replace("'corruption_refusals':['token','output']","'changed_seam_refusals':refusals,'closed01_red_reproduced':True")
(H/'verify.py').write_text(s)
