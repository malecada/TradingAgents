"""Fixed baseline receiver or proof-dependent flat entry; no implicit phase advance."""
from pathlib import Path
import argparse,hashlib,json,os,resource,signal,stat,subprocess,sys,time
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05';FILE=4194304
IOPIN='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb';pins={}
def sig(p):
 s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE;return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks'))
def raw(p):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK);primary=None
 try:
  b=bytearray()
  while len(b)<=FILE:
   chunk=os.read(fd,min(65536,FILE+1-len(b)))
   if not chunk:break
   b.extend(chunk)
  assert len(b)<=FILE,'metadata file bound exceeded'
  return bytes(b)
 except BaseException as error:primary=error;raise
 finally:
  try:os.close(fd)
  except BaseException as cleanup:
   if primary is None:raise
   fatal=lambda error:isinstance(error,MemoryError) or not isinstance(error,Exception)
   if fatal(cleanup) and not fatal(primary):raise cleanup from primary
   try:
    prior=primary.__cause__
    primary.__cause__=cleanup if prior is None else BaseExceptionGroup('prior body/cleanup evidence',[prior,cleanup])
   except BaseException:pass
def read(p,h):
 before=sig(p);b=raw(p);assert sig(p)==before and type(h)is str and len(h)==64 and hashlib.sha256(b).hexdigest()==h;assert p not in pins or pins[p]==before;pins[p]=before;return b
def rejoin():
 for p,s in pins.items():assert sig(p)==s,'verified caller input changed'
def local(name):
 assert type(name)is str and Path(name).as_posix()==name and not Path(name).is_absolute() and all(x not in ('','..','.') for x in name.split('/'));return D/name
def contract(c):
 assert type(c)is dict and c['schema_version']==1 and c['status']=='ROOT_BOUND_BASELINE_ENTRY' and c['phase'] in ('REMOTE','FLAT') and c['owned_root']==str(D) and c['numerical_authority'] is False
 assert type(c['main_commit'])is str and len(c['main_commit'])==40 and all(x in '0123456789abcdef' for x in c['main_commit'])
 assert type(c['helpers'])is dict and {'watch01.py','utilities/owned_io.py','recover01.py','restore_bundle01.py','binding01.py','receipt01.py','cohort01.py','utilities/recovery_pax01.py','utilities/bounded_git01.py'}<=set(c['helpers']) and 1<=len(c['helpers'])<=32 and c['helpers']['utilities/owned_io.py']==IOPIN
 assert c['phase']!='FLAT' or all(type(c[k])is dict for k in ('remote_receipt','remote_root_exit','selected_mode_profile','flat_release','request'))
 return c['phase']
def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--contract-sha256',required=True);p.add_argument('--entry-release',required=True);p.add_argument('--entry-release-sha256',required=True);a=p.parse_args()
 c=json.loads(read(local(a.contract),a.contract_sha256));phase=contract(c);release=json.loads(read(local(a.entry_release),a.entry_release_sha256))
 caller_hash=release['caller_sha256'];read(Path(__file__).absolute(),caller_hash)
 assert release=={'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_BASELINE_'+phase,'contract_sha256':a.contract_sha256,'caller_sha256':caller_hash,'numerical_authority':False}
 for name,h in c['helpers'].items():read(local(name),h)
 assert c['helpers']['utilities/owned_io.py']==IOPIN;sys.path.insert(0,str(D/'utilities'));sys.path.insert(0,str(D));import owned_io as IO;import watch01 as W
 assert Path(IO.__file__)==D/'utilities/owned_io.py' and Path(W.__file__)==D/'watch01.py';assert D.resolve()==D and stat.S_IMODE(D.stat().st_mode)==0o700
 for key in ('selection','request','remote_receipt','remote_root_exit','selected_mode_profile','flat_release'):
  if c.get(key)is not None:row=c[key];read(local(row['path']),row['sha256'])
 selection=json.loads(read(local(c['selection']['path']),c['selection']['sha256']));assert selection['remote_commit']==c['main_commit']
 command=[str(ROOT/'.venv/bin/python'),'-B',str(D/('recover01.py' if phase=='REMOTE' else 'restore_bundle01.py'))]+(['--selection-sha256',c['selection']['sha256']] if phase=='REMOTE' else ['--request',c['request']['path'],'--sha256',c['request']['sha256']])
 prefix='ROOT_BASELINE_'+phase+'01';assert all(not os.path.lexists(D/(prefix+x)) for x in ('_INTENT.json','_SPAWN.json','.stdout','.stderr','_EXIT.json'))
 required_fresh={'fresh-compatibility-baseline02.git','selected','REMOTE_RECOVERY01.json','FAILED01.json'} if phase=='REMOTE' else {'BUNDLE_FLAT_INTENT01.json','BUNDLE_FLAT_RECOVERY01.json','BUNDLE_FLAT_FAILED01.json'}
 assert type(c['fresh_names'])is list and required_fresh<=set(c['fresh_names']) and len(c['fresh_names'])<=64
 for name in c['fresh_names']:assert not os.path.lexists(local(name))
 for p in Path('/proc').iterdir():
  if p.name.isdigit() and int(p.name)!=os.getpid():
   try:argv=raw(p/'cmdline').split(b'\0')
   except (FileNotFoundError,ProcessLookupError,PermissionError):continue
   assert str(D/'recover01.py').encode() not in argv and str(D/'restore_bundle01.py').encode() not in argv
 def put(name,obj):
  b=(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();assert len(b)<=FILE
  with IO._opened(D/name,'xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 observations=[W.census(D)];rejoin();resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE));assert resource.getrlimit(resource.RLIMIT_FSIZE)==(FILE,FILE)
 put(prefix+'_INTENT.json',{'argv':command,'contract_sha256':a.contract_sha256,'entry_release_sha256':a.entry_release_sha256,'parent_pid':os.getpid(),'claim_started':False});begun=time.monotonic();child=None;code=None;primary=None;secondary=[]
 try:
  with IO._opened(D/(prefix+'.stdout'),'xb') as out,IO._opened(D/(prefix+'.stderr'),'xb') as err:
   child=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=err,start_new_session=True);put(prefix+'_SPAWN.json',{'pid':child.pid,'argv':command})
   while child.poll() is None:
    assert time.monotonic()-begun<(630 if phase=='REMOTE' else 210) and len(observations)<4096;observations.append(W.census(D))
    try:code=child.wait(timeout=.25)
    except subprocess.TimeoutExpired:pass
 except BaseException as error:primary=error
 finally:
  def retain(fn):
   try:fn()
   except BaseException as e:secondary.append(e)
  if child is not None:
   def stop():
    if child.poll() is None:
     try:os.killpg(child.pid,signal.SIGKILL)
     except ProcessLookupError:pass
   retain(stop);retain(lambda:child.wait(timeout=10));code=child.returncode
  retain(lambda:observations.append(W.census(D)))
  retain(lambda:put(prefix+'_EXIT.json',{'child_exit':code,'parent_failure_type':None if primary is None else type(primary).__name__,'cleanup_failures':[type(e).__name__ for e in secondary],'elapsed_seconds':time.monotonic()-begun,'observations':observations,'parent_fsize_readback':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'actual_parent_exit':None,'numerical_authority':False}))
  IO._cleanup(tuple((lambda e=e:(_ for _ in ()).throw(e)) for e in secondary),primary=primary)
 if primary is not None:raise primary
 rejoin();assert code is not None;return code
if __name__=='__main__':raise SystemExit(main())
