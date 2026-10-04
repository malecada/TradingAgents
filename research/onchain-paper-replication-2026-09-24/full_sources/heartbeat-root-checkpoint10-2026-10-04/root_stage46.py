from pathlib import Path
import os,stat,json,hashlib,gzip,subprocess,datetime
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='0e65d12400e9c63b0eaf1f93bea2c81b10a82743';assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)==b''
roots=['financial-wrapper-compatibility-operational-delta-root-remote01-2026-10-04','financial-wrapper-compatibility-operational-delta-root-remote02-2026-10-04','financial-wrapper-compatibility-operational-delta-entry-review02-2026-10-04','financial-wrapper-compatibility-operational-delta-root-remote-failed-outcome-review02-2026-10-04','financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04','financial-wrapper-compatibility-preclaim-source01-2026-10-04','financial-wrapper-compatibility-preclaim-source-review01-2026-10-04','financial-wrapper-compatibility-preclaim-correction02-2026-10-04','financial-wrapper-compatibility-preclaim-review02-2026-10-04','financial-wrapper-operational-forensic-watch-correction04-2026-10-04','financial-wrapper-operational-forensic-watch-review04-2026-10-04','financial-wrapper-compatibility-operational-delta-flat-successor02-2026-10-04','financial-wrapper-compatibility-operational-delta-flat-review02-2026-10-04','financial-wrapper-compatibility-operational-delta-remote-successor02-2026-10-04'];rows=[];special=[];encoded=[];skipped=[];E=C/'STAGE46_LOSSLESS_NEGATIVE_BODIES';E.mkdir(mode=0o700)
for name in roots:
 assert (F/name).is_dir()
 for root,ds,fs in os.walk(F/name,followlinks=False):
  for n in list(ds):
   if n=='.git' or n.endswith('.git') or n=='__pycache__':ds.remove(n);skipped.append(str((Path(root)/n).relative_to(R)))
  for n in fs:
   p=Path(root)/n;s=p.lstat();rel=p.relative_to(R).as_posix()
   if stat.S_ISREG(s.st_mode):
    raw=p.read_bytes()
    if len(raw)>4194304:
     z=gzip.compress(raw,mtime=0);q=E/(sha(raw)+'.bin.gz');assert len(z)<4194304
     if q.exists():assert q.read_bytes()==z
     else:q.write_bytes(z)
     assert gzip.decompress(q.read_bytes())==raw;encoded.append({'original':rel,'original_bytes':len(raw),'original_sha256':sha(raw),'mode':stat.S_IMODE(s.st_mode),'lossless_encoded':q.relative_to(R).as_posix(),'encoded_sha256':sha(z),'original_local_preserved':True});rows.append({'path':q.relative_to(R).as_posix(),'kind':'file','bytes':len(z),'sha256':sha(z)});continue
   elif stat.S_ISLNK(s.st_mode):raw=os.fsencode(os.readlink(p))
   else:special.append({'path':rel,'raw_mode':s.st_mode,'bytes':s.st_size,'retained_original_local':True,'Git_or_POSIX_reconstruction_claim':False});continue
   rows.append({'path':rel,'kind':'symlink' if stat.S_ISLNK(s.st_mode) else 'file','bytes':len(raw),'sha256':sha(raw)})
extras=[C/n for n in ['REMOTE_CONFIRMATION45.json','OBSERVATION61_PRE_SOURCE_POLICY_IO01.json','TOP61_CHECKPOINT01.json','root_top61.py','root_operational_remote02.py','REMOTE_SOURCE02_REPORT_ARITHMETIC_ERRATUM01.json','root_stage46.py']]+[R/'research/onchain-paper-replication-2026-09-24/STATE.md',F/'parallel-execution-2026-10-02/COORDINATION.md']
for p in extras:raw=p.read_bytes();rows.append({'path':p.relative_to(R).as_posix(),'kind':'file','bytes':len(raw),'sha256':sha(raw)})
M=C/'STAGE46_PREPARATION01.json';M.write_text(json.dumps({'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':46,'files':rows,'lossless_original_negative_encoding':encoded,'specials_retained_local_metadata':special,'excluded_original_git_directories':skipped,'qualification':'Closed source/refusal/failed_root/localcapture scopes and precise TOP61. Actual failedRoot43 bytes are in exact canonical failed archive; original bare also local immutable. Commit availability is not actual15 selected transfer/freshflat/source-policy proof or numerical release. No active flat03 or remote peer review is selected.'},indent=2)+'\n');names=sorted({x['path'] for x in rows}|{M.relative_to(R).as_posix()})
for start in range(0,len(names),100):subprocess.run(['git','add','--',*names[start:start+100]],cwd=R,check=True)
print(json.dumps({'staged_paths':len(names),'lossless_encoded_negatives':len(encoded),'special_metadata_only':len(special),'excluded_git_directories':len(skipped),'selected_literal15_bodies_staged':True}))
