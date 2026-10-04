from pathlib import Path
import ast,json,hashlib
O=Path(__file__).resolve().parent;T=O.parent/'financial-wrapper-compatibility-preclaim-correction02-2026-10-04';vals={}
for n in ast.parse((T/'root_preclaim_patch02.py').read_text()).body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['a','b','c','d','e','f']:vals[n.targets[0].id]=ast.literal_eval(n.value)
old=(T/'ORIGINAL_preclaim01.py').read_text();new=(T/'preclaim01.py').read_text();rebuild=old
for a,b in [('a','b'),('c','d'),('e','f')]:assert rebuild.count(vals[a])==1;rebuild=rebuild.replace(vals[a],vals[b])
assert rebuild==new
inverse=new
for a,b in [('a','b'),('c','d'),('e','f')]:assert inverse.count(vals[b])==1;inverse=inverse.replace(vals[b],vals[a])
assert inverse==old
(O/'LITERAL_INVERSE03.json').write_text(json.dumps({'schema_version':1,'exact_three_literal_edits':True,'forward_and_reverse_equal':True,'excluded_seal_streams':{n:hashlib.sha256((T/n).read_bytes()).hexdigest() for n in ['FREEZE01.out','FREEZE01.err']},'scope':'No execution of original Root patch script or genuine public preclaim API.'},indent=2)+'\n');print('PASS literal3 exactforward/reverse; original freeze exclusions pinned separately')
