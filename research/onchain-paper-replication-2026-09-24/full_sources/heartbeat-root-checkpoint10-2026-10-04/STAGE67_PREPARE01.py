from pathlib import Path
import datetime,hashlib,json,stat,subprocess
root=Path.cwd();s=root/'research/onchain-paper-replication-2026-09-24';f=s/'full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04';paths=set()
with (c/'STATE_TOP98_SNAPSHOT01.md').open('xb') as w:w.write((s/'STATE.md').read_bytes())
t=(s/'STATE.md').read_text();a=t.index('**TOP98');b=t.index('**',a+2)+2;t=t[:a]+'**TOP99 '+datetime.datetime.now(datetime.timezone.utc).isoformat()+' — successor registration committed; genuine read-only admission passed with34inputs/366sourcepins/allowance20. No numerical claim or launch is active. Complete current preservation draft captured; actual external recovery/release pending.**'+t[b:]
t=t.replace('e2610e49de461716bd78e1fbac43a65c42e1b1be','347429ecc8ee2e1ece6fc15647b7f9a4063b594e').replace('REMOTE_CONFIRMATION65.json','REMOTE_CONFIRMATION66.json')
a=t.index('CAP committed HEAD remains');b=t.index(' No scientific model',a);t=t[:a]+'CAP current/design is `a5bcc943167ad035b45e12ddf9864d46e685b124`;367 tracked/366 admission pins,195 installed bodies. Selected successor gate995d5652 preserves four original definitions and adds one within the same family/extension20.'+t[b:]
a=t.index('Next executable work:');b=t.index('\n\nRoot owns',a)
t=t[:a]+'''Actual progress: source/policy increment was fetched once from actual remote347429ec:12bodies214,532B,46actual reaped Git operations/26.268s, independently accepted recovery proof79acc77d. Root then committed the actual successor gate and caller binding. [Genuine read-only admission](full_sources/heartbeat-root-checkpoint10-2026-10-04/SUCCESSOR_READONLY_ADMISSION01.json) passed in1.3778s, actual ready Admission/current=design/34inputs/effective20/no numerical imports, Owner, Run.start or claim. Independent current gate/cumulative/source-runtime proofs are issued and historical anchors reused.

[Complete current capture](full_sources/financial-wrapper-continuation-successor-current-capture01-2026-10-05/CAPTURE01.json) ran once:CAP839regular/1068typed by nine changed/added regulars plus830accepted unchanged bodies; complete physical Git438logical objects;12actual Parent bodies, frozen review/Root records;506original bodies3,966,494B. Archive3,258,172B2ee08c7a, manifest611ef72a; independently checkede3ec9154. Runtime package bodies/POSIX reconstruction/whole capacity excluded. The actual caller and source/input/runtime-bound preservation draft are captured; draft full_recovery/final_review remain null. The final released envelope references need a separately preserved actual supplement to avoid self-hash cycles.

Next executable action: perform the fresh seven-body current archive/review retrieval once, then fresh flat-byte restore and independent current recovery review. Bind the real proof into final caller/request, obtain exact release, actually preserve/recover final request/review supplement, run genuine preflight, then at most one eligible continuation. Historical interrupt checkpoint,99remaining updates, original model/training/tolerances and3GiB native limits fixed. No successor claim/attempt exists.''' +t[b:]
t=t.replace('[Previous TOP97]','[Previous TOP98]').replace('STATE_TOP97_SNAPSHOT01.md','STATE_TOP98_SNAPSHOT01.md');(s/'STATE.md').write_text(t);paths.add(s/'STATE.md')
for folder in ('financial-wrapper-continuation-successor-review01-2026-10-05','financial-wrapper-continuation-successor-current-capture01-2026-10-05','financial-wrapper-continuation-successor-current-remote01-2026-10-05'):
 for p in (f/folder).rglob('*'):
  if p.is_file() and not p.is_symlink():paths.add(p)
policy=f/'financial-wrapper-continuation-successor-policy-remote01-2026-10-05'
for name in ('REMOTE_RECOVERY01.json','ACTUAL_ROOT_EXIT01.json','ROOT.stdout','ROOT.stderr','SELECTED_BODIES01.json'):paths.add(policy/name)
for name in ('REMOTE_CONFIRMATION66.json','SUCCESSOR_GATE_BUILD01.py','SUCCESSOR_GATE_ADOPTION01.json','SUCCESSOR_PARENT_PRE_SOURCE_BINDING01.py','SUCCESSOR_PROOF_REUSE_UNBOUND01.json','SUCCESSOR_READONLY_ADMISSION01.py','SUCCESSOR_READONLY_ADMISSION01.json','SUCCESSOR_READONLY_ADMISSION01.stdout','SUCCESSOR_READONLY_ADMISSION01.stderr','SUCCESSOR_CURRENT_CAPTURE01.py','SUCCESSOR_CURRENT_CAPTURE_UNCHECKED01.py','SUCCESSOR_CURRENT_CAPTURE01.stdout','SUCCESSOR_CURRENT_CAPTURE01.stderr','SUCCESSOR_CURRENT_RECEIVER_PREPARE01.py','STATE_TOP98_SNAPSHOT01.md','STAGE67_PREPARE01.py'):paths.add(c/name)
rows=[]
for p in sorted(paths):
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size<=4*1024**2;b=p.read_bytes();rows.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
assert sum(r['bytes'] for r in rows)<16*1024**2
manifest=c/'STAGE67_SELECTED_SCOPE01.json';spec=c/'STAGE67_PATHSPEC01.nul'
with manifest.open('x') as w:json.dump({'schema_version':1,'files':rows,'bytes':sum(r['bytes'] for r in rows),'scope':'actual current source/registration/preservation and prior actual policy recovery; no final release or numerical claim'},w,sort_keys=True,indent=2);w.write('\n')
with spec.open('xb') as w:w.write(b''.join(r['path'].encode()+b'\0' for r in rows)+str(manifest.relative_to(root)).encode()+b'\0')
subprocess.run(['git','add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],check=True);subprocess.run(['git','diff','--cached','--check','--',':!*.patch'],check=True)
print(json.dumps({'selected_files':len(rows),'selected_bytes':sum(r['bytes'] for r in rows)}))
