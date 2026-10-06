from pathlib import Path
import hashlib,importlib.util,json,stat
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent
p=F/'real-data-pilot-june6-post-continuation-accounting01-2026-10-06/ACCOUNTING_DRAFT01.json';ev={}
def raw(p):
    s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_size<4*1024**2;b=p.read_bytes();ev[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def bound(ref):
    b=raw(R/ref['path']);assert hashlib.sha256(b).hexdigest()==ref['sha256'];return b
draft=read(p);assert ev[str(p.relative_to(R))]=='075a1c45215b785f8d9b7dfb8ef2e011757fe9ec1f527c95db04749acba6e992'
CONT='eth-paper-real-pilot-may30-ledger-continuation-20261006-01';NAME='eth-paper-real-pilot-graph-20220606-20261005-01'
gp=F/'real-data-pilot-may30-ledger-continuation01-2026-10-06/gate01.json';g=read(gp);assert ev[str(gp.relative_to(R))]=='f9e203de0fe362c1b6c07e147fe5ea3b709fe976f444aa0b18a7e6b50ca4775c'
e=g['experiments'][CONT];family=g['families'][e['family']];assert family['prior_attempts']==17 and family['attempt_budget']==51
# Pure metadata census, no Owner/Run/admission construction.
claims=[]
for p in sorted((R/'research_runs').glob('*/claim.json')):
    c=json.loads(p.read_bytes())
    if c.get('program_id')==g['program_id'] and c.get('family')==family:claims.append(c)
assert len(claims)==25
listed={x['experiment']:x for x in draft['closed_claims']};assert set(listed)=={c['experiment_id'] for c in claims}
for c in claims:
    name=c['experiment_id'];row=listed[name];cp=R/'research_runs'/name/'claim.json';assert hashlib.sha256(raw(cp)).hexdigest()==row['claim_sha256']
    terminal=R/'research_runs'/name/(row['terminal_status']+'.json');t=read(terminal)
    assert ev[str(terminal.relative_to(R))]==row['terminal_sha256'] and t['claim_sha256']==row['claim_sha256'] and t['experiment_id']==name and t['status']==row['terminal_status']
    assert not (terminal.parent/('failed.json' if row['terminal_status']=='complete' else 'complete.json')).exists()
source=R/'tradingagents/research/budget_extensions.py';raw(source);sp=importlib.util.spec_from_file_location('review_budget',source);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
effective=m.effective_budget(R,g['program_id'],NAME,e,family,claims,bound);assert effective==72
extension=json.loads(bound(e['cumulative_budget_extension']['extension']));allocation=json.loads(bound(extension['allocation']));review=json.loads(bound(e['cumulative_budget_extension']['review']))
assert extension['initial_experiment']==CONT and extension['consumed_before']==41 and review['decision']=='accepted'
assert allocation['unchanged_pending_allocation']==draft['unchanged_pending_allocation'] and sum(allocation['unchanged_pending_allocation'].values())==30
assert allocation['refunds']==allocation['category_transfers']==allocation['historical_claims_reopened']==0
adopters=[c for c in claims if c['experiment'].get('cumulative_budget_extension')==e['cumulative_budget_extension']];assert len(adopters)==1 and adopters[0]['experiment_id']==CONT and adopters[0]['effective_attempt_budget']==72
assert not (R/'research_runs'/NAME).exists() and not (R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME).exists() and not (R/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME).exists()
assert listed['eth-paper-real-pilot-graph-20220530-20261005-01']['terminal_status']=='failed'
assert set(ev)>=set(draft['evidence']) and all(ev[k]==v for k,v in draft['evidence'].items())
result={'schema_version':1,'decision':'accepted','identity':NAME,'parent':None,'effective_attempt_budget':effective,'original_allowance_retained':True,'transfer_or_refund':False,'current_closed_claims':25,'prior_attempts':17,'spent_total':42,'remaining_allowances_before_june6':30,'highest_adopted':72,'unchanged_pending_allocation':allocation['unchanged_pending_allocation'],'new_amendment':False,'new_financial_fits':0,'old_may30_failed_remains_spent':True,'validator':'genuine budget_extensions.effective_budget; metadata-only','evidence':ev,'qualification':'Original unused June6 allowance carried through actual first adoption of accepted72 extension. No refund, category transfer, reopened claim, new budget, native/admission/capacity or financial authority. Historical17 exposure retained through accepted original extension basis; not rereclassified.'}
(H/'ACCOUNTING_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':'accepted','effective':effective,'spent':42,'remaining':30,'review_sha256':hashlib.sha256((H/'ACCOUNTING_REVIEW01.json').read_bytes()).hexdigest()}))
