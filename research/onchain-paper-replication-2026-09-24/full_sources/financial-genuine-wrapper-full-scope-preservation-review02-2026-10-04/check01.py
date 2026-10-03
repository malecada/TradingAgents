import ast,gzip,hashlib,importlib.util,io,json,os,shutil,stat,subprocess,sys,tarfile,time
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-root-preservation02-2026-10-04';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(U));spec=importlib.util.spec_from_file_location('archive_primitives_only',U/'recovery04.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def read(p):return a.read(p.parent,p.name)
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'pin '+p.name);v=json.loads(b);ck(a.encode(v)==b,'canonical '+p.name);return v
request=doc(P/'REQUEST01.json');receipt=doc(P/'CAPTURE01.json');manifest=doc(P/'complete-manifest01.json','850667c80ff2b1a66a0c65795178765d6e5ec3d873e52d809a5d7659593ac56f');root=Path(request['source_root']);head='868bfa6404a2c34d6e5b6e0932a2baf4b38eb370';base='44bf99d199acae5a043cf5b472a53e2fcf4caf1b';ck(receipt['request_sha256']==sha(read(P/'REQUEST01.json')) and receipt['source_root']==request['source_root'] and receipt['source']==request['actual_HEAD']==head,'actual capture request/source chain');ck(sha(read(U/'recovery04.py'))=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','exact accepted generic primitives');ck(a.scan(root)==manifest,'whole originalGit/source tree before');archive=read(P/'complete-source01.tar.gz');info=receipt['archive'];ck(len(archive)==info['bytes']==2219301 and sha(archive)==info['sha256']=='497a0ae3c0aba9b5f8bb41e933bed878ba49adf759a880d8a338637d732d1af4' and info['manifest_sha256']==request['complete_manifest_sha256'],'exactactualcompressedarchive')
# Use only prior independent pure raw framing/reencoding definitions.
prior=F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py';tree=ast.parse(read(prior));defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('decode','recode')];ck(len(defs)==2,'independent puredecoderpair');exec(compile(ast.Module(body=defs,type_ignores=[]),str(prior),'exec'));bodies,framing=decode(archive,manifest);ck(recode(manifest,bodies)==archive,'independent fullcanonicalgzip/TAR equality');files={r['path']:r for r in manifest['members'] if r['kind']=='file'};ck(len(manifest['members'])==receipt['members']==755 and len(files)==receipt['regular_bodies']==533 and sum(r['bytes'] for r in files.values())==receipt['logical_bytes']==4926523,'actual755/533/4926523');ck(all(read(root/n)==bodies[n] for n in files),'all533opaque original/archive bodies');ck(stat.S_IMODE(root.lstat().st_mode)==manifest['root_mode'],'originalrootmode');allocated=root.lstat().st_blocks*512+sum((root/r['path']).lstat().st_blocks*512 for r in manifest['members']);ck(allocated<=a.BASE and receipt['logical_bytes']<=a.BASE and len(archive)<=a.FILE,'actual4/128MiB bounds');free=shutil.disk_usage(P).free;ck(free>=a.FLOOR,'current10GiBfloor')
def git(args,data=None):
 r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never','-C',str(root),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_NO_REPLACE_OBJECTS':'1','GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'boundedfinancialGit');return r.stdout
ck(git(['rev-parse','HEAD']).decode().strip()==head,'actualfinancialHEAD');ck(all(not os.path.lexists(root/n) for n in ['.git/objects/info/alternates','.git/info/grafts','.git/refs/replace']),'no foreignGit authority');priorreview=doc(F/'financial-genuine-wrapper-installed-expectation-review01-2026-10-04/READBACK01.json','654c84e1c98110d54bf4b5c91ec1ed2bb2f594b0bb800bdca3e8fe18148b92a6');ck(sha(read(F/'financial-genuine-wrapper-installed-expectation-review01-2026-10-04/REVIEW01.md'))==request['installed_scope_review']['REVIEW01.md'],'accepted actualinstalled review');rows={r['path']:r for r in priorreview['joined']};current={}
for entry in git(['ls-tree','-r','-z',head]).split(b'\0'):
 if not entry:continue
 m,n=entry.split(b'\t');mode,typ,oid=m.decode().split();ck(typ=='blob','actualtrackedtype');current[n.decode()]={'oid':oid,'git_mode':mode}
ck(set(current)==set(rows)=={n for n in files if not n.startswith('.git/')} and len(current)==243,'complete tracked242 vswholeGitFs');reply=git(['cat-file','--batch'],(''.join(current[n]['oid']+'\n' for n in sorted(current))).encode());offset=0
for n in sorted(current):
 end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);body=reply[end+1:end+1+size];offset=end+size+2;r=rows[n];ck(reply[offset-1:offset]==b'\n' and typ=='blob' and oid==current[n]['oid']==r['git_object'] and current[n]['git_mode']==r['git_mode'],'actualcommittedOid/mode');ck(body==bodies[n] and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest()==oid and sha(body)==r['sha256'] and size==r['bytes'] and files[n]['mode']==r['mode'],'all242actualGit/archive/pinjoin')
