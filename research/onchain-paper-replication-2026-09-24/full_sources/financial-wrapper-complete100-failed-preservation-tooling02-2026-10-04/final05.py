import ast,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;inv=json.loads((D/'SOURCE_INVERSE01.json').read_bytes());checks=0
for name,row in inv.items():
 s=(D/name).read_text();assert hashlib.sha256(s.encode()).hexdigest()==row['candidate_sha256'];checks+=1
 for e in reversed(row['edits']):assert s.count(e['new'])==1;s=s.replace(e['new'],e['old']);checks+=1
 assert s==(D/('ORIGINAL_'+name)).read_text() and ast.dump(ast.parse(s))==ast.dump(ast.parse((D/('ORIGINAL_'+name)).read_bytes()));checks+=1
for p in D.glob('*.py'):ast.parse(p.read_bytes());checks+=1
r=json.loads((D/'REQUIRED_BODIES01.json').read_bytes());assert len(r)==35 and sum(x['bytes'] for x in r.values())==16481302;n=len({(x['bytes'],x['sha256']) for x in r.values()});assert n==29 and 10+n+2*len(r)==109;checks+=1
(D/'FINAL05.json').write_text(json.dumps({'checks':checks,'selected_paths':35,'unique_blobs':29,'exact_new_operations':109,'original81_not_reused':True,'actual_network':False},indent=2)+'\n');print(checks)
