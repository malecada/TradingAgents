from pathlib import Path
import hashlib,json,stat,ast,subprocess,os
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';A=F/'financial-wrapper-operational-provenance-compatibility-preparation01-2026-10-04';O=F/'financial-wrapper-operational-provenance-compatibility-review01-2026-10-04';O.mkdir(mode=0o700)
h=lambda b:hashlib.sha256(b).hexdigest();mp=A/'MANIFEST01.json';assert h(mp.read_bytes())=='ac15b2501dc1ca44b8f1505eed49039672e074ac536bf6a26bfde402e3576786';m=json.loads(mp.read_bytes());paths=[]
for x in m['members']:
 p=A/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode'];paths.append(x['path'])
 if x['kind']=='file':assert stat.S_ISREG(s.st_mode) and len(p.read_bytes())==x['bytes'] and h(p.read_bytes())==x['sha256']
 elif x['kind'] in ('directory','dir'):assert stat.S_ISDIR(s.st_mode)
 elif x['kind']=='symlink':assert os.readlink(p)==x.get('target',x.get('link_target'))
 else:raise AssertionError(x)
assert sorted(paths)==sorted(str(p.relative_to(A)) for p in A.rglob('*') if p!=mp)
for n in ['operational_source_compatibility.py','financial_wrapper_fixture.py','training.py','workflow_storage.py','original_financial_wrapper_fixture.py','original_training.py','SOURCE_INVERSES02.json','POLICY_DRAFT01.json','PROOF_ROLES_DRAFT01.json','ROOT_REQUIREMENTS01.json','SOURCE_READBACK01.json']:(O/n).write_bytes((A/n).read_bytes())
assert h((O/'operational_source_compatibility.py').read_bytes())=='6a4b40f3c171e9cab8d25ec611ad9d801a67ae713cfa18b13fe75574fce1b80b'
inv=json.loads((O/'SOURCE_INVERSES02.json').read_bytes())
for name,allowed in [('training.py',{'_reserve'}),('financial_wrapper_fixture.py',{'authorize','_parent','_reference_state'})]:
 new=(O/name).read_text();old=(O/('original_'+name)).read_text();back=new
 for row in reversed(inv['changes'][name]):assert back.count(row['new'])==1;back=back.replace(row['new'],row['old'])
 assert back==old
 aa,bb=ast.parse(old),ast.parse(new)
 for tree in (aa,bb):tree.body=[n for n in tree.body if getattr(n,'name',None) not in allowed]
 assert ast.dump(aa)==ast.dump(bb)
# Preserve genuine protocol and exact source API origin pins; no API imports.
proof=F/'financial-wrapper-operational-provenance-compatibility-investigation01-2026-10-04/PROTOCOL_REQUIREMENTS01.md';assert h(proof.read_bytes())=='0e586ee51ddcbb5f2ede6dd305c88fdf3496e9c47b39bfb46a8322b94f1a7dae';(O/'PROTOCOL_REQUIREMENTS01.md').write_bytes(proof.read_bytes())
(O/'AUTHENTICATION01.json').write_text(json.dumps({'author_manifest_sha256':h(mp.read_bytes()),'members':len(paths),'complete_membership':True,'full_literal_AST_inverse':True,'protocol_sha256':h(proof.read_bytes())},indent=2)+'\n')
d=O/'replay';d.mkdir()
for p in O.iterdir():
 if p.is_file() and p.suffix in ('.py','.json'):(d/p.name).write_bytes(p.read_bytes())
for name in ['check02.py','check03.py']:
 (d/name).write_bytes((A/name).read_bytes())
 with (d/(name+'.stdout')).open('xb') as out,(d/(name+'.stderr')).open('xb') as err:q=subprocess.run([str(R/'.venv/bin/python'),'-B',str(d/name)],stdout=out,stderr=err,timeout=60)
 (d/(name+'.exit')).write_text(str(q.returncode)+'\n');print(name,q.returncode)
