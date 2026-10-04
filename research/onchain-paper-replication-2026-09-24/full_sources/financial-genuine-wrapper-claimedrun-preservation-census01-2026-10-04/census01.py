import ast,gzip,hashlib,io,json,os,shutil,stat,subprocess,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):assert v,m;checks.append(m)
def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'bounded regular canonical body');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  chunks=[];total=0
  while True:
   b=os.read(fd,65536)
   if not b:break
   total+=len(b);ck(total<=s.st_size,'bounded body extent');chunks.append(b)
  ck(total==s.st_size and sig(os.fstat(fd))==sig(s)==sig(p.lstat()),'stable byte observation');return b''.join(chunks)
 finally:os.close(fd)
def git(args):
 p=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never',*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_TERMINAL_PROMPT':'0'});ck(p.returncode==0 and len(p.stdout)<=8*1024**2 and len(p.stderr)<=65536,'bounded readonlylocalGit');return p.stdout
names=['financial-genuine-wrapper-claimed-run-correction-preparation01-2026-10-04','financial-genuine-wrapper-claimed-run-correction-review01-2026-10-04','financial-genuine-wrapper-claimedrun-budget19-review01-2026-10-04','financial-genuine-wrapper-claimedrun-capsule-history-review01-2026-10-04','financial-genuine-wrapper-claimedrun-history-copy-admission-review01-2026-10-04','financial-genuine-wrapper-claimedrun-source-handoff-preparation01-2026-10-04','financial-genuine-wrapper-claimedrun-source-handoff-preparation02-2026-10-04','financial-genuine-wrapper-claimedrun-source-handoff-review01-2026-10-04','financial-genuine-wrapper-claimedrun-source-handoff-review02-2026-10-04','financial-genuine-wrapper-root-claimedrun-budget19-preparation01-2026-10-04','financial-genuine-wrapper-root-claimedrun-capsule-history-preparation01-2026-10-04','financial-genuine-wrapper-root-claimedrun-capsule-history-preparation02-2026-10-04','financial-genuine-wrapper-root-claimedrun-handoff-generation01-2026-10-04','financial-genuine-wrapper-root-claimedrun-source-registration01-2026-10-04','financial-genuine-wrapper-root-claimedrun-source-registration02-2026-10-04']
S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');roots=[('current-source02',S)]+[(n,F/n) for n in names];census=[];manifests={};membership={}
def scan(root):
 rootstat=root.lstat();ck(stat.S_ISDIR(rootstat.st_mode) and root.resolve()==root,'canonical literal root');members=[];bodies={}
 def walk(d):
  for e in sorted(os.scandir(d),key=lambda e:e.name):
   p=Path(e.path);s=p.lstat();n=p.relative_to(root).as_posix();r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
   if stat.S_ISDIR(s.st_mode):r['kind']='directory';members.append(r);walk(p)
   elif stat.S_ISREG(s.st_mode):b=read(p);r.update(kind='file',bytes=len(b),sha256=sha(b));members.append(r);bodies[n]=b
   elif stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p));members.append(r)
   else:raise AssertionError('unsupported actual scope type '+str(p))
 walk(root);members.sort(key=lambda r:r['path']);return {'schema_version':1,'root_mode':stat.S_IMODE(rootstat.st_mode),'members':members},bodies
