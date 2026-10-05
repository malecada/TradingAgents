"""Independent actual refusal capture reconstruction. No capture or restore entry."""
from pathlib import Path
import ast,json,os,stat,subprocess,sys,importlib.util
H=Path(__file__).resolve().parent;F=H.parent;D=F/'financial-wrapper-continuation-refused-outcome-capture01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04'
helper=F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05/verify_capture01.py'
spec=importlib.util.spec_from_file_location('accepted_bounded_reader',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);Reader,R=module.Reader,module.R
rd=Reader();cr=rd.read(D/'CAPTURE01.json');capture=json.loads(cr);mr=rd.read(D/'archive-manifest.json','45a7d86c2e4348fa088182a3402bf717dfce728d8223ff3d22213334a5d9b5d5');m=json.loads(mr);R.validate(m);ar=rd.read(D/'increment.tar.gz','2afffc256189bab85a19a5a7e69d9a45e2e8155db2e1d3c5352622ff4b281508')
rd.need(capture['archive']=={'bytes':len(ar),'sha256':R.digest(ar),'manifest_sha256':R.digest(mr)} and len(ar)==236548 and capture['regular']==len(m['members'])==55 and not capture['external_recovery'],'exact actual55-body local archive')
rd.tree(D/'snapshot',m);expected={r['path']:r for r in m['members']};found={};it=R.framed_members(ar);primary=None
try:
 for name,t,body in it:
  rd.need(name in expected and name not in found,'exact unique PAX population');row=expected[name]
  rd.need(t.isfile() and t.size==len(body)==row['bytes'] and R.digest(body)==row['sha256'] and t.mode==row['mode']==384 and t.uid==t.gid==0 and t.mtime==0 and t.uname==t.gname=='','actual canonical frame/mode/hash');rd.need(rd.read(D/'snapshot'/name,row['sha256'])==body,'actual original saved opaque body');found[name]=body
except BaseException as e:primary=e
R._cleanup((it.close,),primary=primary)
if primary is not None:raise primary
rd.need(set(found)==set(expected),'complete55 denominator');sink=R.Sink();R.tar_stream(D/'snapshot',m,sink);rd.need(sink.count==len(ar) and sink.hash.hexdigest()==R.digest(ar),'full canonical PAX recompression')
comp=json.loads(found['COMPOSITION01.json']);rd.need(R.digest(found['COMPOSITION01.json'])=='62877e6d999745e36fccc6e145a657f6d467f5194eb3d7c6de98b328db80e91a','actual composition pin');saved=comp['materialized'];rd.need(len(saved)==capture['new_original_bodies']==54 and len({r['flat'] for r in saved.values()})==54 and set(r['flat'] for r in saved.values())==set(found)-{'COMPOSITION01.json'} and sum(r['bytes'] for r in saved.values())==capture['new_original_bytes']==750566,'complete54 original mapping')
origins={};scope_counts={}
for label,scope in comp['scopes'].items():
 root=Path(scope['root']);sm=scope['manifest'];R.validate(sm);scope_counts[label]={'regular':sum(r['kind']=='file' for r in sm['members']),'typed':len(sm['members'])}
 if label=='outcome-phase':
  rd.need(root==H,'actual original review scope');phase=json.loads(rd.read(H/'OUTCOME_PHASE_MANIFEST01.json','ff83b37edd3dc9c0253209210559b9d51022a88065b1119bdab50f3cad05b510'));rd.need([r for r in sm['members'] if r['path']!='OUTCOME_PHASE_MANIFEST01.json']==phase['members'],'exact frozen phase plus seal; later review additions excluded')
 else:rd.tree(root,sm)
 for row in sm['members']:
  p=root/row['path'];st=p.lstat();rd.need(stat.S_IMODE(st.st_mode)==row['mode'],'original mode preserved')
  if row['kind']=='file':rd.need(stat.S_ISREG(st.st_mode) and st.st_size==row['bytes'],'actual original file extent/type');origins[label+'/'+row['path']]=(p,row['sha256'])
  else:rd.need(row['kind']=='directory' and stat.S_ISDIR(st.st_mode),'actual original directory')
for name in saved:
 if name.startswith('Root/'):origins[name]=(C/name[5:],saved[name]['sha256'])
rd.need(set(origins)==set(saved) and scope_counts=={'Parent':{'regular':28,'typed':32},'job':{'regular':9,'typed':10},'outcome-phase':{'regular':14,'typed':14}},'exact28+9+14+3 original denominator')
for name,(p,h) in origins.items():
 row=saved[name];body=found[row['flat']];rd.need(R.digest(body)==h==row['sha256'] and len(body)==row['bytes'] and rd.read(p,h)==body,'all54 actual original bytes')
