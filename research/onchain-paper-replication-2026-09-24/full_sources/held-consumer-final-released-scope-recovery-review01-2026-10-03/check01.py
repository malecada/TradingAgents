import ast,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;R=F/'held-consumer-final-released-scope-root-remote-recovery01-2026-10-03';P=F/'held-consumer-final-released-scope-root-capture01-2026-10-03';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';flat=R/'flat01';selected=R/'selected';repo=Path.cwd();sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,msg):
 assert v,msg
 checks.append(msg)
def raw(p):
 st=p.lstat();ck(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=4*1024**2,'bounded regular '+p.name)
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  ck(os.fstat(fd)==st,'stable opened identity '+p.name);b=b''
  while True:
   q=os.read(fd,65536)
   if not q:break
   b+=q;ck(len(b)<=4*1024**2,'read bound')
  ck(os.fstat(fd)==st and p.lstat()==st,'stable read identity '+p.name);return b
 finally:os.close(fd)
def doc(p,pin=None):
 b=raw(p);ck(pin is None or sha(b)==pin,'document pin '+p.name);return json.loads(b)
sys.path.insert(0,str(U));sp=importlib.util.spec_from_file_location('pure_io',U/'recovery04.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
ck(sha(raw(U/'recovery04.py'))=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','accepted source04')
# Reuse only the independent decoder and encoder definitions, not its top-level capture review.
prior=F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py';tree=ast.parse(raw(prior));defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('decode','recode')];ck(len(defs)==2,'two pure framing definitions');exec(compile(ast.Module(body=defs,type_ignores=[]),str(prior),'exec'))
q=doc(P/'REQUEST01.json','660a715bc4da9bfd93e4076cee4d82730301024b9fa95668c8182a48d9ac2061');capture=doc(P/'bundle01/capture.json','122706bfcd5cf8eaaecc31b7230a0553d804606fad4db4d86a74f136dbe27408');remote=doc(R/'REMOTE_RECOVERY03.json','eaaf62de466583661d81a9d03b76a037192776334d3bf8d5ef4decc0312aaffd');pins=doc(R/'FLAT_RUN_PINS01.json');term=doc(R/'FLAT_TERMINAL01.json');recovery=doc(flat/'recovery.json','8b5eb6d58e4e422b38f327bd95056df34780c19fe1d65bed7a4cbfa0d6855371');scope=doc(R/'SOURCE_SCOPE03.json');selection=doc(R/'SELECTED_BODIES03.json');a.request(q)
ck(remote['remote_commit']==scope['commit']==selection['remote_commit']=='a9f18fffbc06b9e3996b67fc2a0139ce98900709','remote commit chain');ck(sha(raw(R/'recover_final03.py'))==scope['source03_sha256']=='6b4d6671f852ab6893a2219c4185efb7106253b3bf48eb07da500bafe54dbfce','remote source pin');ck(sha(raw(R/'SELECTED_BODIES03.json'))==remote['selection_sha256']==scope['selection_sha256']=='7bde62d8a3a549561b879320c672f77b662bc256f141dd47b96569e918447625','selection chain');ck(len(remote['selected_blobs'])==remote['selected_count']==431 and remote['selected_logical_bytes']==12674060,'remote declared scope');ck(all(x['exit']==0 and not x['cleanup_failures'] for x in remote['operations']),'recorded remote operations successful')
ck(term['actual_child_exit']==0 and term['actual_output_files']==689 and term['pid_absent'] and not Path('/proc',str(term['actual_pid'])).exists(),'actual flat terminal/process');ck(term['disk_free_bytes']>=10*1024**3 and term['genuine_run_or_native_started'] is False and term['root_launch_hold'] is True,'retained floor and launchhold');ck(term['recovery_sha256']==sha(raw(flat/'recovery.json')) and pins['remote_recovery_sha256']==sha(raw(R/'REMOTE_RECOVERY03.json')),'terminal receipt joins');ck(pins['helper_sha256']==sha(raw(U/'recovery04.py')) and pins['helper_review_sha256']=='11edd9d352edbcaef1fbf0a8d55778d8ea4cac83611d502efd29da056d448e39','qualified helper pins')
for n in ('FLAT01.stdout','FLAT01.stderr'):ck(raw(R/n)==b'','empty '+n)
for k in ('request_sha256','capture_sha256'):ck(recovery[k]==sha(raw(P/('REQUEST01.json' if k=='request_sha256' else 'bundle01/capture.json'))),'flat capture chain '+k)
for k in ('instantiated_posix_tree','outside_stores_recovered','recovered_tree_git_join','research_authority','runtime_package_bodies_recovered'):ck(recovery[k] is False,'false scope '+k)
ck(stat.S_IMODE(flat.lstat().st_mode)==0o700 and stat.S_ISDIR(flat.lstat().st_mode),'private acquired root')
rows={x['path']:x for x in remote['selected_blobs']};needed=[P/'REQUEST01.json']+list((P/'bundle01').iterdir());joined=[]
for original in needed:
 rel=str(original.relative_to(repo));b=raw(selected/rel);ck(b==raw(original),'fresh selected actual capture bytes '+rel);row=rows[rel];ck(row['bytes']==len(b) and row['sha256']==sha(b),'remote archive row '+rel);joined.append(rel)
want={'recovery.json','capsule-metadata.json','external-metadata.json'};results={};snap={}
for role in ('capsule','external'):
 manifest=q[role+'_manifest'];m=doc(flat/(role+'-metadata.json'));result=recovery['results'][role];ck(m['manifest']==manifest and m['archive']==capture['archives'][role],'full original mode metadata '+role);ck(sha(raw(flat/(role+'-metadata.json')))==result['metadata_sha256'],'metadata receipt '+role);archive=raw(selected/(P/'bundle01'/(role+'.tar.gz')).relative_to(repo));bodies,stats=decode(archive,manifest);files=[r for r in manifest['members'] if r['kind']=='file'];ck(set(m['flat_members'])=={r['path'] for r in files},'complete mapping '+role);recovered={}
 for i,row in enumerate(files):
  name=m['flat_members'][row['path']];ck(name==f'{role}-{i:05d}.body' and name not in want,'exclusive deterministic flat name');want.add(name);p=flat/name;b=raw(p);ck(stat.S_IMODE(p.lstat().st_mode)==0o600,'private flat body mode');ck(b==bodies[row['path']] and len(b)==row['bytes'] and sha(b)==row['sha256'],'actual archive derived opaque body '+row['path']);recovered[row['path']]=b;snap[name]=sha(b)
 for row in manifest['members']:
  if row['kind']=='directory':recovered[row['path']]=b''
 ck(recode(manifest,recovered)==archive,'complete compressed reencoding from actual recovered bodies '+role);ck(result['members']==len(manifest['members']) and result['regular_bodies']==len(files) and result['root_mode']==manifest['root_mode'],'complete count/rootmode '+role);results[role]={'members':len(manifest['members']),'bodies':len(files),'logical_bytes':sum(r['bytes'] for r in files),'archive_sha256':sha(archive),**stats}
old=doc(F/'held-consumer-final-baseline-root-capture01-2026-10-03/REQUEST01.json');ck(old['capsule_manifest']==q['capsule_manifest'],'unchanged925');before={r['path']:r for r in old['external_manifest']['members']};after={r['path']:r for r in q['external_manifest']['members']};ck(len(before)==12 and all(after[k]==v for k,v in before.items()),'original12 preserved');ck(len(after.keys()-before.keys())==13,'13new parent bodies')
ck({p.name for p in flat.iterdir()}==want and len(want)==689,'exact flat689 complete membership')
for p in flat.iterdir():ck(stat.S_ISREG(p.lstat().st_mode) and p.lstat().st_nlink==1 and stat.S_IMODE(p.lstat().st_mode)==0o600,'allflat private regular singlelink')
for n,h in snap.items():ck(sha(raw(flat/n))==h,'unchanged final readback '+n)
ck(not any(n.split('.')[0] in {'numpy','torch','scipy'} for n in sys.modules),'no numerical imports')
out={'decision':'ACCEPTED_ACTUAL_FINAL950_FLAT_ARCHIVAL_RECOVERY_ONLY','checks':len(checks),'results':results,'actual_files':len(want),'actual_recovery_sha256':sha(raw(flat/'recovery.json')),'remote_receipt_sha256':sha(raw(R/'REMOTE_RECOVERY03.json')),'remote_commit':remote['remote_commit'],'joined_capture_files':joined,'actual_terminal':term,'source_git_origin_union_review_separate':True,'native_or_execution_authority':False,'runtime':{'version':sys.version,'executable':sys.executable}}
(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,indent=2))
