import ast,hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;ROOT=Path.cwd();P=F/'financial-genuine-wrapper-root-recordfix-failed-remote01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'regular canonical bounded input');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  ck(sig(os.fstat(fd))==sig(s),'actual opened identity');out=[];total=0
  while True:
   b=os.read(fd,65536)
   if not b:break
   total+=len(b);ck(total<=s.st_size,'bounded extent');out.append(b)
  ck(sig(os.fstat(fd))==sig(s)==sig(p.lstat()) and total==s.st_size,'stable body identity');return b''.join(out)
 finally:os.close(fd)
def git(args,data=None):
 r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never',*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env={'PATH':'/usr/bin:/bin','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'});ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded local Git only');return r.stdout
raw=read(P/'SELECTED_BODIES01.json');ck(sha(raw)=='59bd4601e99418d669f84d4b9f65320bf7e0907a51cbd4a561e9a2495227781f','exact selection pin');raw_selection=raw;v=json.loads(raw);ck((json.dumps(v,sort_keys=True,indent=2)+'\n').encode()==raw,'canonical selection');H='d6859b5cabccde4e4c5af2320cb96b397dfbedd4';ck(v['remote_commit']==H,'explicit committed selection');rows=v['rows'];names=[r['path'] for r in rows];ck(names==sorted(set(names)) and len(rows)==270 and sum(r['bytes'] for r in rows)==17965145,'exact unique270 extent17965145');ck(11+2*len(rows)==551 and len(rows)<=506 and 551<=1024 and sum(r['bytes'] for r in rows)<=64*1024**2,'effective row and operation budgets');ck(git(['rev-parse','HEAD']).decode().strip()==H,'actual MainHEAD selectedcommit')
committed={}
for ent in git(['ls-tree','-r','-z',H,'--',*names]).split(b'\0'):
 if not ent:continue
 meta,path=ent.split(b'\t');mode,typ,oid=meta.decode().split();committed[path.decode()]={'git_mode':mode,'kind':typ,'git_object':oid}
ck(set(committed)==set(names),'exact committed selected tree');reply=b''.join(git(['cat-file','--batch'],(''.join(committed[n]['git_object']+'\n' for n in names[i:i+40])).encode()) for i in range(0,len(names),40));offset=0;joined=[]
for row in rows:
 n=row['path'];p=ROOT/n;meta=committed[n];ck(n.startswith('research/') and Path(n).as_posix()==n and '..' not in Path(n).parts and not any(x in ('.env','keys','apis') for x in Path(n).parts),'safe exact path');ck(type(row['bytes']) is int and 0<=row['bytes']<=4*1024**2 and meta['kind']=='blob' and meta['git_mode'] in ('100644','100755'),'regular selected mode extent');end=reply.index(b'\n',offset);oid,typ,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2
 ck(oid==meta['git_object'] and typ=='blob' and reply[offset-1:offset]==b'\n' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid,'actual Git blob body OID');ck(read(p)==b and sha(b)==row['sha256'] and len(b)==row['bytes'],'complete selected byte joins');mode=stat.S_IMODE(p.lstat().st_mode);ck(meta['git_mode']==('100755' if mode&0o111 else '100644'),'actual executable-mode Git join');joined.append(dict(row,git_mode=meta['git_mode'],git_object=oid,original_filesystem_mode=mode))
ck(offset==len(reply),'complete no trailingGitframe');selected=set(names)


