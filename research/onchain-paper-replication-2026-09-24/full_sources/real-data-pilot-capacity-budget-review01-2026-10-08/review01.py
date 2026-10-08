import ast,collections,hashlib,json,pathlib
R=pathlib.Path.cwd();H=pathlib.Path(__file__).resolve().parent;F=H.parent
C=F/'real-data-pilot-capacity-selection02-2026-10-08';D=F/'real-data-pilot-diagnostic-composition01-2026-10-08';B=F/'real-data-pilot-retry20-registration01-2026-10-08';OLD=F/'real-data-pilot-retry19-registration01-2026-10-08'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
def bound(ref):
 p=R/ref['path'];assert sha(p)==ref['sha256'];return p
assert sha(C/'MANIFEST01.json')=='2539a9d02e84236492635d9898e9db01658fe245df2c483c3deb6a65e0c3b92f'
for n,v in read(C/'MANIFEST01.json')['files'].items():assert (C/n).stat().st_size==v['bytes'] and sha(C/n)==v['sha256']
co=read(D/'COMPOSITION02.json')
for k in ('budget_proposal','charter','capacity_manifest','kernel'):bound(co[k])
for n in ('real_pilot_storage.py','imported_mcm_identity.py','real_pilot_reservations.py'):
 v=co['files'][n];bound(v['candidate']);bound(v['origin']);assert sha(R/'tradingagents/research/onchain_replication'/n)==v['main_before_sha256']
oldname='eth-paper-real-data-end-to-end-resource-20261008-19';name='eth-paper-real-data-end-to-end-resource-20261008-20'
s=(D/'real_pilot_storage.py').read_text();assert s.count(name)==1
assert s.replace(name,oldname)==(R/'tradingagents/research/onchain_replication/real_pilot_storage.py').read_text()
kold='research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py'
knew=str((C/'imported_kernel.py').relative_to(R))
s=(D/'imported_mcm_identity.py').read_text();assert s.count(knew)==1
assert s.replace(knew,kold)==(R/'tradingagents/research/onchain_replication/imported_mcm_identity.py').read_text()
# Complete literal inverse of kernel changes, not a selected function comparison.
s=(C/'imported_kernel.py').read_text()
s=s.replace("set(policy) in (fields,fields|{'extraction_limit'})","set(policy)==fields",1)
s=s.replace("    if 'extraction_limit' in policy:\n        require(type(policy['extraction_limit']) is int and 0<policy['extraction_limit']<2**63,'explicit finite extraction limit required')\n",'',1)
s=s.replace("    extraction_config=dictionary.config\n    if 'extraction_limit' in policy:\n        require(policy['extraction_limit']>=dictionary.config['maximum_neighborhood_nodes'],'extraction ceiling cannot reduce original capacity')\n        extraction_config=dict(dictionary.config)\n        extraction_config['maximum_neighborhood_nodes']=policy['extraction_limit']\n",'',1)
s=s.replace('local=index.neighborhood(center,extraction_config)','local=index.neighborhood(center,dictionary.config)',1)
assert s==(R/kold).read_text();assert ast.dump(ast.parse(s))==ast.dump(ast.parse((R/kold).read_text()))
# Independent capacity arithmetic from authenticated metadata carriers only.
inputs=read(F/'real-data-pilot-capacity-application01-2026-10-08/INPUTS01.json');graphs=inputs['topology']['graphs'];motifs=inputs['motifs']['representatives'];assert len(graphs)==7 and len(motifs)==32
p=read(C/'pair_limits.json');stage=read(C/'compact_policy.json')['stage_policy'];mcm=read(C/'mcm_policy.json')
entries=max(g['maximum_cardinality']*m['nodes'] for g in graphs for m in motifs);assert entries==8402640
shards=(entries+262144-1)//262144;checkpoint=4*(8*entries+128*shards)+3*65536
assert p['max_checkpoint_bytes']==checkpoint==269097984 and p['max_state_bytes']==32*entries+6357376
assert p['normalization_chunk_entries']==max(max(m['nodes'],g['maximum_cardinality'] if m['nodes']==1 else 2*g['maximum_cardinality']) for g in graphs for m in motifs)
assert p['hardening_buffer_bytes']==max(17*g['maximum_cardinality']*m['nodes']+g['maximum_cardinality']+m['nodes']+16*min(g['maximum_cardinality'],m['nodes']) for g in graphs for m in motifs)
assert mcm['numeric']['extraction_limit']==max(g['maximum_cardinality'] for g in graphs)==350110
oldstage=read(F/'real-data-pilot-finite-reservation-correction01-2026-10-06/metadata01/compact_policy.json')['stage_policy']
for k in ('operations_per_call','calls_per_checkpoint','max_checkpoints','max_total_checkpoints'):assert stage['schedule'][k]==oldstage['schedule'][k]
G=stage['schedule']['max_total_checkpoints'];S=G;N=2;small=16384;large=65536;gc=8*large+3*65536
controls=8*small+N*3*small+G*(gc+4*small)+S*(6*large+small)+(S+N)*3*small
rt=stage['restart_retention'];assert rt['max_control_bytes']==controls
assert rt['max_live_bytes']==controls+rt['max_input_bytes']+N*checkpoint+2*checkpoint
assert rt['max_cumulative_bytes']==controls+rt['max_input_bytes']+G*checkpoint+N*checkpoint
assert rt['max_input_bytes']==220672576 # conditional old metadata bound, expressly unresolved
checks=read(H/'CAPACITY_CHECKS01.json');assert checks['status']=='PASS' and checks['pair_cases']==224
# Budget exact actual closed claim joins.
e=read(B/'EXTENSION_PROPOSED91_01.json');a=read(bound(e['allocation']));prev=read(OLD/'EXTENSION_PROPOSED90_02.json');oldalloc=read(OLD/'CUMULATIVE_ALLOCATION_PROPOSED90_02.json')
gate=read(F/'real-data-pilot-final19-2026-10-08/gate01.json')
assert e['base_family']==prev['base_family']==gate['families']['paper'];assert e['program_id']==prev['program_id'];assert e['initial_experiment']==name
assert e['claims'][:-1]==prev['claims'];assert a['closed_claims']==e['claims'];assert a['identities']==[name]
actual={};ceil=[]
for pth in sorted((R/'research_runs').glob('*/claim.json')):
 c=read(pth)
 if c.get('program_id')!=e['program_id'] or c['experiment']['family']!='paper':continue
 n=c['experiment_id'];terminal=[s for s in ('complete','failed') if (pth.parent/(s+'.json')).exists()];assert len(terminal)==1
 st=terminal[0];t=pth.parent/(st+'.json');body=read(t)
 assert body['experiment_id']==n and body['claim_sha256']==sha(pth) and body['status']==st
 actual[n]={'experiment':n,'claim_sha256':sha(pth),'terminal_status':st,'terminal_sha256':sha(t)};ceil.append(c.get('effective_attempt_budget',51))
