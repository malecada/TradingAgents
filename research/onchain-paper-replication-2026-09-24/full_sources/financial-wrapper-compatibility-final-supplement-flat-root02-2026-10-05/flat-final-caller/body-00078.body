"""Finite opaque final-caller capture; reuses accepted PAX/IO, grants no entry."""
import datetime, hashlib, importlib.util, json, os, shutil, stat, sys
from pathlib import Path
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
FS=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
C=FS/'heartbeat-root-checkpoint10-2026-10-04'
PARENT=ROOT.parent/'onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01'
PREP=FS/'financial-wrapper-compatibility-final-supplement-transport-preparation02-2026-10-05'
DEST=FS/'financial-wrapper-compatibility-final-supplement-capture01-2026-10-05'
sys.path.insert(0,str(PREP/'utilities'))
import recovery_pax01 as R
import owned_io as IO
def put(p,b):
 R.require(len(b)<=R.FILE and p.is_relative_to(DEST),'owned bounded file')
 p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 with IO._opened(p,'xb') as f:
  R.require(f.write(b)==len(b),'complete write');f.flush();os.fsync(f.fileno())
def ref(p):
 b=R.read(p.parent,p.name)
 return {'path':p.relative_to(ROOT).as_posix(),'bytes':len(b),'sha256':R.digest(b)}
def main():
 R.require(not os.path.lexists(DEST),'one fresh finite capture')
 R.require(shutil.disk_usage(FS).free>=10*1024**3,'10GiB floor')
 raw=R.read(PARENT,'REQUEST_FINAL01.json')
 R.require(R.digest(raw)=='cfecfd3e12d81628b9bc6f10171dd0345ac6e62c5481edccab64e5207254e03d','actual final request')
 q=json.loads(raw);R.require(not os.path.lexists(PARENT/'attempt'),'no numerical attempt')
 envpath=FS/'financial-wrapper-compatibility-preclaim-baseline-envelope01-2026-10-05/ENVELOPE01.json'
 baseline=json.loads(R.read(envpath.parent,envpath.name))
 common={k:baseline['evidence'][k] for k in ('accepted_basis_byte_review','coalesced_actual_review','source_runtime_bridge','postinstall_review','independent_population_review')}
 scopes={
  'parent':PARENT,
  'baseline-review':FS/'financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05',
  'parent-review':FS/'financial-wrapper-compatibility-final-parent-release-review01-2026-10-05',
  'failed-flat-review':FS/'financial-wrapper-compatibility-baseline-recovery-review01-2026-10-05',
  'transport':PREP,
 }
 snapshots={k:R.scan(p) for k,p in scopes.items()}
 R.require(len(snapshots['parent']['members'])==12 and all(x['kind']=='file' for x in snapshots['parent']['members']),'complete current twelve Parent bodies')
 inputs={};origins=[]
 def add(name,p):
  R.path_name(name);b=R.read(p.parent,p.name);s=p.lstat()
  R.require(name not in inputs,'unique snapshot role')
  inputs[name]=b;origins.append({'snapshot_path':name,'original_path':str(p),'original_mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':R.digest(b)})
 for role,p in scopes.items():
  for x in snapshots[role]['members']:
   if x['kind']=='file':add(role+'/'+x['path'],p/x['path'])
 for k,v in common.items():add('common/'+k+'.body',ROOT/v['path'])
 add('common/baseline-envelope.json',envpath)
 for role,v in q['proofs'].items():add('proofs/'+role+'.body',Path(v['path']))
 old=FS/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05'
 failed_names=('ROOT_BASELINE_FLAT01_EXIT.json','ROOT_TOOL_EXIT_FLAT01.json')
 for n in failed_names:add('failed-flat-original/'+n,old/n)
 for n in ('PARENT_FINAL_PREFLIGHT01.stdout','PARENT_FINAL_PREFLIGHT01.stderr','PARENT_FINAL_PREFLIGHT01_TOOL_EXIT.json'):
  add('preflight/'+n,C/n)
 add('root-source/root_final_supplement_capture01.py',Path(__file__))
 for k,p in scopes.items():R.same(p,snapshots[k])
 for x in origins:
  p=Path(x['original_path']);R.require(stat.S_IMODE(p.lstat().st_mode)==x['original_mode'] and len(R.read(p.parent,p.name))==x['bytes'] and R.digest(R.read(p.parent,p.name))==x['sha256'],'all original bodies/modes current')
 DEST.mkdir(mode=0o700);snap=DEST/'snapshot';snap.mkdir(mode=0o700)
 for n,b in inputs.items():put(snap/n,b)
 put(snap/'ORIGINS01.json',R.encode({'schema_version':1,'scope':'complete final Parent twelve bodies, exact proofs/release and finite evidence; earlier actual baseline reused','origins':origins,'original_typed_scopes':snapshots,'excluded':['installed runtime package bodies','POSIX reconstruction','numerical authority','whole-fit capacity'],'failed_flat_prefix':'169 immutable original bodies authenticated by accepted closure; original receiver is not modified or refetched'}))
 m=R.scan(snap);R.validate(m);put(DEST/'MANIFEST01.json',R.encode(m))
 archive=R.pack(snap,m,DEST/'final-supplement01.tar.gz')
 for k,p in scopes.items():R.same(p,snapshots[k])
 proofrefs=[]
 for role,v in sorted(q['proofs'].items()):
  original=Path(v['path']);p=original if original.is_relative_to(FS) else snap/('proofs/'+role+'.body')
  proofrefs.append(ref(p))
 evidence={**common,'baseline_envelope':ref(envpath),'baseline_recovery_review':ref(scopes['baseline-review']/'MACHINE01.json'),'complete_final_request':ref(snap/'parent/REQUEST_FINAL01.json'),'complete_final_release':ref(Path(q['final_review']['path'])),'complete_three_proofs':proofrefs}
 put(DEST/'CAPTURE01.json',R.encode({'schema_version':1,'status':'ACTUAL_LOCAL_FINAL_CALLER_CAPTURE_NO_REMOTE_OR_ENTRY','captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':q['source'],'parent_final_sha256':R.digest(raw),'archive':archive,'manifest_sha256':R.digest(R.encode(m)),'payload_regular':sum(x['kind']=='file' for x in m['members']),'payload_typed':len(m['members']),'evidence':evidence,'source_capsule_recovery':'accepted actual605/407 baseline reused unchanged','numerical_authority':False}))
 print(json.dumps({'destination':str(DEST),'archive':archive,'payload_regular':sum(x['kind']=='file' for x in m['members']),'payload_typed':len(m['members'])},sort_keys=True))
if __name__=='__main__':main()
