"""One explicit, reviewed source-only resume2 allowance; no economic amendment."""
import hashlib
import json
from pathlib import Path

from tradingagents.research import admit

BASE = 'research/onchain-graph-2026-09-16/comparison/'
EXPERIMENT = 'eth-graph-source-resume2-20260918'
PARENT = 'eth-graph-source-resume-20260917'
LINEAGE = ['eth-graph-source-20260916', 'eth-graph-prototype-20260916',
           'eth-temporal-motifs-20260916', 'eth-temporal-motifs-8gib-20260916',
           'eth-panel-readiness-20260916', 'eth-seven-day-pilot-20260916',
           'eth-matched-input-capture-20260916', 'eth-remaining-graph-capture-20260916', 'eth-graph-source-recovery-20260917', PARENT]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def target_contract(experiment):
    value = dict(experiment)
    value['inputs'] = {k:v for k,v in value['inputs'].items() if k != 'resume2_amendment'}
    return digest(canonical(value))


def validate_policy(gate, certificate, baseline, cohort, summary, history, review):
    exp = gate['experiments'][EXPERIMENT]
    family = gate['families'][exp['family']]
    parent = baseline['experiments'][PARENT]
    old_family = baseline['families'][parent['family']]
    expected = dict(schema_version=1, amendment_id='eth-raw-resume2-single-20260918',
                    target_experiment=EXPERIMENT, baseline_experiment=PARENT,
                    baseline_family_sha256=digest(canonical(old_family)),
                    original_family_cap=10, cumulative_prior_claims=10,
                    additional_claims=1, cumulative_cap=11, raw_only=True,
                    automatic_restart=False, monitor_authorized=True, max_attempts_per_request=4, retry_delays_seconds=[5,15,45])
    for key, value in expected.items():
        if certificate.get(key) != value or type(certificate.get(key)) is not type(value):
            raise ValueError('source resume2 amendment differs: '+key)
    if old_family['attempt_budget'] != 10 or old_family['prior_attempts'] != 9:
        raise ValueError('original family budget changed')
    if family['prior_attempts'] != 10 or family['attempt_budget'] != 11:
        raise ValueError('resume2 cumulative budget differs')
    if family['mechanism_id'] != 'ethereum-bounded-transport-source-resume2':
        raise ValueError('resume2 mechanism changed')
    if certificate['target_contract_sha256'] != target_contract(exp):
        raise ValueError('resume2 contract differs from amendment')
    cells = summary['cells']
    source = {r['id'][6:]:r['status'] for r in cells if r['id'].startswith('graph-')}
    if len(source) != 507 or len(cells) != 508:
        raise ValueError('baseline cell denominator differs')
    missing = sorted(d for d,s in source.items() if s == 'unavailable')
    complete = sorted(d for d,s in source.items() if s == 'complete')
    if len(missing) != 446 or len(complete) != 61 or cohort['dates'] != missing or cohort['parent_complete_dates'] != complete:
        raise ValueError('resume2 does not match exact unavailable cohort')
    old_cohort = baseline['_parent_cohort']
    expected_complete = sorted(old_cohort['prior_complete_dates'] + complete)
    if len(expected_complete) != 638 or cohort['prior_complete_dates'] != expected_complete:
        raise ValueError('excluded completed dates differ')
    if exp['cells'] != ['graph-'+d for d in missing]+['index']:
        raise ValueError('resume2 lifecycle cells differ')
    if exp['outputs'] != [c+'.json' for c in exp['cells']]+['summary.json']:
        raise ValueError('resume2 outputs differ')
    if set(cohort['prefixes']) - set(missing):
        raise ValueError('reuse prefix outside missing cohort')
    if (cohort['raw_baseline_bytes'] != 62*1024**3 or
        cohort['prior_metadata_baseline_bytes'] != 1024*1024**2 or
        cohort['lifecycle_reserve_bytes'] != 128*1024**2 or
        cohort['max_attempts_per_request'] != 4 or cohort['retry_delays_seconds'] != [5,15,45] or
        cohort['monitor_authorized'] is not True or cohort['automatic_restart'] is not False):
        raise ValueError('resume2 storage/stop policy differs')
    if history['lineage'] != LINEAGE:
        raise ValueError('cumulative source lineage differs')
    failed = {'eth-temporal-motifs-20260916', 'eth-seven-day-pilot-20260916'}
    expected_receipts = {f'research_runs/{name}/{file}' for name in LINEAGE
                         for file in ['claim.json', 'failed.json' if name in failed else 'complete.json']}
    if set(history['metadata_hashes']) != expected_receipts:
        raise ValueError('predecessor receipt inventory differs')
    if (review.get('decision') != 'approve-single-source-resume2' or review.get('target_experiment') != EXPERIMENT
            or type(review.get('additional_claims')) is not int or review['additional_claims'] != 1):
        raise ValueError('independent source-resume2 approval missing')


def validate_baseline(cohort, index):
    days = index['days']
    if len(days) != 507:
        raise ValueError('parent accounting date denominator differs')
    for row in days:
        budget = row.get('capture', row)['budget']
        for field, limit in [('total_raw_bytes', cohort['raw_baseline_bytes']),
                             ('total_metadata_bytes', cohort['prior_metadata_baseline_bytes'])]:
            value = budget[field]
            if type(value) is not int or not 0 <= value <= limit:
                raise ValueError('continuation baseline undercounts retained parent: '+field)


def admit_resume2(root, source):
    root = Path(root)
    result = admit(root=root, registration=BASE+'resume2-gates.json',
                   experiment=EXPERIMENT, source=source)
    gate = json.loads((root/(BASE+'resume2-gates.json')).read_bytes())
    exp = gate['experiments'][EXPERIMENT]
    def read(name):
        ref = exp['inputs'][name]
        path = (root/ref['path']).resolve()
        path.relative_to(root.resolve())
        raw = path.read_bytes()
        if digest(raw) != ref['sha256']:
            raise ValueError('resume2 metadata hash differs: '+name)
        return raw
    certificate = json.loads(read('resume2_amendment'))
    baseline_raw = read('baseline_gate')
    cohort_raw = read('cohort')
    history = json.loads(read('history'))
    review = json.loads(read('resume2_approval'))
    baseline = json.loads(baseline_raw)
    baseline['_parent_cohort'] = json.loads(read('parent_cohort'))
    validate_policy(gate, certificate, baseline, json.loads(cohort_raw),
                    json.loads(read('baseline_summary')), history, review)
    validate_baseline(json.loads(cohort_raw), json.loads(read('baseline_index')))
    for field, raw in [('baseline_gate_sha256', baseline_raw), ('cohort_sha256', cohort_raw),
                       ('baseline_claim_sha256', read('baseline_claim')),
                       ('baseline_terminal_sha256', read('baseline_terminal'))]:
        if certificate[field] != digest(raw):
            raise ValueError('amendment provenance differs: '+field)
    if certificate['approval_sha256'] != digest(read('resume2_approval')):
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
            raise ValueError('resume2 identity is already claimed; no restart')
        inputs = claim['experiment'].get('inputs', {})
        ref = inputs.get('resume2_amendment')
        if ref and ref.get('sha256') == exp['inputs']['resume2_amendment']['sha256']:
            raise ValueError('source resume2 amendment already consumed')
        parent_ref = inputs.get('baseline_terminal')
        if ref and parent_ref and parent_ref.get('sha256') == certificate['baseline_terminal_sha256']:
            raise ValueError('same source parent already received a resume2 allowance')
    return result
