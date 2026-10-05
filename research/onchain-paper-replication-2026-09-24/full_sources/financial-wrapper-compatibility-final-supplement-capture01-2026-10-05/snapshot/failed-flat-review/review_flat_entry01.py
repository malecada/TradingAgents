"""Read-only exact actual baseline recovery checker. No helper entry or network.
Needs genuine Root actual receipt refs supplied after the operations; absence
refuses before any verdict. Outputs only in this new review directory.
"""
from pathlib import Path
import argparse,hashlib,json,os,stat,time,io,gzip,tarfile,sys,subprocess
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B.parents[2];D=B/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05';CAP=ROOT.parent/'onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source';PARENT=CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01'
MAIN='d15e720ff6143350052b90c563ead1f950dd8be3';SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41';FILE=4194304;START=time.monotonic();cache={};pins={};treepins={};count=0;total=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,msg):
 global count
 if not v:raise ValueError(msg)
 count+=1
sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p,pin=None):
 global total
 p=Path(p);s=p.lstat();ok(time.monotonic()-START<180 and p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE,'bounded stable regular')
 if p not in cache:
  with p.open('rb') as f:b=f.read(FILE+1)
  ok(len(b)==s.st_size and sig(s)==sig(p.lstat()),'physical read stable');cache[p]=b;pins[p]=sig(s);total+=len(b);ok(total<=64*1024**2,'64MiB total audit bytes')
 else:ok(pins[p]==sig(s),'retained exact signature');b=cache[p]
 ok(pin is None or sha(b)==pin,'exact real body hash');return b
def j(p,pin=None):return json.loads(read(p,pin))
def ref(v):
 ok(type(v)is dict and set(v)=={'path','sha256'},'literal actual evidence ref');return read(Path(v['path']),v['sha256'])
def census(root,exclude=()):
 out={};todo=[root]
 while todo:
  p=todo.pop()
  with os.scandir(p) as it:
   for e in it:
    if p==root and e.name in exclude:continue
    s=e.stat(follow_symlinks=False);ok(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode),'whole ordinary population');n=str(Path(e.path).relative_to(root));out[n]=sig(s)
    if stat.S_ISDIR(s.st_mode):todo.append(Path(e.path))
 ok(len(out)<32768,'finite population');prior=treepins.get(root);ok(prior is None or prior==(tuple(exclude),out),'unchanged whole namespace');treepins[root]=(tuple(exclude),out);return out

