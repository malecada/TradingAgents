import hashlib,json,os,stat,subprocess
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';H=B/'financial-genuine-wrapper-root-claimedrun-source339-remote01-2026-10-04'
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert commit=='c29b1580b0a198aa5a55c17215869e2d914a9580'
legacy=json.loads((B/'financial-genuine-wrapper-root-recordfix-failed-remote01-2026-10-04/SELECTED_BODIES01.json').read_bytes())
prefix='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-recordfix-capture01-2026-10-04/'
paths={M/r['path']for r in legacy['rows']if r['path'].startswith(prefix)};assert len(paths)==6
scopes=['financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04','financial-genuine-wrapper-claimedrun-actual-source-admission-review01-2026-10-04','financial-genuine-wrapper-root-claimedrun-actual-admission01-2026-10-04','financial-genuine-wrapper-root-claimedrun-budget19-preparation01-2026-10-04','financial-genuine-wrapper-claimedrun-budget19-review01-2026-10-04','financial-genuine-wrapper-claimedrun-history-copy-admission-review01-2026-10-04','financial-genuine-wrapper-root-claimedrun-capsule-history-preparation01-2026-10-04','financial-genuine-wrapper-root-claimedrun-capsule-history-preparation02-2026-10-04','financial-genuine-wrapper-claimedrun-capsule-history-review01-2026-10-04','financial-genuine-wrapper-root-claimedrun-handoff-generation01-2026-10-04','financial-genuine-wrapper-root-claimedrun-source-registration01-2026-10-04','financial-genuine-wrapper-root-claimedrun-source-registration02-2026-10-04','financial-genuine-wrapper-claimedrun-preservation-census01-2026-10-04','financial-genuine-wrapper-root-claimedrun-witness-capture01-2026-10-04','financial-genuine-wrapper-claimedrun-witness-actual-capture-review01-2026-10-04','financial-genuine-wrapper-root-claimedrun-recovery-evidence-capture01-2026-10-04','financial-genuine-wrapper-claimedrun-recovery-evidence-capture-review01-2026-10-04','financial-genuine-wrapper-claimedrun-source-recovery-review03-2026-10-04','financial-genuine-wrapper-root-claimedrun-source339-remote01-2026-10-04','financial-genuine-wrapper-claimedrun-source339-flat-20261004-01']
for n in scopes:
 for root,dirs,files in os.walk(B/n,followlinks=False):
  root=Path(root);dirs[:]=[n for n in dirs if not(root/n).is_symlink()and n not in('.git','__pycache__','selected','union-bytes01')and not n.endswith('.git')]
  for n in files:
   p=root/n
   if p.is_symlink():continue
   paths.add(p)
paths.add(B/'financial-genuine-wrapper-root-claimedrun-witness-capture01-2026-10-04/union-bytes01/ORIGINAL_TREES01.json')
rows=[]
for p in sorted(paths):
 rel=p.relative_to(M).as_posix();assert not any(n.lower() in('keys','apis','.env','.ssh','hf_token.txt')or n.lower().endswith(('.pem','.key'))for n in p.parts)
 st=p.lstat();assert stat.S_ISREG(st.st_mode)and st.st_size<=4*1024**2;raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 gitbody=subprocess.check_output(['git','show',commit+':'+rel]);assert gitbody==raw
 rows.append({'path':rel,'bytes':len(raw),'sha256':sha})
assert len(rows)<=506 and sum(r['bytes']for r in rows)<=64*1024**2
body=(json.dumps({'remote_commit':commit,'rows':rows},sort_keys=True,indent=2)+'\n').encode()
with(H/'SELECTED_BODIES01.json').open('xb')as f:f.write(body)
summary={'selection_sha256':hashlib.sha256(body).hexdigest(),'selected_count':len(rows),'logical_bytes':sum(r['bytes']for r in rows),'remote_commit':commit,'scope':'Complete Source339 capture/Git/history/correction registration and actual read-only admission; all source01 failed partial and source02 ordinary preparation bytes; applicable handoff four-root archive and full strict recovery02/03 source/review archives. Six legacy Source325 required transport pins are supplemental. Current selected scope does not supply final Parent/caller/release/full witness supplement, installed-runtime bodies or empirical stores; those remain separate before numerical release. No selected direct symlinks; literal handoff links are preserved as archive metadata.','actual_external':False,'new_claim_or_native':False}
with(H/'SELECTION_SCOPE01.json').open('x')as f:json.dump(summary,f,sort_keys=True,indent=2);f.write('\n')
with(H/'SELECTION_BUILDER01.py').open('xb')as f:f.write(Path(__file__).read_bytes())
print(json.dumps(summary,sort_keys=True))
