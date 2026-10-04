import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;A=F/'financial-genuine-wrapper-claimedrun-parent-preparation01-2026-10-04';sys.path.insert(0,str(A));import parent01 as P
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):assert v,m;checks.append(m)
def rd(p):return P.R.read(p.parent,p.name)
def refuse(f,label):
 try:f()
 except (ValueError,TypeError,KeyError,FileNotFoundError) as e:checks.append(label);return type(e).__name__+': '+str(e)
 raise AssertionError('unexpected acceptance '+label)
ck(sha(rd(A/'parent01.py'))=='5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda','candidate exact body');ck(sha(rd(A/'MANIFEST01.json'))=='9c29f83031acde0e8c4794ca162756b481416d34711bd3770e7327ca4d2436cb','author frozen manifest')
m=json.loads(rd(A/'MANIFEST01.json'));ck({p.name for p in A.iterdir()}=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'full candidate membership')
for r in m['members']:
 p=A/r['path'];s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==int(r['mode'],8),'original author type/mode');b=rd(p);ck(len(b)==r['bytes'] and sha(b)==r['sha256'],'each frozen body')
s=rd(A/'parent01.py').decode();old=rd(A/'original-parent01.py').decode();back=s
for e in reversed(json.loads(rd(A/'INVERSE01.json'))['edits']):ck(back.count(e['new'])==1,'inverse unique');back=back.replace(e['new'],e['old'])
ck(back==old and ast.dump(ast.parse(back))==ast.dump(ast.parse(old)),'complete body and AST inverse');q=json.loads(rd(A/'REQUEST_TEMPLATE01.json'));ck(q['final_review'] is None and q['proofs']['full_recovery'] is None and q['proofs']['independent_source_input_runtime'] is None,'pending genuine proofs remain null');refusals=[refuse(lambda:P.validate_release(q),'genuine draft refuses')]
for key in q:
 bad=copy.deepcopy(q);del bad[key];refusals.append(refuse(lambda:P.validate_release(bad),'missing exact field '+key))
for k in ['parent_root','identity','source','design_source','registration','registration_sha256','source_files','input_hashes','runtime_mapping','caller_sha256','helper_hashes','proofs','final_review','expected_phase']:
 bad=copy.deepcopy(q);bad['status']='RELEASED_ONE_USE_FINANCIAL_PARENT';bad[k]=None;refusals.append(refuse(lambda:P.validate_release(bad),'null field refuses '+k))
# No acceptance object is synthesized; even released-status metadata refuses the actual missing review.
bad=copy.deepcopy(q);bad['status']='RELEASED_ONE_USE_FINANCIAL_PARENT';refusals.append(refuse(lambda:P.validate_release(bad),'status cannot supply missing genuine release'))
ck(not os.path.lexists(P.PARENT) and not os.path.lexists(P.CAP/'research_runs'/P.IDENTITY),'actual future namespaces absent')
for n,pin in q['helper_hashes'].items():ck(sha(rd(A/n))==pin,'all six exact helper bodies')
for name in ['child_cleanup','launch','stream_hash','memory','reference','contract','main']:
 fn=lambda txt:ast.dump(next(n for n in ast.parse(txt).body if isinstance(n,ast.FunctionDef) and n.name==name));ck(fn(s)==fn(old),'unchanged full '+name)
