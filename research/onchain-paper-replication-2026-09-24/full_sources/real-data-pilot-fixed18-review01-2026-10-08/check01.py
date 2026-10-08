"""Independent stdlib-only source metadata review; never imports candidate code."""
import ast,datetime,difflib,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
F=OUT.parent
OLD=F/'real-data-pilot-fixed17-metadata-successor01-2026-10-08'
NEW=F/'real-data-pilot-fixed18-metadata-successor01-2026-10-08'
ID17='eth-paper-real-data-end-to-end-resource-20261008-17'
ID18='eth-paper-real-data-end-to-end-resource-20261008-18'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
prior=F/'real-data-pilot-retry17-review01-2026-10-08/SOURCE_ADOPTION_REVIEW01.json'
a=json.loads(prior.read_text());assert a['decision']=='accepted-source-adoption-only'
changed=['candidate/build_inputs03.py','candidate/controls01.py','candidate/real_pilot_storage.py']
checks=[];evidence={};changes={}
for rel in changed:
 x=(OLD/rel).read_bytes();y=(NEW/rel).read_bytes()
 assert sha(OLD/rel)==a['changes'][rel]['candidate']['sha256']
 assert x.count(ID17.encode())==1 and y.count(ID18.encode())==1
 assert x.replace(ID17.encode(),ID18.encode())==y and ID17.encode() not in y
 assert y.replace(ID18.encode(),ID17.encode())==x
 compile(y,str(NEW/rel),'exec')
 assert ast.dump(ast.parse(y.decode().replace(ID18,ID17)))==ast.dump(ast.parse(x))
 changes[rel]={'baseline':ref(OLD/rel),'candidate':ref(NEW/rel),'exact_one_literal_replacement':True,'inverse_bytes_equal':True,'normalized_ast_equal':True}
s='successor02.py';assert (OLD/s).read_bytes()==(NEW/s).read_bytes();assert sha(OLD/s)==a['successor']['sha256'];compile((NEW/s).read_bytes(),str(NEW/s),'exec')
b=json.loads((OLD/'DEPENDENCIES02.json').read_text());n=json.loads((NEW/'DEPENDENCIES02.json').read_text());assert len(b)==len(n)==8
assert sha(OLD/'DEPENDENCIES02.json')==a['dependency_map']['sha256']
for key in b:
 assert sha(ROOT/b[key]['path'])==b[key]['sha256'];assert sha(ROOT/n[key]['path'])==n[key]['sha256']
 if key in ('builder','controls'):
  assert n[key]['path']==b[key]['path'].replace(OLD.name,NEW.name)
 else:assert b[key]==n[key]==a['external_immutable_dependencies'][key]
# Independently reconstruct exact submitted unified delta bodies in both directions.
rels=['DEPENDENCIES02.json']+changed
for patch,origin,dest in [('FORWARD01.patch',OLD,NEW),('INVERSE01.patch',NEW,OLD)]:
 body=''.join(''.join(difflib.unified_diff((origin/r).read_text().splitlines(True),(dest/r).read_text().splitlines(True),fromfile='a/'+r,tofile='b/'+r)) for r in rels)
 assert body==(NEW/patch).read_text(),patch
storage=ROOT/'tradingagents/research/onchain_replication/real_pilot_storage.py'
assert storage.read_bytes()==(OLD/'candidate/real_pilot_storage.py').read_bytes()
paths=[ROOT/'research_runs'/ID18,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID18,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/ID18,ROOT/'research_artifacts/archive-dispatch-ethpilot-20261008-18']
rep=ROOT/'research_artifacts/onchain_representations'
paths.extend(p/ID18 for p in sorted(rep.iterdir()) if p.is_dir())
absence=[{'path':str(p.relative_to(ROOT)),'exists_or_symlink':os.path.lexists(p)} for p in paths]
assert not any(p['exists_or_symlink'] for p in absence)
manifest=json.loads((NEW/'MANIFEST01.json').read_text())
for rel,pin in manifest['files'].items():assert sha(NEW/rel)==pin['sha256'] and (NEW/rel).stat().st_size==pin['bytes']
result={'schema_version':1,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'accepted-source-adoption-only','scope':'Exact fixed17 to fixed18 metadata helper identity amendment and strict storage candidate only.','qualification':'Accept strictstorage18 source adoption and successor metadata preparation only. No registration, release, resource-capacity, numerical or empirical admission claim. Later actual metadata/source/runtime/budget/binding and fresh eligibility require separate review.','reused_review':ref(prior),'changes':changes,'successor':ref(NEW/s),'successor_byte_identical':True,'dependency_map':ref(NEW/'DEPENDENCIES02.json'),'external_immutable_dependencies':{k:v for k,v in n.items() if k not in ('builder','controls')},'live_storage':ref(storage),'live_storage_still_exact_fixed17':True,'checks':['four Python sources compile without execution/import','three exact literal substitutions with byte inverse and normalized AST equality','two self dependency path/hash changes; six external dependencies unchanged and all hashes verified','submitted forward/inverse unified patches independently reconstructed exactly','candidate manifest files independently hashed','point-in-time namespace absence across lifecycle supervisor parent archive and existing representation parents'],'namespace_absence':absence,'manifest':ref(NEW/'MANIFEST01.json'),'review_script':ref(Path(__file__))}
with (OUT/'SOURCE_ADOPTION_REVIEW01.json').open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({'decision':result['decision'],'review':ref(OUT/'SOURCE_ADOPTION_REVIEW01.json'),'namespace_paths':len(paths)}))
