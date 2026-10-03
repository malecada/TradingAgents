from pathlib import Path
import hashlib,json,os,stat,subprocess,sys
from flat_checks01 import check,read
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-final-baseline-root-remote-recovery02-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(read(p));pins=J(A/'FLAT_RUN_PINS03.json');terminal=J(A/'FLAT_TERMINAL03.json');flat=Path(terminal['flat_root']);assert flat==A/'flat03';assert terminal['exit']==0 and terminal['recovery_sha256']=='48c24f5b7c015cb902db19afbb2b171edefadb88a3bb10ef86d8815067c8bf34';assert terminal['argv']==pins['argv'];assert H(read(flat/'recovery.json'))==terminal['recovery_sha256']
for label in ('stdout','stderr'):assert H(read(A/('FLAT03.'+label)))==terminal[label+'_sha256']==H(b'')
argv=pins['argv'];assert argv[3:5]==['--mode','recover'];vals=dict(zip(argv[3::2],argv[4::2]));assert vals['--destination']==str(flat);helper=Path(argv[2]);assert H(read(helper))==pins['helper_sha256']=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
review=R.parent/'held-consumer-final-recovery-review04-2026-10-03';assert H(read(review/'REVIEW04.md'))==pins['helper_review_sha256']=='11edd9d352edbcaef1fbf0a8d55778d8ea4cac83611d502efd29da056d448e39';assert H(read(review/'MANIFEST04.json'))==pins['helper_review_manifest_sha256']
assert H(read(helper.parent/'owned_io.py'))=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb';assert H(read(helper.parent/'bounded_git01.py'))=='db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'
qpath=Path(vals['--request']);bundle=Path(vals['--bundle']);assert qpath.is_relative_to(A/'selected') and bundle.is_relative_to(A/'selected');qraw=read(qpath);assert H(qraw)==vals['--request-sha256']=='3d5481584c69034d696276431465064d01788e0fd651bdc8fe7df203bc52bf71';q=json.loads(qraw);assert H(read(bundle/'capture.json'))==vals['--capture-sha256']=='b9f1d20bedb3e9eff6ca7390684c439de29f5eaab062663e8419f2a3b7a40227'
origin=J(A/'REMOTE_RECOVERY02.json');assert H(read(A/'REMOTE_RECOVERY02.json'))=='e4c0d191f87816717e3239c627421d5096e79466f4234a85ed6d4cdaf610ea9d';repo=Path(origin['fresh_git_root']);commit=origin['remote_commit'];assert commit=='d9ebc6cb0be3b3b5f7247ff486e44455136b21ef'
env=dict(os.environ);env.update(GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_TERMINAL_PROMPT='0',GIT_NO_REPLACE_OBJECTS='1')
selected={row['path']:row for row in origin['selected_blobs']};assert len(selected)==137
# Rejoin each of the six fetched request/capture/manifest/archive bodies to actual
# offline original commit:path (never to a donor or a newly synthesized store).
origin_bodies={}
for p in [qpath,bundle/'capture.json',bundle/'capsule-manifest.json',bundle/'external-manifest.json',bundle/'capsule.tar.gz',bundle/'external.tar.gz']:
 rel=p.relative_to(A/'selected').as_posix();row=selected[rel];raw=read(p);assert H(raw)==row['sha256'] and len(raw)==row['bytes'];res=subprocess.run(['git','show',commit+':'+rel],cwd=repo,env=env,capture_output=True,timeout=15);assert res.returncode==0 and len(res.stdout)<=4194304 and res.stdout==raw;origin_bodies[rel]=H(raw)
prior=R.parent/'held-consumer-final-baseline-remote-recovery-review01-2026-10-03';assert H(read(prior/'REVIEW_ORIGIN_AND_FAILURE01.md'))=='7f3c77a6121b65566357773495c5977ef41b344ae4d563c29728a74668956a49'
result=check(flat,bundle,q);assert result['flat_files']==676 and result['roles']['capsule']['regular_bodies']==663 and result['roles']['external']['regular_bodies']==10
r=J(flat/'recovery.json');assert r['request_sha256']==H(qraw)
for role in ('capsule','external'):
 for key in ('instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority'):assert r['results'][role][key] is False
# Recovered unreleased release/request/caller/parser are authenticated flat bodies.
meta=J(flat/'external-metadata.json');mapping=meta['flat_members'];release=J(flat/mapping['release-unreleased01.json']);request=J(flat/mapping['request-unreleased01.json']);assert release['status']=='UNRELEASED-investigation-template' and request['status']=='UNRELEASED-parent-preparation';assert H(read(flat/mapping['launch_success01.py']))=='7a197e2f57db3fff44fce453356d187f62dce5f119125e6814831eb6008f38dc';assert H(read(flat/mapping['held_outcome02.py']))=='95affaa3867b0f50dedc706121b47304126c6def39715133414ef149b9eae153'
# Preservation of real earlier failures; no promotion or deletion.
assert J(A/'FLAT_FAILURE01.json')['exit']==J(A/'FLAT_TERMINAL02.json')['exit']==1;assert not list((A/'flat01').iterdir()) and len(list((A/'flat02').iterdir()))==470 and not (A/'flat02/recovery.json').exists()
assert not os.path.lexists(Path(q['external_root'])/'attempt');cap=Path(q['capsule_root'])
for identity in ('original-import-held-success-20261003-01','original-import-held-publication-failure-20261003-01'):
 for prefix in ('research_runs','fixture_outer','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not os.path.lexists(cap/prefix/identity)
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal() or int(p.name)==os.getpid():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 if any(Path(a.decode('utf8','replace')).name in ('recovery04.py','outer_controller01.py','launch_success01.py') for a in args if a) or b'tradingagents.research.onchain_replication.job' in args:active.append(int(p.name))
assert not active and not any(n in sys.modules for n in ('numpy','torch','scipy'));assert terminal['free_bytes']>=10737418240
members=[]
for p in sorted(flat.iterdir()):
 s=p.lstat();raw=read(p);members.append({'path':p.name,'mode':stat.S_IMODE(s.st_mode),'bytes':len(raw),'sha256':H(raw),'device':s.st_dev,'inode':s.st_ino})
(R/'ACTUAL_FLAT_INVENTORY02.json').write_text(json.dumps({'root':str(flat),'root_mode':448,'members':members},sort_keys=True,indent=2)+'\n')
result.update(schema_version=1,decision='accepted_complete_actual_external_archival_baseline_only',recovery_sha256=H(read(flat/'recovery.json')),origin_receipt_sha256=H(read(A/'REMOTE_RECOVERY02.json')),source04_sha256=H(read(helper)),offline_fetched_commit_body_joins=origin_bodies,original_failures_preserved=True,active_selected_process_pids=active,root_terminal_exit=0,root_terminal_elapsed_seconds=terminal['elapsed_seconds'],native_execution_authorized=False,recovered_git_proved=False,full_later_final_union_recovered=False)
(R/'READBACK02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print('PASS actualfreshflat03:676exactfiles=663+10bodies+2metadata+1receipt;937logicalmembers;allbodyhashes/modesmetadata/canonicalarchives;6offlineoriginbodyjoins;source04/terminal;oldfailurespreserved;noactivejob. ArchivalbaselineONLY.')
