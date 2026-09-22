"""One cumulative16/16 continuation; original206completed days are immutable."""
import hashlib
import json
from pathlib import Path
from tradingagents.research import admit
BASE='research/onchain-graph-2026-09-16/fullpanel_resume2/'
EXPERIMENT='eth-full-history-feature-panel-resume2-20260922'
PRIOR='eth-full-history-feature-panel-resume-20260922'
SOURCE='c739b6f0958e23b90ff5038dd46c9356581369c3'
LINEAGE=['eth-graph-source-20260916', 'eth-graph-prototype-20260916', 'eth-temporal-motifs-20260916', 'eth-temporal-motifs-8gib-20260916', 'eth-panel-readiness-20260916', 'eth-seven-day-pilot-20260916', 'eth-matched-input-capture-20260916', 'eth-remaining-graph-capture-20260916', 'eth-graph-source-recovery-20260917', 'eth-graph-source-resume-20260917', 'eth-graph-source-resume2-20260918', 'eth-graph-source-resume3-20260918', 'eth-seven-day-offline-pilot-20260922', 'eth-full-history-feature-panel-20260922', 'eth-full-history-feature-panel-resume-20260922']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def contract(exp):
    value=dict(exp,inputs={k:v for k,v in exp['inputs'].items() if k!='amendment'})
    return sha(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())

def validate(gate,plan,amendment,history,approval):
    from datetime import date,timedelta
    dates=[str(date(2022,1,1)+timedelta(days=i)) for i in range(1096)]
    e=gate['experiments'][EXPERIMENT];f=gate['families'][e['family']]
    if f['prior_attempts']!=15 or f['attempt_budget']!=16 or f['mechanism_id']!='ethereum-full-history-daily-feature-extraction-resume2':raise ValueError('cumulative continuation budget differs')
    if e['parent'] is not None or e['continuation_of']!=PRIOR:raise ValueError('continuation ancestry differs')
    if plan['dates']!=dates or plan['seed_count']!=206 or plan['seed_dates']!=dates[:206] or plan['remaining_dates']!=dates[206:]:raise ValueError('frozen retained/remaining calendar differs')
    if plan['prior_run_id']!=PRIOR or plan['prior_source']!=SOURCE or plan['network_allowed'] is not False:raise ValueError('prior source/scope differs')
    if [r['day_indices'] for r in plan['hash_roots']]!=[list(range(206)),list(range(206,1096))]:raise ValueError('identity partition differs')
    if plan['hash_roots'][0]['path']!='/home/malecada/master_thesis/onchain-fullpanel-hash-scratch-20260922' or plan['hash_roots'][1]['path']!='/home/malecada/master_thesis/onchain-fullpanel-resume2-hash-scratch-20260922':raise ValueError('scratch ownership differs')
    if plan['excluded_empty_hash_root']!='/home/malecada/master_thesis/onchain-fullpanel-resume-hash-scratch-20260922':raise ValueError('empty predecessor hash ownership differs')
    if plan['memory']!=dict(memory_max_bytes=6*2**30,memory_high_bytes=6*2**30,memory_swap_max_bytes=512*2**20,reserve_bytes=3*2**30,start_reserve_bytes=9*2**30):raise ValueError('shared-host protection differs')
    if amendment!=dict(schema_version=1,target_experiment=EXPERIMENT,prior_claims=15,additional_claims=1,cumulative_cap=16,target_contract_sha256=contract(e),network_allowed=False,prices_or_models_allowed=False):raise ValueError('single continuation amendment differs')
    failed={'eth-temporal-motifs-20260916','eth-seven-day-pilot-20260916','eth-full-history-feature-panel-20260922',PRIOR}
    receipts={f'research_runs/{name}/{file}' for name in LINEAGE for file in ['claim.json','failed.json' if name in failed else 'complete.json']}
    if history['lineage']!=LINEAGE or set(history['metadata_hashes'])!=receipts:raise ValueError('prior history differs')
    if approval.get('decision')!='approve-single-fullpanel-continuation':raise ValueError('independent continuation approval missing')
    if e['cells']!=[k+'-'+d for d in dates for k in ('source','graph')]+['global-uniqueness'] or e['outputs']!=['day-'+d+'.json' for d in dates]+['hash-audit.json','panel.json','summary.json']:raise ValueError('full denominator differs')
    seed_outputs={p for p in plan['seed_files'] if p.startswith('research_runs/')}
    if seed_outputs!={f'research_runs/{PRIOR}/outputs/day-{d}.json' for d in dates[:206]}:raise ValueError('seeded outputs differ')
    if any('2022-07-26' in p or '/scratch/' in p for p in plan['seed_files']):raise ValueError('unadmitted partial day in seed')

def admit_resume(root,source,*,review=False):
    root=Path(root);a=admit(root=root,registration=BASE+'gates.json',experiment=EXPERIMENT,source=source,_own_claim=EXPERIMENT if review else None)
    def read(name):
        ref=a.inputs[name];raw=(root/ref['path']).read_bytes()
        if sha(raw)!=ref['sha256']:raise ValueError('metadata binding differs: '+name)
        return json.loads(raw)
    history=read('history');approval=read('approval')
    if approval['review_sha256']!=a.inputs['review']['sha256']:raise ValueError('review binding differs')
    plan=read('plan')
    validate(a.spec,plan,read('amendment'),history,approval)
    if list(Path(plan['excluded_empty_hash_root']).iterdir()):raise ValueError('excluded predecessor hash root is not empty')
    for path,digest in history['metadata_hashes'].items():
        if sha((root/path).read_bytes())!=digest:raise ValueError('ancestor receipt changed')
    return a
