from pathlib import Path
import json,hashlib,stat
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');C=F/'pilot40-parent-accounting-continuation-candidate-2026-10-12';D=F/'pilot40-prefix-inputs-2026-10-12'
h=lambda b:hashlib.sha256(b).hexdigest();body=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
c=json.loads((C/'EXACT_CONTRACT03.json').read_text());roles=json.loads((D/'REGISTERED_ROLE_MAP.json').read_text());a=json.loads((D/'DERIVED_ACCOUNTING.json').read_text());draft=json.loads((D/'MANIFEST_FIELDS_DRAFT.json').read_text());evidence={}
assert len(roles)==127 and len(set(r['path'] for r in roles.values()))==127
for role,r in roles.items():
 p=Path(r['path']);s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_size==r['bytes']<=32*1024**2
 raw=p.read_bytes();assert h(raw)==r['sha256'];evidence[str(p)]=h(raw)
assert a['format']==c['format'] and a['parent_experiment']==c['parent'] and a['parent_claim_sha256']==c['claim_sha256'] and a['parent_failed_sha256']==c['failed_sha256']
assert a['spent_counters']==c['costs'] and a['retained_partial_work']=={k:0 for k in c['costs']} and all(type(v)is int for d in ('spent_counters','retained_partial_work') for v in a[d].values())
assert a['preserved_unknowns']==['telemetry','cache','transport','outer_disposition']
for k,v in c['evidence'].items():assert a['evidence'][k]['sha256']==v['sha256'] and roles[a['evidence'][k]['role']]['path']==v['path']
for p,sha in c['sources'].items():assert a['source_bodies'][p]['sha256']==sha
for i,hashes in enumerate(c['batches']):
 assert [x['sha256'] for x in draft['batches'][i]]==hashes
 assert h((D/f'origin-{i:02d}.bin').read_bytes())==hashes[3]
 pending=json.loads(Path(roles[draft['batches'][i][0]['role']]['path']).read_text());assert pending['workload_sha256'] in draft['descriptors']
 assert h(body(draft['descriptors'][pending['workload_sha256']]))==pending['workload_sha256']
assert draft['ready_roles']==127 and draft['total_distinct_roles_if_no_existing_aliases']==131 and len(draft['additional_required_roles'])==4 and all(x is None for x in draft['additional_required_roles'].values())
assert draft['status']=='UNREVIEWED_NOT_RELEASED' and draft['original_outputs_modified'] is False and draft['full_graph_completion_proved'] is False
assert draft['parent_accounting']['sha256']==h((D/'DERIVED_ACCOUNTING.json').read_bytes())
for p in D.iterdir():evidence[str(p)]=h(p.read_bytes())
assert len(list(D.iterdir()))==19
print(json.dumps({'status':'PASS_actual_generated_metadata_only','ready_roles':127,'output_files':19,'future_authority_roles_null':4,'all16_six_body_refs_match_fixed_original_contract':True,'evidence':evidence,'builder_rerun':False,'registration_admission_or_recovery_claim':False},indent=2))