SEL=P;selected_rows=joined;selected_commit=H;P=F/'financial-genuine-wrapper-root-recordfix-failed-scope-capture01-2026-10-04'
import gzip,io,tarfile,importlib.util
RP=F/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(RP));sp=importlib.util.spec_from_file_location('failed_archive_r4',RP/'recovery04.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
for n,pin in {'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():ck(sha(read(RP/n))==pin,'unchanged accepted primitive')
prior=F/'held-consumer-final-released-scope-capture-review01-2026-10-03/check01.py';defs=[n for n in ast.parse(read(prior)).body if isinstance(n,ast.FunctionDef) and n.name in ['decode','recode']];exec(compile(ast.Module(body=defs,type_ignores=[]),str(prior),'exec'))
capraw=read(P/'CAPTURE01.json');ck(sha(capraw)=='37c3f6b064b005398535c8b49636ef4e9190dd508d29200034c81823b699786c','actual complete failed capture');cap=json.loads(capraw);allman={};allbody={};arch=[]
for role in ['source','parent','outer']:
 mr=read(P/(role+'-manifest.json'));m=json.loads(mr);root=Path(cap['source_roots'][role]);raw=read(P/(role+'.tar.gz'));pin=cap['archives'][role];ck(sha(mr)==pin['manifest_sha256'] and sha(raw)==pin['sha256'] and len(raw)==pin['bytes'],'actual archive manifest pins '+role);ck(a.scan(root)==m,'fresh exact closed current tree '+role);bodies,frame=decode(raw,m);ck(recode(m,bodies)==raw,'whole canonical compressed reconstruction '+role)
 for r in m['members']:
  if r['kind']=='file':ck(bodies[r['path']]==a.read(root,r['path']),'every complete opaque current original body '+role)
 ck(len(m['members'])==cap['typed_members'][role] and sum(r['kind']=='file' for r in m['members'])==cap['regular_members'][role] and sum(r.get('bytes',0) for r in m['members'])==cap['logical_bytes'][role],'actual complete extent denominators '+role);allman[role]=m;allbody[role]=bodies;arch.append({'role':role,**pin,'members':len(m['members']),'regular':cap['regular_members'][role],'framing':frame})
S=Path(cap['source_roots']['source']);Par=Path(cap['source_roots']['parent']);Ext=Path(cap['source_roots']['outer']);identity=cap['identity'];H='649fb8a11089524aaef7843dffeeb90a3a55ca17';sb=allbody['source'];pb=allbody['parent'];eb=allbody['outer'];old=json.loads(read(F/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04/source-manifest.json'));new={r['path']:r for r in allman['source']['members']}
for r in old['members']:ck(new[r['path']]==r,'every original frozen986 Source member unchanged')
ck(len(new)==1011 and len(old['members'])==986,'exact Source25 typed appendages');source_delta=[r['path'] for r in allman['source']['members'] if r['path'] not in {x['path'] for x in old['members']}]
ck(git(['-C',str(S),'rev-parse','HEAD']).decode().strip()==H,'actual frozen SourceHEAD');tree=git(['-C',str(S),'ls-tree','-r','-z',H]);entries=[]
for item in tree.split(b'\0'):
 if item:meta,n=item.split(b'\t');mode,kind,oid=meta.decode().split();entries.append((n.decode(),mode,kind,oid))
ck(len(entries)==325,'complete325 tracked Source');reply=b''.join(git(['-C',str(S),'cat-file','--batch'],(''.join(r[3]+'\n' for r in entries[i:i+40])).encode()) for i in range(0,len(entries),40));offset=0
for name,mode,kind,oid in entries:
 end=reply.index(b'\n',offset);actualoid,actualkind,size=reply[offset:end].decode().split();size=int(size);b=reply[end+1:end+1+size];offset=end+size+2;ck(kind==actualkind=='blob' and actualoid==oid and b==sb[name] and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid and mode==('100755' if new[name]['mode']&0o111 else '100644'),'every committed Source body mode/OID/current archive join')
ck(offset==len(reply),'complete boundedGit framing');claimpath='research_runs/'+identity+'/claim.json';failedpath='research_runs/'+identity+'/failed.json';ck(sha(sb[claimpath])==cap['claim_sha256']=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128' and sha(sb[failedpath])==cap['failed_sha256']=='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','actual genuine claim and permanentFAILED exact bodies');claim=json.loads(sb[claimpath]);failed=json.loads(sb[failedpath]);ck(claim['source']==claim['design_source']==H and claim['effective_attempt_budget']==18 and failed['claim_sha256']==sha(sb[claimpath]) and failed['status']=='failed' and failed['output_sha256']=={} and failed['reason']=='ValueError: repeat run prohibited; use a separately justified registration','actual failed accounting no outputs');ck(len([n for n in sb if n.startswith('research_runs/') and n.endswith('/claim.json')])==1,'actual one spent genuine claim')
for n,pin in claim['experiment']['source_files'].items():ck(sha(sb[n])==pin,'all actual claim source pins')
ck(len(claim['experiment']['source_files'])==324 and len(claim['inputs'])==8,'exact324sources eight actualroles')
for role,row in claim['inputs'].items():ck(sha(sb[row['path']])==row['sha256'],'genuine current input opaque pin '+role)
closure=json.loads(sb['fixture_inputs/financial_wrapper_recordfix01/source_closure.json']);ck(len(closure['installed'])==194 and sum(n.startswith('tradingagents/') for n in closure['installed'])==149,'actual194implementation149package closure')
for n,pin in closure['installed'].items():ck(sha(sb[n])==pin,'all194 method bodies unchanged')
base='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity+'/';j=lambda n:json.loads(sb[base+n]);guard=j('guard/final.json');owner=j('owner.json');observer=j('observer.json');outer=json.loads(eb['ACTUAL_TERMINAL01.json']);pt=json.loads(pb['attempt/parent-terminal.json']);cleanup=json.loads(pb['attempt/owned-tree-cleanup.json']);captureterminal=json.loads(read(P/'ACTUAL_TERMINAL01.json'));captureintent=json.loads(read(P/'ACTUAL_INTENT01.json'))
ck(guard['child_exit_code']==1 and guard['cleanup_verified'] is True and guard['cleanup_stop_returncode']==0 and guard['peak_sampled_memory_current_bytes']==325218304,'original failed guard cleanup and sampled memory');ck(outer['actual_exit']==1 and outer['actual_session']==58508 and outer['actual_start_tool']=='b185ed' and outer['actual_completion_tool']=='ea4290' and outer['actual_guard']['memory_peak_bytes'] is None,'actual Root native exit and preserved null alias');ck(pt['actual_parent_exit'] is None and pt['actual_child_exit']==1 and pt['cleanup']['original_parent_exit']==1 and pt['outcome_semantics_accepted'] is False,'original Parent self-null preserved with additive child/root1');ck(b'325218304' in eb['MEMORY_FIELD_QUALIFICATION02.json'],'actual sampled memory qualification retained');ck(observer['financial_completion'] is False and observer['status']=='failed' and observer['terminal_sha256']==sha(sb[failedpath]) and observer['owner_sha256']==sha(sb[base+'owner.json']),'genuine observer/owner/failed chain')
for n,pin in observer['evidence_sha256'].items():ck(sha(sb[base+n])==pin,'original observer evidence exactbody')
ck(j('unsealed-journals.json')==[] and all(c['status']=='unavailable' for c in j('postmortem-cells.json')),'original unavailable dependent cells and empty journals');ck(b'repeat run prohibited' in sb[base+'guard/child.log'],'original actual worker fatal trace retained')
absent_outputs=['wrapper-native-cpu-readback.json','wrapper-summary.json','artifact-index.json','cell-ledger.json','fit-checkpoint']
# Complete captured namespace proves all registered output leaves absent; no checkpoint file exists anywhere in attempted output namespace.
for name in claim['experiment']['outputs']:ck(not any(n.startswith('research_runs/'+identity+'/outputs/') and n.endswith('/'+name) for n in sb),'registered output absent '+name)
ck(not any(n.startswith(base) and any(w in n.lower() for w in ['checkpoint','wrapper-summary','wrapper-native','fit-summary','fit-evidence']) for n in sb),'no wrapper native/fit/checkpoint bodies')
ck(cleanup['remaining_original_identities']==[] and pt['cleanup']['cgroup_absent'] and pt['cleanup']['joined_unit_stopped'],'original Parent drainage evidence');pids={outer['actual_parent_pid'],owner['supervisor_pid'],owner['monitor_pid'],guard['monitor_pid'],j('guard/child_exit.json')['workload_pid'],j('guard/cpu_ready.json')['pid'],captureintent['pid']};pids.update(int(n) for n in guard['cpu_thread_readback']);pids.update(r['pid'] for r in cleanup['owned_pid_start_records']);groups={r['pgrp'] for r in cleanup['owned_pid_start_records']}
for op,row in pt['cleanup']['actual_control_operations'].items():ck(row['exit_code']==0 and pb['attempt/'+op+'/stdout']==row['stdout'].encode() and pb['attempt/'+op+'/stderr']==row['stderr'].encode(),'actual controller operation and rawstreams '+op);pids.add(row['pid'])
for pid in sorted(pids):ck(not Path('/proc',str(pid)).exists(),'recorded original PID or TID currently absent')
for group in sorted(groups):
 try:os.killpg(group,0)
 except ProcessLookupError:pass
 else:raise AssertionError('recorded group remains')
ck(not Path(guard['cgroup']).exists(),'actual exact cgroup absent');ck(captureterminal['actual_exit']==0 and captureterminal['actual_session']==75520 and captureterminal['actual_start_tool']=='119d83' and captureterminal['actual_completion_tool']=='e28242' and captureterminal['capture_sha256']==sha(capraw),'actual original capture tool exit receipt');ck(captureterminal['actual_parent_pid']==captureintent['pid']==334390 and captureterminal['actual_parent_start_ticks']==captureintent['start_ticks']=='14967492','actual recorded capture parent identity');ck(len(cap['observed_free_bytes'])==6 and min(cap['observed_free_bytes'])>=10*1024**3,'all six actual recorded diskfloor samples')
for role,manifest in allman.items():ck(a.scan(Path(cap['source_roots'][role]))==manifest,'final stable current full tree '+role)
ck(sha(read(P/'capture01.py'))==json.loads(read(P/'CAPTURE_SOURCE01.json'))['script_sha256'],'actual capture source provenance');ck(sum(cap['typed_members'].values())==1049 and sum(cap['regular_members'].values())==763,'full1049typed763body scope');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
selected_by={r['path']:r for r in selected_rows};ck(len({r['git_object'] for r in selected_rows})==226,'exact226 immutable selected objects');covered=dict(selected_by)
for role,bodymap in allbody.items():
 root=Path(cap['source_roots'][role])
 for name,b in bodymap.items():
  actualpath=root/name
  if actualpath.is_relative_to(ROOT):covered[actualpath.relative_to(ROOT).as_posix()]={'sha256':sha(b),'bytes':len(b)}
complete_dirs=['financial-genuine-wrapper-recordfix-first-failure-review01-2026-10-04','financial-genuine-wrapper-recordfix-first-failure-capture-review01-2026-10-04','financial-genuine-wrapper-claimed-run-correction-preparation01-2026-10-04','financial-genuine-wrapper-claimed-run-correction-review01-2026-10-04','financial-genuine-wrapper-recordfix-final-union-actual-recovery-review01-2026-10-04']
closure=[];missing=[]
for dirname in complete_dirs:
 d=F/dirname
 for p in d.rglob('*'):
  st=p.lstat()
  if stat.S_ISREG(st.st_mode):ck(p.relative_to(ROOT).as_posix() in selected_by,'full declared selected directory member '+str(p.relative_to(d)))
  elif stat.S_ISLNK(st.st_mode):raise AssertionError('unexpected link in directly selected review')
  else:ck(stat.S_ISDIR(st.st_mode),'declared directory only')
 for p in sorted(d.glob('MANIFEST*.json')):
  doc=json.loads(read(p))
  for row in doc.get('members',doc.get('entries',[])):
   target=p.parent/row['path'];mode=row.get('mode');kind=row.get('kind',row.get('type'));st=target.lstat();ck(mode==stat.S_IMODE(st.st_mode),'every frozen review original mode')
   if kind=='file':
    relative=target.relative_to(ROOT).as_posix();actual=covered.get(relative)
    if actual is None:missing.append({'manifest':str(p),'member':row['path']});continue
    ck(stat.S_ISREG(st.st_mode) and actual['sha256']==row['sha256']==sha(read(target)) and actual['bytes']==row.get('bytes',row.get('size')),'every relevant selected review witness body exact');closure.append(relative)
   elif kind in ('directory','dir'):ck(stat.S_ISDIR(st.st_mode),'review typed directory')
   else:raise AssertionError('unexpected declared witness kind '+str(kind))
(O/'MANIFEST_CLOSURE_DIAGNOSTIC01.json').write_text(json.dumps({'missing':missing,'joined_count':len(closure)},sort_keys=True,indent=2)+'\n');ck(not missing,'complete relevant original review-body closure')
ck(sha(read(SEL/'recover01.py'))=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','unchanged accepted bounded firstfatal transport helper')
for n in ['fresh-recordfix-source325-01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json','INTENT01.json']:ck(not os.path.lexists(SEL/n),'fresh failed transport namespace absent '+n)
legacy=F/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04'
for n in ['ACTUAL_TERMINAL02.json','request.json','source-authentication.json','source-manifest.json','source.tar.gz','terminal.json']:ck((legacy/n).relative_to(ROOT).as_posix() in selected_by,'six required legacy supplement present')
ck(git(['rev-parse','HEAD']).decode().strip()==selected_commit,'Main immutable selected commit after checks');free=shutil.disk_usage(SEL).free;ck(free>=10*1024**3,'actual observed current disk floor')
out={'schema_version':1,'decision':'ACCEPTED_EXACT_FAILED_SCOPE_SELECTION_PENDING_ONE_ACTUAL_REMOTE','checks':len(checks),'selected_commit':selected_commit,'selection_sha256':sha(raw_selection),'selected_count':270,'logical_bytes':17965145,'unique_git_objects':226,'expected_git_operations':551,'capture_sha256':sha(capraw),'archives':arch,'source_commit':H,'source_typed':1011,'source_regular':730,'parent_typed':33,'parent_regular':28,'outer_typed':5,'outer_regular':5,'complete_selected_review_directories':complete_dirs,'review_body_manifest_joins':len(closure),'six_legacy_source_captures_are_supplemental_only':True,'genuine_failed_claims':1,'numerical_ceiling':18,'original_parent_self_exit':None,'actual_root_exit':1,'sampled_memory_current_bytes':325218304,'null_root_alias_preserved':True,'fresh_remote_namespaces_absent':True,'observed_free_bytes':free,'actual_remote_or_flat_recovery':False,'numerical_authority':False,'joined':selected_rows};(O/'SELECTION_READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='joined'},sort_keys=True))
