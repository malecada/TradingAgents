from pathlib import Path
import ast,hashlib,json
D=Path(__file__).resolve().parent;F=D.parent;M=F.parents[2];C=F/'real-data-pilot-fourth-graph-preservation-preparation01-2026-10-06';evidence={}
def read(p):
 assert p.stat().st_size<4*1024**2
 b=p.read_bytes();evidence[str(p.relative_to(M))]=hashlib.sha256(b).hexdigest();return b
manifest=read(C/'MANIFEST01.json');assert hashlib.sha256(manifest).hexdigest()=='b570932545bb1f66b90a0247f3f7ec016f929263078e8e669428ce726f1dbd99'
for name,sha in json.loads(manifest).items():assert hashlib.sha256(read(C/name)).hexdigest()==sha
inverse=json.loads(read(C/'INVERSE01.json'));results={}
expected={'entry01.py':'44a394c90961aa528674e401686aeed12ff0ba72c730cec2ccfba0786e7f0da8','keep.py':'4f5c32cb5fd7066471b6f02ba58633d4e009cbf39701afe04e3da13fe38f53fb','prepare01.py':'2e2cdb4bbc064f71aef89ba31a05dda495af5f616e20fad3420f23d16e6ba93b'}
for name,changes in inverse.items():
 old=read(M/changes['baseline']);new=read(C/name);assert hashlib.sha256(old).hexdigest()==changes['before_sha256'];assert hashlib.sha256(new).hexdigest()==changes['after_sha256']==expected[name]
 generated=old.decode()
 for pair in changes['literal_edits']:
  assert pair['before'] in generated;generated=generated.replace(pair['before'],pair['after'])
 assert generated.encode()==new
 restored=new.decode()
 for pair in reversed(changes['literal_edits']):
  assert pair['after'] in restored;restored=restored.replace(pair['after'],pair['before'])
 assert restored.encode()==old;ast.parse(new);results[name]={'exact_forward_and_inverse':True,'candidate_sha256':expected[name],'baseline_sha256':changes['before_sha256'],'literal_edits':changes['literal_edits']}
values={}
for n in ast.parse(read(C/'prepare01.py')).body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['ID','GRAPH','SOURCE']:values[n.targets[0].id]=ast.literal_eval(n.value)
assert values=={'ID':'real-pilot-fourth-graph-preservation-20261006-01','GRAPH':'eth-paper-real-pilot-graph-20220523-20261005-01','SOURCE':'50df679a64cfee1b28b35554acab70d5ff4fa9c7'}
result={'decision':'pass-source-only','source_manifest_sha256':hashlib.sha256(manifest).hexdigest(),'source_literal_bindings':values,'inverses':results,'evidence':evidence,'active_outputs_read':False,'payload_or_header_reads':0,'selector_or_entry_executed':False,'scope':'Exact literal adaptation and unchanged finite preservation/default/failure machinery; genuine closed source/outcome and actual selection/envelope/current source release remain pending.'}
(D/'SOURCE_CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':result['decision'],'exact_inverses':len(results),'active_output_reads':False}))
