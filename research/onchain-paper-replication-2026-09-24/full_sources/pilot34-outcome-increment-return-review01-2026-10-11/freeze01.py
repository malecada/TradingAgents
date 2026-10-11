import hashlib,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
P=Path(__file__).resolve().parent;R=P.parents[3]
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
value={'decision':'ACCEPT_ACTUAL_OUTCOME27_DECLARED_FAILED34_RETURN','files':{p.name:{k:v for k,v in ref(p).items() if k!='path'} for p in sorted(P.iterdir()) if p.is_file() and p.name!='MANIFEST01.json'}}
with (P/'MANIFEST01.json').open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'review':ref(P/'REVIEW01.json'),'manifest':ref(P/'MANIFEST01.json')},sort_keys=True))
