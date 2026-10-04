import ast,gzip,hashlib,importlib.metadata,importlib.util,io,json,os,platform,shutil,stat,subprocess,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-root-flat-recovery04-2026-10-04';REMOTE=F/'financial-genuine-wrapper-root-remote-recovery04-2026-10-04';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
ck(sha((U/'recovery04.py').read_bytes())=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','actualunchangedR4');sys.path.insert(0,str(U));sp=importlib.util.spec_from_file_location('two_flat_review',U/'recovery04.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def read(p):return a.read(p.parent,p.name)
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'pin '+p.name);v=json.loads(b);ck(a.encode(v)==b,'canonical '+p.name);return v
old=doc(O/'MANIFEST01.json','263733b168add2376a4f1ec7acee9a057c569e6c9b6b7b5f9d54aa3733c2e77e')
for row in old['members']:ck(sha(read(O/row['path']))==row['sha256'] and stat.S_IMODE((O/row['path']).stat().st_mode)==row['mode'],'priorremote01 immutable')
r=doc(P/'RECOVERY01.json','2eb6546ab3e3953847610d328c301129441d38afa9f0fb8eeca056a192264f49');rr=doc(REMOTE/'REMOTE_RECOVERY01.json',r['remote_receipt_sha256']);ck(r['remote_receipt_sha256']=='f1e0a5d30b6a570dfab324ae87a8cab5b4a63695939de8479365765b0702b27e' and r['independent_flat_source_review_manifest_sha256']=='0bb4ea9214ec1c393fe2bdddb1eb66cdfafee15bdec11cd281f57837bd33b67c','actualaccepted external/source lineage');ck(len(rr['selected_blobs'])==394 and len({x['path'] for x in rr['selected_blobs']})==394,'actual394uniqueorigin rows')
for row in rr['selected_blobs']:
 b=read(REMOTE/'selected'/row['path']);ck(len(b)==row['bytes'] and sha(b)==row['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_object'],'all394external body/OIDpins retained')
B=REMOTE/'selected/research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-preservation06-2026-10-04';cap=doc(B/'CAPTURE01.json',r['capture_sha256']);q=doc(B/'REQUEST01.json',cap['request_sha256']);H='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0';ck(r['source']==q['source']==cap['source']==H,'actual current financial source');prior=F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py';tree=ast.parse(read(prior));defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('decode','recode')];exec(compile(ast.Module(body=defs,type_ignores=[]),str(prior),'exec'));results={};recovered={};manifests={};inode_rows=[]
for role,count,regular in [('source',878,631),('parent',30,28),('outer',8,8)]:
 D=P/('flat-'+role+'01');root=Path(q['roots'][role]);info=r['actual'][role];m=doc(B/(role.upper()+'_MANIFEST01.json'),info['manifest_sha256']);meta=doc(D/info['metadata_file'],info['metadata_sha256']);ck(meta['manifest']==m and meta['archive']==cap['archives'][role] and len(m['members'])==info['members']==count,'full targetmetadata lineage');mapping=meta['flat_members'];files={x['path']:x for x in m['members'] if x['kind']=='file'};ck(set(mapping)==set(files) and len(mapping)==len(set(mapping.values()))==regular and set(mapping.values())=={f'body-{i:05d}.body' for i in range(regular)},'complete distinct targetbody mapping');ck({p.name for p in D.iterdir()}==set(mapping.values())|{'body-metadata.json'} and stat.S_IMODE(D.stat().st_mode)==0o700 and D.resolve()==D,'exactprivateflat membership');bodies={}
 for n,leaf in mapping.items():
  p=D/leaf;s=p.lstat();b=read(p);ck(s.st_nlink==1 and stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and len(b)==files[n]['bytes'] and sha(b)==files[n]['sha256'] and b==read(root/n),'everyrecovered originalsinglelink0600body');bodies[n]=b;inode_rows.append({'role':role,'semantic_path':n,'flat_file':leaf,'observed_device':s.st_dev,'observed_inode':s.st_ino,'bytes':len(b),'sha256':sha(b),'original_mode':files[n]['mode'],'actual_mode':0o600})
 ck((D/'body-metadata.json').stat().st_nlink==1 and stat.S_IMODE((D/'body-metadata.json').stat().st_mode)==0o600 and a.scan(root)==m,'actualmetadata0600/fulloriginalmodetree stable');raw=read(B/('complete-'+role+'01.tar.gz'));ck(sha(raw)==info['archive_sha256']==cap['archives'][role]['sha256'] and len(raw)==cap['archives'][role]['bytes'],'actual fetched archivepin');decoded,framing=decode(raw,m);ck(all(decoded[n]==b for n,b in bodies.items()) and recode(m,bodies)==raw,'wholecompressed canonicalreconstruction from actualflat');ck(info['root_mode']==m['root_mode']==stat.S_IMODE(root.stat().st_mode),'actualrootmodemetadata');ck(all(info[k] is False for k in ['instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority']),'no broad recoveryauthority');results[role]={'members':count,'regular_bodies':regular,'actual_flat_files':regular+1,'archive':cap['archives'][role],'metadata_sha256':info['metadata_sha256'],'framing':framing};recovered[role]=bodies;manifests[role]=m