reg=json.loads(rd(P.CAP/q['registration']));exp=reg['experiments'][P.IDENTITY];ck(sha(rd(P.CAP/q['registration']))==q['registration_sha256'] and exp['source_files']==q['source_files'],'actual gate/source map');ck(len(q['source_files'])==338 and len(reg['experiments'])==12,'exact current cardinality')
for n,pin in q['source_files'].items():ck(sha(rd(P.CAP/n))==pin,'all actual338 source bodies')
for role,r in exp['inputs'].items():ck(sha(rd(P.CAP/r['path']))==r['sha256']==q['input_hashes'][role],'eight actual role pins')
for filename,source in [('original-job.py','tradingagents/research/onchain_replication/job.py'),('original-resources.py','tradingagents/research/onchain_replication/resources.py'),('original-admission.py','tradingagents/research/admission.py')]:ck(rd(A/filename)==rd(P.CAP/source),'actual original API source '+source)
ck(P.sha(P.reference(q['proofs']['cumulative']))=='3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e','real cumulative review body');ck(s.index('admitted,admitted_job=job._admitted(args)')<s.index("command=job._command(args,'launch')"),'genuine admission before dispatch construction')
# Genuine pure command constructor only. No Research module import or admission.
node=next(n for n in ast.parse(rd(A/'original-job.py')).body if isinstance(n,ast.FunctionDef) and n.name=='_command');ns={'sys':sys,'Path':Path,'MODULE':'tradingagents.research.onchain_replication.job'};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual command>','exec'),ns);args=P.SimpleNamespace(root=str(P.CAP),registration=q['registration'],experiment=P.IDENTITY,source=q['source']);cmd=ns['_command'](args,'launch');ck(cmd[cmd.index('--root')+1]==str(P.CAP) and cmd[cmd.index('--source')+1]==q['source'],'real launch command exact source/root')
# Real own opaque IO controls, with exact installed cleanup reducer and actual FDs.
T=O/'tiny';T.mkdir(mode=0o700);body=T/'body';body.write_bytes(b'opaque\x00body');ck(P.stream_hash(body,11)==sha(body.read_bytes()),'real bounded stream hash');refuse(lambda:P.stream_hash(body,2),'real extent refusal');link=T/'link';link.symlink_to('body');refuse(lambda:P.stream_hash(link,20),'real lexical link refusal')
original_read=P.os.read;original_close=P.os.close
for i,primary in enumerate([MemoryError('actual memory sentinel'),SystemExit(37),KeyboardInterrupt('actual interrupt sentinel'),ValueError('ordinary sentinel')]):
 captured=[];closed=[]
 def failread(fd,n):captured.append(fd);raise primary
 def failclose(fd):original_close(fd);closed.append(fd);raise OSError('injected error after genuine close')
 P.os.read=failread;P.os.close=failclose
 try:
  try:P.stream_hash(body,20)
  except BaseException as got:
   if isinstance(primary,ValueError):ck(isinstance(got,P.R.CleanupFailure) if hasattr(P.R,'CleanupFailure') else type(got).__name__=='CleanupFailure','ordinary close uncertainty stops')
   else:ck(got is primary,'original first fatal identity preserved')
  else:raise AssertionError('stream control accepted')
 finally:P.os.read=original_read;P.os.close=original_close
 ck(len(captured)==len(closed)==1 and captured==closed,'owned FD closed exactly once')
 try:os.fstat(closed[0])
 except OSError:checks.append('actual descriptor absent')
 else:raise AssertionError('descriptor leaked')
# Real tiny subprocesses exercise unchanged supervisor; no Source/Parent subprocess or numeric job.
processes=[]
for label,fatal in [('normal',None),('fatal',MemoryError('spawn callback actual firstfatal'))]:
 d=T/label;d.mkdir(mode=0o700)
 def spawned(p):
  processes.append(p)
  if fatal is not None:raise fatal
 try:result=P.supervise(['/bin/true'] if fatal is None else ['/bin/sleep','10'],O,{'PATH':'/usr/bin:/bin'},d,2,on_spawn=spawned)
 except BaseException as got:ck(got is fatal and fatal is not None,'real spawned child firstfatal preserved')
 else:ck(fatal is None and result['exit_code']==0,'real benign child exit0')
 ck(processes[-1].poll() is not None,'actual tiny child reaped');cleanup=json.loads(rd(d/'owned-tree-cleanup.json'));ck(cleanup['remaining_original_identities']==[],'actual owned tiny descendant drainage')
try:os.killpg(processes[-1].pid,0)
except ProcessLookupError:checks.append('actual tiny process group absent')
else:raise AssertionError('tiny group remains')
ck(not os.path.lexists(P.PARENT) and not os.path.lexists(P.CAP/'research_runs'/P.IDENTITY),'no actual reservation or claim created');ck(not any(n.split('.')[0] in {'tradingagents','numpy','torch','pandas','scipy'} for n in sys.modules),'no research or numerical imports')
x={'schema_version':1,'decision':'ACCEPTED_CLAIMEDRUN_PARENT_SOURCE_ONLY_PENDING_ACTUAL_PROOFS_AND_EXACT_RELEASE','caller_sha256':sha(rd(A/'parent01.py')),'author_manifest_sha256':sha(rd(A/'MANIFEST01.json')),'source':q['source'],'registration_sha256':q['registration_sha256'],'checks':len(checks),'tracked':339,'source_pins':338,'input_roles':8,'base_attempt_budget':18,'prior_attempts':0,'prospective_required_effective_budget':19,'actual_admission_calls':0,'claims_created':0,'actual_parent_installed':False,'genuine_final_release_created':False,'full_recovery_proof':None,'source_input_runtime_proof':None,'refusals':refusals,'tiny_real_child_pids':[p.pid for p in processes],'tiny_processes_reaped':True,'qualification':'Exact source preparation only. No actual runtime equality, full final scope recovery, release, fresh capacity or future native eligibility is established by these controls.'};(O/'READBACK01.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');print(json.dumps(x,sort_keys=True))
