from pathlib import Path
import os,stat,json,hashlib,importlib.util,io,gzip,tarfile,shutil,datetime
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B.parents[2];D=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';C=B/'heartbeat-root-checkpoint10-2026-10-04';V=B/'financial-wrapper-compatibility-operational-delta-flat-entry-review05-2026-10-04';checks=[];exports=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,s):
 if not v:raise AssertionError(s)
 checks.append(s)
def read(p,pin=None):
 s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded canonical file '+str(p));b=p.read_bytes();t=p.lstat();ok(tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))==tuple(getattr(t,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')),'stable body '+str(p));ok(pin is None or sha(b)==pin,'hash '+str(p));return b
def exp(p,n,pin=None):
 b=read(p,pin);q=H/'evidence'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);exports.append({'original':str(p),'copy':n,'sha256':sha(b),'bytes':len(b),'mode':stat.S_IMODE(p.lstat().st_mode)});return b
pinmap={'FLAT_RECOVERY01.json':'e702f568f1ec84bff0ccc7c4441adcd5f3209777e243dcae58b3f9432f8bd9e3','FLAT_POSTWRITE_OBSERVATION01.json':'72c9103653932d90d6ab4b42a1151557d982822f84c9ccf86feafee0f379489c','ROOT_FLAT05_EXIT01.json':'d3952457ab8d3799c1cc2af52ec61b14934d968045ba924842a3804fd0a2d94f','REMOTE_RECOVERY01.json':'64c74556c7060fc7d118b5b07354bb737e5c157446ffef8c27fe77ea6cef4d47','ROOT_REMOTE03_EXIT01.json':'0f0eba1ace202b735e4a94f7f5b24dadbafbd0dd95173251a7773134f92af916','SELECTED_BODIES01.json':'d2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b','ROOT_FLAT04_INSTALLATION_DRAFT01.json':'770f509c8a65a1a5a6cb33e2efbf8215c9466ba5af235251b883ac1452299e21'}
objects={n:json.loads(exp(D/n,n,p)) for n,p in pinmap.items()};f=objects['FLAT_RECOVERY01.json'];side=objects['FLAT_POSTWRITE_OBSERVATION01.json'];exit=objects['ROOT_FLAT05_EXIT01.json'];remote=objects['REMOTE_RECOVERY01.json'];sel=objects['SELECTED_BODIES01.json'];draft=objects['ROOT_FLAT04_INSTALLATION_DRAFT01.json']
for n in ['ROOT_FLAT05_INTENT01.json','ROOT_FLAT05_SPAWN01.json','FLAT_INTENT01.json']:objects[n]=json.loads(exp(D/n,n))
intent=objects['ROOT_FLAT05_INTENT01.json'];spawn=objects['ROOT_FLAT05_SPAWN01.json'];inner=objects['FLAT_INTENT01.json']
release=json.loads(exp(V/'MACHINE01.json','ENTRY_RELEASE05.json','18d36caf892c98f61232846058c61bbe7abe1c1522dce5954dff9765abbd276f'));exp(V/'MANIFEST01.json','ENTRY_MANIFEST05.json','f745feaf28ad7390a8e87ed2d3885b3e90c2b6dffe780a718aaa48d26a15c9c7');exp(C/'root_operational_flat05.py','root_operational_flat05.py',release['root_outer_caller_sha256'])
for n,p in draft['helpers_and_metadata'].items():b=exp(D/n,'installed/'+n,p['sha256']);ok(len(b)==p['bytes'] and stat.S_IMODE((D/n).lstat().st_mode)==p['mode'],'actual unchanged installed mode '+n)
sp=importlib.util.spec_from_file_location('actualreview',D/'restore01.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);co=M.VerifiedCohort();records=M.authenticate_selected(D,remote,sel,pinmap['SELECTED_BODIES01.json'],co);ok(len(records)==15,'actual remote15 still authenticated')
ok(release['decision']=='ACCEPTED_EXACT_ONE_USE_OPERATIONAL_FLAT_ENTRY_ONLY' and release['flat_execution_released'] is True and release['remote_execution_released'] is False and release['numerical_authority'] is False,'genuine exact flat-only release')
ok(intent['entry_review_sha256']==sha((V/'MACHINE01.json').read_bytes()) and intent['outer_caller_sha256']==release['root_outer_caller_sha256'] and intent['installation_draft_sha256']==release['installation_draft_sha256'],'intent release/caller/draft join')
ok(intent['argv']==spawn['argv']==[str(ROOT/'.venv/bin/python'),'-B',str(D/'restore01.py'),'--remote-receipt-sha256',pinmap['REMOTE_RECOVERY01.json'],'--selection-sha256',pinmap['SELECTED_BODIES01.json']],'exact actual source/pins argv')
ok(intent['parent_pid']==spawn['parent_pid'] and spawn['pid']==exit['actual_child_pid']==1026975 and intent['one_use'] is True,'actual parent/child identities')
ok(exit['actual_outer_exit']==exit['actual_child_exit']==0 and exit['cleanup_failures']==[] and exit['parent_failure_type'] is None,'actual terminal clean zero');ok(exit['actual_parent_fsize_readback']==[4194304,4194304] and exit['child_fsize_inheritance']=='default subprocess inheritance; no separate child readback claimed','actual parent limits distinct from child inheritance')
for x in [intent,exit]:ok(x['remote_relaunched'] is False and x['native_or_claim_started'] is False,'no remote replay/native in original receipt')
for n in ['stdout','stderr']:
 b=exp(D/('ROOT_FLAT05.'+n),'ROOT_FLAT05.'+n);ok(len(b)==exit[n+'_bytes'] and sha(b)==exit[n+'_sha256'],'actual '+n+' terminal byte hash')
stdout=json.loads((D/'ROOT_FLAT05.stdout').read_bytes());ok(stdout['status']==f['status'] and stdout['regular_bodies']==64,'actual child stdout joins outcome')
ok(f['actual_root_exit'] is None and f['numerical_release'] is None and f['whole_fit_capacity'] is None and f['native_or_claim_started'] is False and f['posix_tree_restored'] is False,'original nulls and source-only exclusions remain')
ok(f['remote_receipt_sha256']==release['remote_receipt_sha256'] and f['selection_sha256']==release['selection_sha256'] and f['read_only_selected_mode_profile_sha256']==M.PINS['COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json'],'actual flat exact remote/profile lineage')
ok(f['source']==M.SOURCE and f['policy_sha256']==M.POLICY and f['capture_sha256']==M.CAPTURE and f['failed_capture_sha256']==M.FAILED_CAPTURE,'genuine source policy both captures')
for k in ['source','policy_sha256','capture_sha256','failed_capture_sha256','remote_receipt_sha256','selection_sha256']:ok(inner[k]==f[k],'inner intent '+k)
flatrows=[];archival=[];maps={}
for out,key,rel,loader,aname in [(M.OUTPUT,'restored',M.REL,M.load_capture,'operational-delta01.tar.gz'),(M.FAILED_OUTPUT,'failed_restored',M.FAILED_REL,M.load_failed_capture,'failed-remote02.tar.gz')]:
 dest=D/out;bundle=D/'selected'/rel;capture,manifest=loader(bundle,co);result=f[key];meta=M.verify_flat(dest,result,capture,manifest,lambda:None,co);maps[key]=meta
 ok(result['members']==len(manifest['members']) and result['regular_bodies']==sum(z['kind']=='file' for z in manifest['members']),'actual full denominator '+out)
 for flag in ['instantiated_posix_tree','outside_stores_recovered','recovered_tree_git_join','research_authority','runtime_package_bodies_recovered']:ok(result[flag] is False,'honest result exclusion '+flag)
 exp(dest/result['metadata_file'],out+'-metadata.json',result['metadata_sha256'])
 archive=read(bundle/aname,capture['archive']['sha256']);ok(len(list(M.R.framed_members(archive)))==len(manifest['members']),'original full canonical framing/footer '+out)
 buf=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=buf,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for z in manifest['members']:
    ti=tarfile.TarInfo(z['path']);ti.mode=z['mode'];ti.uid=ti.gid=0;ti.uname=ti.gname='';ti.mtime=0
    if z['kind']=='directory':ti.type=tarfile.DIRTYPE;ti.size=0;tar.addfile(ti);continue
    leaf=meta['flat_members'][z['path']];p=dest/leaf;body=read(p,z['sha256']);ok(len(body)==z['bytes'] and stat.S_IMODE(p.lstat().st_mode)==0o600,'actual body private extent '+z['path']);ok(body==read(ROOT/rel/'snapshot'/z['path']),'actual restored versus original snapshot '+z['path']);ti.size=len(body);tar.addfile(ti,io.BytesIO(body));flatrows.append({'scope':out,'original':z['path'],'flat':leaf,'bytes':len(body),'sha256':sha(body),'original_mode':z['mode'],'physical_mode':0o600})
 ok(buf.getvalue()==archive,'independent full canonical gzip reencoding from actual flat '+out);archival.append({'scope':out,'typed':len(manifest['members']),'files':result['regular_bodies'],'metadata_sha256':result['metadata_sha256'],'archive_sha256':sha(archive)})
 ok(set(p.name for p in dest.iterdir())==set(meta['flat_members'].values())|{result['metadata_file']},'exact flat namespace no omitted/extra/partial '+out)
ok(len(flatrows)==64,'complete64 originals/66 physical files')
# Genuine historical failure evidence from restored opaque JSON, no checkpoint/scientific decoding.
failedmeta=maps['failed_restored'];failedroot=D/M.FAILED_OUTPUT
failed=json.loads(read(failedroot/failedmeta['flat_members']['FAILED01.json'],'7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a'))
ok([z['exit'] for z in failed['operations']]==[0,0,None] and [z['actual_reaped_exit'] for z in failed['operations']]==[0,0,0],'restored original init NULL versus reap0 remains')
oldexit=json.loads(read(failedroot/failedmeta['flat_members']['ROOT_REMOTE02_EXIT01.json']));ok(oldexit['actual_outer_exit']==1,'restored original root failure remains1')
# Sidecar was not covered by helper byte cohort: authenticate explicitly now.
ok(side['recovery_sha256']==pinmap['FLAT_RECOVERY01.json'] and side['qualification']=='post recovery-receipt write; this sidecar itself is outside that observation','sidecar exact original binding/qualification');ok(f['initial_owned_allocation']==f['whole_tree_observations'][0] and f['whole_tree_policy']==M.W.POLICY,'original observation baseline/policy')
observations=f['whole_tree_observations']+[side['observation'],stdout['postwrite_observation']]+exit['whole_owned_observations']
for i,o in enumerate(observations):
 ok(o['logical_bytes']<=67108864 and o['allocated_bytes']<=100663296 and o['members']<=32768 and 0<=o['seconds']<5 and 1<=o['complete_attempts']<=3,'all actual whole-tree observation '+str(i))
 if 'free_bytes' in o:ok(o['free_bytes']>=10737418240,'actual observed floor '+str(i))
 if 'elapsed_seconds' in o:ok(o['elapsed_seconds']<180,'actual inner bounded deadline '+str(i))
ok(len(f['whole_tree_observations'])<64 and len(exit['whole_owned_observations'])<=130 and exit['elapsed_seconds']<210,'original finite orchestration counts/deadlines')
for n in ['FLAT_FAILED01.json','ROOT_FLAT04_INTENT01.json','ROOT_FLAT04_SPAWN01.json','ROOT_FLAT04_EXIT01.json','ROOT_FLAT04.stdout','ROOT_FLAT04.stderr']:ok(not os.path.lexists(D/n),'absent failure/withheld04 namespace '+n)
pids={intent['parent_pid'],spawn['pid']}|{z['pid'] for z in remote['operations']};pids|={json.loads((D/'ROOT_REMOTE03_INTENT01.json').read_bytes())['parent_pid'],json.loads((D/'ROOT_REMOTE03_SPAWN01.json').read_bytes())['pid']}
for p in sorted(pids):ok(not Path('/proc',str(p)).exists(),'actual recorded PID absent '+str(p))
groups={}
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:b=(p/'stat').read_text();g=int(b[b.rindex(')')+2:].split()[2])
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 if g in pids:groups.setdefault(str(g),[]).append(int(p.name))
ok(not groups,'all recorded possible processgroup IDs absent');co.check();ok(True,'final shared input+actual outputs byte cohort rejoin')
current=M.W.census(D);floor=shutil.disk_usage(D).free;ok(floor>=M.R.FLOOR,'current floor still adequate')
# Rejoin separately read sidecar/Root terminal after all reads.
for n in pinmap:ok(sha(read(D/n))==pinmap[n],'final independent receipt/sidecar pin '+n)
result={'status':'ACCEPTED_ACTUAL_TWO_SCOPE_BYTE_RECOVERY','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'assertions':len(checks),'checks':checks,'flat_receipt_sha256':pinmap['FLAT_RECOVERY01.json'],'sidecar_sha256':pinmap['FLAT_POSTWRITE_OBSERVATION01.json'],'root_exit_sha256':pinmap['ROOT_FLAT05_EXIT01.json'],'release_sha256':intent['entry_review_sha256'],'root_elapsed_seconds':exit['elapsed_seconds'],'recorded_flat_pid':spawn['pid'],'recorded_parent_pid':intent['parent_pid'],'recorded_processes_absent':sorted(pids),'matching_groups':groups,'archival_scopes':archival,'flat_files':flatrows,'physical_regular_files':66,'original_regular_bodies':64,'original_typed_descendants':83,'failed_original_typed_including_root':43,'inner_receipt_samples':len(f['whole_tree_observations']),'sidecar_samples':1,'stdout_final_samples':1,'root_samples':len(exit['whole_owned_observations']),'combined_maxima':{k:max(o[k] for o in observations) for k in ['logical_bytes','allocated_bytes','members']},'current_owned_observation':current,'current_floor':floor,'exports':exports,'composed_git385_plus9_proof':None,'posix_tree':False,'runtime_bodies':False,'numerical_authority':False,'actual_helper_rerun':False,'tool_event_attribution':'Root supplied e38e0a exit0; raw actual caller/child receipts authenticated here, no independent original tool event available'}
(H/'READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:result[k] for k in ['status','assertions','physical_regular_files','inner_receipt_samples','root_samples','combined_maxima']}))
