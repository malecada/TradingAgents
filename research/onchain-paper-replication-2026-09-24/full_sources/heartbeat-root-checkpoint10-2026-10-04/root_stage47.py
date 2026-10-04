from pathlib import Path
import os,stat,json,hashlib,gzip,subprocess,datetime
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714';assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)==b''
roots=['financial-wrapper-compatibility-operational-delta-remote-review02-2026-10-04','financial-wrapper-compatibility-operational-delta-flat-successor03-2026-10-04','financial-wrapper-compatibility-operational-delta-flat-review03-2026-10-04','financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04','financial-wrapper-compatibility-operational-delta-entry-review03-2026-10-04','financial-wrapper-compatibility-operational-delta-entry-review04-2026-10-04','financial-wrapper-compatibility-operational-delta-remote-outcome-review03-2026-10-04'];rows=[];enc=[];special=[];skip=[];E=C/'STAGE47_LOSSLESS_NEGATIVE_BODIES';E.mkdir(mode=0o700)
for n in roots:
 assert (F/n).is_dir()
 for root,ds,fs in os.walk(F/n,followlinks=False):
  for n in list(ds):
   if n=='.git' or n.endswith('.git') or n=='__pycache__':ds.remove(n);skip.append((Path(root)/n).relative_to(R).as_posix())
  for n in fs:
   p=Path(root)/n;s=p.lstat();name=p.relative_to(R).as_posix()
   if stat.S_ISREG(s.st_mode):
    b=p.read_bytes()
    if len(b)>4194304:
     z=gzip.compress(b,mtime=0);q=E/(h(b)+'.bin.gz');assert len(z)<4194304
     if q.exists():assert q.read_bytes()==z
     else:q.write_bytes(z)
     assert gzip.decompress(q.read_bytes())==b;enc.append({'original':name,'bytes':len(b),'sha256':h(b),'mode':stat.S_IMODE(s.st_mode),'lossless_encoded':q.relative_to(R).as_posix(),'encoded_sha256':h(z),'local_original_preserved':True});rows.append({'path':q.relative_to(R).as_posix(),'kind':'file','bytes':len(z),'sha256':h(z)});continue
   elif stat.S_ISLNK(s.st_mode):b=os.fsencode(os.readlink(p))
   else:special.append({'path':name,'raw_mode':s.st_mode,'size':s.st_size,'original_local_retained':True});continue
   rows.append({'path':name,'kind':'symlink' if stat.S_ISLNK(s.st_mode) else 'file','bytes':len(b),'sha256':h(b)})
extras=['REMOTE_CONFIRMATION46.json','REMOTE_CONFIRMATION46_COMPLETE01.json','root_operational_install03.py','root_operational_remote03.py','root_operational_remote04.py','ROOT_REMOTE_CALLER04_SOURCE_INVERSE01.json','root_remote_caller04_checks.py','ROOT_REMOTE_CALLER04_CHECK01.out','ROOT_REMOTE_CALLER04_CHECK01.err','ROOT_REMOTE_CALLER04_AUTH_CHECKS01.json','FLAT_SOURCE03_AUXILIARY_SCOPE_QUALIFICATION01.json','OBSERVATION62_PRE_FRESH_ENTRY01.json','TOP62_CHECKPOINT01.json','root_top63.py','TOP63_CHECKPOINT01.json','COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json','root_stage47.py']
for n in extras:p=C/n;b=p.read_bytes();rows.append({'path':p.relative_to(R).as_posix(),'kind':'file','bytes':len(b),'sha256':h(b)})
for root,ds,fs in os.walk(C/'ROOT_REMOTE_CALLER04_AUTH_CONTROLS01',followlinks=False):
 for n in fs:p=Path(root)/n;b=p.read_bytes();rows.append({'path':p.relative_to(R).as_posix(),'kind':'file','bytes':len(b),'sha256':h(b)})
for p in [R/'research/onchain-paper-replication-2026-09-24/STATE.md',F/'parallel-execution-2026-10-02/COORDINATION.md']:b=p.read_bytes();rows.append({'path':p.relative_to(R).as_posix(),'kind':'file','bytes':len(b),'sha256':h(b)})
M=C/'STAGE47_PREPARATION01.json';M.write_text(json.dumps({'stage':47,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows,'lossless_negative_encoding':enc,'specials_local_metadata':special,'original_git_dirs_retained_local_not_staged':skip,'qualification':'Closed actual successful remote/actual bytes accepted but flatentry withheldRM1; all originals/raw/modes preserved. No flat/source-policy composedproof/NUM grant. No active mode04 worker directory selected. Actualpartial receiver bare remains local immutable; actualreceivedselected blobs/raw receipts/source are committed here. Gitcommit availability is separate from freshcomplete recovery.'},indent=2)+'\n');names=sorted({r['path'] for r in rows}|{M.relative_to(R).as_posix()})
for i in range(0,len(names),100):subprocess.run(['git','add','--',*names[i:i+100]],cwd=R,check=True)
print(json.dumps({'paths':len(names),'lossless_negatives':len(enc),'specials':len(special),'excluded_git_dirs':len(skip)}))
