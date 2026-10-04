from pathlib import Path
import ast,hashlib,json,os,stat,sys
D=Path(__file__).resolve().parent;B=D.parent
H=lambda b:hashlib.sha256(b).hexdigest()
def save(p,o):p.write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
lineage=[]
for dirname,pin in [('financial-wrapper-complete100-failed-preservation-tooling03-2026-10-04','dc698101a432dff3ac745c457558d654850355f150a1d4ab328e04f586356828'),('financial-wrapper-compatibility-operational-delta-root-remote-failed-outcome-review02-2026-10-04','8a1f8907883936d89baac1b2b076ebe45e1323e5c735dfd8cddd3c3e8e99453e')]:
 root=B/dirname;body=(root/'MANIFEST01.json').read_bytes();assert H(body)==pin;m=json.loads(body)
 for r in m['members']:
  p=root/r['path'];assert p.is_relative_to(root) and '..' not in Path(r['path']).parts;s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
  if r['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256']
  elif r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  elif r['kind']=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==r.get('target',r.get('link_target'))
  else:raise AssertionError(r)
 lineage.append({'root':str(root),'manifest_sha256':pin,'authenticated_members':len(m['members'])})
 hist=D/('historical-source03' if 'tooling03' in dirname else 'historical-failed-remote02');hist.mkdir()
 if 'tooling03' in dirname:
  (hist/'MANIFEST01.json').write_bytes(body)
 else:
  for r in m['members']:(hist/r['path']).write_bytes((root/r['path']).read_bytes())
  (hist/'MANIFEST01.json').write_bytes(body)
