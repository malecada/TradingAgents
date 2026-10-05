"""Independent new27 body joins and old accepted ancestry; no old818 rescan."""
from pathlib import Path
import os,sys,json,stat,hashlib,importlib.util
H=Path(__file__).resolve().parent;F=H.parent;P=F/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05';sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'));from verify_capture01 import Reader,R
rd=Reader();manifest=json.loads(rd.read(P/'MANIFEST01.json','19e6a0794f4604fbd7b5b81f9fab76befdf9a382c90fe220b30de3cf434128c5'));seen=set()
for row in manifest['members']:
 p=P/row['path'];s=p.lstat();rd.need(stat.S_IMODE(s.st_mode)==row['mode'],'author typedseal mode')
 if row['kind']=='symlink':rd.need(stat.S_ISLNK(s.st_mode) and os.readlink(p)==row['target'],'literal test symlink; never followed')
 elif row['kind']=='file':rd.need(len(rd.read(p,row['sha256']))==row['bytes'],'all author regular bodies')
 else:rd.need(stat.S_ISDIR(s.st_mode),'typed directory')
 seen.add(row['path'])
actual=set()
for root,ds,fs in os.walk(P,followlinks=False):
 for n in ds+fs:actual.add((Path(root)/n).relative_to(P).as_posix())
rd.need(actual==seen|{'MANIFEST01.json'},'complete author declared seal')
comp=json.loads(rd.read(P/'CURRENT_COMPOSITION02.json','65ee768ba3a6569b125920bbc61f01d64487a90a5ced608df31b505cd008f370'));sel=json.loads(rd.read(P/'SELECTED_BODIES02.json','afa2f09dc897f15d63433982fe3afb43119fd95cfeb3d1e289836281fecfc20a'));prior=json.loads(rd.read(P/'CURRENT_COMPOSITION01.json',comp['initial_measurement']['sha256']));refs={}
for r in comp['basis_refs']:refs[r['path']]=json.loads(rd.read(Path(r['path']),r['sha256']))
capture=next(v for v in refs.values() if v.get('kind')=='complete-terminal-opaque-sharded-capture-v1');old=capture['originals']['capsule'];cap=Path(old['root']);parent=Path(comp['source_bound_request']['path']).parent
rd.need(comp['source']=='664e2ca5fa11d6640ab79f64c5aa222aeb3a9128' and comp['capsule']==prior['capsule'],'retained initial whole capsule census exact');rd.tree(cap,comp['capsule'],('.git',));rd.tree(parent,comp['parent'])
oldrows={r['path']:r for r in old['manifest']['members']};current={r['path']:r for r in comp['capsule']['members']};rd.need(all(current[n]==r for n,r in oldrows.items()) and len(current)==1049 and sum(r['kind']=='file' for r in current.values())==823,'old1043typed818files exact metadata/hash reuse plus six new members');rd.need(len(oldrows)==1043 and sum(r['kind']=='file' for r in oldrows.values())==818,'historical denominator');rd.need(set(current)-set(oldrows)==set(comp['new_capsule_files'])|{'fixture_inputs/financial_wrapper_continuation01'},'only five new CAP files and their directory')
rd.need(sel['count']==len(sel['bodies'])==27 and sel['bytes']==sum(r['bytes'] for r in sel['bodies'])==842160,'full selected denominator');roles={};bodies={}
for row in sel['bodies']:
 raw=rd.read(P/row['path'],row['sha256']);rd.need(len(raw)==row['bytes'] and stat.S_IMODE((P/row['path']).stat().st_mode)==row['stored_mode']==0o600,'retained new ordinary body');roles[row['role']]=roles.get(row['role'],0)+1;k=(row['original_root'],row['original_path']);rd.need(k not in bodies,'unique origin');bodies[k]=raw
 if row['role']!='git':
  original=Path(row['original_root'])/row['original_path'];rd.need(rd.read(original,row['sha256'])==raw and stat.S_IMODE(original.lstat().st_mode)==row['original_mode'],'actual original new body/mode join')