ck(offset==len(reply),'completeGitbatch');ck(priorreview['implementation']==194 and sum(n.startswith('tradingagents/') for n in current)==149,'194code149package vs48aux');ck(git(['rev-parse',head+'^']).decode().strip()==base,'actual390baselineparent');ck(not any(n.startswith(('research_runs/','research_artifacts/','fixture_outer/')) for n in files),'noRunclaimoutputnamespace');D='fixture_inputs/financial_wrapper_draft01/';draft=json.loads(bodies[D+'DRAFT01.json']);env=json.loads(bodies[D+'environment.DRAFT.json']);mapping=json.loads(bodies[D+'runtime_mapping.json']);ck(sha(bodies['uv.lock'])==mapping['lock_sha256'],'archivedrootlock joins originalruntime metadata');ck(all(env[k] is None for k in ['torch_version','cuda_build','cuda_available']),'actual liveTorch unavailable');ck(all(v is None for v in draft['future'].values()) and draft['future_admitted_source_total'] is None,'notregistered/unreleased')
for slot in draft['slots']:
 ck(len(slot['inputs'])==8 and slot['admitted'] is False and slot['actual_outcome'] is None,'18draftslots notactualdeps')
 for ref in slot['inputs'].values():ck(sha(bodies[D+Path(ref['prepared_path']).name])==ref['sha256'] and ref['path'] is None and ref['dataset'] is None,'144archivebodydraftjoins')
ck(len(draft['slots'])==18,'18unreserved phases')
# Targeted same-user writer snapshot reads fd links/flags only, never environment.
writers=[];denied=[];fdcount=0;deadline=time.monotonic()+20
for p in Path('/proc').iterdir():
 if not p.name.isdecimal() or int(p.name)==os.getpid():continue
 ck(time.monotonic()<deadline,'finitewriter snapshot')
 try:
  if p.stat().st_uid!=os.geteuid():continue
  for f in (p/'fd').iterdir():
   fdcount+=1;ck(fdcount<=32768,'finitefdcount')
   try:
    target=os.readlink(f).removesuffix(' (deleted)');path=Path(target)
    if not path.is_absolute() or not path.is_relative_to(root):continue
    props=dict(line.split(':',1) for line in (p/'fdinfo'/f.name).read_text().splitlines() if ':' in line);flags=int(props['flags'].strip(),8)
    if flags&os.O_ACCMODE in (os.O_WRONLY,os.O_RDWR):writers.append({'pid':p.name,'fd':f.name,'target':target})
   except FileNotFoundError:pass
   except PermissionError:denied.append({'pid':p.name,'fd':f.name})
 except FileNotFoundError:pass
 except PermissionError:denied.append({'pid':p.name,'fd':None})
