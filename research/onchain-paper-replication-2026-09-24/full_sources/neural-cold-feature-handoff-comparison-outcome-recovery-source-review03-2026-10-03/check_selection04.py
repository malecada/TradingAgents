"""Readonly exact selected enumeration, run only after this manifest is frozen."""
import ast,hashlib,json,stat
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03';p=OUT/'recover_comparison_outcome04.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='6ee87bca15f17d3425732d3cf78f42fd4fb29edbb06fedc91404911d0a6d6fa8';tree=ast.parse(raw)
first=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='names' for x in n.targets));last=next(i for i,n in enumerate(tree.body[first:],first) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='selected' for x in n.targets))
ns={'HERE':OUT,'PurePosixPath':PurePosixPath,'json':json,'digest':lambda b:hashlib.sha256(b).hexdigest()};exec(compile(ast.Module(body=tree.body[first:last],type_ignores=[]),str(p),'exec'),ns)
rows=[]
for path in ns['names']:
 info=path.lstat();assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=4194304;body=path.read_bytes();rows.append({'path':str(path),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
assert len(rows)==len({x['path'] for x in rows})
result={'status':'EXACT_HELPER04_SELECTED_FILES_READY','helper_sha256':hashlib.sha256(raw).hexdigest(),'files':rows,'count':len(rows),'total_bytes':sum(x['bytes'] for x in rows),'network_or_helper_main_invoked':False}
# Stdout only avoids a self-referential selected manifest/readback hash cycle.
print(json.dumps(result,indent=2,sort_keys=True))
