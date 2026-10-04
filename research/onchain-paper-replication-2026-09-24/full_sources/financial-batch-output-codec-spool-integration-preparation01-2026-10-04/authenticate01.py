from pathlib import Path
import ast,hashlib,json,os,stat
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
roots=[('financial-batch-output-chunk-storage-preparation02-2026-10-04','MANIFEST02.json','a513146948a0c469120eaa26844e2298cc5350e0135742c5bbe7d411c9c4238e'),('financial-batch-output-chunk-storage-source-review02-2026-10-04','MANIFEST01.json','b0a83b95fe7d8b4b6c5e04e5aa01946db8261d63880be58930c141a76efa44a1'),('financial-batch-output-transport-spool-preparation03-2026-10-04','MANIFEST01.json','b154c571ee476a9e7835949d3494be74de879fc94403354717ccbf2dc9fb019f'),('financial-batch-output-transport-spool-source-review03-2026-10-04','MANIFEST03.json','e25958c107ee2cede66cfed205f6ef3e32d64db98159eac904447f7685ec8d7b')]
results=[]
for dirname,mname,pin in roots:
 root=F/dirname;manifest=root/mname;assert h(manifest)==pin
 rows=json.loads(manifest.read_bytes())['members']
 for row in rows:
  p=root/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode'],row
  if row['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and h(p)==row['sha256'],row
  elif row['kind']=='directory':assert stat.S_ISDIR(s.st_mode),row
  else:assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==row.get('target',row.get('link_target')),row
 assert {x['path'] for x in rows}=={str(p.relative_to(root)) for p in root.rglob('*') if str(p.relative_to(root))!=mname}
 results.append({'root':str(root),'manifest':mname,'sha256':pin,'complete_typed_members':len(rows)})
C=F/roots[0][0];S=F/roots[2][0];copies=[]
for name in ('codec01.py','local_store01.py','owned_io.py','recovery04.py','bounded_git01.py','spool05.py'):
 source=(S if name=='spool05.py' else C)/name
 assert source.read_bytes()==(P/name).read_bytes()
 assert ast.dump(ast.parse(source.read_bytes()),include_attributes=False)==ast.dump(ast.parse((P/name).read_bytes()),include_attributes=False)
 copies.append({'name':name,'source':str(source),'sha256':h(source),'literal_and_AST_inverse':True})
authority=[F/'batch-output-produced-f32-adapter-preparation02-2026-10-03'/n for n in ('completed_f32.py','archive_non_tail.py','selected_non_tail_transport.py')]
authority += [R/'tradingagents/research/onchain_replication'/n for n in ('compact_owner.py','compact_mcm.py')]
authority += [F/'held-consumer-source02-preservation-preparation01-2026-10-03/source-bodies/tradingagents/research/onchain_replication/imported_mcm_identity.py']
pins=[{'path':str(p),'sha256':h(p),'bytes':p.stat().st_size,'qualification':'read-only genuine ancestry source; not imported or granted to engineering router'} for p in authority]
(P/'AUTHENTICATION01.json').write_text(json.dumps({'frozen_scopes':results,'unchanged_copies':copies,'authority_sources':pins},sort_keys=True,indent=2)+'\n');print('all frozen scopes and six exact copies authenticated')
