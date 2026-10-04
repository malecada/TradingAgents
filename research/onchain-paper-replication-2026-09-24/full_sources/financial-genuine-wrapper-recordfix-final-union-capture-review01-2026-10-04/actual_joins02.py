import hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE/'financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04';PRIM=BASE/'held-consumer-final-recovery-preparation04-2026-10-03'
sys.path.insert(0,str(PRIM));spec=importlib.util.spec_from_file_location('r4_final',PRIM/'recovery04.py');r4=importlib.util.module_from_spec(spec);spec.loader.exec_module(r4)
checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
terminal=json.loads((ROOT/'ACTUAL_TERMINAL01.json').read_bytes());intent=json.loads((ROOT/'ACTUAL_INTENT01.json').read_bytes())
for name,pin in terminal['files'].items():
 b=(ROOT/name).read_bytes();check(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'actual terminal body '+name)
check(terminal['actual_exit']==0 and terminal['actual_start_tool']=='42e314' and terminal['actual_completion_tool']=='c071a7' and terminal['actual_session']==23613,'Root actual tool/exit receipt')
check(terminal['actual_parent_pid']==intent['pid']==305468 and terminal['actual_parent_start_ticks']==intent['start_ticks'],'original PID/start ticks join')
check(not Path('/proc/'+str(intent['pid'])).exists(),'actual original capture PID currently absent')
check(terminal['actual_parent_absent'] is True and terminal['genuine_native_or_numerical_started'] is False,'terminal status boundaries')
check(sha((ROOT/'capture03.py').read_bytes())==terminal['capture_source_sha256']==intent['source_sha256'],'actual source join')
check(sha((HERE/'MANIFEST01.json').read_bytes())==terminal['source_review_manifest_sha256']==intent['source_review_manifest_sha256'],'source preflight review join')
for n in ('ACTUAL_TERMINAL01.json','ACTUAL_INTENT01.json','ACTUAL_CAPTURE01.out','ACTUAL_CAPTURE01.err'):
 with (HERE/('ROOT_'+n)).open('xb') as f:f.write((ROOT/n).read_bytes())
manifest=json.loads((ROOT/'union-manifest.json').read_bytes());raw=(ROOT/'union.tar.gz').read_bytes();framed=list(r4.framed_members(raw));check(len(framed)==len(manifest['members']),'raw R4 complete framing')
for (name,t,b),r in zip(framed,manifest['members']):
 check(name==r['path'] and t.mode==r['mode'],'R4 raw header '+name)
 if r['kind']=='file':check(len(b)==r['bytes'] and sha(b)==r['sha256'],'R4 raw body '+name)
 else:check(t.isdir() and b==b'','R4 raw directory '+name)
source=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');sourcecap=BASE/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04'
m=json.loads((sourcecap/'source-manifest.json').read_bytes());r4.same(source,m);checks.append('actual final Source649 whole986 same')
check(sha((sourcecap/'source.tar.gz').read_bytes())=='8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb','original Source archive unchanged')
# Reauthenticate original full manifests, not their copies in metadata-only directories.
for directory,filename in [('financial-genuine-wrapper-recordfix-final-parent-review01-2026-10-04','MANIFEST01.json'),('financial-genuine-wrapper-recordfix-parent-review01-2026-10-04','MANIFEST01.json'),('financial-genuine-wrapper-first-outcome-verifier-review03-2026-10-04','MANIFEST03.json'),('financial-genuine-wrapper-recordfix-generated-verifier-review01-2026-10-04','MANIFEST01.json'),('financial-genuine-wrapper-root-recordfix-verifier-binding01-2026-10-04','MANIFEST_ACTUAL02.json')]:
 root=BASE/directory;mm=json.loads((root/filename).read_bytes());members=mm['members'];names=[]
 for row in members:
  q=root/row['path'];s=q.lstat();names.append(row['path']);check(stat.S_IMODE(s.st_mode)==row['mode'],'original manifest mode '+directory+'/'+row['path'])
  if row['kind']=='file':b=q.read_bytes();check(stat.S_ISREG(s.st_mode) and len(b)==row['bytes'] and sha(b)==row['sha256'],'original manifest body '+directory+'/'+row['path'])
  elif row['kind']=='directory':check(stat.S_ISDIR(s.st_mode),'original directory type')
  else:check(stat.S_ISLNK(s.st_mode) and os.readlink(q)==row['target'],'original lexical target')
 actual=[]
 def visit(p):
  for q in p.iterdir():
   rel=str(q.relative_to(root));actual.append(rel)
   if stat.S_ISDIR(q.lstat().st_mode):visit(q)
 visit(root);check(set(actual)==set(names)|{filename},'full original manifest namespace '+directory)
# Frozen first review remains a complete original preflight snapshot; later additions are explicit.
mm=json.loads((HERE/'MANIFEST01.json').read_bytes())
for row in mm['members']:
 q=HERE/row['path'];s=q.lstat();check(stat.S_IMODE(s.st_mode)==row['mode'],'unchanged own preflight mode '+row['path'])
 if row['kind']=='file':check(sha(q.read_bytes())==row['sha256'],'unchanged own preflight body '+row['path'])
 elif row['kind']=='lexical-symlink':check(os.readlink(q)==row['target'],'unchanged own lexical witness')
out={'checks':len(checks),'check_names':checks,'actual_terminal_sha256':sha((ROOT/'ACTUAL_TERMINAL01.json').read_bytes()),'actual_intent_sha256':sha((ROOT/'ACTUAL_INTENT01.json').read_bytes()),'actual_root_exit':0,'actual_pid':intent['pid'],'actual_pid_start_ticks':intent['start_ticks'],'actual_pid_currently_absent':True,'source_current_complete_tree_unchanged':True,'full_process_group_history':None,'original_Source_capture_pid_history':None,'native_eligibility':None,'actual_external_recovery':None,'actual_flat_recovery':None}
with (HERE/'ACTUAL_JOINS02.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k!='check_names'}))