ck(not writers,'no observed sameuser rootwritable descriptors');ck(a.scan(root)==manifest,'whole actualsourceGit stableafter');ck(git(['rev-parse','HEAD']).decode().strip()==head and git(['status','--porcelain','--untracked-files=all'])==b'','current clean stableHEAD');support=[]
for f in sorted(P.iterdir()):
 ck(f.is_file() and not f.is_symlink(),'capture support regular');raw=read(f);support.append({'path':f.name,'kind':'file','mode':stat.S_IMODE(f.lstat().st_mode),'bytes':len(raw),'sha256':sha(raw)})
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numericalimports');terminal=doc(P/'ACTUAL_CAPTURE_TERMINAL01.json');ck(terminal['actual_exit']==0 and terminal['actual_capture_sha256']==sha(read(P/'CAPTURE01.json')) and terminal['actual_capture_elapsed_seconds']==receipt['elapsed_seconds'] and terminal['native_or_claim_started'] is False,'actual terminal capture joins')
ck(len(receipt['disk_floor_observations'])==4 and all(x['free_bytes']>=a.FLOOR for x in receipt['disk_floor_observations']) and receipt['continuous_disk_watch_claim'] is False,'four actual observed disk floors')
for name,pin in request['capture_primitive_sha256'].items():ck(sha(read(U/name))==pin,'actual accepted primitive '+name)
I=F/'financial-genuine-wrapper-installed-expectation-review01-2026-10-04'
ck(request['installed_scope_review']['MANIFEST01.json']=='3ff3490c90313d5477174292b736b5974b9512e62dba3b18dd03ab33f3ed944d','exact accepted review pin')
ck(set(request['installed_scope_review'])=={p.name for p in I.iterdir()},'complete installed review request joins')
for name,pin in request['installed_scope_review'].items():ck(sha(read(I/name))==pin,'actual installed review member '+name)
ck(sha(read(P/'capture_source02.py'))=='9c7cd6cb545040cd2146e84fb06623d95d1a79c557241eddacece2067212fef1','actual accepted caller02');intent=doc(P/'INTENT01.json');ck(intent['source']==head and intent['request_sha256']==receipt['request_sha256'],'actual one-use intent chain')
ck(sha(bodies['fixture_inputs/financial_wrapper_expectation01/environment.json'])=='1ff7418a2b7c77300aea731cea5bba78277d323241ac0ec59f41f43207c66d87','actual historical expectation archived')
ck(git(['rev-parse',base+'^']).decode().strip()=='390c82a9958e135c24bcca80f3a636313ca27932','actual original194 ancestry');(O/'SUPPORT01.json').write_bytes(a.encode({'members':support,'scope':'complete observed capture directory support; fixed cardinality not assumed'}))
out={'decision':'ACCEPTED_LOCAL_COMPLETE_FINANCIAL_SOURCE_ARCHIVE_ONLY','checks':len(checks),'request_sha256':sha(read(P/'REQUEST01.json')),'capture_sha256':sha(read(P/'CAPTURE01.json')),'manifest_sha256':info['manifest_sha256'],'archive':info,'current_commit':head,'baseline_commit':base,'whole_typed_members':755,'whole_regular_bodies':533,'tracked243':243,'implementation194':194,'package149':149,'draft_and_expectation_auxiliary49':49,'logical_bytes':4926523,'allocated_bytes':allocated,'disk_free_bytes':free,'framing':framing,'writer_snapshot':{'writers':writers,'inaccessible':denied,'fd_count':fdcount,'qualification':'observed accessible same-user descriptors only; complete repeated tree stability is verified; no universal/future writer guarantee'},'external_or_flat_recovery':False,'held205_33_authenticator_used':False,'genuine_runtime_or_registration':False};(O/'READBACK01.json').write_bytes(a.encode(out));print(json.dumps(out,indent=2))
