"""Final readonly original-tree/anchor and actual tool-observation joins."""
import hashlib,json,os,stat
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03';original=OUT/'collection01';restored=OUT/'outcome-recovery02/collection';retained=json.loads((OUT/'OUTCOME_RETENTION01.json').read_bytes());rows=retained['members'];expected={r['path']:r for r in rows}
def digest(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304;return hashlib.sha256(p.read_bytes()).hexdigest()
seen=set()
for p in original.rglob('*'):
 name=p.relative_to(original).as_posix();r=expected[name];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode'];seen.add(name)
 if r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:assert stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and digest(p)==digest(restored/name)==r['sha256']
assert seen==set(expected) and len(seen)==2313 and stat.S_IMODE(original.stat().st_mode)==stat.S_IMODE(restored.stat().st_mode)==509
cap=restored/'data/capsule';anchor=json.loads((cap/'cold_prep/anchor.json').read_bytes());assert len(anchor['files'])==147
for name,h in anchor['files'].items():assert digest(cap/name)==h
q=json.loads((restored/'request.json').read_bytes());current=Path(q['root']);report=json.loads((restored/'collection.json').read_bytes());capsule_rows=[]
for ref in report['member_pages']['capsule']:
 p=restored/'members/capsule'/ref['path'];assert digest(p)==ref['sha256'];capsule_rows.extend(json.loads(p.read_bytes()))
actual=set()
for p in current.rglob('*'):
 name=p.relative_to(current).as_posix();actual.add(name)
assert actual=={x['path'] for x in capsule_rows}
for r in capsule_rows:
 p=current/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
 if r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:assert s.st_size==r['bytes'] and digest(p)==r['sha256']
exitdoc=json.loads((OUT/'ACTUAL_RECOVERY_TOOL_EXIT02.json').read_bytes());assert exitdoc['tool_session_id']==99885 and exitdoc['tool_exit_code']==0 and exitdoc['genuine_recovery_receipt_sha256']==digest(OUT/'REMOTE_OUTCOME_RECOVERY02.json') and exitdoc['helper_sha256']=='6ee87bca15f17d3425732d3cf78f42fd4fb29edbb06fedc91404911d0a6d6fa8'
r={'status':'ORIGINAL_COLLECTION_CURRENT_CAPSULE_ANCHOR_TOOL_EXIT_MATCH','original_collection_members':2313,'current_capsule_members':len(capsule_rows),'package_anchor_files':147,'root_mode':509,'tool_session':99885,'tool_exit':0,'tool_observation_sha256':digest(OUT/'ACTUAL_RECOVERY_TOOL_EXIT02.json'),'receipt_sha256':digest(OUT/'REMOTE_OUTCOME_RECOVERY02.json'),'qualification':'Root actual-tool observation is explicitly transcribed metadata, independently joined to actual recovered bytes; no new native/process/claim receipt fabricated.'}
(HERE/'ORIGINAL_READBACK03.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