for name,root in roots:
 m,bodies=scan(root);manifests[name]=m;membership[name]={r['path'] for r in m['members']};logical=sum(len(b) for b in bodies.values());ck(logical<=128*1024**2,'per-scope128MiB baseline');sink=io.BytesIO()
 # Canonical in-memory feasibility only; never writes an archive or copies a source tree.
 with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in m['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    elif r['kind']=='lexical-symlink':t.type=tarfile.SYMTYPE;t.linkname=r['target'];t.size=0;tar.addfile(t)
    else:t.size=r['bytes'];tar.addfile(t,io.BytesIO(bodies[r['path']]))
 projected=sink.getvalue();ck(len(projected)<=4*1024**2,'projected opaque archive fits selected4MiB cap');m2,_=scan(root);ck(m2==m,'scope stable over byte measurement');census.append({'name':name,'root':str(root),'members_excluding_root':len(m['members']),'regular':len(bodies),'lexical_links':sum(r['kind']=='lexical-symlink' for r in m['members']),'logical_bytes':logical,'maximum_regular_bytes':max(map(len,bodies.values()),default=0),'projected_canonical_archive_bytes':len(projected),'projected_archive_sha256':sha(projected),'archive_written':False,'manifest_sha256':sha((json.dumps(m,sort_keys=True,indent=2)+'\n').encode())})
H='0a2e7639b42b9423b90743feadcda4078aa21816';ck(git(['-C',str(S),'rev-parse','HEAD']).decode().strip()==H,'actual new currentSource');tree=git(['-C',str(S),'ls-tree','-r','-z',H]);rows=[]
for ent in tree.split(b'\0'):
 if ent:meta,n=ent.split(b'\t');mode,kind,oid=meta.decode().split();body=read(S/n.decode());ck(kind=='blob' and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'actual current tracked body/OID');rows.append(n.decode())
ck(len(rows)==339,'actual339tracked source');gatepath=S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json';ck(sha(read(gatepath))=='3a20293832fa7ecc5e2821fb27dc940d1a997ab7f2ad373bc28f73e893e8781a','actual committed gate bytes');closure=json.loads(read(S/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json'));ck(len(closure['installed'])==194 and sum(n.startswith('tradingagents/') for n in closure['installed'])==149,'actual method/package count')
for n,pin in closure['installed'].items():ck(sha(read(S/n))==pin,'all194 opaque implementation pins')
ID='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';claimroot=S/'research_runs'/ID;ck(sha(read(claimroot/'claim.json'))=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128' and sha(read(claimroot/'failed.json'))=='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','genuine copied spent history in fullscope');ck({p.name for p in (S/'research_runs').iterdir()}=={ID,'.lock'},'no newclaim census');ck(not os.path.lexists(S/'research_artifacts'),'no new native/fit output root')
# Verify recorded complete snapshots against every frozen manifest without following literal witnesses.
manifest_gaps=[];frozen_manifest_joins=0
for name,root in roots[1:]:
 by={r['path']:r for r in manifests[name]['members']}
 for p in sorted(root.glob('MANIFEST*.json')):
  doc=json.loads(read(p))
  for r in doc.get('members',doc.get('entries',[])):
   if r['path'] not in by:manifest_gaps.append({'scope':name,'manifest':p.name,'member':r['path']});continue
   actual=by[r['path']];mode=r.get('mode');mode=int(mode,8) if isinstance(mode,str) else mode;ck(mode==actual['mode'],'original frozen witness literal mode')
   if r.get('kind',r.get('type'))=='file':ck(actual['kind']=='file' and actual['sha256']==r['sha256'] and actual['bytes']==r.get('bytes',r.get('size')),'complete original frozen witness body')
   frozen_manifest_joins+=1
ck(not manifest_gaps,'no gaps in whole original review scopes')
selected_previous=json.loads(read(F/'financial-genuine-wrapper-root-recordfix-failed-remote01-2026-10-04/SELECTED_BODIES01.json'));previous={r['path']:r for r in selected_previous['rows']};reused=[]
for r in census:
 root=Path(r['root']);m=manifests[r['name']];regular=[x for x in m['members'] if x['kind']=='file'];covered=[]
 for x in regular:
  p=root/x['path']
  if p.is_relative_to(ROOT):v=previous.get(p.relative_to(ROOT).as_posix());covered.append(v is not None and v['sha256']==x['sha256'] and v['bytes']==x['bytes'])
 r['already_selected_same_body_previous61ce_regular']=sum(covered)
 if regular and sum(covered)==len(regular):reused.append(r['name'])
for n,m in manifests.items():(O/(n+'.manifest.json')).write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
free=shutil.disk_usage(F).free;ck(free>=10*1024**3,'actual current10GiBfloor');minimum_bundle_paths=6+3*len(census)+4;expected_ops=11+2*minimum_bundle_paths;ck(minimum_bundle_paths<=506 and expected_ops<=1024,'provisional packaging selection finite before pendingParent/reviews');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
x={'schema_version':1,'decision':'CURRENT_KNOWN_BYTE_SCOPE_CENSUS_ONLY_FINAL_PARENT_AND_REVIEW_APPENDAGES_PENDING','checks':len(checks),'source':H,'tracked':339,'prospective_source_pins':338,'implementation':194,'package':149,'known_scopes':census,'fully_already_selected_in_actual_failed_remote61ce':reused,'frozen_original_manifest_member_joins':frozen_manifest_joins,'all_known_logical_bytes':sum(r['logical_bytes'] for r in census),'all_projected_compressed_bytes':sum(r['projected_canonical_archive_bytes'] for r in census),'provisional_packaging_paths_with_six_legacy_and_four_records':minimum_bundle_paths,'provisional_expected_git_calls':expected_ops,'pending_scopes':['actual current Source admission review','frozen new Parent preparation and independent source review','actual Parent complete installed tree including final request/proofs/release','Root actual Parent composition/validation records','actual verifier/binding and complete original verifier review witnesses if applicable','this complete final census and later exact capture/selection/remote/flat source reviews'],'observed_free_bytes':free,'actual_archive_written_or_external_recovery':False,'genuine_spent_identity_count':1,'highest_actual_claim_budget':18,'cumulative19_admission_or_native_authority':False,'qualification':'Whole opaque review snapshots preserve each literal symlink as metadata and never follow/extract it. Actual source capture, final Parent closure, external selection, remote and fresh recovery require exact later immutable inventories and independent release.'};(O/'CENSUS01.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items() if k!='known_scopes'},sort_keys=True))