sb=recovered['source'];pb=recovered['parent'];S=Path(q['roots']['source']);gate=json.loads(sb['fixture_inputs/financial_wrapper_registration01/gates.json']);draft=json.loads(pb['REQUEST_DRAFT01.json']);ck(draft['source']==draft['design_source']==H and draft['status']=='DRAFT_NOT_RELEASED' and draft['final_review'] is None and draft['proofs']['full_recovery'] is None,'actualrecovered draft nofinalrelease');exp=gate['experiments'][draft['identity']];ck(exp['source_files']==draft['source_files'] and len(exp['source_files'])==289 and len(gate['experiments'])==10,'actual289 source10initial')
for e in gate['experiments'].values():
 for role,ref in e['inputs'].items():ck(sha(sb[ref['path']])==ref['sha256'],'all80archived inputbodyjoins')
for n,h in exp['source_files'].items():ck(sha(sb[n])==h,'all289actualsourcepins');
installed=doc(F/'financial-genuine-wrapper-installed-gate-admission-review01-2026-10-04/READBACK01.json');rows={x['path']:x for x in installed['joined']}
def git(args):
 z=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never','-C',str(S),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1'});ck(z.returncode==0 and len(z.stdout)<=8*1024**2 and len(z.stderr)<=65536,'boundedofflinecurrentGit');return z.stdout
tree={}
for item in git(['ls-tree','-r','-z',H]).split(b'\0'):
 if not item:continue
 left,n=item.split(b'\t');mode,typ,oid=left.decode().split();ck(typ=='blob','actualtrackedregularGit');tree[n.decode()]=(mode,oid)
ck(set(tree)==set(rows)==set(exp['source_files'])|{'fixture_inputs/financial_wrapper_registration01/gates.json'} and len(tree)==290,'complete recoveredtracked290');fm={x['path']:x for x in manifests['source']['members']}
for n,row in rows.items():
 b=sb[n];ck(sha(b)==row['sha256'] and len(b)==row['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_oid']==tree[n][1] and tree[n][0]==row['git_mode'] and fm[n]['mode']==row['mode'],'all290actualrecovered OID/mode/body')