proof=json.loads(rd.read(Path(comp['basis']['path']),comp['basis']['sha256']));rd.need(comp['basis']==capture['recovery_basis'] and comp['basis']['sha256']=='4bb7781345617bf5529e63b0c2d0a630aad726df87c3dc895ab4e02ca323aa79','genuine accepted old823/1049/422 basis');rd.read(Path(proof['review']['path']),proof['review']['sha256'])
old=json.loads(rd.read(F/'financial-wrapper-continuation-canonical-delta-root01-2026-10-05/snapshot/COMPOSITION01.json'))['capsule'];oldrows={r['path']:r for r in old['members']};current={r['path']:r for r in comp['capsule']['members']};CAP=Path(proof['capsule_root']);job=comp['scopes']['job'];jroot=Path(job['root']);prefix=jroot.relative_to(CAP).as_posix();newrows={prefix:{'path':prefix,'kind':'directory','mode':job['manifest']['root_mode']}}
for row in job['manifest']['members']:newrows[prefix+'/'+row['path']]={**row,'path':prefix+'/'+row['path']}
rd.need(current==oldrows|newrows and not set(oldrows)&set(newrows) and len(current)==1060 and sum(r['kind']=='file' for r in current.values())==832,'complete current old823/1049 plus exact9/11, no prior byte rehash');rd.tree(CAP,comp['capsule'],('.git',))
previous=json.loads(rd.read(F/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05/CURRENT_COMPOSITION02.json','65ee768ba3a6569b125920bbc61f01d64487a90a5ced608df31b505cd008f370'));delta=json.loads(rd.read(F/'financial-wrapper-continuation-canonical-delta-root01-2026-10-05/snapshot/COMPOSITION01.json'));gitset=set(previous['git']['current416'])|{v['oid'] for v in delta['Git']['new_objects']}
head=rd.read(CAP/'.git/HEAD').decode().strip();source=rd.read(CAP/'.git'/head[5:]).decode().strip() if head.startswith('ref: ') else head;rd.need(source==capture['source']==comp['source']==proof['source'],'actual unchanged d4c source')
p=subprocess.run(['git','--no-optional-locks','-C',str(CAP),'rev-list','--objects',source],capture_output=True,check=True,timeout=10);rd.need(len(p.stdout)<1024*1024 and not p.stderr and {x.split()[0] for x in p.stdout.decode().splitlines()}==gitset and len(gitset)==comp['Git_logical_objects']==422,'actual unchanged422 Git metadata closure')
outcome=json.loads(rd.read(H/'OUTCOME_READBACK01.json'));rd.need(comp['identity']==capture['identity']==outcome['identity'] and not comp['numerical_claim'] and comp['namespace_reserved'] and comp['external_recovery'] is None and not comp['runtime_bodies_recovered'] and not comp['POSIX_reconstruction'],'honest original not-admitted and unrecovered semantics')
for p in outcome['absent_namespaces']:rd.need(not os.path.lexists(p),'original claim/fit/workload release absent')
# Source scope is the already-consumed ordinary capture; authenticate exact reused primitives.
src=rd.read(C/'CANONICAL_CONTINUATION_OUTCOME_CAPTURE01.py');ast.parse(src);parent=Path(comp['scopes']['Parent']['root']);q=json.loads(rd.read(parent/'REQUEST_FINAL01.json','a9a04d60abced0ae01f192a7fc3897bf3972891d374a98f33f15522b8dc20e18'))
for n in ('recovery04.py','owned_io.py','bounded_git01.py'):rd.read(parent/n,q['helper_hashes'][n])
rd.need("import recovery04 as R" in src.decode() and "R.pack(snapshot,manifest,OUT/'increment.tar.gz')" in src.decode() and "R.same(snapshot,manifest)" in src.decode(),'exact accepted PAX primitive and actual output validation route')
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_LOCAL_REFUSAL_CAPTURE_ONLY','source':source,'identity':comp['identity'],'capture_sha256':R.digest(cr),'archive_sha256':R.digest(ar),'archive_bytes':len(ar),'archive_manifest_sha256':R.digest(mr),'composition_sha256':R.digest(found['COMPOSITION01.json']),'capture_source_sha256':R.digest(src),'source_scope':'actual once-consumed ordinary capture plus independent full byte reconstruction; no reusable execution grant','original_bodies':54,'original_bytes':750566,'archive_bodies':55,'archive_logical_bytes':sum(r['bytes'] for r in m['members']),'scope_counts':scope_counts,'Root_original_bodies':3,'current_CAP_regular':832,'current_CAP_typed':1060,'Git_logical_objects':422,'old823_body_hashes_reused_not_reread':True,'runtime251_not_reread':True,'accepted_basis':comp['basis'],'new_lifecycle_claim':False,'namespace_reserved':True,'relaunch_authorized':False,'external_recovery':False,'POSIX_reconstruction':False,'runtime_bodies_recovered':False,'sampled_currentness_only':True,'checks':rd.checks,'read_bytes':rd.total}
R.put(H/'CAPTURE_READBACK01.json',result);print(json.dumps(result))
