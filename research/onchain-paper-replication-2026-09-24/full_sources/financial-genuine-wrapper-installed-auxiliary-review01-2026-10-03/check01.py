import hashlib,json,os,stat,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;MAIN=Path.cwd();A=F/'financial-genuine-wrapper-root-auxiliary-adoption01-2026-10-03';G=F/'financial-genuine-wrapper-auxiliary-preparation01-2026-10-03/generated02';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');H='44bf99d199acae5a043cf5b472a53e2fcf4caf1b';BASE='390c82a9958e135c24bcca80f3a636313ca27932';checks=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,m):
 assert v,m
 checks.append(m)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2 and p.resolve()==p,'bounded immutable file');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);parts=[];total=0
 try:
  ck(os.fstat(fd)==s,'opened identity')
  while True:
   b=os.read(fd,65536)
   if not b:break
   total+=len(b);ck(total<=4*1024**2,'file extent');parts.append(b)
  ck(total==s.st_size and os.fstat(fd)==s and p.lstat()==s,'stable body');return b''.join(parts)
 finally:os.close(fd)
def doc(p):return json.loads(read(p))
def git(args,data=None):
 env={'PATH':'/usr/bin:/bin','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_REPLACE_OBJECTS':'1','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0'};r=subprocess.run(['git','--no-replace-objects','-c','protocol.allow=never','-C',str(S),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,env=env);ck(r.returncode==0 and len(r.stdout)<=8*1024**2 and len(r.stderr)<=65536,'bounded read-only Git '+args[0]);return r.stdout
ad=doc(A/'ADOPTION01.json');failure=doc(A/'FAILED_PREPARATION01.json');prior=doc(F/'financial-genuine-wrapper-root-source-review01-2026-10-03/READBACK01.json');ck(git(['rev-parse','HEAD']).decode().strip()==ad['actual_new_commit']==H and ad['baseline_source_commit']==prior['source_commit']==BASE,'actual current andbaseline joins');commit=git(['cat-file','-p',H]);parents=[line.split()[1].decode() for line in commit.splitlines() if line.startswith(b'parent ')];ck(parents==[BASE],'direct original390 parent');git(['merge-base','--is-ancestor',BASE,H]);ck(all(not os.path.lexists(S/n) for n in ['.git/objects/info/alternates','.git/info/grafts','.git/refs/replace']),'no foreignGit roots')
def tree(rev):
 result={}
 for item in git(['ls-tree','-r','-z',rev]).split(b'\0'):
  if not item:continue
  meta,name=item.split(b'\t');mode,typ,oid=meta.decode().split();ck(typ=='blob' and mode in ('100644','100755'),'regular committedsource');result[name.decode()]={'git_mode':mode,'oid':oid}
 return result
old=tree(BASE);current=tree(H);base={r['path']:r for r in prior['joined']};aux={r['path']:r for r in ad['rows']};ck(len(base)==len(old)==194 and set(base)==set(old) and all(current.get(n)==old[n] for n in old),'all194 unchanged committedblob/mode');ck(len(aux)==48 and set(aux).isdisjoint(base) and set(current)==set(base)|set(aux) and len(current)==242,'exact242 union');ck({Path(r['origin']).name for r in aux.values()}=={p.name for p in G.iterdir()},'all48 accepted generated bodies adopted');actual=set()
for root,ds,fs in os.walk(S,followlinks=False):
 if Path(root)==S:ds.remove('.git')
 for n in ds:ck(stat.S_ISDIR((Path(root)/n).lstat().st_mode),'no symlink directory')
 for n in fs:actual.add(str((Path(root)/n).relative_to(S)))
ck(actual==set(current),'complete live242 no untracked files');ck(len([n for n in actual if n.startswith('tradingagents/')])==149 and 'tradingagents/research/onchain_replication/held_score_consumer.py' not in actual,'no foreignpackage149')
bodyreply=git(['cat-file','--batch'],(''.join(current[n]['oid']+'\n' for n in sorted(current))).encode());offset=0;joined=[]
for n in sorted(current):
 end=bodyreply.index(b'\n',offset);oid,typ,size=bodyreply[offset:end].decode().split();size=int(size);b=bodyreply[end+1:end+1+size];offset=end+size+2;ck(typ=='blob' and oid==current[n]['oid'] and bodyreply[offset-1:offset]==b'\n','exact blobframing');ck(hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==oid,'actualGitOID recomputed');live=read(S/n);row=(base if n in base else aux)[n];ck(live==b and sha(b)==row['sha256'] and len(b)==row['bytes'] and stat.S_IMODE((S/n).lstat().st_mode)==row['mode'],'actual body/mode matches acceptedrow');ck(current[n]['git_mode']==('100755' if row['mode']&0o111 else '100644'),'Gitmode joins')
 if n in aux:ck(read(MAIN/row['origin'])==b and (MAIN/row['origin']).parent==G,'exact48accepted auxiliary origins')
 joined.append({'path':n,'role':'implementation' if n in base else 'installed-unadmitted-draft-auxiliary','bytes':len(b),'sha256':sha(b),'mode':row['mode'],**current[n]})
ck(offset==len(bodyreply),'no trailingGitbytes');D=S/'fixture_inputs/financial_wrapper_draft01';draft=doc(D/'DRAFT01.json');ck(sha(read(D/'DRAFT01.json'))=='34438a5011ca7dac6ddf1890aa9d4d57b76d1560d7dc32a351343ba62897a7a1','accepted draft unchanged');mapping=doc(D/'runtime_mapping.json');runtime=doc(D/'RUNTIME_READBACK01.json');env=doc(D/'environment.DRAFT.json');closure=doc(D/'source_closure.json')
ck(set(closure['installed'])==set(base) and len(closure['installed'])==194,'source closure remains recipe194');ck(draft['source_commit_observed']==BASE and runtime['financial_root_lock_installed'] is False,'old prepared metadata retained honestly');ck(all(env[k] is None for k in ['torch_version','cuda_build','cuda_available']),'liveTorch unresolved');ck(draft['future_admitted_source_total'] is None and all(v is None for v in draft['future'].values()),'future actualrelease null')
for n in ['uv.lock','pyproject.toml','.python-version']:ck(read(S/n)==read(MAIN/n)==read(G/('proposed-'+n)),'actualadopted metadata '+n)
ck(sha(read(S/'uv.lock'))==mapping['lock_sha256']=='f7a1829c0ae554fb00923eb07c3c5e5370c1eadb52698ea657446c64d6c83b9a','actualrootlock nowmatches originalruntime')
for i,slot in enumerate(draft['slots'],1):
 ck(slot['admitted'] is False and slot['actual_outcome'] is None and len(slot['inputs'])==8,'all18unadmitted')
 for role,ref in slot['inputs'].items():
  name=Path(ref['prepared_path']).name;ck(ref['path'] is None and ref['dataset'] is None and sha(read(D/name))==ref['sha256'],'144actual installed inputbody joins')
 plan=doc(D/f'plan-{i:02d}.DRAFT.json');ck(all(plan[k] is None for k in ['cell_id','experiment','namespace']),'null actualidentity/cell/namespace')
ck(len(draft['slots'])==18 and draft['paper_financial_fit_credit']==0,'18slots zero papercredit');ck(all(not (S/n).exists() for n in ['research_runs','research_artifacts','fixture_outer','held-fixture-registration01.json']),'no actualRun/output/heldregistration namespaces');ck(failure['actual_count']==48 and failure['incorrect_expected_count']==50 and failure['failure_after_48_exclusive_copies_before_git_add_or_commit'] is True and failure['all_copied_bytes_preserved_verified_no_recopy'] is True,'original failedcount assertion retained');ck(git(['status','--porcelain','--untracked-files=all'])==b'' and git(['rev-parse','HEAD']).decode().strip()==H,'unchanged clean finalHEAD');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'decision':'ACCEPTED_ACTUAL_INSTALLED_DRAFT_AUXILIARY_ONLY','checks':len(checks),'actual_current_commit':H,'actual_baseline_parent':BASE,'implementation_sources':194,'package_sources':149,'other_implementation_sources':45,'installed_draft_auxiliary':48,'full_tracked_and_live_scope':242,'logical_bytes':sum(r['bytes'] for r in joined),'actual_uv_lock_present':True,'actual_live_torch_environment':None,'registration_or_budget_approved':False,'phase_claims':0,'adoption_receipt_sha256':sha(read(A/'ADOPTION01.json')),'retained_failed_preparation_sha256':sha(read(A/'FAILED_PREPARATION01.json')),'joined':joined};(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='joined'},indent=2))