save(D/'AUTHENTICATION01.json',{'lineages':lineage,'total_authenticated_members':sum(x['authenticated_members'] for x in lineage)})
s=(D/'watch.original03.py').read_text();t=(D/'watch01.py').read_text();inv=json.loads((D/'SOURCE_INVERSE01.json').read_text());assert t.count(inv['new_segment'])==1 and t.replace(inv['new_segment'],inv['old_segment'])==s
assert H(s.encode())==inv['old_sha256'] and H(t.encode())==inv['new_sha256']
a=ast.parse(s);b=ast.parse(t)
assert [ast.dump(x) for x in a.body if not isinstance(x,ast.FunctionDef) or x.name!='census']==[ast.dump(x) for x in b.body if not isinstance(x,ast.FunctionDef) or x.name!='census']
for n in ('recover01.py','utilities/owned_io.py'):assert (D/n).read_bytes()==(B/'financial-wrapper-complete100-failed-preservation-tooling03-2026-10-04'/n).read_bytes()
cs=[json.loads((D/f'CONTROLS0{i}.json').read_text()) for i in (1,2)];assert len(cs[0])==34 and len(cs[1])==10 and all(x[-1]['name']=='complete' for x in cs)
assert all((D/f'CONTROLS0{i}.stderr').read_bytes()==b'' for i in (1,2))
h=json.loads((D/'historical-failed-remote02/FAILED01.json').read_text());assert H((D/'historical-failed-remote02/FAILED01.json').read_bytes())=='7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a'
report='''# Finite directory-publication retry scheduling candidate04

Status: prepared for independent source-only review. No adoption, registration, release, financial claim, external recovery, or numerical authority is issued.

The only candidate source change is in `watch01.py:census`: after a caught `ChangingTree` or `FileNotFoundError`, wait a fixed 0.100 seconds before either of the two remaining complete attempts. The existing three-attempt ceiling is unchanged. A monotonic check refuses before waiting if the entire wait cannot fit inside the original five-second deadline; another check refuses after the wait. No wait occurs after attempt three. Non-retriable exceptions and fatal exceptions remain immediate. This is an explicitly declared operational scheduling deviation motivated by genuine publication churn; it is not a scientific-method change or a resource-cap extension.

The literal inverse reproduces source03 cd2200b071cf14c8191c7b7e95ee660b6bc9a10c49a6de252e77f9832ede8673. Every other AST node, the entire census implementation, and all POLICY values are unchanged. Receiver source9ddc59dd and owned-IO source09d1fbcc are literal copies. Fixed limits remain 64 MiB logical, 96 MiB allocated, 4 MiB per regular file, 32768 members, depth32, 10 GiB observed disk floor, five seconds, and 8192 samples. Both observed regular extents remain included by their maximum. Directory signatures, device/type/path/mode/link/identity and full sampled namespace rejoin remain required; no pending-name exemption is introduced.

CONTROLS01 and CONTROLS02 retain42 substantive control rows and two completion markers. Three pairs use a genuine publisher thread, real directory creation, and actual read-endpoint lstat results: original source exhausts three attempts; successor completes attempt two after the pause and counts the new directory. These are bounded owned reproductions, not reconstructed historical events. Additional controls cover a vanished enumerated body, publication during real iterator close, persistent churn, directory-mode and inode replacement, file growth/shrink endpoint maxima, aggregate growth, all resource/type refusal branches, and the8192 ceiling. The floor and reduced capacities use explicitly synthetic readback or lower test caps; no operational cap was raised. Fake-clock boundary controls cover insufficient remaining time, sleep overshoot, exact two-wait ceiling, immediate stable success, and original fatal objects.

An actual local tiny bare Git initialization passes through the unchanged receiver's real subprocess, pipe limit readback, monitoring, and cleanup. The child reports hard/soft RLIMIT_FSIZE=[4194304,4194304] and reaps0. Three additional genuine local Git children receive a watch failure after their real limit readback; all are killed and reaped-9, with exact original fatal/limit exception objects, empty cleanup-failure lists, balanced parent descriptors, and absent observed PID/process groups. These local controls never call recovery entry/main or remote Git operations. Actual iterator cleanup controls close the real descriptor before a secondary close exception and preserve the first fatal object.

Original source03 manifest177 members and the historical failed-remote02 review13 members are independently byte/type/mode authenticated in AUTHENTICATION01. Historical FAILED7491cc3 is copied literally with its raw trace, readback and review. Root-remote02 remains permanently failed: original outer exit1; init observed exit null; separately reaped0; no remote-success or flat-recovery outcome. The exact historical changed path, signature component and earlier discarded attempt exceptions were not recorded and remain unknown.

Scope limits: the 100 ms schedule helps the reproduced finite publication burst but cannot guarantee progress under arbitrary churn. The deadline is checked in user space; sleep/OS scheduling can overshoot, which is refused before the next attempt, and it is not a hard real-time bound. The returned `seconds` field retains its original meaning: elapsed time of the accepted final sample, not total retry/wait elapsed time; control records separately retain outer elapsed time. Namespace and extent observations remain sampled metadata, not continuous atomicity, immutable bytes, a kernel aggregate quota, or full-capacity validation. No numerical AST was edited or imported; financial timing/returns/fees/funding/exposure and scientific outcomes were not tested. Genuine remote preservation, actual recovery and any future final Parent/caller/source-policy binding remain Root-owned and pending.
'''
(D/'REPORT01.md').write_text(report)
save(D/'MACHINE01.json',{'schema_version':1,'decision':'PREPARED_FOR_INDEPENDENT_SOURCE_ONLY_REVIEW','watch_sha256':H(t.encode()),'original_watch_sha256':H(s.encode()),'recover_sha256':H((D/'recover01.py').read_bytes()),'owned_io_sha256':H((D/'utilities/owned_io.py').read_bytes()),'source_inverse_sha256':H((D/'SOURCE_INVERSE01.json').read_bytes()),'control_rows':44,'substantive_control_rows':42,'complete_attempt_ceiling':3,'delay_seconds':0.1,'delay_count_ceiling':2,'whole_deadline_seconds':5,'historical_failed_sha256':H((D/'historical-failed-remote02/FAILED01.json').read_bytes()),'historical_changed_path':None,'historical_changed_signature_component':None,'actual_recovery':None,'source_adoption':None,'release':None,'admission':None,'native':None,'research_claim':None,'report_sha256':H((D/'REPORT01.md').read_bytes()),'authentication_sha256':H((D/'AUTHENTICATION01.json').read_bytes()),'no_network':True,'no_actual_recovery_entry':True})
# Typed, non-following seal includes retained negative FIFO/link/hardlink fixtures.
rows=[]
def walk(p):
 for x in sorted(p.iterdir()):
  if x==D/'MANIFEST01.json':continue
  s=x.lstat();r={'path':str(x.relative_to(D)),'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):r['kind']='directory';rows.append(r);walk(x)
  elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=H(x.read_bytes()),nlink=s.st_nlink);rows.append(r)
  elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(x));rows.append(r)
  elif stat.S_ISFIFO(s.st_mode):r.update(kind='fifo');rows.append(r)
  else:raise AssertionError(x)
walk(D);save(D/'MANIFEST01.json',{'schema_version':1,'root_mode':stat.S_IMODE(D.stat().st_mode),'members':rows,'negative_special_and_hardlink_fixtures_retained':True})
print(json.dumps({n:H((D/n).read_bytes()) for n in ('watch01.py','MACHINE01.json','REPORT01.md','MANIFEST01.json')}));print(json.dumps({'members':len(rows),'regular_files':sum(r['kind']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows)}))
