import datetime, hashlib, json, os, shutil, stat, subprocess
from pathlib import Path
root=Path.cwd();s=root/'research/onchain-paper-replication-2026-09-24';f=s/'full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04'
def put(p,raw):
 with p.open('xb') as w:w.write(raw)
def enc(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
head=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
assert head=='b94682059c2d7a739d18db0d299d8c3a0a5019be'
proof=f/'financial-wrapper-continuation-outcome-review01-2026-10-05/FULL_REFUSAL_RECOVERY_PROOF01.json'
assert sha(proof)=='a5357602f130838bbf52fd6fe54288401e91bfd045c96aac73fa128f4be41a42'
mem={k:int(v.split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()) if k in ('MemTotal','MemAvailable')}
selected=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal() or int(p.name)==os.getpid():continue
 try:
  argv=(p/'cmdline').read_bytes().split(b'\0')
 except (OSError,PermissionError):continue
 if any(a==b'tradingagents.research.onchain_replication.job' or a.endswith(b'/genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01/parent01.py') for a in argv):selected.append(int(p.name))
obs={'schema_version':1,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'main_head':head,'memory_bytes':mem,'disk_free_bytes':shutil.disk_usage(root).free,'selected_processes':selected,'qualification':'instantaneous metadata; no launch, lifecycle claim, numerical import or whole capacity proof','verified_refusal_recovery_sha256':sha(proof)}
assert not selected
put(c/'RESTART_OBSERVATION01.json',enc(obs));put(c/'STATE_TOP96_SNAPSHOT01.md',(s/'STATE.md').read_bytes());put(c/'COORDINATION_PRE_RESTART01.md',(f/'parallel-execution-2026-10-02/COORDINATION.md').read_bytes())
old=(s/'STATE.md').read_text();accounting=old[old.index('Accounting:'):old.index('[Previous TOP95]')]
text=f'''# Current replication checkpoint

**TOP97 {obs['observed_utc']} — restart reconciled; no numerical job is active. Seven financial fitting/checkpoint modules are integrated, 45 focused regressions passed, and actual recovery of the reserved continuation refusal is complete.**

Main/local and verified remote HEAD: `{head}` ([confirmation64](full_sources/heartbeat-root-checkpoint10-2026-10-04/REMOTE_CONFIRMATION64.json)). CAP current/design remains `d4c81c0961342bfe4c5771aabbef1d46a14cffb8`, 360 tracked/359 admission pins. No scientific model, configuration, tolerance, budget or native limit changed.

Completed implementation: financial_execution, model_registry, checkpoints, training, replay, run and evaluation were adopted from the independently accepted seven-module candidate. Existing named-profile regressions passed 45/45 in 34.76s, in a 1GiB native ordinary test unit with actual 4MiB file limits, two CPUs and unchanged source pins. [Result](full_sources/heartbeat-root-checkpoint10-2026-10-04/main-financial-integration-native-check01/RESULT01.json). These checks survived the restart and are reused; they do not constitute paper fits or whole-population capacity evidence.

The old continuation identity `financial-wrapper-classification-eager-continue100-compatibility-20261004-01` and its Parent remain permanently reserved/not-admitted. The once-only launch refused before ResearchRun.start because available RAM was 4,812,800B below the fixed 6GiB startup requirement; zero updates and no new checkpoint. Original unknown exits stay null; separate actual Root exit1 and launcher125 remain distinct. Its actual changed-byte capture, eight-body remote retrieval (34 reaped Git operations), and fresh flat-byte recovery are independently accepted in one closed consolidated [review](full_sources/financial-wrapper-continuation-outcome-review01-2026-10-05/MANIFEST01.json), manifest672a7b23, [full recovery proof](full_sources/financial-wrapper-continuation-outcome-review01-2026-10-05/FULL_REFUSAL_RECOVERY_PROOF01.json)a5357602. Installed runtime package bodies, POSIX reconstruction and unrelated empirical stores remain excluded. Original bare, flat, snapshot, CAP and Parent trees are retained. No repeat retrieval or historical review is needed.

[Restart observation](full_sources/heartbeat-root-checkpoint10-2026-10-04/RESTART_OBSERVATION01.json): MemAvailable {mem['MemAvailable']}B; disk free {obs['disk_free_bytes']}B; selected processes absent. This is current eligibility evidence only, not a release or capacity claim.

Next executable work: add the narrowly validated successor identity/source compatibility edge, preserving the original policy and COMPLETE100 reference authority. A literal clone cannot pass the existing policy/reference predicates. Root prepares the exact fresh registration/caller for `financial-wrapper-classification-eager-continue100-resource-successor-20261005-01` under the same family/extension20, then obtains one changed-scope independent review, actual incremental recovery and exact release before at most one eligible launch. Historical interrupt checkpoint, 99 remaining updates, original model/training/tolerances and numerical caps remain fixed. No successor claim or attempt exists yet.

Root owns live integration, registrations/accounting/STATE/Git, external preservation and one numerical launcher. One bounded worker owns a NEW successor source candidate; investigation is complete. See [coordination](full_sources/parallel-execution-2026-10-02/COORDINATION.md). User priority: functional implementation and focused checks; reuse accepted evidence, review changed seams once and preserve only actual new bytes incrementally.

{accounting}[Previous TOP96](full_sources/heartbeat-root-checkpoint10-2026-10-04/STATE_TOP96_SNAPSHOT01.md); [older history](STATE_HISTORY_THROUGH_TOP77_2026-10-05.md).
'''
(s/'STATE.md').write_text(text)
(f/'parallel-execution-2026-10-02/COORDINATION.md').write_text('''# Current parallel coordination

Read the [latest study checkpoint](../../STATE.md) for evidence, accounting and next safe action. Root alone owns live Main/CAP/Parent/Git, registration, STATE, actual external preservation and one native numerical launcher.

- `continuation_successor_admission`: bounded read-only investigation complete; no live edits.
- `continuation_successor_implementation`: owns only NEW financial-wrapper-continuation-successor-source01-2026-10-05; implements the finite compatibility edge and focused nonnumerical regressions.

Previous integration and refusal-outcome reviews are closed. No numerical job is active. The old continuation Parent and identity are permanently reserved; never relaunch. Reuse accepted immutable evidence and review changed seams once.
''')
print(json.dumps(obs,sort_keys=True))
