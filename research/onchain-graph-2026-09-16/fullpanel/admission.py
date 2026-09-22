"""One explicit full-panel extraction allowance after thirteen retained attempts."""
import hashlib
import json
from pathlib import Path
from tradingagents.research import admit
BASE='research/onchain-graph-2026-09-16/fullpanel/'
EXPERIMENT='eth-full-history-feature-panel-20260922'
LINEAGE=['eth-graph-source-20260916', 'eth-graph-prototype-20260916', 'eth-temporal-motifs-20260916', 'eth-temporal-motifs-8gib-20260916', 'eth-panel-readiness-20260916', 'eth-seven-day-pilot-20260916', 'eth-matched-input-capture-20260916', 'eth-remaining-graph-capture-20260916', 'eth-graph-source-recovery-20260917', 'eth-graph-source-resume-20260917', 'eth-graph-source-resume2-20260918', 'eth-graph-source-resume3-20260918', 'eth-seven-day-offline-pilot-20260922']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def contract(exp):
    exp=dict(exp,inputs={k:v for k,v in exp['inputs'].items() if k!='amendment'})
    return sha(json.dumps(exp,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def validate(gate,amendment,plan,history,approval):
    exp=gate['experiments'][EXPERIMENT];family=gate['families'][exp['family']]
    if family['prior_attempts']!=13 or family['attempt_budget']!=14 or family['mechanism_id']!='ethereum-full-history-daily-feature-extraction':raise ValueError('cumulative budget differs')
    if exp['parent'] is not None or exp['continuation_of']!='eth-seven-day-offline-pilot-20260922':raise ValueError('continuation ancestry differs')
    if amendment!=dict(schema_version=1,target_experiment=EXPERIMENT,prior_claims=13,additional_claims=1,cumulative_cap=14,target_contract_sha256=contract(exp),network_allowed=False,prices_or_models_allowed=False):raise ValueError('single extraction amendment differs')
    failed={'eth-temporal-motifs-20260916','eth-seven-day-pilot-20260916'}
    expected_receipts={f'research_runs/{n}/{f}' for n in LINEAGE for f in ['claim.json','failed.json' if n in failed else 'complete.json']}
    if history['lineage']!=LINEAGE or set(history['metadata_hashes'])!=expected_receipts:raise ValueError('retained history differs')
    from datetime import date,timedelta
    dates=[str(date(2022,1,1)+timedelta(days=i)) for i in range(1096)]
    if plan['dates']!=dates or set(plan['expected_rows'])!=set(dates) or sum(plan['expected_rows'].values())!=1221389903:raise ValueError('frozen calendar/row metadata differs')
    if any(type(n) is not int or not 0<n<=2_000_000 for n in plan['expected_rows'].values()):raise ValueError('per-day metadata rows invalid')
    if plan['expected_hash_bytes']!=39084476896 or plan['network_allowed'] is not False:raise ValueError('population policy differs')
    for key,value in dict(max_requests=0,max_total_bytes=0,max_derived_bytes=2*2**30,max_scratch_bytes=2*2**30,max_hash_bytes=40*2**30,min_free_bytes=20*2**30).items():
        if type(plan['limits'][key]) is not int or plan['limits'][key]!=value:raise ValueError('resource policy differs')
    if approval.get('decision')!='approve-single-fullpanel-extraction':raise ValueError('independent approval missing')
    cells=[c+'-'+d for d in dates for c in ['source','graph']]+['global-uniqueness']
    outputs=['day-'+d+'.json' for d in dates]+['hash-audit.json','panel.json','summary.json']
    if exp['cells']!=cells or exp['outputs']!=outputs:raise ValueError('full denominator differs')

def admit_panel(root,source):
    root=Path(root);a=admit(root=root,registration=BASE+'gates.json',experiment=EXPERIMENT,source=source)
    gate=json.loads((root/(BASE+'gates.json')).read_bytes());exp=gate['experiments'][EXPERIMENT]
    def read(name):
        ref=exp['inputs'][name];raw=(root/ref['path']).read_bytes()
        if sha(raw)!=ref['sha256']:raise ValueError('input differs: '+name)
        return json.loads(raw)
    history=read('history');approval=read('approval')
    if approval['review_sha256']!=exp['inputs']['review']['sha256']:raise ValueError('approval review differs')
    validate(gate,read('amendment'),read('plan'),history,approval)
    for path,digest in history['metadata_hashes'].items():
        if sha((root/path).read_bytes())!=digest:raise ValueError('ancestor receipt differs')
    return a
