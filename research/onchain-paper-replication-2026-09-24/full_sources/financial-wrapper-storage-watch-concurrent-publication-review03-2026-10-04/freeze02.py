from pathlib import Path
import json,hashlib,stat,os
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';O=F/'financial-wrapper-storage-watch-concurrent-publication-review03-2026-10-04';A=F/'financial-wrapper-storage-watch-concurrent-publication-correction03-2026-10-04'
h=lambda b:hashlib.sha256(b).hexdigest()
assert (O/'setup01.py').read_bytes()==Path('/tmp/review_storage03_setup.py').read_bytes()
replays=[]
for p in sorted(O.glob('replay-*')):
 d=json.loads((p/'stdout.json').read_bytes());replays.append({'script':p.name,'rows':d['cases'] if 'cases' in d else len(d['results']),'returncode':json.loads((p/'exit.json').read_bytes())['returncode'],'stdout_sha256':h((p/'stdout.json').read_bytes()),'stderr_sha256':h((p/'stderr.txt').read_bytes())})
assert sum(x['rows'] for x in replays)==105
ind=json.loads((O/'INDEPENDENT01.out').read_bytes())
# Final source-manifest rejoin without changing or rerunning author evidence.
m=json.loads((A/'MANIFEST01.json').read_bytes());current=[]
for x in m['members']:
 p=A/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode']
 if x['kind']=='file':assert h(p.read_bytes())==x['sha256'] and s.st_size==x['bytes']
 current.append(x['path'])
assert sorted(current)==sorted(str(p.relative_to(A)) for p in A.rglob('*') if p.name!='MANIFEST01.json')
read={'schema_version':1,'source_sha256':h((A/'workflow_storage.py').read_bytes()),'author_manifest_sha256':h((A/'MANIFEST01.json').read_bytes()),'author_members':len(current),'replayed_rows':105,'replays':replays,'independent_rows':ind['cases'],'final_author_scope_unchanged':True,'literal_inverse_and_other_ast':True,'actual_execution':'stdlib tiny owned files and descriptors only','no_project_imports':True}
(O/'READBACK01.json').write_text(json.dumps(read,indent=2)+'\n')
report='''# Independent storage-watch correction03 review

SOURCE ONLY ACCEPTED. The exact candidate 91e21c525a156cc8c25877ac35f0308896a1a0d1e6279d5aecf91d7e02567780 corrects the inherited fatal diagnostic ordering. The complete author manifest was authenticated twice, including literal types, modes, file sizes/hashes and membership. The inverse reconstructs every correction02 byte; only StorageWatch.check and StorageWatch._check diagnostic branches differ. Other AST, nested cleanup, census, fixed limits and sampled namespace rejoin remain unchanged. The original bf52 source copy is retained and pinned in AUTHENTICATION01.

All 105 final author rows were independently executed in fresh owned directories, retaining the actual old-source counterexamples and stderr. These are replications of author controls, not independent designs. An additional 20 independently written cases exercised real link/fsync/unlink publication, terminal publication over-limit, three-level real descriptor traversal with KeyboardInterrupt/MemoryError/SystemExit primaries and ordinary/fatal close errors, strict policy field types, four terminal limits and final FD census. Every selected primary retained object identity and all actual cleanup error objects; each owned descriptor closed once, no fatal body retry. All four observed caps remained terminal. Complete raw stdout, stderr, scripts and fixtures remain available.

The fatal guard precedes overridable cause/context diagnostics. Protected annotation cannot replace the already-selected original fatal. Existing nested cleanup accumulation is unchanged. Ordinary failures retain diagnostic/no-retry behavior. The publication event legitimately changed the namespace and was fully recounted on the second bounded census; no pending filename is ignored.

This is finite sampled metadata enforcement. Existing same-tick late-publication limitations remain; no atomic snapshot, immutable byte proof, continuous quota, writer exclusion, blocked-syscall preemption or whole-fit capacity is claimed. Hostile arbitrary asynchronous process behavior is outside these bounded controls. The original scientific source, epoch count, batch size, tolerance, CPU and native resource limits were not changed or executed. This source acceptance does not admit source integration, checkpoint provenance migration, allowance changes, recovery, a new identity or a native launch. Three permanently failed claims and all prior withheld candidates remain immutable.
'''
assert ind['cases']==20
(O/'REPORT01.md').write_text(report)
machine={'schema_version':1,'decision':'ACCEPTED_SOURCE_ONLY_STORAGE_WATCH_CORRECTION03','source_sha256':read['source_sha256'],'author_manifest_sha256':read['author_manifest_sha256'],'readback_sha256':h((O/'READBACK01.json').read_bytes()),'report_sha256':h((O/'REPORT01.md').read_bytes()),'author_rows_replayed':105,'independent_control_rows':20,'literal_inverse':True,'all_other_ast_equal':True,'numerical_authority':False,'source_adoption_authority':False,'recovery_authority':False,'continuous_filesystem_immunity':False,'remaining_material_source_findings':[]}
(O/'MACHINE01.json').write_text(json.dumps(machine,indent=2)+'\n')
rows=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();row={'path':str(p.relative_to(O)),'mode':stat.S_IMODE(s.st_mode),'links':s.st_nlink}
 if stat.S_ISREG(s.st_mode):row.update(kind='file',bytes=s.st_size,sha256=h(p.read_bytes()))
 elif stat.S_ISDIR(s.st_mode):row.update(kind='directory')
 elif stat.S_ISLNK(s.st_mode):row.update(kind='symlink',target=os.readlink(p))
 else:raise AssertionError(str(p))
 rows.append(row)
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'manifest_self_excluded':True,'members':rows},indent=2)+'\n')
print(json.dumps({'directory':str(O),'members':len(rows),'MANIFEST01':h((O/'MANIFEST01.json').read_bytes()),'MACHINE01':h((O/'MACHINE01.json').read_bytes()),'REPORT01':h((O/'REPORT01.md').read_bytes())}))
