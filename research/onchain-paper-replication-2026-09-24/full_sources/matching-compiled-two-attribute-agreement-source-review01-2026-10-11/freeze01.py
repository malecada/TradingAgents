import hashlib,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'matching-compiled-two-attribute-agreement01-2026-10-11'
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(n,v):
 with (P/n).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
out={'schema_version':1,'decision':'ACCEPTED_C_ADAPTER_SOURCE_ONLY_FIXTURE_EXECUTION_WITHHELD','reviewer':'independent outcome16_release_review','candidate_manifest':ref(D/'MANIFEST01.json'),'source':ref(D/'edge_chunk.c'),'adapter':ref(D/'edge_chunk_adapter.py'),'fixture':ref(D/'fixture01.py'),'result':ref(P/'RESULT01.json'),'findings':[{'severity':'P2','path':str((D/'fixture01.py').relative_to(R)),'line':54,'issue':'write_text overwrites prior result and no pre-load exclusive attempt namespace exists.','repair':'New fixture-only successor with exclusive attempt before native/science imports, exclusive result, retained raw outer exit.'}],'source_scope':'Two-attribute readonly contiguous float64 arithmetic and existing prefix/error interface. Original Python arithmetic order retained; no actual numerical proof.','limitations':['Tuple allocation and generator/zip/len elimination change allocation and tracing/profiling events; allocator timing equivalence excluded','Initial source/runtime ownership and existing outer currentness remain required','Old EdgeOwner03 hashes and argument signature cannot select candidate','Native binary bytes not independently read or loaded; compile receipt only inspected','Actual loader/numeric/prefix/full-chain integration/genuine authority/performance pending'],'execution_released':False,'main_or_registration_changed':False}
write('REVIEW01.json',out);write('MANIFEST01.json',{'decision':out['decision'],'files':{p.name:{k:v for k,v in ref(p).items() if k!='path'} for p in sorted(P.iterdir()) if p.is_file() and p.name!='MANIFEST01.json'}})
print(json.dumps({'review':ref(P/'REVIEW01.json'),'manifest':ref(P/'MANIFEST01.json')},sort_keys=True))