ck(installed['implementation']==194 and sum(n.startswith('tradingagents/') for n in rows)==149,'194149 scientificsource');comp=doc(F/'financial-genuine-wrapper-root-parent-composition01-2026-10-04/COMPOSITION01.json')
for n,ref in comp['proof_origins'].items():ck(pb['proofs/'+n]==read(Path(ref['path'])) and sha(pb['proofs/'+n])==ref['sha256'],'all5actualrecoveredproof origins')
for n in ['parent01.py','supervisor01.py','descendants01.py','owned_io.py','recovery04.py','bounded_git01.py','PROTOCOL_PINS01.json']:ck(pb[n]==read(F/'financial-genuine-wrapper-parent-preparation03-2026-10-04'/n),'7actualrecoveredacceptedhelpers')
ck(sha(pb['CASE_ORDER01.json'])=='341c045b452d9367c43a24916c80108f8a2a8cc9db669a02ada943c0f9e4108f' and json.loads(pb['CASE_ORDER01.json'])['first_initial']==draft['identity'],'exactrecoveredfixedorder/firstcase');runtime=json.loads(sb[exp['inputs']['runtime_mapping']['path']]);ck(runtime==draft['runtime_mapping'] and len(runtime['distribution_records'])==251,'runtime metadata recoveredidentically')
for row in runtime['distribution_records']:
 p=Path(row['record']);s=p.lstat();ck(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_size<=a.FILE and p.name=='RECORD' and p.is_relative_to(Path(sys.prefix)/'lib/python3.13/site-packages'),'readonly251RECORDscope');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);h=hashlib.sha256();count=0
 try:
  while True:
   b=os.read(fd,65536)
   if not b:break
   count+=len(b);ck(count<=a.FILE,'boundedRECORDbytes');h.update(b)
  ck(a.sig(s)==a.sig(os.fstat(fd))==a.sig(p.lstat()) and count==s.st_size and h.hexdigest()==row['record_sha256'] and importlib.metadata.version(row['name'])==row['version'],'actualmetadata stablehash/version')
 finally:os.close(fd)
env=json.loads(sb[exp['inputs']['environment']['path']]);ck(env['python']==platform.python_version() and env['cpu_count']==os.cpu_count() and all(importlib.metadata.version(n)==v for n,v in env['packages'].items()),'basicenvironment metadata only');ck(sha(sb['uv.lock'])==runtime['lock_sha256']==env['lock_sha256'],'actual recovered runtime lockpins');
final=json.loads(pb['REQUEST_FINAL03.json']);ck(sha(pb['REQUEST_FINAL03.json'])==r['original_failed_final_request_sha256']=='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc','original failed finalrequest unchanged')
contract=sha(a.encode({k:v for k,v in final.items() if k!='final_review'}));ck(contract=='6884fa8027cf49b519f5c635828244d4685ce0f989691593e816792e2586704a','original whole contract unchanged')
for role,ref in final['proofs'].items():
 n=Path(ref['path']).relative_to(Path(q['roots']['parent'])).as_posix();ck(sha(pb[n])==ref['sha256'],'original actual proof binding '+role)
ck(sha(pb['proofs/FINAL_RELEASE_REVIEW01.json'])=='7d18390bc44df519fcf43e88c1fb20e016994378fbc34b7d96d6e73690f8cd60','original genuine release machine preserved not renewed')
oldparent=doc(F/'financial-genuine-wrapper-root-preservation05-2026-10-04/PARENT_MANIFEST01.json');current={x['path']:x for x in manifests['parent']['members']};ck(all(current[x['path']]==x for x in oldparent['members']) and len(set(current)-{x['path'] for x in oldparent['members']})==7,'all23 original parent exact plus7 failure appendages')
pt=json.loads(pb['attempt/parent-terminal.json']);outer=recovered['outer'];ot=json.loads(outer['ACTUAL_TERMINAL01.json'])
ck(pt['actual_parent_exit'] is None and pt['actual_child_exit']==1 and pt['cleanup']['source_bound_no_dispatch'] is True and pt['outcome_semantics_accepted'] is False,'original NULL actualchild1 no-dispatch not accepted phase')
ck(ot['actual_parent_exit']==1,'separate Root actual parent exit1')
ck(b"runtime installed RECORD unavailable" in pb['attempt/stderr'] and pb['attempt/stdout']==b'','original actual fatal retained')
ck(sha(pb['attempt/owned-tree-cleanup.json'])==pt['cleanup']['owned_tree_cleanup_sha256'],'original cleanup hash authentic')
t=doc(P/'ACTUAL_TERMINAL01.json');intent=doc(P/'INTENT01.json');outerintent=doc(P/'ACTUAL_FLAT_INTENT01.json');stdout=read(P/'ACTUAL_RECOVERY01.out');stderr=read(P/'ACTUAL_RECOVERY01.err')
ck(t['actual_exit']==0 and t['actual_flat_receipt_sha256']==sha(read(P/'RECOVERY01.json')) and t['actual_stdout_sha256']==sha(stdout) and t['actual_stderr_sha256']==sha(stderr) and not stderr,'actual flat terminal and original streams')
summary=json.loads(stdout);ck(all(summary[k]==r[k] for k in summary),'actual flat stdout receipt')
ck(t['actual_session']==47434 and t['actual_start_tool']=='c2a9f1' and t['actual_completion_tool']=='06a32b','actual original flat tool records')
ck(intent['source']==H and intent['targets']==['source','parent','outer'] and intent['remote_receipt_sha256']==r['remote_receipt_sha256'],'actual original source intention lineage')
absent=[]
for pid in [intent['pid'],163035,163026]+[x['pid'] for x in rr['operations']]:
 ck(not Path('/proc',str(pid)).exists(),'actual original PID absent')
 try:os.killpg(pid,0)
 except ProcessLookupError:absent.append(pid)
 else:raise AssertionError('original process group remains')
