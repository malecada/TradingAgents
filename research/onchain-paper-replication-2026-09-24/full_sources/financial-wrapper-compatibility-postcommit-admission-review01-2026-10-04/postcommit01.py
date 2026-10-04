from pathlib import Path
import hashlib,json,os,stat,subprocess,time
D=Path(__file__).resolve().parent;F=D.parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');BEFORE='7b056a574e3e7b3c7ba209a39ee6a615e649d60c';HEAD='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41';checks=[];reads={};begin=time.monotonic()
def h(b):return hashlib.sha256(b).hexdigest()
def sig(s):return [s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_uid,s.st_gid]
def ok(v,n):assert v,n;checks.append(n)
def read(p,pin=None):
 p=Path(p);s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded canonical regular');b=p.read_bytes();ok(sig(p.lstat())==sig(s) and len(b)==s.st_size,'sampled current');ok(pin is None or h(b)==pin,'exact body');reads[str(p)]={'sha256':h(b),'bytes':len(b),'signature':sig(s)};ok(time.monotonic()-begin<60,'bounded review');return b
def J(p,pin=None):return json.loads(read(p,pin))
def git(*args):
 r=subprocess.run(['git','--no-replace-objects',*args],cwd=CAP,env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_OPTIONAL_LOCKS='0'),capture_output=True,timeout=10);ok(r.returncode==0 and len(r.stdout)<=4194304,'bounded local Git');return r.stdout
A=F/'financial-wrapper-compatibility-gate-adoption-outcome01-2026-10-04';m=J(A/'MACHINE01.json','233fd22e21a7fc344caa350141780f1bdbf5cbc3234da9711e63056ba53e2b0a');seal=J(A/'MANIFEST01.json','279c8a016d7bcee6adda62c8f41faaeb9606ac02f769445a7fe0281559679ae7');q=J(A/'READBACK01.json',m['readback_sha256']);scope=m['allowed_new_file_pins']
for x in seal['members']:
 if x['kind']=='file':ok(len(read(A/x['path'],x['sha256']))==x['bytes'],'complete prior outcome seal')
oldfiles={Path(p).relative_to(CAP).as_posix():x for p,x in q['checked_files'].items() if Path(p).is_relative_to(CAP)}
for n,x in oldfiles.items():read(CAP/n,x['sha256'])
whole={}
for root,ds,fs in os.walk(CAP,followlinks=False):
 if Path(root)==CAP:ds.remove('.git')
 for n in ds+fs:
  p=Path(root)/n;r=p.relative_to(CAP).as_posix();s=p.lstat();ok(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode),'whole ordinary types');whole[r]=sig(s)
