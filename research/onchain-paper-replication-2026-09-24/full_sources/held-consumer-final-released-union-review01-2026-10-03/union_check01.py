from pathlib import Path
import ast,hashlib,json,os,stat,sys,time,types
from flat_checks01 import read,check
R=Path(__file__).resolve().parent;B=R.parent;MAIN=B.parents[2];A=B/'held-consumer-final-released-scope-root-remote-recovery01-2026-10-03';D=B/'held-consumer-final-released-scope-root-capture01-2026-10-03'
H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(read(p));pins=J(A/'FLAT_RUN_PINS01.json');term=J(A/'FLAT_TERMINAL01.json');flat=A/'flat01';receipt=J(flat/'recovery.json')
assert term['actual_child_exit']==0 and term['actual_output_files']==689 and term['pid_absent'] is True and not (Path('/proc')/str(term['actual_pid'])).exists()
assert H(read(flat/'recovery.json'))==term['recovery_sha256']=='8b5eb6d58e4e422b38f327bd95056df34780c19fe1d65bed7a4cbfa0d6855371'
assert term['root_launch_hold'] is True and term['genuine_run_or_native_started'] is False
for label in ('stdout','stderr'):assert H(read(A/('FLAT01.'+label)))==term[label+'_sha256']==H(b'')
argv=pins['argv'];assert argv[1]=='-B' and argv[3:5]==['--mode','recover'];vals=dict(zip(argv[3::2],argv[4::2]));assert vals['--destination']==str(flat)
helper=Path(argv[2]);assert H(read(helper))==pins['helper_sha256']=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
assert H(read(B/'held-consumer-final-recovery-review04-2026-10-03/REVIEW04.md'))==pins['helper_review_sha256']=='11edd9d352edbcaef1fbf0a8d55778d8ea4cac83611d502efd29da056d448e39'
origin=J(A/'REMOTE_RECOVERY03.json');assert H(read(A/'REMOTE_RECOVERY03.json'))==pins['remote_recovery_sha256']==J(R/'ORIGIN_READBACK01.json')['receipt_sha256']
qpath=Path(vals['--request']);bundle=Path(vals['--bundle']);assert qpath.is_relative_to(A/'selected') and bundle.is_relative_to(A/'selected')
q=J(qpath);assert H(read(qpath))==vals['--request-sha256']=='660a715bc4da9bfd93e4076cee4d82730301024b9fa95668c8182a48d9ac2061';assert H(read(bundle/'capture.json'))==vals['--capture-sha256']=='122706bfcd5cf8eaaecc31b7230a0553d804606fad4db4d86a74f136dbe27408'
selected={x['path']:x for x in origin['selected_blobs']}
for p in (qpath,*bundle.iterdir()):
 rel=p.relative_to(A/'selected').as_posix();assert rel in selected and len(read(p))==selected[rel]['bytes'] and H(read(p))==selected[rel]['sha256']