ck(outerintent['actual_remote_review_manifest_sha256']==sha(read(O/'MANIFEST01.json')) and outerintent['flat_source_review_manifest_sha256']==r['independent_flat_source_review_manifest_sha256'],'actual genuine review prerequisites')
ck(sha(read(P/'restore01.py'))=='1b36e40c96045f35ea4a4e6926b9da6a594ab82c0346aa0ddb6c2bbb5aa5c02c','actual caller unchanged')
ck(len(r['disk_floor_observations'])==7 and all(x['free_bytes']>=a.FLOOR for x in r['disk_floor_observations']) and r['continuous_floor_watch_claim'] is False,'seven sampled floor observations')
ck(all(a.scan(Path(q['roots'][role]))==manifests[role] for role in ['source','parent','outer']) and git(['rev-parse','HEAD']).decode().strip()==H and git(['status','--porcelain','--untracked-files=all'])==b'','complete current source/Parent/outer stable and current Git unchanged')
ck(all(not os.path.lexists(S/n) for n in ['research_runs','research_artifacts','fixture_outer']),'actual numerical claims and native base absent')
ck(r['independent_failed_scope_acceptance'] is False and r['native_or_claim_started'] is False and r['complete_original_failed_scope_bytes_recovered'] is True and r['original_identity_permanently_reserved'] is True,'original honest failure recovery flags')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'FAILED_SCOPE_BYTE_UNION_ACCEPTED','checks':len(checks),'source':H,'flat_receipt_sha256':sha(read(P/'RECOVERY01.json')),'remote_receipt_sha256':r['remote_receipt_sha256'],'selection_sha256':rr['selection_sha256'],'actual_terminal_sha256':sha(read(P/'ACTUAL_TERMINAL01.json')),'prior_remote_review_manifest_sha256':sha(read(O/'MANIFEST01.json')),'capture_sha256':r['capture_sha256'],'original_final_request_sha256':r['original_failed_final_request_sha256'],'targets':results,'actual_flat_files':sum(v['actual_flat_files'] for v in results.values()),'tracked':290,'source_pins':289,'implementation':194,'package':149,'input_binding_joins':80,'runtime_records_metadata_only':251,'actual_elapsed_seconds':r['elapsed_seconds'],'original_intent_pid':intent['pid'],'all_reviewed_PIDs_groups_absent':absent,'claim_count_observed':0,'original_parent_terminal_exit':None,'actual_outer_exit':1,'original_identity_permanently_reserved':True,'native_absence_basis':'source-bound ordering and absent original output namespaces; not native OS property readback','current_Torch_API_equality':None,'source_correction_admitted':False,'original_posix_or_git_database_instantiated':False,'runtime_store_capacity_native_authority':False,'actual_inodes':inode_rows}
(O/'FLAT_READBACK02.json').write_bytes(a.encode(out));print(json.dumps({k:v for k,v in out.items() if k not in ('actual_inodes','all_reviewed_PIDs_groups_absent')},indent=2))