rd.need(roles=={'capsule':5,'parent':11,'git':9,'source-proof':2},'exact finite roles');q=json.loads(bodies[str(parent),'REQUEST_SOURCE_BOUND_DRAFT01.json']);rd.need(R.digest(bodies[str(parent),'REQUEST_SOURCE_BOUND_DRAFT01.json'])==comp['source_bound_request']['sha256']=='eb5aaac1fa444f792c87c914094f7cd2b8f024295a4daf33f82e11ec1d1417db','real draft pin');rd.need(q['source']==q['design_source']==comp['source'] and q['status']=='DRAFT_NOT_RELEASED' and q['final_review'] is None and q['proofs']['full_recovery'] is None,'unreleased actual current draft')
rd.need(R.digest(bodies[str(parent),'parent01.py'])==q['caller_sha256']=='b50d1e727979a989f3da1e18a5b204cc3d29169ad425806e8550aa88af5ed0be','exact current caller')
for n,h in q['helper_hashes'].items():rd.need(R.digest(bodies[str(parent),n])==h,'actual source-bound helper')
rd.need(len(q['source_files'])==359 and len(q['input_hashes'])==29 and all(current[n]['sha256']==h for n,h in q['source_files'].items()),'all current source paths/pins and exact29roles')
gate=json.loads(bodies[str(cap),q['registration']]);definition=gate['experiments'][q['identity']];rd.need(definition['source_files']==q['source_files'] and R.digest(bodies[str(cap),q['registration']])==q['registration_sha256'],'new gate exact');rd.need(set(definition['inputs'])==set(q['input_hashes']) and all(current[r['path']]['sha256']==r['sha256']==q['input_hashes'][role] for role,r in definition['inputs'].items()),'actual input full mapping')
for role in ('cumulative','independent_source_input_runtime'):r=q['proofs'][role];rd.read(Path(r['path']),r['sha256'])
# Read-only bounded original Git primitive, accepted immutable source; no git writes.
rd.read(P/'bounded_git01.py','db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f');sys.path.insert(0,str(P));from bounded_git01 import git
rd.need(git(cap,['rev-parse','HEAD'],cap=128).decode().strip()==comp['source'],'current CAP HEAD')
oldset={r.split()[0] for r in git(cap,['rev-list','--objects',comp['git']['old_source']]).decode().splitlines()};newset={r.split()[0] for r in git(cap,['rev-list','--objects',comp['source']]).decode().splitlines()};rd.need(oldset==set(comp['git']['old407']) and newset==set(comp['git']['current416']) and oldset<=newset and len(oldset)==407 and len(newset)==416,'actual407+9 Git denominator')
objects={r['oid']:r for r in comp['git']['new_objects']};rd.need(set(objects)==newset-oldset,'exact nine new Git objects')
for oid,row in objects.items():
 raw=bodies['git',oid];rd.need(len(raw)==row['bytes'] and R.digest(raw)==row['sha256'] and hashlib.sha1(row['kind'].encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,'new object logical OID')
 actual=git(cap,['cat-file',row['kind'],oid]);rd.need(actual==raw,'actual original Git-tail body')
head=rd.read(cap/'.git/HEAD').decode().strip();ref=rd.read(cap/'.git'/head.removeprefix('ref: ')).decode().strip() if head.startswith('ref: ') else head;rd.need(ref==comp['source'],'final retained current source reference')
rd.need(not os.path.lexists(parent/'attempt') and not os.path.lexists(cap/'research_runs'/q['identity']),'current fresh identity has no attempt/run')
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_EXACT_CURRENT_LOCAL_COMPOSITION_BYTES_ONLY_HELPER_RELEASE_WITHHELD','source':comp['source'],'new_bodies':27,'new_bytes':842160,'roles':roles,'current_CAP_regular':823,'current_CAP_typed':1049,'old818_hashes_reread':False,'old818_basis':'accepted actual complete100 recovery32acf316 and original captureef828893','metadata_currentness':'whole current namespace/type/mode/extent and final sampled signatures only','Git407_reused':True,'Git_current':416,'Parent_regular':11,'old_and_new_drafts_retained':True,'full_recovery':None,'final_review':None,'numerical_authority':False,'helper_execution_release':False,'checks':rd.checks,'read_bytes':rd.total};R.put(H/'COMPOSITION_READBACK01.json',result);print(json.dumps(result))
