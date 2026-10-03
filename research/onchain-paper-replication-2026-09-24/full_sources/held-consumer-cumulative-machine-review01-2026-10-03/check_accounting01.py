from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;F=H.parent;P=F/'held-consumer-cumulative-admission-preparation02-2026-10-03';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-05/source')
sha=lambda b:hashlib.sha256(b).hexdigest()
ext_raw=(P/'cumulative-extension04-proposal.json').read_bytes();alloc_raw=(P/'successor-allocation04-proposal.json').read_bytes()
assert sha(ext_raw)=='b1d56965524c870c3233e828cc94f28402c4d9b0cffe82f4d87bf090cbe3ce1c';assert sha(alloc_raw)=='7f882018f3d34bbd98a4ac1c1498e25fc3f4d577309832c87a98455e229c7120'
e=json.loads(ext_raw);a=json.loads(alloc_raw);assert e['allocation']=={'path':'successor-allocation04-proposal.json','sha256':sha(alloc_raw)}
assert e['base_family']['attempt_budget']==2 and e['base_family']['prior_attempts']==0 and e['base_family']['mechanism_id']=='original-dictionary-import-engineering-v1'
assert e['program_id']==a['program_id']=='original-dictionary-import-engineering-2026-10-02'
assert len(e['claims'])==len({r['experiment'] for r in e['claims']})==4
assert {p.name for p in (S/'research_runs').iterdir()}=={r['experiment'] for r in e['claims']}
rows=[]
for row in e['claims']:
 d=S/'research_runs'/row['experiment'];cb=(d/'claim.json').read_bytes();tb=(d/'failed.json').read_bytes();c=json.loads(cb);t=json.loads(tb)
 assert sha(cb)==row['claim_sha256'] and sha(tb)==row['terminal_sha256'] and row['terminal_status']==t['status']=='failed'
 assert t['claim_sha256']==sha(cb) and t['experiment_id']==c['experiment_id']==row['experiment']
 assert not (d/'complete.json').exists() and c['family']==e['base_family'] and c['program_id']==e['program_id']
 assert (P/'prior_claims'/d.name/'claim.json').read_bytes()==cb and (P/'prior_claims'/d.name/'failed.json').read_bytes()==tb
 actual={p.name for p in (d/'outputs').iterdir()};assert actual==set(t['output_sha256'])
 for n,pin in t['output_sha256'].items():assert sha((d/'outputs'/n).read_bytes())==pin
 rows.append({'identity':d.name,'claim_sha256':sha(cb),'failed_sha256':sha(tb),'source':c['source'],'effective_budget':c['effective_attempt_budget'],'retained_outputs':sorted(actual),'missing_outputs':sorted(set(c['experiment']['outputs'])-actual)})
assert [r['effective_budget'] for r in rows]==[2,3,4,5] and [len(r['retained_outputs']) for r in rows]==[4,4,2,1]
assert e['consumed_before']==a['closed_before']==len(rows)==4 and e['cumulative_ceiling']==a['proposed_cumulative_ceiling']==6 and a['highest_adopted_before']==5
ids=['original-import-held-success-20261003-01','original-import-held-publication-failure-20261003-01']
assert [r['identity'] for r in a['new_attempts']]==ids and all(r['maximum_claims']==1 for r in a['new_attempts']) and e['initial_experiment']==ids[0]
for name in ids:
 for p in [S/'research_runs'/name,S/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name,S/'fixture_outer'/name]:assert not p.exists()
assert a['paper_accounting_unchanged']=={'budget65_authority':False,'closed':36,'complete':27,'failed':9,'financial_fits_pending':1420,'highest_adopted_ceiling':64}
assert a['case_denominators']['success']['scalar_reference_comparisons']==160 and a['case_denominators']['success']['expected_score_batch_members']==[1,2] and a['case_denominators']['success']['score_chunk_cells']==64
assert a['case_denominators']['second_target_publication_failure']['first_target_scalar_reference_comparisons']==64 and a['case_denominators']['second_target_publication_failure']['second_target_numerical_cells']==96
assert a['guard']=={'disk_floor_bytes':10737418240,'file_size_bytes':4194304,'host_reserve_bytes':3221225472,'memory_high_bytes':3221225472,'memory_max_bytes':3221225472,'memory_swap_max_bytes':0,'native_wall_seconds':1800,'outer_active_seconds':1840,'startup_available_bytes':6442450944,'whole_capsule_sampled_stop_bytes':1073741824}
for name in ['original-import-native-publication-failure-20261003-0'+str(i) for i in range(1,5)]:assert not (S/'research_runs'/name).exists()
report={'schema_version':1,'extension_sha256':sha(ext_raw),'allocation_sha256':sha(alloc_raw),'claims':rows,'base':2,'prior':0,'highest_actually_adopted':5,'consumed':4,'proposed_ceiling':6,'new_fixed_identities':ids,'new_allowance_adopted':False,'native_release':False,'scope':'Exact prospective engineering accounting only; no genuine admission/claim or source execution'}
(H/'READBACK01.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS exact proposal/allocation; actualfourFAILED+output4/4/2/1 andmissing; originalceilings2/3/4/5;fourspent+twofresh=6;fixedlimits/denominators;noadoption')
