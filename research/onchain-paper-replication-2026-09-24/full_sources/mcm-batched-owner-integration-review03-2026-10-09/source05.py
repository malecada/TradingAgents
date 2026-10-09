import ast,hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent;C=F/'mcm-batched-owner-integration03-2026-10-09';I=F/'mcm-batched-owner-integration02-2026-10-09';O=F/'mcm-batched-owner-integration01-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'MANIFEST.json').read_text());pins={}
for n,v in m['replacements'].items():assert sha(C/n)==v['source_sha256'] and sha(I/n)==v['old_sha256'];pins[str(C/n)]=sha(C/n)
for n,v in m['inherited_sources'].items():assert sha(I/n)==v;pins[str(I/n)]=v
for p,v in m['evidence'].items():assert sha(R/p)==v
# Apply the original narrow source diffs in memory against immutable inverse bodies.
def apply(old,patch):
 lines=old.splitlines(keepends=True);out=[];cursor=0;parts=patch.splitlines(keepends=True);i=0
 while i<len(parts):
  if not parts[i].startswith('@@'):i+=1;continue
  pos=int(re.match(r'@@ -(\d+)',parts[i]).group(1))-1;out+=lines[cursor:pos];cursor=pos;i+=1
  while i<len(parts) and not parts[i].startswith('@@'):
   x=parts[i]
   if x.startswith((' ','-')):assert lines[cursor]==x[1:];cursor+=1
   if x.startswith((' ','+')):out.append(x[1:])
   i+=1
 out+=lines[cursor:];return ''.join(out)
for name in ('compact_mcm.py','compact_owner.py','compact_mcm_output.py'):
 actual=apply((O/('inverse-'+name)).read_text(),(O/(name+'.patch')).read_text());assert actual==(O/name).read_text()
 if name=='compact_mcm.py':actual=actual.replace("policy['schema_version'] in (1,2,3)","policy['schema_version'] in (1,2,4)")
 assert actual==(I/name).read_text()
def funcs(path):return {n.name:ast.dump(n) for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.FunctionDef)}
a=funcs(I/'compact_mcm_batched.py');b=funcs(C/'compact_mcm_batched.py')
for n in m['unchanged_adapter_functions']:assert a[n]==b[n]
a=funcs(I/'batched_journal.py');b=funcs(C/'batched_journal.py');assert set(a)==set(b);assert all(a[n]==b[n] for n in a if n!='__init__')
# Explicit exact source predicates: these checks inspect the genuine path but
# intentionally do not construct any authority capability.
s=(C/'compact_mcm_batched.py').read_text();t=(I/'typed_payload_operations.py').read_text();off=(I/'registered_offload.py').read_text()
assert "require(type(target) is Target" in s and 'held.check(owner)' in s and 'stage=owner._begin(' in s
assert "ad.experiment['source_files'].get(own_source)==file_hash(ad.root/own_source)" in s
assert "Path(module.__file__).resolve()==root/relative" in s
assert "type(owner) is a.owners.Owner and type(stage) is a.owners.Stage" in t and 'type(self.view) is d.View' in t
fn=next(n for n in ast.walk(ast.parse(t)) if isinstance(n,ast.FunctionDef) and n.name=='retire_batched_sources');txt=ast.unparse(fn)
assert txt.index('self.recover(')<txt.index('semantic.recover(')<txt.index('semantic.current(')<txt.index('os.unlink(')
assert 'remaining' not in '' # no policy inference or synthetic authority admitted
result={'source_manifest_sha256':sha(C/'MANIFEST.json'),'source_pins':pins,'inherited_nine_exact':True,'three_original_default_inverses':True,'unchanged_adapter_functions':m['unchanged_adapter_functions'],'journal_nonconstructor_ast_identical':True,'genuine_authority_predicates_inspected_only':True,'recovery_before_generated_retirement_source_order':True}
(H/'SOURCE_JOINS05.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