import ast
CALLER='13548eb3206febfb13e1dff0d5f63159176fb8ba1dae819f8de89b9a499cb8b7';CONTRACT='caf3f63b0b665eb241cd76c27dbd07e30ea6cfdf1d791abc06b2156080ae31b6'
c=j(D/'FLAT_CONTRACT01.json',CONTRACT);old=j(D/'REMOTE_CONTRACT01.json','ffe5b475e31ad63d04ef6416b462eac093fe9db4315e83c743a8324d723db224');q=j(D/'ROOT_REQUEST_FLAT01.json','ca196899877c4210c5900ce55ba5dc491551e8bf58a341b3752e6135fbc50c1a');draft=j(D/'ROOT_REQUEST_FLAT_DRAFT01.json','46722ede3d775754553a2c17a85d267111e31562e1ec516c82a39e8a85f5f3b4');inner=read(H/'INNER_FLAT_RELEASE01.json','ca25c4dcfe07e9c8c55c7b70e213d5b68855cf6d45e4f3c12ec3aa9e1c457160');previous=j(H/'REMOTE_READBACK01.json','d697507dbda8e7bb4411dc5d70e74874a3c30540ea2a91fb853eaaff18648aca')
ok({k:v for k,v in q.items() if k!='actual_restore_release'}=={k:v for k,v in draft.items() if k!='actual_restore_release'} and draft['actual_restore_release'] is None,'only genuine new inner release ref')
r=q['actual_restore_release'];ok(ROOT/r['path']==D/'INNER_FLAT_RELEASE01.json' and read(ROOT/r['path'],r['sha256'])==inner and len(inner)==r['bytes'],'literal installed genuine inner release')
changes={'phase','request','remote_receipt','remote_root_exit','selected_mode_profile','flat_release','fresh_names'};ok({k:v for k,v in c.items() if k not in changes}=={k:v for k,v in old.items() if k not in changes},'exact declared outer FLAT delta only')
body=read(D/'caller02.py',CALLER);tree=ast.parse(body);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='contract');ns={'D':D,'IOPIN':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'};exec(compile(ast.Module(body=[function],type_ignores=[]),str(D/'caller02.py'),'exec'),ns);ok(ns['contract'](c)=='FLAT','actual source contract predicate')
for n,h in c['helpers'].items():read(D/n,h)
for field in ['selection','request','remote_receipt','remote_root_exit','selected_mode_profile','flat_release']:
 r=c[field];ok(Path(r['path']).name==r['path'],'bounded local exact reference');read(D/r['path'],r['sha256'])
ok(c['remote_receipt']['sha256']==previous['actual_remote_sha256'] and c['remote_root_exit']['sha256']==previous['original_root_exit_sha256'] and c['selected_mode_profile']['sha256']==previous['profile_sha256'],'actual independently reviewed remote bindings')
read(D/'ROOT_TOOL_EXIT_REMOTE01.json',previous['actual_root_tool_exit_sha256'])
sys.path.insert(0,str(D/'utilities'));sys.path.insert(0,str(D));import binding01 as BINDER;import recovery_pax01 as R;import watch01 as W
ok(json.loads(inner)=={'schema_version':1,'decision':'ACCEPTED_EXACT_BASELINE_BUNDLE_FLAT','contract_sha256':sha(R.encode({k:v for k,v in q.items() if k!='actual_restore_release'})),'remote_sha256':c['remote_receipt']['sha256'],'source_sha256':c['helpers']['restore_bundle01.py']},'exact actual inner contract')
BINDER.validate(q);ok(R.scan(D/'selected')==j(D/'SELECTED_MODE_PROFILE01.json')['full_manifest'],'retained all actual selected bytes/modes')
fresh=['BUNDLE_FLAT_INTENT01.json','BUNDLE_FLAT_RECOVERY01.json','BUNDLE_FLAT_FAILED01.json']+['flat-'+b['name'] for b in q['bundles']];ok(c['fresh_names']==fresh,'exact six future flat namespaces')
for n in fresh+['ROOT_BASELINE_FLAT01'+s for s in ('_INTENT.json','_SPAWN.json','.stdout','.stderr','_EXIT.json')]:ok(not os.path.lexists(D/n),'fresh fixed outputs')
for pid in previous['recorded_pids_currently_absent']:ok(not Path('/proc',str(pid)).exists(),'prior recorded processes remain absent')
now=W.census(D);v=os.statvfs(D);free=v.f_bavail*v.f_frsize;ok(free>=10*1024**3,'current floor')
for p,s in pins.items():ok(sig(p.lstat())==s,'final actual currentness')
release={'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_BASELINE_FLAT','contract_sha256':CONTRACT,'caller_sha256':CALLER,'numerical_authority':False}
result={'schema_version':1,'decision':release['decision'],'reviewer':'combined_worker_review','contract_sha256':CONTRACT,'caller_sha256':CALLER,'request_sha256':c['request']['sha256'],'remote_receipt_sha256':c['remote_receipt']['sha256'],'inner_release_sha256':sha(inner),'outer_release_sha256':sha(R.encode(release)),'checks':count,'files_read':len(cache),'bytes_read':total,'current_storage':now,'current_free_bytes':free,'actual_flat_recovery':None,'numerical_authority':False,'fresh_fixed_outputs':fresh}
for n,obj in [('OUTER_FLAT_RELEASE01.json',release),('FLAT_ENTRY_READBACK01.json',result)]:
 with (H/n).open('xb') as f:f.write(R.encode(obj))
print(json.dumps(result))
