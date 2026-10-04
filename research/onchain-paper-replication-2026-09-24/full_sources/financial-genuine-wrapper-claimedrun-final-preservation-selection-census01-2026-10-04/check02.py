import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;checks=[]
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
rows=load(H/'CANDIDATE_ROWS01.json')['rows'];by={r['path']:r for r in rows};ck(len(by)==len(rows) and list(by)==sorted(by),'all candidate paths sorted unique');ck(all(r['bytes']<=4194304 for r in rows),'every observed regular <=4MiB');core=load(H/'CURRENT_CORE_ROWS01.json')['rows'];ck(len(core)==117 and sum(r['bytes'] for r in core)==22672976,'exact mandatory current core')
roles=load(H/'ROLE_SUMMARY01.json');ck(roles['required_transport_source325_supplement']['regular_paths']==6,'six immutable supplemental bodies');ck(roles['old_failed_exact8_outside_union']['regular_paths']==8,'eight failed support bodies');ck(roles['complete_actual_admission_review']['regular_paths']==5,'complete actual admission five file tree');ck(sha(B/'financial-genuine-wrapper-claimedrun-actual-admission-review01-2026-10-04/MANIFEST01.json')=='24e6451d2a9c5ec516b99ca95bb477567e5f9ef5d13adef3bb41c0633b93e5c7','actualadmission5 seal');ck(sha(B/'financial-genuine-wrapper-claimedrun-actual-admission-review01-2026-10-04/INDEPENDENT_SOURCE_INPUT_RUNTIME01.json')=='059232d0f7fc8922cee526a1bd30fef2ecb51ee17103284bcaac18c77e77641c','genuine missing-before proof included');ck(roles['actual_final11_shards']['regular_paths']==22,'eleven paired archive manifests');ck(roles['complete_witness_exporter_preparation02']['regular_paths']==123,'complete exporter123regular');ck(sum(v['regular_paths'] for k,v in roles.items() if k.startswith('future_witness_source_'))==2302,'fullfive2302regular paths retained')
reuse=load(H/'EXPLICIT_REUSE_CANDIDATES01.json')['mapping'];target={r['path'] for r in rows if {'complete_witness_exporter_preparation02','current_witness_exporter_independent_review02'}&set(r['roles'])};ck({r['original_path'] for r in reuse}==target and len(reuse)==len(target)==316,'complete exporter original paths in explicit mapping')
for r in reuse:
 original=by[r['original_path']];ck((r['bytes'],r['sha256'],r['original_mode'])==(original['bytes'],original['sha256'],original['mode']),'original byte/mode preserved')
 if r['exact_byte_source']['kind'] in ('selected_current_core_exact_body','additional_raw_exact_body_representative'):
  donor=by[r['exact_byte_source']['path']];ck((r['bytes'],r['sha256'])==(donor['bytes'],donor['sha256']),'exact existing raw donor match')
# Authenticate final exporter source-review seal when actually observed; preserve earlier unknown status.
p=B/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-review02-2026-10-04';m=load(p/'MANIFEST01.json');ck(sha(p/'MANIFEST01.json')=='d0bd935a4f693f56dd5b43a7a4b5f3f9463bdf7afee29995b61aa9ba44016c3f','actual observed completed reviewer seal');typed=load(H/'COMPLETE_TYPED_TREES01.json')['current_witness_exporter_independent_review02']['members'];actual={r['path']:r for r in typed if r['path'] not in ('.','MANIFEST01.json')};ck(set(actual)=={r['path'] for r in m['members']},'full407 reviewer sealed entries')
for r in m['members']:
 a=dict(actual[r['path']]);ck(a==r,'review sealed member '+r['path'])
summary=load(H/'SUMMARY01.json');summary['exporter_review_final_seal']={'path':str(p/'MANIFEST01.json'),'sha256':sha(p/'MANIFEST01.json'),'sealed_members':407,'regular_files_including_manifest':193,'regular_bytes':17470329};summary['updated_from_unknown_only_after_actual_seal_verification']=True;summary['snapshot_roles_unchanged_since_initial_census']=True
(H/'SUMMARY02.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n');(H/'CHECKS01.json').write_text(json.dumps({'checks':len(checks),'check_names':checks,'no_recovery_or_selection_executed':True},sort_keys=True,indent=2)+'\n');print('PASS',len(checks))