result=check(flat,bundle,q);assert result['flat_files']==689 and result['roles']['capsule']['members']==925 and result['roles']['external']['members']==25
maps={role:J(flat/(role+'-metadata.json'))['flat_members'] for role in ('capsule','external')}
C=Path(q['capsule_root']);P=Path(q['external_root'])
# Every recovered opaque body, rather than only the documents used below, joins
# current original inventory. Directory metadata and full current roster checked.
for role,root in (('capsule',C),('external',P)):
 m=q[role+'_manifest'];assert stat.S_IMODE(root.lstat().st_mode)==m['root_mode'];expected={r['path']:r for r in m['members']};seen=set()
 for parent,dirs,files in os.walk(root,followlinks=False):
  for name in dirs+files:
   p=Path(parent)/name;n=p.relative_to(root).as_posix();seen.add(n);s=p.lstat();row=expected[n];assert p.resolve()==p and stat.S_IMODE(s.st_mode)==row['mode']
   if row['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
   else:assert read(p)==read(flat/maps[role][n])
 assert seen==set(expected)
old=J(B/'held-consumer-final-baseline-root-capture01-2026-10-03/REQUEST01.json');assert q['capsule_manifest']==old['capsule_manifest'];oldrows={r['path']:r for r in old['external_manifest']['members']};newrows={r['path']:r for r in q['external_manifest']['members']};assert all(newrows[n]==r for n,r in oldrows.items());delta=sorted(set(newrows)-set(oldrows));assert len(delta)==13 and delta==J(D/'PRECAPTURE_SCOPE01.json')['added_files']
def recovered(n):return read(flat/maps['external'][n])
request=json.loads(recovered('request-final01.json'));release=json.loads(recovered('release-final01.json'));assert H(recovered('request-final01.json'))=='bc482b1196e691d8a0a06e3c866a11877b8cf8556ef407e5d3da72743412e4d4';assert H(recovered('release-final01.json'))=='eeac08eef932caccea1346149ec8a7f7473de03e774e0285634a74ae71b8774f'
for row in [request['caller'],request['semantic_parser'],request['release'],*request['evidence'].values()]:assert H(recovered(row['path']))==row['sha256']
proof_fields=('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256')
contract=H(json.dumps({k:v for k,v in release.items() if k not in proof_fields},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode());assert contract=='17e513bb0fa4ae667c822d80118578ae487138a3c6ad1cdd1123b7d68c435110'
for field,key in zip(proof_fields,('release_review','external_recovery','external_recovery_review')):assert release[field]==request['evidence'][key]['sha256']
baseline=json.loads(recovered(request['evidence']['external_recovery']['path']));assert baseline['later_appended_changed_proof_release_request_bodies_recovered'] is False and baseline['full_final_union_accepted'] is False
# Every supporting body directly referenced by the genuine baseline decision
# is independently selected, remotely fetched and checked by origin_check01.
for row in baseline['refs'].values():assert row['path'] in selected and selected[row['path']]['sha256']==row['sha256'] and selected[row['path']]['bytes']==row['bytes']
# Execute only genuine original Parent03 prepared/read-only branch. This is not
# a capability/claim, no native launch, no synthetic proof and no recovered code replay.
os.environ.update(GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_NO_REPLACE_OBJECTS='1',GIT_TERMINAL_PROMPT='0')
caller=read(P/'launch_success01.py');assert caller==recovered('launch_success01.py') and H(caller)=='7a197e2f57db3fff44fce453356d187f62dce5f119125e6814831eb6008f38dc'
m=types.ModuleType('_independent_final_parent');m.__file__=str(P/'launch_success01.py');exec(compile(caller,m.__file__,'exec'),m.__dict__);os.chdir(C);prepared=m.prepared(P/'request-final01.json',H(recovered('request-final01.json')));os.chdir(R)
assert prepared[0]==request and prepared[1]==release and prepared[2]==H(recovered('release-final01.json')) and not any(n in sys.modules for n in ('numpy','torch','scipy'))
# Exact sole root argv derived from actual source interface, never invoked.
command=[str(MAIN/'.venv/bin/python'),'-B',str(P/'launch_success01.py'),'--request',str(P/'request-final01.json'),'--request-sha256',H(recovered('request-final01.json')),'--launch']
assert argv[0]==command[0] and not os.path.lexists(P/'attempt')
for case in release['cases'].values():
 assert case['experiment']['parent'] is None and len(case['experiment']['inputs'])==33 and len(case['experiment']['outputs'])==6
 for pref in ('research_runs','fixture_outer','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not os.path.lexists(C/pref/case['identity'])
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal() or int(p.name)==os.getpid():continue
 try:args=(p/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 if b'tradingagents.research.onchain_replication.job' in args or any(Path(a.decode('utf8','replace')).name in ('launch_success01.py','outer_controller01.py','recovery04.py') for a in args if a):active.append(int(p.name))
assert not active
result.update(schema_version=1,decision='accepted_actual_final950_recovered_union_and_exact_request_fresh_root_eligibility_required',remote_commit=origin['remote_commit'],origin_receipt_sha256=H(read(A/'REMOTE_RECOVERY03.json')),recovery_sha256=H(read(flat/'recovery.json')),flat_terminal_sha256=H(read(A/'FLAT_TERMINAL01.json')),request_sha256=H(recovered('request-final01.json')),release_sha256=H(recovered('release-final01.json')),contract_sha256=contract,old_capsule925_and_parent12_preserved=True,parent_added_regular_bodies=13,current_original_readonly_prepared_passed=True,numerical_imports=False,original_claims_or_units_started=0,active_selected_process_pids=active,root_launch_command=command,root_launch_cwd=str(C),fresh_original_eligibility_still_required=True,dependent_failure_launch_not_authorized=True)
(R/'UNION_READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
