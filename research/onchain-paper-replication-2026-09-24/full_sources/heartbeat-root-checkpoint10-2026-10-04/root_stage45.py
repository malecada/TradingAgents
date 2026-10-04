from pathlib import Path
import os,stat,json,hashlib,gzip,subprocess,datetime
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='7bec5c009156fa6954a433659dec2ef55957a5dc';assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)==b''
roots=['financial-wrapper-compatibility-operational-delta-flat-tooling01-2026-10-04','financial-wrapper-compatibility-operational-recovery-source-review01-2026-10-04','financial-wrapper-compatibility-operational-delta-root-remote01-2026-10-04'];rows=[];special=[];encoded=[]
E=C/'STAGE45_LOSSLESS_NEGATIVE_BODIES';E.mkdir(mode=0o700)
for name in roots:
 for root,ds,fs in os.walk(F/name,followlinks=False):
  ds[:]=[n for n in ds if n!='.git' and not n.endswith('.git') and n!='__pycache__']
  for n in fs:
   p=Path(root)/n;s=p.lstat();rel=p.relative_to(R).as_posix()
   if stat.S_ISREG(s.st_mode):
    raw=p.read_bytes()
    if len(raw)>4*1024**2:
     compressed=gzip.compress(raw,mtime=0);q=E/(hashlib.sha256(raw).hexdigest()+'.bin.gz');assert len(compressed)<4*1024**2
     if q.exists():assert q.read_bytes()==compressed
     else:q.write_bytes(compressed)
     assert gzip.decompress(q.read_bytes())==raw;encoded.append({'original':rel,'original_bytes':len(raw),'original_sha256':hashlib.sha256(raw).hexdigest(),'original_mode':stat.S_IMODE(s.st_mode),'lossless_encoded':q.relative_to(R).as_posix(),'encoded_sha256':hashlib.sha256(compressed).hexdigest(),'original_local_file_preserved':True});rows.append({'path':q.relative_to(R).as_posix(),'kind':'file','bytes':len(compressed),'sha256':hashlib.sha256(compressed).hexdigest()});continue
   elif stat.S_ISLNK(s.st_mode):raw=os.fsencode(os.readlink(p))
   else:special.append({'path':rel,'mode':s.st_mode,'bytes':s.st_size,'retained_original_local':True,'git_reconstruction_claim':False});continue
   rows.append({'path':rel,'kind':'symlink' if stat.S_ISLNK(s.st_mode) else 'file','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
for p in [C/'REMOTE_CONFIRMATION44.json']:
 raw=p.read_bytes();rows.append({'path':p.relative_to(R).as_posix(),'kind':'file','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
M=C/'STAGE45_PREPARATION01.json';M.write_text(json.dumps({'schema_version':1,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':45,'files':rows,'encoded_original_large_negative_bodies':encoded,'special_retained_local_metadata':special,'qualification':'Only source/controls/Root installed unreleased preparation. Original Root selection01 remains7bec; next actualremote selection must use new actual HEAD. No IO/NUM entry or numerical grant.'},indent=2)+'\n')
names=sorted({x['path'] for x in rows}|{M.relative_to(R).as_posix()})
for start in range(0,len(names),100):subprocess.run(['git','add','--',*names[start:start+100]],cwd=R,check=True)
print(len(names),len(encoded),len(special))
