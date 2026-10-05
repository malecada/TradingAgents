import datetime,hashlib,json,stat,subprocess
from pathlib import Path
root=Path.cwd();s=root/'research/onchain-paper-replication-2026-09-24';f=s/'full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04'
with (c/'STATE_TOP97_SNAPSHOT01.md').open('xb') as w:w.write((s/'STATE.md').read_bytes())
t=(s/'STATE.md').read_text();t=t.replace('TOP97','TOP98',1).replace('restart reconciled; no numerical job is active. Seven financial fitting/checkpoint modules are integrated, 45 focused regressions passed, and actual recovery of the reserved continuation refusal is complete.','successor source implementation is installed in the isolated CAP; no numerical job or new claim is active. Source review and 11 focused regressions passed; concrete gate and recovery remain pending.',1).replace('b94682059c2d7a739d18db0d299d8c3a0a5019be','e2610e49de461716bd78e1fbac43a65c42e1b1be').replace('REMOTE_CONFIRMATION64.json','REMOTE_CONFIRMATION65.json')
t=t.replace('CAP current/design remains `d4c81c0961342bfe4c5771aabbef1d46a14cffb8`, 360 tracked/359 admission pins.','CAP committed HEAD remains `d4c81c0961342bfe4c5771aabbef1d46a14cffb8`; two operational source bodies and five new inputs are prepared in its working tree, not yet admitted under a new committed gate.')
start=t.index('Next executable work:');end=t.index('\n\nRoot owns',start)
t=t[:start]+'''New functional implementation: a separate registered successor edge preserves the original policy, COMPLETE100 reference and all 193 other installed bodies. Exactly the compatibility helper and fixture reference predicate changed; new external preclaim validates all 34 input roles. [Sealed source](full_sources/financial-wrapper-continuation-successor-source01-2026-10-05/MANIFEST01.json)36689eae; 11 focused nonnumerical regressions pass, including genuine retained COMPLETE100 claim/checkpoint metadata joins. [Independent source proof](full_sources/financial-wrapper-continuation-successor-review01-2026-10-05/SOURCE_REVIEW_PROOF01.json)cff01105 and 33 finite checks accepted the exact edge9c63d040/current map50e868ba. Initial two review findings and preparation01 remain preserved; preparation02 uses the accepted final source. New caller has actual six unchanged helpers and new preclaim, but its source binding and final release are null.

Next executable work: recover the exact 12-body 214,532B source/policy/review increment once, then finish the concrete same-family gate and current source binding for `financial-wrapper-classification-eager-continue100-resource-successor-20261005-01`. Reuse actual prior recovery; review only changed registration/caller seams, preserve/recover the final current capsule/Parent increment, obtain exact final release, then run genuine preflight and at most one eligible continuation. Historical interrupt checkpoint, 99 remaining updates, original model/training/tolerances and numerical caps remain fixed. No successor claim or attempt exists yet.''' +t[end:]
t=t.replace('One bounded worker owns a NEW successor source candidate; investigation is complete.','Source author and investigation are complete. One independent reviewer owns the single open successor review through concrete registration, recovery and exact release.').replace('[Previous TOP96]','[Previous TOP97]').replace('STATE_TOP96_SNAPSHOT01.md','STATE_TOP97_SNAPSHOT01.md')
(s/'STATE.md').write_text(t)
(f/'parallel-execution-2026-10-02/COORDINATION.md').write_text('''# Current parallel coordination

Read the [latest study checkpoint](../../STATE.md) for evidence, accounting and next safe action. Root alone owns live Main/CAP/Parent/Git, registration, STATE, actual external preservation and one native numerical launcher.

- `continuation_successor_admission`: read-only investigation complete.
- `continuation_successor_implementation`: sealed new source candidate complete; no live ownership.
- `continuation_successor_review`: owns the single OPEN financial-wrapper-continuation-successor-review01-2026-10-05, changed source/registration/caller/recovery/release only. Source phase frozen; later phases add files.

No numerical job or new claim is active. The old continuation Parent and identity are permanently reserved; never relaunch. Reuse accepted immutable evidence and review changed seams once.
''')
paths={s/'STATE.md',f/'parallel-execution-2026-10-02/COORDINATION.md'}
for folder in ('financial-wrapper-continuation-successor-source01-2026-10-05','financial-wrapper-continuation-successor-preparation01-2026-10-05','financial-wrapper-continuation-successor-preparation02-2026-10-05','financial-wrapper-continuation-successor-review01-2026-10-05','financial-wrapper-continuation-successor-policy-remote01-2026-10-05'):
 for p in (f/folder).rglob('*'):
  if p.is_file() and not p.is_symlink():paths.add(p)
for name in ('REMOTE_CONFIRMATION65.json','SUCCESSOR_PARENT_PREPARE01.py','SUCCESSOR_PARENT_DRAFT_PREPARATION01.json','SUCCESSOR_INPUT_PREPARE01.py','SUCCESSOR_INPUT_PREPARE02.py','SUCCESSOR_SOURCE_ADOPT01.py','SUCCESSOR_SOURCE_ADOPTION01.json','SUCCESSOR_PARENT_SOURCE_UNBOUND01.py','SUCCESSOR_POLICY_RECEIVER_PREPARE01.py','SUCCESSOR_POLICY_RECEIVER_PREPARATION01.json','STATE_TOP97_SNAPSHOT01.md','STAGE66_PREPARE01.py'):paths.add(c/name)
rows=[]
for p in sorted(paths):
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size<=4*1024**2;b=p.read_bytes();rows.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
assert sum(r['bytes'] for r in rows)<4*1024**2
manifest=c/'STAGE66_SELECTED_SCOPE01.json';spec=c/'STAGE66_PATHSPEC01.nul'
with manifest.open('x') as w:json.dump({'schema_version':1,'prior_head':'e2610e49de461716bd78e1fbac43a65c42e1b1be','files':rows,'bytes':sum(r['bytes'] for r in rows),'qualification':'source preparation/review only; no final registration, claim, numerical execution or full recovery'},w,sort_keys=True,indent=2);w.write('\n')
with spec.open('xb') as w:w.write(b''.join(r['path'].encode()+b'\0' for r in rows)+str(manifest.relative_to(root)).encode()+b'\0')
subprocess.run(['git','add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],check=True);subprocess.run(['git','diff','--cached','--check'],check=True)
print(json.dumps({'selected_files':len(rows),'selected_bytes':sum(r['bytes'] for r in rows)}))
