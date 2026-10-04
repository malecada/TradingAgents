"""Treatment lineage at population and fit boundaries. Stdlib at import.

Pure checks establish consistency, never authority. Runtime paths require the
real active ResearchRun and independently verify retained committed claims.
Fund vintage policy is deliberately unadmitted in this source candidate.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

LIMIT = 4 * 1024**2
PREFIX = 'research_artifacts/onchain-paper-replication-2026-09-24'
# Root must freeze an independently reviewed producer successor, not producer01.
PRODUCER_SOURCE_PINS = None


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def stamp(value):
    require(type(value) is str and value.endswith('Z'), 'canonical UTC clock required')
    t = datetime.fromisoformat(value[:-1] + '+00:00')
    require(t.isoformat().replace('+00:00', 'Z') == value, 'canonical UTC clock required')
    return t


def pin(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'SHA256 required')


def role(value):
    require(type(value) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,127}', value) is not None, 'registered role required')


def schema(value, asset, variant, weeks):
    require(type(value) is dict and set(value) == {'schema_version', 'asset', 'variant', 'expected_weeks', 'weeks'}, 'treatment admission fields differ')
    require(type(value['schema_version']) is int and value['schema_version'] == 1, 'treatment version differs')
    require(asset in ('BTC', 'ETH') and variant in ('whale', 'fund') and (variant != 'fund' or asset == 'ETH'), 'paper treatment identity differs')
    require(value['asset'] == asset and value['variant'] == variant, 'requested treatment differs')
    require(type(weeks) in (list, tuple) and 0 < len(weeks) <= 1024 and list(weeks) == sorted(set(weeks)), 'finite full weekly denominator required')
    require(value['expected_weeks'] == list(weeks) and set(value['weeks']) == set(weeks), 'treatment weekly denominator differs')
    for week in weeks:
        t = stamp(week)
        require(t.weekday() == 0 and t.time().isoformat() == '00:00:00', 'full Monday week required')
        r = value['weeks'][week]
        require(type(r) is dict and set(r) == {'status', 'claim_input', 'terminal_input', 'ledger_input', 'job_input', 'plan_input', 'disposition_input', 'receipt_input', 'coverage_input', 'manifest_input', 'components', 'aliases'}, 'weekly lineage fields differ')
        require(r['status'] in ('complete', 'unavailable'), 'unknown treatment disposition')
        for key in ('claim_input', 'terminal_input', 'ledger_input', 'job_input', 'plan_input'):
            role(r[key])
        require(type(r['components']) is dict and len(r['components']) <= 10 and type(r['aliases']) is dict and len(r['aliases']) <= 100, 'bounded component/alias map required')
        for a, b in r['aliases'].items():
            role(a); role(b)
        for path, name in r['components'].items():
            require(path in ('graph/manifest.json', 'edge_satoshis.hex', 'incident_satoshis.hex', 'node_ids.npy', 'node_features.npy', 'edge_index.npy', 'edge_features.npy', 'edge_aggregates.npy', 'graph/node_ids.npy', 'graph/node_features.npy', 'graph/edge_index.npy', 'graph/edge_features.npy', 'graph/edge_aggregates.npy'), 'unknown component member')
            role(name)
        if r['status'] == 'complete':
            role(r['disposition_input'])
            for key in ('receipt_input', 'coverage_input', 'manifest_input'):
                role(r[key])
            require(r['components'], 'complete component lineage required')
        else:
            if r['disposition_input'] is not None: role(r['disposition_input'])
            require(all(r[k] is None for k in ('receipt_input', 'coverage_input', 'manifest_input')) and r['components'] == {}, 'unavailable must not impersonate a completed graph')
    return value


def disposition(claim, terminal, ledger, claim_hash, ledger_hash, plan, week, variant, asset, *, absent=False):
    """Pure join; caller must separately authenticate actual committed claim."""
    pin(claim_hash); pin(ledger_hash)
    require(terminal.get('claim_sha256') == claim_hash and terminal.get('experiment_id') == claim.get('experiment_id'), 'terminal/claim identity differs')
    require(type(ledger) is list and [r['id'] for r in ledger] == claim['experiment']['cells'], 'complete ordered cell denominator differs')
    ids = ['treatment-' + asset.lower() + '-' + variant + '-' + w[:10] for w in plan['expected_weeks']]
    require(claim['experiment']['cells'] == ids, 'registered treatment cells differ')
    for r in ledger:
        require(r.get('status') in ('complete', 'unavailable') and (r['status'] != 'unavailable' or r.get('reason')), 'explicit disposition required')
    if terminal.get('status') == 'complete':
        require(terminal.get('source') == claim['source'] and terminal.get('registration_sha256') == claim['registration_sha256'], 'terminal source/registration differs')
        require(terminal.get('output_sha256', {}).get('cell-ledger.json') == ledger_hash and terminal.get('cells') == ledger, 'terminal ledger differs')
        require(terminal.get('cell_count') == len(ledger) and terminal.get('unavailable_count') == sum(r['status'] == 'unavailable' for r in ledger), 'terminal counts differ')
    else:
        require(terminal.get('status') == 'failed', 'unknown/active outcome unavailable for consumption')
    selected = next(r for r in ledger if r['id'] == 'treatment-' + asset.lower() + '-' + variant + '-' + week[:10])
    if terminal['status'] == 'failed':
        require(selected['status'] == 'unavailable', 'failed producer cannot grant completed treatment admission')
    if absent:
        require(terminal['status'] == 'failed' and selected['status'] == 'unavailable' and set(selected) == {'id', 'status', 'reason'}, 'exact failed absent-row shape required')
        # Cell identity is already bound to registered asset/variant/week above.
        # Return the real fallback unchanged; never fabricate asset/week fields.
    else:
        require(selected.get('asset') == asset and selected.get('week') == week, 'cell asset/week differs')
    return selected


def graph_join(receipt, row, graph, graph_hash, coverage, coverage_hash, receipt_hash, claim, claim_hash, plan_hash, parent, parent_hash, week, asset, variant):
    """Validate exact declared graph transform; no array decoding or method change."""
    for p in (graph_hash, coverage_hash, receipt_hash, claim_hash, plan_hash, parent_hash):
        pin(p)
    require(receipt.get('schema_version') == 1 and receipt.get('kind') == 'registered-graph-treatment-receipt', 'treatment receipt schema differs')
    expected = {'asset': asset, 'variant': variant, 'week': week, 'claim_sha256': claim_hash, 'plan_sha256': plan_hash, 'source': claim['source'], 'manifest_sha256': graph_hash, 'parent_manifest_sha256': parent_hash}
    require(all(receipt.get(k) == v for k, v in expected.items()), 'treatment receipt ancestry differs')
    require(row.get('manifest_sha256') == graph_hash and row.get('coverage_sha256') == coverage_hash and row.get('treatment_receipt_sha256') == receipt_hash, 'cell component receipts differ')
    m, p = graph['metadata'], parent['metadata']
    end = (stamp(week) + timedelta(days=7)).isoformat().replace('+00:00', 'Z')
    require(m['asset'] == p['asset'] == asset and m['start_utc'] == p['start_utc'] == week and m['end_utc'] == p['end_utc'] == receipt['end_utc'] == end, 'graph asset/date differs')
    require(graph['graph_hash'] == receipt['graph_hash'] and parent['graph_hash'] == receipt['parent_graph_hash'], 'graph object ancestry differs')
    require(receipt['available_at'] == m['available_at'] and stamp(m['available_at']) >= stamp(p['available_at']) >= stamp(end) + timedelta(days=1), 'graph availability differs')
    decision = receipt['decision']
    require(decision['variant'] == variant and decision['parent_graph_hash'] == parent['graph_hash'], 'decision parent/treatment differs')
    require(decision['schema_version'] == (3 if asset == 'BTC' else 2), 'original exact treatment encoding required')
    require(m['graph_config_hash'] == sha(canonical({'parent_config': p['graph_config_hash'], 'variant': decision})), 'per-week transformation configuration differs')
    require(m['source_hashes'] == p['source_hashes'] and all(m[k] == p[k] for k in ('raw_count', 'admitted_count', 'exclusion_counts')), 'original raw counters/source membership changed')
    require(coverage['graph_config_hash'] == m['graph_config_hash'] and coverage['graph_manifest_sha256'] == graph_hash and coverage['claim_sha256'] == claim_hash and coverage['plan_sha256'] == plan_hash and coverage['asset'] == asset and coverage['week'] == week and coverage['end_utc'] == end, 'derived coverage differs')
    if variant == 'fund':
        raise ValueError('UNADMITTED: exact historical cohort and known_at policy independent admission required')
    require(receipt['cohort_sha256'] is None and receipt['cohort_review_sha256'] is None and decision['decision'] == {'threshold': .9, 'strict': True}, 'original whale threshold/cohort differs')
    require(m['available_at'] == p['available_at'], 'whale availability must preserve parent clock')
    return {'status': 'complete', 'graph_hash': graph['graph_hash'], 'available_at': m['available_at'], 'graph_config_hash': m['graph_config_hash'], 'manifest_sha256': graph_hash}


def _reader_cleanup(actions, primary):
    """All cleanup attempted; first fatal retained, then first ordinary error."""
    selected = primary
    errors = []
    for action in actions:
        try:
            action()
        except BaseException as error:
            errors.append(error)
            fatal = lambda e: isinstance(e, MemoryError) or not isinstance(e, Exception)
            if selected is None or (fatal(error) and not fatal(selected)):
                selected = error
    if selected is not None:
        others = [e for e in ([primary] if primary is not None else []) + errors if e is not selected]
        if others:
            try:
                if selected.__cause__ is not None and all(selected.__cause__ is not e for e in others):
                    others.append(selected.__cause__)
                selected.__cause__ = BaseExceptionGroup('treatment metadata cleanup failures', others)
            except BaseException:
                pass
        raise selected


def _owned_metadata_bytes(path):
    """Transfer one real fd to one stream; failures preserve acquired ownership."""
    import os, stat
    fd = None
    stream = None
    primary = None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        stream = os.fdopen(fd, 'rb')
        fd = None  # Ownership transfers only after fdopen returned successfully.
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'regular metadata required')
        raw = stream.read(LIMIT + 1)
    except BaseException as error:
        primary = error
    finally:
        _reader_cleanup((lambda: stream.close() if stream is not None else None,
                         lambda: os.close(fd) if fd is not None else None), primary)
    return raw


def _reader(run, name, metadata=True):
    from ..admission import local_path
    role(name)
    item = run.admission.inputs[name]
    path = local_path(run.admission.root, item['path'])
    # Bound before ResearchRun.read_input (which otherwise reads the whole body).
    require(path.is_file() and not path.is_symlink(), 'regular admitted input required')
    if metadata:
        require(path.stat().st_size <= LIMIT, 'metadata exceeds 4MiB')
        raw = _owned_metadata_bytes(path)
        require(len(raw) <= LIMIT and sha(raw) == item['sha256'], 'metadata extent/hash differs')
        return json.loads(raw), raw, path
    from .provenance import file_hash
    require(file_hash(path) == item['sha256'], 'component bytes changed')
    return item['sha256'], path


def _closed(run, claim_role, terminal_role):
    from ..verify import verify_claim
    from .job import _terminal
    claim, raw, path = _reader(run, claim_role)
    terminal, traw, tpath = _reader(run, terminal_role)
    require(path == run.admission.root/'research_runs'/claim['experiment_id']/'claim.json', 'actual retained claim path required')
    require(tpath == path.parent/(terminal['status'] + '.json') and terminal['status'] in ('complete', 'failed'), 'actual terminal path required')
    require(not (path.parent/('failed.json' if terminal['status'] == 'complete' else 'complete.json')).exists(), 'contradictory terminal')
    require(verify_claim(path.parent) == claim, 'committed source/registration claim differs')
    require(_terminal(tpath, claim, sha(raw), run.admission.root, terminal['status']) == terminal, 'terminal output closure differs')
    return claim, terminal, raw, traw


def admit_treatment(run, input_name, *, asset, variant, weeks):
    from ..lifecycle import ResearchRun
    from .treatment_contract import schema as producer_schema, parent_receipts
    require(type(run) is ResearchRun, 'genuine active ResearchRun required')
    run._active(); run._check_source()
    require(type(PRODUCER_SOURCE_PINS) is dict and PRODUCER_SOURCE_PINS, 'UNADMITTED: exact reviewed producer successor pins required')
    from .provenance import file_hash
    source_path = Path(__file__)
    require(run.admission.experiment['source_files'].get(str(source_path.relative_to(run.admission.root))) == file_hash(source_path), 'treatment verifier source is not admitted')
    value, body, _ = _reader(run, input_name)
    schema(value, asset, variant, weeks)
    result = {}
    for week, reference in value['weeks'].items():
        claim, terminal, craw, _ = _closed(run, reference['claim_input'], reference['terminal_input'])
        require(all(claim['experiment']['source_files'].get(k) == v for k, v in PRODUCER_SOURCE_PINS.items()), 'unreviewed producer source closure')
        plan, praw, _ = _reader(run, reference['plan_input'])
        producer_schema(plan)
        require((plan['asset'], plan['variant']) == (asset, variant) and week in plan['expected_weeks'], 'producer plan differs')
        job, jraw, _ = _reader(run, reference['job_input'])
        require(job['kind'] == 'treatments' and claim['inputs']['execution_job']['sha256'] == sha(jraw) and claim['inputs'][job['payload']['plan_input']]['sha256'] == sha(praw), 'actual registered job/plan differs')
        ledger, lraw, lpath = _reader(run, reference['ledger_input'])
        expected_ledger = run.admission.root/'research_runs'/claim['experiment_id']/'outputs'/'cell-ledger.json'
        if terminal['status'] == 'failed':
            expected_ledger = run.admission.root/PREFIX/'runs'/claim['experiment_id']/'postmortem-cells.json'
        require(lpath == expected_ledger, 'actual complete/postmortem ledger path differs')
        row = disposition(claim, terminal, ledger, sha(craw), sha(lraw), plan, week, variant, asset, absent=reference['disposition_input'] is None)
        actual_row_path = run.admission.root/PREFIX/'treatments'/claim['experiment_id']/(row['id']+'.json')
        if reference['disposition_input'] is None:
            require(row['status'] == 'unavailable' and terminal['status'] == 'failed' and not actual_row_path.is_symlink() and not actual_row_path.exists() and actual_row_path.resolve() == actual_row_path, 'only failed absent cell may use postmortem absence')
        else:
            saved, _, spath = _reader(run, reference['disposition_input'])
            require(saved == row and spath == actual_row_path, 'actual per-cell disposition differs')
        require(row['status'] == reference['status'], 'treatment status changed')
        if row['status'] == 'unavailable':
            result[week] = {'status': 'unavailable', 'reason': row['reason'], 'evidence_hashes': [sha(craw), sha(lraw)]}
            continue
        receipt, rraw, rpath = _reader(run, reference['receipt_input'])
        coverage, coraw, copath = _reader(run, reference['coverage_input'])
        outer, mraw, mpath = _reader(run, reference['manifest_input'])
        require(mpath == run.admission.root/row['manifest_path'] and rpath == mpath.parent/'treatment.json' and copath == mpath.parent/'coverage.json', 'actual graph receipt paths differ')
        def original(name, metadata=True):
            alias = reference['aliases'][name]
            require(run.admission.inputs[alias]['sha256'] == claim['inputs'][name]['sha256'], 'original producer input alias differs')
            return _reader(run, alias, metadata)
        parent_ref = plan['parents'][week]
        for key, name in parent_ref.items():
            if key != 'components': original(name)
        parent_outer, pmraw, _ = original(parent_ref['manifest_input'])
        pc, pt, pcraw, ptraw = _closed(run, reference['aliases'][parent_ref['claim_input']], reference['aliases'][parent_ref['terminal_input']])
        pl, plraw, _ = original(parent_ref['ledger_input'])
        parent_row = parent_receipts(pc, pt, pl, sha(pcraw), sha(pmraw), week, asset)
        require(pt['cells'] == pl and pt['output_sha256']['cell-ledger.json'] == sha(plraw), 'parent completed ledger differs')
        pcoverage, pcovraw, _ = original(parent_ref['coverage_input'])
        require(parent_row['coverage_sha256'] == sha(pcovraw), 'parent ledger coverage differs')
        require(coverage['members'] == pcoverage['members'] and pcoverage['claim_sha256'] == sha(pcraw) and pcoverage['graph_manifest_sha256'] == sha(pmraw), 'original complete coverage differs')
        for field, raw in (('parent_coverage_sha256', pcovraw), ('parent_claim_sha256', pcraw), ('parent_terminal_sha256', ptraw), ('parent_ledger_sha256', plraw)):
            require(receipt[field] == sha(raw), 'parent receipt hash differs')
        graph, parent = outer, parent_outer
        if asset == 'BTC':
            graph, grow, _ = _reader(run, reference['components']['graph/manifest.json'])
            parent, pgraw, _ = original(parent_ref['components']['graph/manifest.json'])
            require(sha(grow) == outer['graph_manifest_sha256'] and sha(pgraw) == parent_outer['graph_manifest_sha256'], 'BTC inner manifest differs')
        for manifest, components, reader, base in ((graph, reference['components'], lambda r: _reader(run, r, False), mpath.parent), (parent, parent_ref['components'], lambda r: original(r, False), original(parent_ref['manifest_input'])[2].parent)):
            expected = {('graph/' if asset == 'BTC' else '')+v['path']: v['sha256'] for v in manifest['arrays'].values()}
            if asset == 'BTC':
                current_outer = outer if manifest is graph else parent_outer
                expected.update({'graph/manifest.json': current_outer['graph_manifest_sha256'], **{n+'.hex': v['sha256'] for n,v in current_outer['sidecars'].items()}})
            require(set(components) == set(expected), 'exact component denominator differs')
            for member, expected_hash in expected.items():
                actual_hash, actual_path = reader(components[member])
                require(actual_hash == expected_hash and actual_path == base/member, 'component hash/location differs')
        result[week] = graph_join(receipt, row, graph, sha(mraw), coverage, sha(coraw), sha(rraw), claim, sha(craw), sha(praw), parent, sha(pmraw), week, asset, variant)
        result[week]['population_manifest_sha256'] = sha(canonical(graph)) if asset == 'ETH' else sha(grow)
        if asset == 'ETH':
            result[week]['population_manifest_sha256'] = sha(mraw)
    run._active(); run._check_source()
    return result


def verify_example_metadata(rows, admitted):
    """Only dates, hashes and availability; no prices/targets/test labels read."""
    for dates, hashes, available in rows:
        require(len(dates) == len(hashes) == len(available), 'example treatment membership lengths differ')
        for date, h, a in zip(dates, hashes, available, strict=True):
            step = stamp(date+'T00:00:00Z') + timedelta(days=1)
            lagged = step - timedelta(days=1)
            end = (lagged-timedelta(days=lagged.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            week = (end-timedelta(days=7)).isoformat().replace('+00:00', 'Z')
            r = admitted[week]
            require(r['status'] == 'complete' and r['graph_hash'] == h and r['available_at'] == a and stamp(a) <= step, 'example consumed unavailable/wrong/late treatment graph')


def preflight_treatment(run, reference, cell, examples):
    if cell['variant'] not in ('whale', 'fund'):
        require('treatment_input' not in reference, 'unexpected treatment evidence on untreated population')
        return
    require('treatment_input' in reference and 'treatment_weeks' in reference, 'mandatory treatment population receipt missing')
    require('treatment_population_plan_input' in reference, 'full population calendar/denominator input required')
    population_plan, _, _ = _reader(run, reference['treatment_population_plan_input'])
    require(population_plan.get('treatment_input') == reference['treatment_input'], 'population and fit treatment contracts differ')
    calendar, _, _ = _reader(run, population_plan['calendar_input'])
    from .population_assembly import required_weeks
    from .contracts import Fold
    fold = Fold(**population_plan['fold'])
    require(fold.id == cell['fold'] and fold.member_hash == examples.fold_hash, 'actual fold treatment binding differs')
    weeks = required_weeks(fold, calendar['lookback_days'])
    require(list(weeks) == reference['treatment_weeks'] == population_plan['expected_weeks'], 'full fit treatment week denominator differs')
    admitted = admit_treatment(run, reference['treatment_input'], asset=cell['asset'], variant=cell['variant'], weeks=weeks)
    verify_example_metadata(((x.input_dates, x.graph_hashes, x.graph_available_at) for partition in (examples.train, examples.test) for x in partition), admitted)
