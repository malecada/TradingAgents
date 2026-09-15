"""Independent prospective protocol reconstruction, without controller admission.

Reads hashes and bounded control JSON only. No market body interpretation or
financial calculation. Quiescence is an externally reviewed observation; this
module verifies its binding, not remote process death from an assertion alone.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess

from tradingagents.research.verify import _blob, verify_claim
from tradingagents.research_spread.verify import verify_run as verify_history

TARGET = 'options-episode-20260911'
FAMILY = 'options-volatility'
MECHANISM = 'binance-option-delta-hedged-volatility-premium'
PACKAGES = ('research', 'research_amended', 'research_extended', 'research_spread', 'research_options_capture')
CONTROL_NAMES = {'source-binding.json', 'stop-ack.json', 'analysis-intent.json', 'stop-pending.json'}
MAX_JSON = 4 * 1024**2


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def timestamp(value):
    require(isinstance(value, str), 'UTC clock type')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise VerificationError('UTC clock syntax') from exc
    require(result.tzinfo is not None and result.utcoffset() == timedelta(0), 'explicit UTC required')
    return result


def path_under(root, name):
    require(isinstance(name, str), 'path type')
    relative = Path(name)
    require(bool(relative.parts) and not relative.is_absolute() and '..' not in relative.parts, 'relative safe path required')
    require(not any(p in {'keys', 'apis', '.env', 'hf_token.txt'} or p.startswith('.env.') for p in relative.parts), 'secret path forbidden')
    path = root / relative
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink forbidden')
    return path


def regular(path, cap=None):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode), 'nonregular member refused before reading')
    require(cap is None or info.st_size <= cap, 'retained file byte cap')
    return info.st_size


def file_hash(path):
    regular(path)
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def json_file(path, cap=MAX_JSON):
    regular(path, cap)
    return json.loads(path.read_bytes())


def reference(root, value, commit=None, *, parse=False):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'exact artifact reference')
    require(isinstance(value['sha256'], str) and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'hash syntax')
    path = path_under(root, value['path'])
    regular(path, MAX_JSON if parse or commit else None)
    require(file_hash(path) == value['sha256'], 'artifact hash changed')
    if commit:
        require(digest(_blob(root, commit, value['path'])) == value['sha256'], 'committed artifact changed')
    return json_file(path) if parse else path


def ancestor(root, older, newer):
    require(all(isinstance(x, str) and re.fullmatch('[0-9a-f]{40}', x) for x in (older, newer)), 'commit identity')
    result = subprocess.run(['git', 'merge-base', '--is-ancestor', older, newer], cwd=root, capture_output=True)
    require(result.returncode == 0, 'commit ancestry')


def members(directory, allowed, total, single):
    require(not directory.is_symlink() and directory.is_dir(), 'safe member directory')
    paths = list(directory.iterdir())
    # Inspect ALL names/types/sizes first; no hash may precede rejection.
    sizes = {}
    for p in paths:
        require(p.name in allowed, 'pending or unregistered member retained')
        sizes[p.name] = regular(p, single)
    require(sum(sizes.values()) <= total, 'retained directory byte cap')
    return {p.name: file_hash(p) for p in paths}


def resource_contract(protocol, exp):
    limits = protocol['resources']
    maxima = {'output_total_bytes': 64*1024**2, 'output_file_bytes': 16*1024**2,
              'control_total_bytes': 4*1024**2, 'terminal_reserve_bytes': 1024**2,
              'staging_reserve_bytes': 16*1024**2}
    require(isinstance(limits, dict) and set(limits) == set(maxima), 'resource denominator')
    require(all(type(limits[k]) is int and 0 < limits[k] <= v for k, v in maxima.items()), 'resource ceiling')
    require(limits['output_file_bytes'] <= limits['output_total_bytes'] and limits['terminal_reserve_bytes'] >= 65536, 'resource component bound')
    require(limits['staging_reserve_bytes'] >= max(limits['output_file_bytes'], limits['control_total_bytes'], limits['terminal_reserve_bytes']), 'publication/failure reserve')
    names = exp['outputs']
    require(isinstance(names, list) and 1 <= len(names) <= 16 and len(set(names)) == len(names), 'output denominator')
    require(all(isinstance(n, str) and re.fullmatch('[a-zA-Z0-9_-]{1,64}\\.json', n) for n in names), 'exact bounded output names')
    return limits


def reconstruct(root, claim, now):
    source, design = claim['source'], claim['design_source']
    registration = path_under(root, claim['registration'])
    regular(registration, MAX_JSON)
    raw = _blob(root, source, claim['registration'])
    require(registration.read_bytes() == raw == _blob(root, design, claim['registration']), 'registration physical/design identity')
    spec = json.loads(raw)
    exp = spec['experiments'][TARGET]
    family = spec['families'][FAMILY]
    require(exp['family'] == FAMILY and family['mechanism_id'] == MECHANISM, 'family identity')
    require(type(family['attempt_budget']) is int and family['attempt_budget'] == 4 and type(family['prior_attempts']) is int and family['prior_attempts'] == 1, 'original cumulative family budget')
    require(exp['stage'] in {'development', 'exploratory'} and len(exp['cells']) == len(set(exp['cells'])) == 8, 'eight exploratory cells')
    protocol = exp['episode_protocol']
    require(set(protocol) == {'schema_version', 'observation_window', 'worker_lease', 'analysis_inputs', 'resources'} and type(protocol['schema_version']) is int and protocol['schema_version'] == 2, 'prospective v2 protocol')
    require(claim.get('episode_protocol') == protocol and claim.get('episode_book_grant') == exp['episode_book_grant'] and claim.get('authority') == 'local-master-only', 'claim protocol authority binding')
    require(set(protocol['observation_window']) == {'start', 'end'} and set(protocol['worker_lease']) == {'not_before', 'expires_at'}, 'clock denominator')
    start, end = (timestamp(protocol['observation_window'][k]) for k in ('start', 'end'))
    lease_start, lease_end = (timestamp(protocol['worker_lease'][k]) for k in ('not_before', 'expires_at'))
    require(lease_start <= start < end <= lease_end and timedelta(0) < lease_end - lease_start <= timedelta(days=46), 'future lease bound')
    freeze = max(datetime.fromisoformat(subprocess.check_output(['git', 'show', '-s', '--format=%cI', c], cwd=root, text=True).strip()).astimezone(timezone.utc) for c in {source, design})
    require(freeze <= timestamp(claim['started_at']) < lease_start and timestamp(claim['started_at']) <= now and freeze < lease_start, 'pre-observation source freeze and claim')
    require(any(w['start'] == protocol['observation_window']['start'] and w['end'] == protocol['observation_window']['end'] and w['availability'] == 'prospective' for w in exp['windows']), 'honest prospective sample identity')
    require(claim['bindings'] is None and claim['bindings_sha256'] is None and bool(exp['inputs']), 'existing initial design inputs')
    for item in exp['inputs'].values():
        reference(root, {k: item[k] for k in ('path', 'sha256')})
    require(isinstance(protocol['analysis_inputs'], dict) and bool(protocol['analysis_inputs']), 'analysis denominator')
    for name, item in protocol['analysis_inputs'].items():
        require(re.fullmatch('[a-z][a-z0-9_-]{0,63}', name) and set(item) == {'path'}, 'analysis input schema')
        path_under(root, item['path'])
    limits = resource_contract(protocol, exp)
    runtime = {}
    for package in PACKAGES:
        for p in sorted((root / 'tradingagents' / package).glob('*.py')):
            runtime[package + '/' + p.name] = file_hash(p)
    require(runtime == exp['runtime_hashes'], 'runtime inventory/pins')
    pins = dict(exp['source_files'])
    for key in ('charter', 'selection'):
        require(bool(exp.get(key)), 'required scientific source pin')
        pins[exp[key]['path']] = exp[key]['sha256']
    pins.update({'tradingagents/' + k: v for k, v in runtime.items()})
    for name, hashed in pins.items():
        for commit in {source, design}:
            reference(root, {'path': name, 'sha256': hashed}, commit)
    grant = reference(root, exp['episode_book_grant'], source, parse=True)
    reference(root, exp['episode_book_grant'], design)
    keys = {'schema_version','target_experiment','program_id','family_id','mechanism_id','original_budget','prior_attempts','increment','effective_budget','target_contract_sha256','history_source','prior_claims','options_prior_ids','review','preflight'}
    require(set(grant) == keys, 'grant denominator')
    for key, value in {'schema_version':1, 'original_budget':4, 'prior_attempts':1, 'increment':1, 'effective_budget':5}.items():
        require(type(grant[key]) is int and grant[key] == value, 'grant cumulative accounting')
    target_hash = digest(canonical({k: v for k, v in exp.items() if k != 'episode_book_grant'}))
    require((grant['target_experiment'], grant['program_id'], grant['family_id'], grant['mechanism_id'], grant['target_contract_sha256']) == (TARGET, spec['program_id'], FAMILY, MECHANISM, target_hash), 'named grant identity')
    prior = grant['prior_claims']
    require(isinstance(prior, dict) and len(prior) == 19, 'all nineteen predecessors')
    old_claims = {}
    for directory in sorted((root / 'research_runs').iterdir()):
        if directory.name.startswith('.') or directory.name == TARGET:
            continue
        require(not directory.is_symlink() and directory.is_dir(), 'historical directory safety')
        regular(directory / 'claim.json', MAX_JSON)
        old = verify_claim(directory)
        old_claims[directory.name] = old
        if directory.name not in prior:
            require(old['family']['mechanism_id'] != MECHANISM and timestamp(old['started_at']) > timestamp(claim['started_at']), 'unbound prior or same-family descendant')
            continue
        names = [n for n in ('complete.json', 'failed.json') if (directory / n).exists()]
        require(len(names) == 1, 'retained historical terminal')
        receipt = json_file(directory / names[0])
        for p in (directory / 'outputs').iterdir():
            regular(p)
        verify_history(directory)
        observed = {'claim_sha256': file_hash(directory/'claim.json'), 'terminal': names[0], 'terminal_sha256': file_hash(directory/names[0]), 'output_sha256': receipt['output_sha256']}
        require(observed == prior[directory.name], 'historical claim/terminal/output inventory')
        oldspec = json.loads(_blob(root, old['source'], old['registration']))
        require(all(all(spec[group].get(k) == v for k, v in oldspec[group].items()) for group in ('experiments', 'families', 'datasets')), 'historical gate preservation')
        baseline = _blob(root, grant['history_source'], old['registration'])
        require(path_under(root, old['registration']).read_bytes() == baseline == _blob(root, source, old['registration']), 'physical old registration preserved')
        oldpins = dict(old['experiment']['source_files'])
        for key in ('charter', 'selection'):
            if old['experiment'].get(key):
                oldpins[old['experiment'][key]['path']] = old['experiment'][key]['sha256']
        for name, hashed in oldpins.items():
            reference(root, {'path':name, 'sha256':hashed}, source)
        package = 'research_spread' if 'budget_book_grant' in old['experiment'] else 'research_extended' if 'budget_extension' in old['experiment'] else 'research_amended' if 'budget_amendment' in old['experiment'] else 'research'
        aliases = {'original':'research', 'amended':'research_amended', 'extended':'research_extended'}
        for name, hashed in old['experiment'].get('runtime_hashes', {}).items():
            if '/' in name:
                prefix, filename = name.split('/', 1)
                name = aliases.get(prefix, prefix) + '/' + filename
            else:
                name = package + '/' + name
            require(runtime.get(name) == hashed, 'frozen ancestor runtime')
    require(set(prior) <= set(old_claims), 'missing historical claim')
    options = sorted(k for k in prior if old_claims[k]['family']['mechanism_id'] == MECHANISM)
    require(len(options) == 3 and options == grant['options_prior_ids'] and all(old_claims[k]['family'] == family for k in options), 'three prior options claims and unchanged family')
    ancestor(root, grant['history_source'], design)
    common = {'target_experiment':TARGET, 'target_contract_sha256':target_hash, 'prior_claims_sha256':digest(canonical(prior))}
    review = reference(root, grant['review'], source, parse=True)
    preflight = reference(root, grant['preflight'], source, parse=True)
    require(set(review) == {*common, 'decision', 'independent_review'} and review['decision'] == 'approve-single-prospective-options-book-episode' and all(review[k] == v for k,v in common.items()), 'independent grant approval')
    require(set(preflight) == {*common, 'status', 'reports'} and preflight['status'] == 'pass' and bool(preflight['reports']) and all(preflight[k] == v for k,v in common.items()), 'bound resource preflight')
    for ref in [grant['review'], grant['preflight'], review['independent_review'], *preflight['reports']]:
        for commit in {source, design}:
            reference(root, ref, commit)
    return exp, protocol, limits, target_hash


def quiescence(root, claim, claim_hash, now, evidence):
    if evidence is None:
        return None
    require(isinstance(evidence, dict) and set(evidence) == {'path','sha256','commit'}, 'external quiescence reference')
    commit = evidence['commit']
    ancestor(root, claim['source'], commit)
    review = reference(root, {k:evidence[k] for k in ('path','sha256')}, commit, parse=True)
    require(set(review) == {'decision','claim_sha256','worker_lease_sha256','mode','observed_at','evidence'}, 'quiescence review denominator')
    require(review['decision'] == 'verify-options-worker-quiescence' and review['claim_sha256'] == claim_hash and review['worker_lease_sha256'] == digest(canonical(claim['episode_protocol']['worker_lease'])), 'external quiescence identity')
    observed = timestamp(review['observed_at'])
    require(timestamp(claim['started_at']) <= observed <= now, 'quiescence observed clock')
    require(review['mode'] in {'sealed-worker-exit', 'lease-expired'}, 'quiescence mode')
    if review['mode'] == 'lease-expired':
        require(observed >= timestamp(claim['episode_protocol']['worker_lease']['expires_at']), 'premature lease-expiry review')
    reference(root, review['evidence'])
    return observed


def verify(*, root, now_utc, quiescence_evidence=None):
    """Reconstruct protocol; supplied review is trusted external observation.

    Call while the cooperative local controller lock is held or all writers are
    stopped. No automatic lock file creation, mutation, replay or network call.
    """
    root = Path(root).resolve()
    now = timestamp(now_utc)
    directory = path_under(root, 'research_runs/' + TARGET)
    require(directory.is_dir(), 'episode directory missing')
    regular(directory/'claim.json', MAX_JSON)
    # Legacy function is used only for structural envelope reconstruction.
    claim = verify_claim(directory)
    exp, protocol, limits, target_hash = reconstruct(root, claim, now)
    claimed = file_hash(directory/'claim.json')
    controls = members(directory/'control', CONTROL_NAMES, limits['control_total_bytes'], limits['control_total_bytes'])
    outputs = members(directory/'outputs', exp['outputs'], limits['output_total_bytes'], limits['output_file_bytes'])
    allowed = {'claim.json','control','outputs','complete.json','failed.json'}
    require(all(p.name in allowed for p in directory.iterdir()), 'pending or unexpected episode root member')
    quiet_at = quiescence(root, claim, claimed, now, quiescence_evidence)
    source = None
    phase_times = []
    if 'source-binding.json' in controls:
        source = json_file(directory/'control/source-binding.json')
        require(set(source) == {'claim_sha256','seal','manifest'} and source['claim_sha256'] == claimed, 'source binding')
        seal = reference(root, source['seal'], parse=True)
        reference(root, source['manifest'])
        require(set(seal) == {'claim_sha256','worker_lease_sha256','manifest_sha256','worker_stopped','sealed_at'} and seal['claim_sha256'] == claimed and seal['worker_lease_sha256'] == digest(canonical(protocol['worker_lease'])) and seal['manifest_sha256'] == source['manifest']['sha256'] and seal['worker_stopped'] is True, 'source seal binding')
        require(timestamp(claim['started_at']) <= timestamp(seal['sealed_at']) <= now, 'source seal clock')
        phase_times.append(timestamp(seal['sealed_at']))
    if 'stop-ack.json' in controls:
        bound = json_file(directory/'control/stop-ack.json')
        require(set(bound) == {'claim_sha256','ack'} and bound['claim_sha256'] == claimed, 'stop acknowledgment binding')
        ack = reference(root, bound['ack'], parse=True)
        require(set(ack) == {'claim_sha256','worker_lease_sha256','stopped_at','status'} and ack['claim_sha256'] == claimed and ack['worker_lease_sha256'] == digest(canonical(protocol['worker_lease'])) and ack['status'] == 'stopped' and timestamp(claim['started_at']) <= timestamp(ack['stopped_at']) <= now, 'stop acknowledgment declaration')
        phase_times.append(timestamp(ack['stopped_at']))
    if 'stop-pending.json' in controls:
        pending = json_file(directory/'control/stop-pending.json')
        require(set(pending) == {'claim_sha256','requested_at','reason'} and pending['claim_sha256'] == claimed and timestamp(claim['started_at']) <= timestamp(pending['requested_at']) <= now, 'stop pending identity')
        phase_times.append(timestamp(pending['requested_at']))
    intent = None
    if 'analysis-intent.json' in controls:
        intent = json_file(directory/'control/analysis-intent.json')
        require(set(intent) == {'claim_sha256','binding','commit','started_at'} and intent['claim_sha256'] == claimed, 'single analysis intent identity')
        when = timestamp(intent['started_at'])
        require(timestamp(protocol['observation_window']['end']) <= when <= now, 'analysis before observation end')
        require(quiet_at is not None and quiet_at <= when, 'analysis lacks externally reviewed prior quiescence')
        require(source is not None, 'analysis lacks sealed source')
        require(timestamp(seal['sealed_at']) <= when, 'analysis precedes retained source phase')
        phase_times.append(when)
        ancestor(root, claim['source'], intent['commit'])
        binding = reference(root, intent['binding'], intent['commit'], parse=True)
        require(set(binding) == {'claim_sha256','target_contract_sha256','source_manifest','inputs','independent_review'} and binding['claim_sha256'] == claimed and binding['target_contract_sha256'] == target_hash and binding['source_manifest'] == source['manifest'], 'analysis frozen contract')
        require(set(binding['inputs']) == set(protocol['analysis_inputs']), 'analysis input denominator')
        for name, item in binding['inputs'].items():
            require(set(item) == {'path','sha256','availability'} and item['path'] == protocol['analysis_inputs'][name]['path'] and item['availability'] in {'complete','unavailable'}, 'analysis input availability binding')
            reference(root, {k:item[k] for k in ('path','sha256')})
        review = reference(root, binding['independent_review'], intent['commit'], parse=True)
        require(review == {'decision':'admit-frozen-options-source','claim_sha256':claimed,'source_manifest_sha256':source['manifest']['sha256'],'inputs_sha256':digest(canonical(binding['inputs']))}, 'independent source admission binding')
    require(not outputs or intent is not None, 'outputs before exclusive analysis intent')
    terminals = [name for name in ('complete.json','failed.json') if (directory/name).exists()]
    require(len(terminals) <= 1, 'duplicate terminal')
    if not terminals:
        return {'status':'active','claim_sha256':claimed,'quiescence':'externally-reviewed' if quiet_at else 'unavailable','history_count':19,'scientific_validation':False}
    receipt = json_file(directory/terminals[0], limits['terminal_reserve_bytes'])
    status = terminals[0][:-5]
    keys = {'schema_version','experiment_id','status','ended_at','source','registration_sha256','claim_sha256','output_sha256','control_sha256','cells','cell_count','unavailable_count','reason'}
    require(set(receipt) == keys and type(receipt['schema_version']) is int and receipt['schema_version'] == 1, 'terminal grammar')
    ended = timestamp(receipt['ended_at'])
    require(quiet_at is not None and quiet_at <= ended <= now, 'terminal lacks externally reviewed prior quiescence')
    require(all(t <= ended for t in phase_times), 'terminal predates retained control phase')
    require(receipt['experiment_id'] == TARGET and receipt['status'] == status and receipt['claim_sha256'] == claimed and receipt['source'] == claim['source'] and receipt['registration_sha256'] == claim['registration_sha256'], 'terminal provenance')
    require(receipt['output_sha256'] == outputs and receipt['control_sha256'] == controls, 'terminal inventory hashes')
    cells = receipt['cells']
    require(isinstance(cells,list) and len(cells) <= 8 and all(isinstance(c,dict) and c.get('id') in exp['cells'] and c.get('status') in {'complete','unavailable'} and (c['status'] != 'unavailable' or bool(c.get('reason'))) for c in cells), 'terminal cell grammar')
    require(len({c['id'] for c in cells}) == len(cells) and receipt['cell_count'] == len(cells) and receipt['unavailable_count'] == sum(c['status']=='unavailable' for c in cells), 'terminal cell accounting')
    if status == 'complete':
        require(intent is not None and timestamp(intent['started_at']) <= ended and set(outputs) == set(exp['outputs']) and {c['id'] for c in cells} == set(exp['cells']), 'complete episode denominator')
    return {'status':status,'claim_sha256':claimed,'history_count':19,'quiescence':'externally-reviewed','scientific_validation':False}
