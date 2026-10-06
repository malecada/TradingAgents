"""Build only this metadata successor; pinned predecessor and candidates immutable."""
import ast,difflib,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;F=HERE.parent;ROOT=HERE.parents[3]
OLD=F/'real-data-pilot-feature-integration-successor01-2026-10-06'
PACKED=F/'real-data-pilot-final-control-inventory01-2026-10-06/archive-control-footprint03'
def raw(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert ref(OLD/'successor01.py')['sha256']=='710fac4de18630fccdb6aa1531c09c4026a78d8ae38db77285b59720556edd72'
assert ref(PACKED/'MANIFEST03.json')['sha256']=='84942d35103224cb0665988971c6f2ffb106fff59954bf86b02c1f5a13a297b0'
manifest=json.loads((PACKED/'MANIFEST03.json').read_text());deps=json.loads((OLD/'DEPENDENCIES01.json').read_text());mapping={}
for name,leaf in {'controls':'controls01.py','handoff':'prepare_builder03_input02.py','read_capacity':'archive_read_control_capacity.py'}.items():
    source=PACKED/'candidate'/leaf;body=source.read_bytes();assert hashlib.sha256(body).hexdigest()==manifest['files']['candidate/'+leaf]['sha256']
    dest=HERE/'candidate'/leaf;dest.write_bytes(body);deps[name]=ref(dest);mapping[name]={'accepted_source':ref(source),'new_copy':ref(dest),'byte_equal':True}
for name,pin in deps.items():assert ref(ROOT/pin['path'])==pin
(HERE/'DEPENDENCIES02.json').write_bytes(raw(deps))
old=(OLD/'successor01.py').read_text();source=old[:old.index('\ndef generate(out):')]
source=source.replace("'DEPENDENCIES01.json'","'DEPENDENCIES02.json'")
anchor="    m=types.ModuleType(name);m.__file__=str(p)"
addition="""    if name=='controls':
        read_line='        from tradingagents.research.onchain_replication.archive_read_control_capacity import capacity as read_capacity\\n'
        need(text.count(read_line)==1,'packed scalar import seam differs');text=text.replace(read_line,'')
"""
assert source.count(anchor)==1;source=source.replace(anchor,addition+anchor)
anchor="    if name in ('builder','controls'):m.capacity=load('history').capacity"
assert source.count(anchor)==1;source=source.replace(anchor,anchor+"\n    if name=='controls':m.read_capacity=load('read_capacity').capacity")
source+='''
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser(description='Pinned metadata prepare only; no generation or admission.')
    a.add_argument('--prepare',type=Path,required=True);v=a.parse_args()
    with v.prepare.open('rb') as stream:body=stream.read(4*1024**2+1)
    need(len(body)<=4*1024**2,'metadata input too large')
    print(json.dumps(prepare(ROOT,json.loads(body)),sort_keys=True,allow_nan=False))
'''
(HERE/'successor02.py').write_text(source);compile(source,str(HERE/'successor02.py'),'exec')
(HERE/'DELTA02.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),source.splitlines(True),fromfile='a/successor01.py',tofile='b/successor02.py')))
# Only load import injection and dependency filename changed in the retained functions.
a={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)}
b={n.name:n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
assert set(b)=={'need','raw','load','prepare'}
for name in ('need','raw'):assert ast.dump(a[name])==ast.dump(b[name])
previous_prepare=ast.get_source_segment(old,a['prepare']);new_prepare=ast.get_source_segment(source,b['prepare'])
assert previous_prepare==new_prepare.replace('DEPENDENCIES02.json','DEPENDENCIES01.json')
(HERE/'SOURCE_MAP02.json').write_bytes(raw({'status':'METADATA_DRAFT_NOT_ADMITTED','predecessor':ref(OLD/'successor01.py'),'packed_manifest':ref(PACKED/'MANIFEST03.json'),'adopted':mapping,'reused_without_copy':{k:v for k,v in deps.items() if k not in mapping},'retained_prepare_literal_inverse_equal':True,'need_raw_ast_unchanged':True,'removed_entry':'obsolete five-graph generate; never executed','root_owned_integration':'No runtime source, state, gate, baseline or registrations changed.'}))
