"""One explicit, reviewed source-only resume3 allowance; no economic amendment."""
import hashlib
import json
import os
from pathlib import Path

from tradingagents.research import admit

BASE = 'research/onchain-graph-2026-09-16/comparison/'
EXPERIMENT = 'eth-graph-source-resume3-20260918'
PARENT = 'eth-graph-source-resume2-20260918'
LINEAGE = ['eth-graph-source-20260916', 'eth-graph-prototype-20260916',
           'eth-temporal-motifs-20260916', 'eth-temporal-motifs-8gib-20260916',
           'eth-panel-readiness-20260916', 'eth-seven-day-pilot-20260916',
           'eth-matched-input-capture-20260916', 'eth-remaining-graph-capture-20260916', 'eth-graph-source-recovery-20260917', 'eth-graph-source-resume-20260917', PARENT]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def target_contract(experiment):
    value = dict(experiment)
    value['inputs'] = {k:v for k,v in value['inputs'].items() if k != 'resume3_amendment'}
    return digest(canonical(value))


def validate_policy(gate, certificate, baseline, cohort, summary, history, review):
    exp = gate['experiments'][EXPERIMENT]
    family = gate['families'][exp['family']]
    parent = baseline['experiments'][PARENT]
    old_family = baseline['families'][parent['family']]
    expected = dict(schema_version=1, amendment_id='eth-raw-resume3-single-20260918',
                    target_experiment=EXPERIMENT, baseline_experiment=PARENT,
                    baseline_family_sha256=digest(canonical(old_family)),
                    original_family_cap=11, cumulative_prior_claims=11,
                    additional_claims=1, cumulative_cap=12, raw_only=True,
                    automatic_restart=False, monitor_authorized=True, max_attempts_per_request=4, retry_delays_seconds=[5,15,45])
    for key, value in expected.items():
        if certificate.get(key) != value or type(certificate.get(key)) is not type(value):
            raise ValueError('source resume3 amendment differs: '+key)
    if old_family['attempt_budget'] != 11 or old_family['prior_attempts'] != 10:
        raise ValueError('original family budget changed')
    if family['prior_attempts'] != 11 or family['attempt_budget'] != 12:
        raise ValueError('resume3 cumulative budget differs')
    if family['mechanism_id'] != 'ethereum-bounded-transport-source-resume3':
        raise ValueError('resume3 mechanism changed')
    if certificate['target_contract_sha256'] != target_contract(exp):
        raise ValueError('resume3 contract differs from amendment')
    cells = summary['cells']
    source = {r['id'][6:]:r['status'] for r in cells if r['id'].startswith('graph-')}
    if len(source) != 446 or len(cells) != 447:
        raise ValueError('baseline cell denominator differs')
    missing = sorted(d for d,s in source.items() if s == 'unavailable')
    complete = sorted(d for d,s in source.items() if s == 'complete')
    if len(missing) != 446 or len(complete) != 0 or cohort['dates'] != missing or cohort['parent_complete_dates'] != complete:
        raise ValueError('resume3 does not match exact unavailable cohort')
    old_cohort = baseline['_parent_cohort']
    expected_complete = sorted(old_cohort['prior_complete_dates'] + complete)
    if len(expected_complete) != 638 or cohort['prior_complete_dates'] != expected_complete:
        raise ValueError('excluded completed dates differ')
    if exp['cells'] != ['graph-'+d for d in missing]+['index']:
        raise ValueError('resume3 lifecycle cells differ')
    if exp['outputs'] != [c+'.json' for c in exp['cells']]+['summary.json']:
        raise ValueError('resume3 outputs differ')
    if set(cohort['prefixes']) - set(missing):
        raise ValueError('reuse prefix outside missing cohort')
    if (cohort['raw_baseline_bytes'] != 63*1024**3 or
        cohort['prior_metadata_baseline_bytes'] != 1160*1024**2 or
        cohort['lifecycle_reserve_bytes'] != 0 or
        cohort['inherited_lifecycle_allowance_bytes'] != 64*1024**2 or
        cohort['inherited_closure_allowance_bytes'] != 44*1024**2 or
        cohort['max_attempts_per_request'] != 4 or cohort['retry_delays_seconds'] != [5,15,45] or
        cohort['monitor_authorized'] is not True or cohort['automatic_restart'] is not False):
        raise ValueError('resume3 storage/stop policy differs')
    if history['lineage'] != LINEAGE:
        raise ValueError('cumulative source lineage differs')
    failed = {'eth-temporal-motifs-20260916', 'eth-seven-day-pilot-20260916'}
    expected_receipts = {f'research_runs/{name}/{file}' for name in LINEAGE
                         for file in ['claim.json', 'failed.json' if name in failed else 'complete.json']}
    if set(history['metadata_hashes']) != expected_receipts:
        raise ValueError('predecessor receipt inventory differs')
    if (review.get('decision') != 'approve-single-source-resume3' or review.get('target_experiment') != EXPERIMENT
            or type(review.get('additional_claims')) is not int or review['additional_claims'] != 1):
        raise ValueError('independent source-resume3 approval missing')


def validate_baseline(cohort, index):
    days = index['days']
    if len(days) != 446:
        raise ValueError('parent accounting date denominator differs')
    for row in days:
        budget = row.get('capture', row)['budget']
        for field, limit in [('total_raw_bytes', cohort['raw_baseline_bytes']),
                             ('total_metadata_bytes', cohort['prior_metadata_baseline_bytes'])]:
            value = budget[field]
            if type(value) is not int or not 0 <= value <= limit:
                raise ValueError('continuation baseline undercounts retained parent: '+field)


