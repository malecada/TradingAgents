from pathlib import Path
import json,hashlib
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).resolve().parent;P=F/'real-data-pilot-full29-entry01-2026-10-09';O=F/'real-data-pilot-full28-entry01-2026-10-09'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
afile=P/'CUMULATIVE_ALLOCATION_PROPOSED100_01.json';efile=P/'EXTENSION_PROPOSED100_01.json';assert h(afile)=='bcfe3bc18dc27f2e84061037398ad483ea3270206d438f2c39bb669e5d6f0ca1';assert h(efile)=='98644bbf178b18cb8a381db06a1675863624f5e6843da7a497fccc490b80fe27'
a=read(afile);e=read(efile);oa=read(O/'CUMULATIVE_ALLOCATION_PROPOSED99_01.json');oe=read(O/'EXTENSION_PROPOSED99_01.json');review=F/'real-data-pilot-full28-allocation-review01-2026-10-09/EXTENSION99_REVIEW01.json';assert h(review)=='c68b0e95300ae867f6b758a5cabb0bbf4e208437324187e2d57a6d577e24d22c';assert read(review)['extension_sha256']==h(O/'EXTENSION_PROPOSED99_01.json')
assert e['allocation']=={'path':str(afile.relative_to(R)),'sha256':h(afile)}
assert e['claims'][:-1]==oe['claims'] and a['closed_claims'][:-1]==oa['closed_claims'] and len(e['claims'])==51
assert a['closed_claims']==e['claims'];assert len({x['experiment'] for x in e['claims']})==51
for k in ('base_family','unchanged_pending_allocation','preserved_reserved_preclaim_allowances','new_fixed_allocation','new_financial_fits','maximum_unique_financial_fits_unchanged','refunds','category_transfers','historical_claims_reopened'):assert a[k]==oa[k],k
assert e['base_family']==oe['base_family']==a['base_family'];assert e['consumed_before']==a['consumed_before']==17+51==68
assert sum(a['unchanged_pending_allocation'].values())==28 and len(a['preserved_reserved_preclaim_allowances'])==3
assert e['cumulative_ceiling']==a['proposed_cumulative_ceiling']==68+28+3+1==100
assert a['prior_adopted_cumulative_ceiling']==a['prior_reviewed_reserved_ceiling']==99
last=e['claims'][-1];name=last['experiment'];root=R/'research_runs'/name;assert name.endswith('-28') and last['terminal_status']=='failed';assert h(root/'claim.json')==last['claim_sha256'];assert h(root/'failed.json')==last['terminal_sha256'];failed=read(root/'failed.json');assert failed['claim_sha256']==last['claim_sha256'] and failed['status']=='failed' and failed['experiment_id']==name;assert not (root/'complete.json').exists();claim=read(root/'claim.json');assert claim['effective_attempt_budget']==99
fresh=e['initial_experiment'];assert a['identities']==[fresh] and fresh.endswith('-29') and not (R/'research_runs'/fresh).exists()
# Reuse original50 hash evidence; current terminal existence (not reauthentication) only.
assert all((R/'research_runs'/x['experiment']/(x['terminal_status']+'.json')).is_file() for x in e['claims'])
rec=F/'pilot-full28-outcome-increment-tools-review01-2026-10-09/returned13/RECOVERY_REVIEW01.json';assert read(rec)['decision']=='accepted' and h(rec).startswith('ade5')
terminal=O/'ROOT_TERMINAL01.json';term=read(terminal);assert term['root_session']==47933 and term['terminal_poll']['exit_code']==1 and term['terminal_poll']['chunk_id']=='56fc48'
checks={'decision':'accepted_allocation_delta_only','spent':68,'actual_closed':51,'historical_spent':17,'pending':28,'closed_preclaim_reserved':3,'fresh_unused':1,'ceiling':100,'prior50_rows_unchanged':True,'prior28_permanently_failed':last,'new_financial_fits':a['new_financial_fits'],'financial_fit_maximum':a['maximum_unique_financial_fits_unchanged'],'recovery_review_sha256':h(rec),'terminal_sha256':h(terminal),'charter_sha256':h(P/'CHARTER01.md'),'extension_sha256':h(efile),'allocation_sha256':h(afile),'gate_dependency':'effective_budget requires no concrete Gate to issue exact5field review. Future genuine admission must supply reviewed extension and actual relevant ledger; source/runtime/input/resource release and Gate29 remain unverified.'};(D/'RESULT01.json').write_text(json.dumps(checks,indent=2)+'\n');print('PASS')
