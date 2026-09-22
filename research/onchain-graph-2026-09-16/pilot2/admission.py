"""Explicit one-use offline numerical continuation; old budgets remain immutable."""
import hashlib
import json
from pathlib import Path
from tradingagents.research import admit
BASE='research/onchain-graph-2026-09-16/pilot2/'
EXPERIMENT='eth-seven-day-offline-pilot-20260922'
LINEAGE=['eth-graph-source-20260916','eth-graph-prototype-20260916',
'eth-temporal-motifs-20260916','eth-temporal-motifs-8gib-20260916',
'eth-panel-readiness-20260916','eth-seven-day-pilot-20260916',
'eth-matched-input-capture-20260916','eth-remaining-graph-capture-20260916',
'eth-graph-source-recovery-20260917','eth-graph-source-resume-20260917',
'eth-graph-source-resume2-20260918','eth-graph-source-resume3-20260918']
DATES=[f'2024-01-{i:02d}' for i in range(2,9)]
CELLS=['context','boundary']+['source-'+d for d in DATES]+['uniqueness']+['motifs-'+d for d in DATES]
OUTPUTS=['context.json','boundary.json']+['source-'+d+'.json' for d in DATES]+['cross-day-integrity.json']+['features-'+d+'.json' for d in DATES]+['manifest.json','features.json','summary.json']
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def contract(exp):
    value=dict(exp);value['inputs']={k:v for k,v in exp['inputs'].items() if k!='amendment'}
    return digest(canonical(value))
def validate(gate,cert,history,plan,approval,old_pilot,old_source):
    exp=gate['experiments'][EXPERIMENT];family=gate['families'][exp['family']]
    expected=dict(schema_version=1,target_experiment=EXPERIMENT,prior_claims=12,additional_claims=1,cumulative_cap=13,
                  network_allowed=False,prices_or_models_allowed=False,automatic_restart=False)
    if any(type(cert.get(k)) is not type(v) or cert[k]!=v for k,v in expected.items()):raise ValueError('one-use amendment policy differs')
    if cert['target_contract_sha256']!=contract(exp):raise ValueError('amendment contract binding differs')
    if family['prior_attempts']!=12 or family['attempt_budget']!=13 or family['mechanism_id']!='ethereum-seven-day-offline-numerical-continuation':raise ValueError('cumulative family differs')
    if history['lineage']!=LINEAGE:raise ValueError('history lineage differs')
    failed={'eth-temporal-motifs-20260916','eth-seven-day-pilot-20260916'}
    paths={f'research_runs/{n}/{f}' for n in LINEAGE for f in ['claim.json','failed.json' if n in failed else 'complete.json']}
    if set(history['metadata_hashes'])!=paths:raise ValueError('history receipt denominator differs')
    old=old_pilot['families']['eth-seven-day-pilot'];src=old_source['families']['eth-graph-source-resume3']
    if old['prior_attempts']!=5 or old['attempt_budget']!=6 or src['prior_attempts']!=11 or src['attempt_budget']!=12:raise ValueError('old budgets changed')
    if exp['parent']!='eth-seven-day-pilot-20260916' or exp['cells']!=CELLS or exp['outputs']!=OUTPUTS:raise ValueError('pilot denominator differs')
    if plan['dates']!=DATES or plan['network_allowed'] is not False or set(plan['captures'])!={f'2024-01-{i:02d}' for i in range(2,10)}:raise ValueError('fixed offline window differs')
    for k,v in {'max_requests':0,'max_total_bytes':0,'max_derived_bytes':8*2**30,'min_free_bytes':20*2**30}.items():
        if type(plan['limits'][k]) is not int or plan['limits'][k]!=v:raise ValueError('resource policy differs')
    if approval.get('decision')!='approve-single-offline-pilot' or approval.get('target_experiment')!=EXPERIMENT:raise ValueError('independent approval missing')

def admit_pilot(root,source):
    root=Path(root);a=admit(root=root,registration=BASE+'gates.json',experiment=EXPERIMENT,source=source)
    gate=json.loads((root/(BASE+'gates.json')).read_bytes());exp=gate['experiments'][EXPERIMENT]
    def read(name):
        ref=exp['inputs'][name];p=(root/ref['path']).resolve();p.relative_to(root.resolve());raw=p.read_bytes()
        if digest(raw)!=ref['sha256']:raise ValueError('input metadata hash differs: '+name)
        return json.loads(raw)
    history=read('history');approval=read('approval')
    if approval.get('review_sha256')!=exp['inputs']['review']['sha256']:
        raise ValueError('approval review binding differs')
    validate(gate,read('amendment'),history,read('plan'),approval,read('old_pilot_gate'),read('old_source_gate'))
    for path,sha in history['metadata_hashes'].items():
        if digest((root/path).read_bytes())!=sha:raise ValueError('ancestor receipt changed')
    return a