def validate_reserve(audit):
    expected = dict(schema_version=1, pool_origin_experiment=PARENT,
                    original_charged_reserve_bytes=128*1024**2,
                    additional_overhead_reserve_bytes=8*1024**2,
                    continuation_allowance_bytes=64*1024**2, closure_mirror_allowance_bytes=44*1024**2, new_charge_bytes=0)
    for key, value in expected.items():
        if type(audit.get(key)) is not type(value) or audit[key] != value:
            raise ValueError('inherited lifecycle reserve policy differs: '+key)
    entries = audit['files']
    if len({e['path'] for e in entries}) != len(entries) or not entries:
        raise ValueError('reserve audit denominator differs')
    spent = sum(e['allocated_bytes'] for e in entries)
    if any(type(e['allocated_bytes']) is not int or e['allocated_bytes'] < e['bytes'] for e in entries):
        raise ValueError('invalid physical allocation')
    if spent != audit['spent_allocated_bytes'] or spent + 116*1024**2 > 128*1024**2:
        raise ValueError('inherited reservation is insufficient')


def reserve_paths():
    coordinator = Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
    parent = Path('/home/malecada/Data/onchain-research/TradingAgents-onchain-resume2')
    run = Path('research_runs') / PARENT
    base = Path(BASE)
    paths = list((parent/run).rglob('*.json')) + list((coordinator/run).rglob('*.json'))
    paths += list((coordinator/base/'resume2-closure').rglob('*.json'))
    paths += list((coordinator/base/'resume2-launch-evidence').rglob('*.json'))
    paths += [parent/base/name for name in ('resume2-progress.log', 'resume2-resource.json',
              'resume2-started.json', 'resume2-launch-intent.json')]
    paths += [coordinator/base/'RESUME2_START_REVIEW.md']
    return {str(p) for p in paths}


def admit_resume3(root, source):
    root = Path(root)
    result = admit(root=root, registration=BASE+'resume3-gates.json',
                   experiment=EXPERIMENT, source=source)
    gate = json.loads((root/(BASE+'resume3-gates.json')).read_bytes())
    exp = gate['experiments'][EXPERIMENT]
    def read(name):
        ref = exp['inputs'][name]
        path = (root/ref['path']).resolve()
        path.relative_to(root.resolve())
        raw = path.read_bytes()
        if digest(raw) != ref['sha256']:
            raise ValueError('resume3 metadata hash differs: '+name)
        return raw
    certificate = json.loads(read('resume3_amendment'))
    baseline_raw = read('baseline_gate')
    cohort_raw = read('cohort')
    history = json.loads(read('history'))
    review = json.loads(read('resume3_approval'))
    baseline = json.loads(baseline_raw)
    baseline['_parent_cohort'] = json.loads(read('parent_cohort'))
    validate_policy(gate, certificate, baseline, json.loads(cohort_raw),
                    json.loads(read('baseline_summary')), history, review)
    validate_baseline(json.loads(cohort_raw), json.loads(read('baseline_index')))
    reserve = json.loads(read('inherited_reserve'))
    validate_reserve(reserve)
    if {entry['path'] for entry in reserve['files']} != reserve_paths():
        raise ValueError('inherited reserve scope denominator differs')
    if baseline['_parent_cohort']['lifecycle_reserve_bytes'] != 128*1024**2:
        raise ValueError('original inherited lifecycle pool was not charged')
    for entry in reserve['files']:
        path = Path(entry['path'])
        if not path.is_absolute() or path.is_symlink():
            raise ValueError('invalid reserve audit path')
        raw = path.read_bytes()
        stat = path.stat()
        fragment = max(4096, os.statvfs(path).f_frsize)
        allocated = max(stat.st_blocks*512, ((len(raw)+fragment-1)//fragment)*fragment)
        if len(raw) != entry['bytes'] or digest(raw) != entry['sha256'] or allocated != entry['allocated_bytes']:
            raise ValueError('inherited reserve evidence changed')
    for field, raw in [('baseline_gate_sha256', baseline_raw), ('cohort_sha256', cohort_raw),
                       ('baseline_claim_sha256', read('baseline_claim')),
                       ('baseline_terminal_sha256', read('baseline_terminal'))]:
        if certificate[field] != digest(raw):
            raise ValueError('amendment provenance differs: '+field)
    if certificate['approval_sha256'] != digest(read('resume3_approval')):
        raise ValueError('approval binding differs')
    review_ref = review['independent_review']
    if (review_ref['path'] != exp['inputs']['independent_review']['path'] or
            review_ref['sha256'] != digest(read('independent_review'))):
        raise ValueError('independent review binding differs')
    for relative, expected in history['metadata_hashes'].items():
        if digest((root/relative).read_bytes()) != expected:
            raise ValueError('predecessor receipt changed')
    # Disallow another family/identity from reusing this policy allowance.
    for path in (root/'research_runs').glob('*/claim.json'):
        claim = json.loads(path.read_bytes())
        if claim['experiment_id'] == EXPERIMENT:
            raise ValueError('resume3 identity is already claimed; no restart')
        inputs = claim['experiment'].get('inputs', {})
        ref = inputs.get('resume3_amendment')
        if ref and ref.get('sha256') == exp['inputs']['resume3_amendment']['sha256']:
            raise ValueError('source resume3 amendment already consumed')
        parent_ref = inputs.get('baseline_terminal')
        if ref and parent_ref and parent_ref.get('sha256') == certificate['baseline_terminal_sha256']:
            raise ValueError('same source parent already received a resume3 allowance')
    return result