ok(whole==q['current605_signatures'] and len(whole)==605,'all605 exact durable prior outcome signatures unchanged')
ok(git('rev-parse','HEAD').decode().strip()==HEAD,'actual expected current commit');ok(git('rev-parse',HEAD+'^').decode().strip()==BEFORE,'actual direct parent')
parents=git('rev-list','--parents','-n','1',HEAD).decode().split();ok(parents==[HEAD,BEFORE],'single direct ancestor')
diff=git('diff-tree','--no-commit-id','--name-status','-r',HEAD).decode().splitlines();ok(set(diff)=={'A\t'+n for n in scope} and len(diff)==15,'exact15 additions only')
tracked=git('ls-files','-z').decode().split('\0')[:-1];ok(len(tracked)==len(set(tracked))==355,'actual355 tracked');ok(not git('status','--porcelain','--untracked-files=no'),'clean tracked and index')
for n,pin in scope.items():ok(h(git('show',HEAD+':'+n))==pin==h(read(CAP/n)),'new committed literal body')
oldindex=J(F/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04/snapshot/SOURCE_GIT394_METADATA01.json');old={x['oid']:x for x in oldindex['objects']};oids=git('rev-list','--objects','--all','--no-object-names').decode().splitlines();ok(len(oids)==len(set(oids)) and set(old)<=set(oids),'original394 reachable retained');objects=[]
for oid in sorted(oids):
 typ=git('cat-file','-t',oid).decode().strip();b=git('cat-file',typ,oid);ok(hashlib.sha1((typ+' '+str(len(b))+'\0').encode()+b).hexdigest()==oid,'actual logical Git object id')
 if oid in old:ok(typ==old[oid]['type'] and len(b)==old[oid]['bytes'] and h(b)==old[oid]['sha256'],'original Git exact content')
 objects.append({'oid':oid,'type':typ,'bytes':len(b),'sha256':h(b),'prior394':oid in old})
N='fixture_inputs/financial_wrapper_compatibility01';gate=J(CAP/N/'gates.json',scope[N+'/gates.json']);ident='financial-wrapper-classification-eager-complete100-compatibility-20261004-01';exp=gate['experiments'][ident]
ok(len(exp['source_files'])==354 and len(exp['inputs'])==11 and exp['parent'] is None,'actual354pins11rolesnullparent');ok(set(exp['source_files'])==set(tracked)-{N+'/gates.json'},'all committed paths except newgate pinned')
for n,pin in exp['source_files'].items():ok(h(read(CAP/n))==pin==h(git('show',HEAD+':'+n)),'committed and live source exact')
oldgate=J(CAP/'fixture_inputs/financial_wrapper_claimedrun01/gates.json','752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c');trim=json.loads(json.dumps(gate));del trim['experiments'][ident];ok(trim==oldgate and len(oldgate['experiments'])==12,'all12 historical definitions exact')
ok(set(p.name for p in (CAP/'research_runs').iterdir())=={x['identity'] for x in q['actual_claims']}|{'.lock'},'still only3 historical claims')
for row in q['actual_claims']:
 p=CAP/'research_runs'/row['identity'];read(p/'claim.json',row['claim_sha256']);read(p/'failed.json',row['failed_sha256']);ok(not (p/'complete.json').exists(),'failed remains failed')
O=F/'financial-wrapper-compatibility-root-admission01-2026-10-04';receipt=J(O/'ACTUAL_ADMISSION01.json','dcbef49b6fd6c89b3c0eb022113ff51dd987edb84d1b5ce7ddc8cb4b30bfbb65');stdout=J(O/'stdout',receipt['stdout_sha256']);err=read(O/'stderr',receipt['stderr_sha256']);ok(not err and receipt['actual_child_exit']==0 and receipt['source']==HEAD and receipt['cwd']==str(CAP),'actual Root CLI exit source');ok(stdout=={'experiment':ident,'stage':'development','ready':True,'status':'metadata_admitted','empirical_inputs_opened':False,'run_started':False},'actual CLI result exact')
c=J(F/'heartbeat-root-checkpoint10-2026-10-04/CAP_COMPATIBILITY_GATE_COMMIT01.json');ok(c['current_source_design']==HEAD and c['source_before']==BEFORE and set(c['scope'])==set(scope) and c['actual_new_claim'] is False,'Root commit receipt exact')
i=J(D/'INTEGRATION02.json');ok(i['status']=='GENUINE_READ_ONLY_JOB_ADMITTED' and i['ready'] and i['source']==HEAD and i['inputs']==11 and i['source_pins']==354 and i['claim_absent'] and i['numerical_imports']==[],'independent genuine job integration');ok(len(i['runtime_records'])==251 and i['package_bodies']==150 and i['required_sources']==195,'251runtime195source150package')
for v in i['module_origins'].values():read(v['path'],v['sha256'])
for p,x in list(reads.items()):ok(h(read(p))==x['sha256'],'final all read body rejoin')
for n,s in whole.items():ok(sig((CAP/n).lstat())==s,'final605 signature join')
ok(not (CAP/'research_runs'/ident).exists() and git('rev-parse','HEAD').decode().strip()==HEAD,'no new claim final HEAD')
(D/'READBACK01.json').write_text(json.dumps({'decision':'ACTUAL_COMMITTED_SOURCE_AND_READ_ONLY_ADMISSION_AUTHENTICATED','checks':len(checks),'source':HEAD,'direct_parent':BEFORE,'diff':diff,'whole605':whole,'git_objects':objects,'original394_retained':True,'new_git_objects':len(objects)-394,'tracked':355,'source_pins':354,'roles':11,'actual_highest_claimed_allowance':19,'failed_spent_attempts':3,'prospective_amendment':20,'reads':reads,'root_cli_receipt':receipt,'runtime_qualification':i['runtime_qualification'],'numerical_authority':False,'claim_authority':False},indent=2)+'\n');print(len(checks),len(objects),len(reads))
