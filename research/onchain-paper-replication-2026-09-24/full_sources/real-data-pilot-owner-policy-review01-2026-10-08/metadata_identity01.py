import ast,hashlib,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';O=F/'real-data-pilot-fixed20-metadata-successor01-2026-10-08';N=F/'real-data-pilot-fixed21-metadata-successor01-2026-10-08';H=Path(__file__).resolve().parent;ev={};checks=[]
a='eth-paper-real-data-end-to-end-resource-20261008-20';b=a[:-2]+'21'
def read(p):
 raw=p.read_bytes();ev[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return raw
def check(n,v):
 assert v,n
 checks.append(n)
for name in ('real_pilot_storage.py','controls02.py','build_inputs04.py'):
 old=read(O/'candidate'/name).decode();new=read(N/'candidate'/name).decode();check('single_identity_occurrence_'+name,new.count(b)==old.count(a)==1);check('literal_inverse_'+name,new.replace(b,a)==old);check('ast_inverse_'+name,ast.dump(ast.parse(new.replace(b,a)))==ast.dump(ast.parse(old)))
check('main_storage_original_exact',read(R/'tradingagents/research/onchain_replication/real_pilot_storage.py')==read(O/'candidate/real_pilot_storage.py'))
check('loader_identical',read(N/'successor04.py')==read(O/'successor04.py'))
old=json.loads(read(O/'DEPENDENCIES04.json'));new=json.loads(read(N/'DEPENDENCIES04.json'));check('only_builder_controls_refs_changed',{k for k in old.keys()|new.keys() if old.get(k)!=new.get(k)}=={'builder','controls'})
for name,v in new.items():check('pin_'+name,hashlib.sha256(read(R/v['path'])).hexdigest()==v['sha256'])
for name in ('builder','controls'):check('new_path_'+name,new[name]['path']==old[name]['path'].replace('fixed20-','fixed21-'))
result={'schema_version':1,'decision':'accepted-source-only','identity':b,'evidence':ev,'checks':checks,'candidate_storage':{'path':str((N/'candidate/real_pilot_storage.py').relative_to(R)),'sha256':ev[str((N/'candidate/real_pilot_storage.py').relative_to(R))]},'scope':'Exactly three20-to21 identity literals; source and AST inverse restore accepted immutable20 bodies. Loader byte-identical; dependency delta only builder/controls references and hashes; all pins verified. Resource limits, numerical calculations, diagnostic behavior and strict writable scopes unchanged except fixed identity. No Main mutation, authority, registration/admission, empirical execution or old suite repeated. Fresh21 preclaim metadata refusal remains preserved.'}
(H/'METADATA_IDENTITY_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted-source-only','checks':len(checks),'sha256':hashlib.sha256((H/'METADATA_IDENTITY_REVIEW01.json').read_bytes()).hexdigest()}))
