import hashlib,json,os,stat,subprocess
from pathlib import Path
M=Path.cwd();S=M/'research/onchain-paper-replication-2026-09-24';B=S/'full_sources';C=B/'heartbeat-root-checkpoint10-2026-10-04'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='d6859b5cabccde4e4c5af2320cb96b397dfbedd4'
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
scopes=[
'financial-genuine-wrapper-recordfix-failed-scope-actual-recovery-review01-2026-10-04',
'financial-genuine-wrapper-recordfix-failed-scope-recovery-preparation01-2026-10-04',
'financial-genuine-wrapper-recordfix-failed-scope-recovery-review01-2026-10-04',
'financial-genuine-wrapper-root-recordfix-failed-remote01-2026-10-04',
'financial-genuine-wrapper-root-recordfix-failed-flat01-2026-10-04',
'financial-genuine-wrapper-postclaim-budget-investigation01-2026-10-04',
'financial-genuine-wrapper-root-claimedrun-budget19-preparation01-2026-10-04',
'financial-genuine-wrapper-claimedrun-budget19-review01-2026-10-04',
'financial-genuine-wrapper-claimedrun-history-copy-admission-review01-2026-10-04',
'financial-genuine-wrapper-root-claimedrun-capsule-history-preparation01-2026-10-04',
'financial-genuine-wrapper-root-claimedrun-capsule-history-preparation02-2026-10-04',
'financial-genuine-wrapper-claimedrun-capsule-history-review01-2026-10-04',
'financial-genuine-wrapper-claimedrun-source-handoff-preparation01-2026-10-04',
'financial-genuine-wrapper-claimedrun-source-handoff-review01-2026-10-04',
'financial-genuine-wrapper-claimedrun-source-handoff-preparation02-2026-10-04',
'financial-genuine-wrapper-claimedrun-source-handoff-review02-2026-10-04',
'financial-genuine-wrapper-root-claimedrun-handoff-generation01-2026-10-04',
'financial-genuine-wrapper-root-claimedrun-source-registration01-2026-10-04',
'financial-genuine-wrapper-root-claimedrun-source-registration02-2026-10-04',
'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04',
'financial-genuine-wrapper-claimedrun-actual-source-admission-review01-2026-10-04',
'financial-genuine-wrapper-root-claimedrun-actual-admission01-2026-10-04',
'financial-genuine-wrapper-claimedrun-parent-preparation01-2026-10-04',
]
paths=[S/'STATE.md',B/'parallel-execution-2026-10-02/COORDINATION.md']
for tree in [C,*[B/n for n in scopes]]:
 assert tree.is_dir()
 for root,dirs,files in os.walk(tree,followlinks=False):
  root=Path(root)
  links=[n for n in dirs if (root/n).is_symlink()];paths.extend(root/n for n in links)
  dirs[:]=[n for n in dirs if n not in links and n not in ('.git','selected','__pycache__','flat') and not n.endswith('.git')]
  paths.extend(root/n for n in files)
F=B/'financial-genuine-wrapper-recordfix-failed-scope-flat-20261004-01'
paths.extend(F/n for n in ('intent.json','request.json','RECOVERY01.json'))
copy=C/'STAGE17_BUILDER01.py';assert not copy.exists();copy.write_bytes(Path(__file__).read_bytes());paths.append(copy)
rows=[]
for p in sorted(set(paths)):
 rel=p.relative_to(M).as_posix();assert not any(n.lower() in ('keys','apis','.env','.ssh','hf_token.txt') or n.lower().endswith(('.pem','.key')) for n in p.parts)
 s=p.lstat()
 if stat.S_ISLNK(s.st_mode):body=os.readlink(p).encode();kind='lexical-link'
 else:assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2;body=p.read_bytes();kind='file'
 rows.append({'path':rel,'kind':kind,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
receipt=C/'STAGE17.json'
with receipt.open('x')as f:json.dump({'rows':rows,'count':len(rows),'scope':'Closed complete failed actual external/flat recovery, prospective19 amendment/review, withheld/corrected source handoffs and full witnesses, actual original closed-history relocation, all ordinary preparation failures, Source339 commit/capture and actual read-only admission. Fresh bare Git, selected/flat duplicates and secret locations excluded. Original complete source archives retained. No numerical release.'},f,sort_keys=True,indent=2);f.write('\n')
names=[r['path']for r in rows]+[receipt.relative_to(M).as_posix()]
for start in range(0,len(names),80):subprocess.run(['git','add','-f','--',*names[start:start+80]],check=True)
print(json.dumps({'staged_paths':len(names),'new_native':False,'actual_claims':1,'highest_actual_claim_budget':18,'prospective_effective_metadata_budget':19}))
