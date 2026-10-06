"""Read-only fixed pre-entry seam; no experiment/runtime imports or invocation."""
from pathlib import Path
import ast
import hashlib
import json
import os
import stat
import subprocess

R=Path.cwd()
F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
D=F/'real-data-pilot-final01-2026-10-06'
H=F/'real-data-pilot-final-release-completion01-2026-10-06/preentry-parent01'
N='eth-paper-real-data-end-to-end-resource-20261005-01'
def raw(p):
    p=R/p
    assert p.resolve(strict=True)==p and p.is_file() and p.stat().st_size<=4*1024**2
    return p.read_bytes()
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(name,obj):
    p=H/name
    with p.open('x') as f:f.write(json.dumps(obj,sort_keys=True,indent=2)+'\n')
    return p

release=read(D/'RELEASE_REVIEW01.json')
assert sha(D/'RELEASE_REVIEW01.json')=='f74069c0dfe0bd5b834fea75e391dfc460b4ab7e07e37182d63a0c56a8d6ab3e'
for leaf in ('gate01.json','BINDING01.json','preflight01.py','root_io.py'):
    assert sha(D/leaf)==release['evidence'][str(D/leaf)]
failed=read(D/'ROOT_PRE_ENTRY_FAILED01.json')
prepared=read(D/'LOG_PARENT_PREPARED01.json')
assert failed['actual_outer_root_exit_code']==1 and failed['error_type']=='FileNotFoundError'
assert failed['outer_root_session_id']==13833 and failed['terminal_chunk']=='520c33'
assert failed['original_scientific_identity']==N
assert all(failed[k] is False for k in ('actual_scientific_claim_exists','native_job_started','scientific_attempt_namespace_present'))
prefix=R/'research_artifacts/onchain-paper-replication-2026-09-24'
parent=prefix/'pilot-parent'
assert failed['missing_declared_parent']==prepared['declared_parent']==str(parent)
assert prepared['no_scientific_namespace_created'] is True and prepared['source_or_gate_changed'] is False
s=parent.lstat()
assert parent.resolve(strict=True)==parent and stat.S_ISDIR(s.st_mode)
assert stat.S_IMODE(s.st_mode)==0o700 and s.st_uid==os.getuid()
assert (s.st_dev,s.st_ino,stat.S_IMODE(s.st_mode),s.st_blocks*512)==(prepared['device'],prepared['inode'],prepared['mode'],prepared['allocated_bytes'])
paths=(R/'research_runs'/N,prefix/'runs'/N,prefix/'sources'/N,parent/N,
       R/D/'launch-attempt01.json',R/D/'outer-exit01.json')
assert all(not p.exists() and not p.is_symlink() for p in paths)
units=subprocess.run(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],check=True,capture_output=True,text=True)
assert units.stdout.strip()==''

# Static sequence: the failed parent resolution precedes any reservation/Popen.
tree=ast.parse(raw(D/'root_io.py'))
launch=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='launch_checked')
parent_guard=next(n for n in launch.body if isinstance(n,ast.If) and 'logs.parent.resolve' in ast.unparse(n.test))
reservation=next(n for n in launch.body if isinstance(n,ast.Expr) and '_immutable(here' in ast.unparse(n))
capture=next(n for n in launch.body if isinstance(n,ast.Return))
assert parent_guard.lineno < reservation.lineno < capture.lineno
preflight=ast.parse(raw(D/'preflight01.py'))
resources=next(ast.literal_eval(n.value) for n in preflight.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED_RESOURCES' for t in n.targets))
assert resources['start_reserve_bytes']==9663676416 and resources['disk_floor_bytes']==10737418240
assert resources['memory_max_bytes']==6442450944 and resources['memory_high_bytes']==5368709120
assert resources['reserve_bytes']==3221225472 and resources['wall_seconds']==28800
assert resources['storage_budget']['limits']['max_logical_bytes']==17179869184
assert resources['storage_budget']['limits']['max_allocated_bytes']==21474836480
report={'schema_version':1,'identity':N,'decision':'accepted',
    'scope':'Exact unchanged released Root entry after canonical shared log parent preparation.',
    'classification':'Outer CLI pre-entry failure; no scientific/native attempt or terminal scientific claim.',
    'prior_failure_preserved':ref(D/'ROOT_PRE_ENTRY_FAILED01.json'),
    'parent_preparation':ref(D/'LOG_PARENT_PREPARED01.json'),
    'release':ref(D/'RELEASE_REVIEW01.json'),
    'committed_public_body_proof_reused':ref(D/'RELEASE_COMMITTED_READBACK01.json'),
    'exact_current_source_gate_binding_unchanged':True,
    'parent_current_observation':{'canonical':True,'directory':True,'mode':stat.S_IMODE(s.st_mode),
         'owner_matches':True,'device':s.st_dev,'inode':s.st_ino,'allocated_bytes':s.st_blocks*512},
    'unused_namespaces_observed':[str(p.relative_to(R)) for p in paths],
    'active_or_activating_matching_native_units':0,
    'source_sequence_verified':{'parent_guard_line':parent_guard.lineno,'reservation_line':reservation.lineno,'capture_line':capture.lineno},
    'unchanged_resource_envelope':resources,
    'permitted_next_step':'Root may perform the FIRST actual unused native/scientific launch once through the exact unchanged released entry only if its fresh mandatory preflight succeeds. This is not resuming or relaunching a closed scientific claim.',
    'conditions':['Authenticate final committed release/gate/source/input/binding bodies and effective72 genuine admission.',
       'Recheck unused identity, no competing native job/program claim, original runtime and native limits.',
       'Fresh complete writable union must include the added shared parent and all modeled growth within unchanged16/20GiB ceilings; fresh disk growth plus10GiB floor and RAM>=9GiB are mandatory.',
       'Preserve original outer failure; any subsequent failure remains recorded. No refund, identity reset, cap change or direct worker bypass.'],
    'not_tested':['Original outer command/preflight was not rerun; failed command details rely on preserved Root terminal record and independently checked source sequence.',
       'No fresh RAM/disk/union, Git batch admission, native start, ResearchRun, Owner/Binding, private/data/scientific payload, numerical import or financial result check.'],
    'reviewer_started_experiment':False,'reviewer_modified_registration_or_ledger':False}
review_path=write('REVIEW01.json',report)
manifest_path=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','identity':N,
    'files':[ref(H/'check01.py'),ref(review_path)]})
print(json.dumps({'review':ref(review_path),'manifest':ref(manifest_path),'decision':'accepted'},sort_keys=True))
