from pathlib import Path
import json,hashlib,stat,ast
D=Path(__file__).parent;ROOT=D.resolve().parents[3]
def write(n,v):(D/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
origins=[]
for name in ('verify.py','admission.py','lifecycle.py'):
 p=ROOT/'tradingagents/research'/name;out=D/'origins'/('research-'+name);out.write_bytes(p.read_bytes());origins.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for name in ('job_payload.py','calendar.py','dataset.py','contracts.py','subsets.py','btc_subsets.py','graph_store.py','btc_store.py','model_registry.py','cells.py'):
 p=ROOT/'tradingagents/research/onchain_replication'/name;(D/'origins'/name).write_bytes(p.read_bytes());origins.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
financial=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source/tradingagents/research/onchain_replication/financial_execution.py')
(D/'origins/isolated-financial-execution.py').write_bytes(financial.read_bytes());origins.append({'path':str(financial),'sha256':hashlib.sha256(financial.read_bytes()).hexdigest(),'qualification':'read-only existing execution selection; not the baseline for this overlay'})
write('ORIGINS01.json',origins)
write('ADMISSION_TEMPLATE01.json',{'status':'DRAFT_NOT_RELEASED','producer_source_pins':None,'independent_source_review':None,'historical_fund_cohort':None,'historical_fund_known_at_policy':None,'genuine_registration':None,'cumulative_allowance':None,'resource_capacity':None,'complete_external_recovery':None,'financial_credit':0,'fit_population_reference_required_fields':['treatment_input','treatment_weeks','treatment_population_plan_input'],'population_optional_extension':'treatment_input (only registered input role); original versions1/2 unchanged otherwise','config_rule':'source_admission.graph_config_hash = sha256(canonical exact complete-week -> transformed graph_config_hash map)','unavailable_rule':'every expected week retained, exact reason/evidence; failed producer never grants complete graph admission','source_counts':{'main_required_sources_before':135,'producer_after':137,'combined_producer_and_consumer_after':138,'new_consumer_modules':1,'modified_existing_consumer_modules':3},'future_source_commit':None})
for p in (D/'overlay').rglob('*.py'):ast.parse(p.read_text())
