from pathlib import Path
import hashlib,json,stat
D=Path(__file__).resolve().parent;F=D.parent;B=F/'financial-wrapper-complete100-baseline-remote01-2026-10-04';C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');m=json.loads((B/'flat-capsule01/body-metadata.json').read_bytes());rows=m['manifest']['members'];n=0
actual={p.relative_to(C).as_posix() for p in C.rglob('*') if '.git' not in p.relative_to(C).parts};assert actual=={r['path'] for r in rows};n+=1
for r in rows:
 p=C/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode'];n+=1
 if r['kind']=='file':
  raw=p.read_bytes();assert stat.S_ISREG(s.st_mode) and len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];assert raw==(B/'flat-capsule01'/m['flat_members'][r['path']]).read_bytes();n+=2
 else:assert stat.S_ISDIR(s.st_mode);n+=1
out={'checks':n,'current_non_git_members':len(rows),'current_regular_bodies':len(m['flat_members']),'entire_current_non_git_capsule_matches_accepted_baseline':True,'claim_or_native_started_by_review':False};(D/'CURRENT03.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