assert len(actual)==42 and {x['experiment']:x for x in e['claims']}==actual
assert collections.Counter(x['terminal_status'] for x in actual.values())=={'complete':20,'failed':22};assert max(ceil)==90
assert e['consumed_before']==a['consumed_before']==17+len(actual)==59 and e['cumulative_ceiling']==a['proposed_cumulative_ceiling']==91
assert a['unchanged_pending_allocation']==oldalloc['unchanged_pending_allocation'] and sum(a['unchanged_pending_allocation'].values())==28
assert a['preserved_reserved_preclaim_allowances']==oldalloc['preserved_reserved_preclaim_allowances'] and len(a['preserved_reserved_preclaim_allowances'])==3
assert e['cumulative_ceiling']==59+28+3+1
assert all(a[k]==0 for k in ('refunds','category_transfers','historical_claims_reopened','new_financial_fits'))
assert a['maximum_unique_financial_fits_unchanged']==1420 and name not in gate['experiments'] and not (R/'research_runs'/name).exists()
snapshot=read(B/'ACTUAL_ACCOUNTING_SNAPSHOT01.json');assert snapshot['claim_snapshot']==e['claims'] and snapshot['active_claims']==[];bound(snapshot['proposal'])
charter=bound(co['charter']).read_text();assert name in charter and '1024 completed pair-log comparisons' in charter and 'permanently FAILED' in charter and 'independently `null`' in charter
review={'schema_version':1,'decision':'accepted','extension_sha256':sha(B/'EXTENSION_PROPOSED91_01.json'),'reviewer':'independent scoring_cost agent; exact snapshot and source-only capacity review','scope':'Exact prospective cumulative91 metadata only:42 genuine closed local claims plus17 preserved historical prior,28 unchanged pending,3 unchanged closed preclaim reservations,1 fresh fixed20 diagnostic. All claim/terminal SHA and identities joined, highest adopted90, no refund/transfer/reopen. No source, resource, numerical, whole-capacity or launch admission follows.'}
(H/'EXTENSION91_REVIEW01.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
(H/'CHECKS01.json').write_text(json.dumps({'status':'PASS_NARROW','capacity_cases':224,'actual_local_closed_claims':42,'consumed':59,'ceiling':91,'source_literal_inverses':3,'capacity_manifest_sha256':sha(C/'MANIFEST01.json'),'composition_sha256':sha(D/'COMPOSITION02.json'),'charter_sha256':sha(bound(co['charter'])),'whole_capacity_proven':False,'execution_admitted':False},indent=2,sort_keys=True)+'\n')
print('capacity source, strict identity relocation, kernel inverse and actual91 accounting accepted narrowly')
