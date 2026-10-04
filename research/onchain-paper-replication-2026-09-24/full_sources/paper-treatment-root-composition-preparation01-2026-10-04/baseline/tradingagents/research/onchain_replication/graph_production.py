"""Registered source-only raw-to-graph producer with retained aggregation evidence.

All weeks in one build share a ledger. Exact BTC sidecars remain bound to their
outer manifest. Graph outputs require explicit admission to a later population
claim; producing them does not admit a fit or consume an implicit extra claim.
"""
from datetime import timedelta
import json
from pathlib import Path

from ..lifecycle import ResearchRun, _immutable
from .aggregation import SourceBoundary
from .cache import cache_key
from .provenance import digest, durable_mkdir, file_hash, sync_directory, utc, require_hash
from .weekly import build_weekly, stamp, week_start, _complete

PREFIX = 'research_artifacts/onchain-paper-replication-2026-09-24/sources'


def _plan(run, name):
    raw = run.read_input(name)
    plan = json.loads(raw)
    base = {'schema_version', 'mode', 'asset', 'graph_config_input', 'coverage', 'expected_weeks'}
    if (not isinstance(plan, dict) or plan.get('schema_version') != 1
            or plan.get('mode') not in ('build', 'reuse') or plan.get('asset') not in ('ETH', 'BTC')
            or set(plan) != base | ({'source_inputs', 'decoder'} if plan.get('mode') == 'build' else {'graphs'})):
        raise ValueError('graph production plan schema differs')
    coverage = plan['coverage']
    if not isinstance(coverage, list) or not coverage:
        raise ValueError('explicit complete-week coverage required')
    weeks = []
    for interval in coverage:
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError('invalid coverage interval')
        first, last = map(utc, interval)
        if first >= last or any(week_start(t, 'MON') != t for t in interval):
            raise ValueError('complete Monday-week coverage required')
        cursor = first
        while cursor < last:
            weeks.append(stamp(cursor)); cursor += timedelta(days=7)
    if weeks != sorted(set(weeks)) or weeks != plan['expected_weeks']:
        raise ValueError('graph week denominator differs')
    windows = [(w['start'], w['end']) for w in run.admission.experiment['windows']]
    if any(not _complete(utc(a), utc(b), windows) for a, b in coverage):
        raise ValueError('graph coverage outside registered windows')
    if plan['mode'] == 'reuse':
        if not isinstance(plan['graphs'], dict) or set(plan['graphs']) != set(weeks):
            raise ValueError('reuse graph denominator differs')
        for ref in plan['graphs'].values():
            if not isinstance(ref, dict) or set(ref) != {'input', 'source_hashes', 'coverage_input'} or not ref['source_hashes']:
                raise ValueError('reuse requires graph input and source membership')
        return plan, digest(raw)
    sources = plan['source_inputs']
    if (not isinstance(sources, list) or not sources or len(sources) != len(set(sources))
            or any(not isinstance(s, str) or not s for s in sources)):
        raise ValueError('explicit unique source inputs required')
    decoder = plan['decoder']
    if plan['asset'] == 'ETH':
        if not isinstance(decoder, dict) or set(decoder) != {'schema_input'}:
            raise ValueError('ETH schema input required')
    elif decoder != {'precision_policy': 'binary64_satoshi_grid_inverse_v1'}:
        raise ValueError('BTC precision policy differs')
    return plan, digest(raw)



def _source_inventory(run, plan):
    """Validate all declared partitions before decoding; seeing rows is not coverage."""
    sources = []
    members = []
    seen = set()
    for name in plan['source_inputs']:
        raw = run.read_input(name)
        source = json.loads(raw)
        if source.get('status') != 'complete' or type(source.get('expected_rows')) is not int or source['expected_rows'] < 0:
            raise ValueError('source coverage requires complete counted partitions')
        if plan['asset'] == 'ETH':
            first, last = source['start_utc'], source['end_utc']
            if utc(first) >= utc(last) or not source.get('members') or source.get('expected_members') != len(source['members']):
                raise ValueError('invalid source coverage inventory')
            selected = []
            for m in source['members']:
                a, b = m.get('start_utc', first), m.get('end_utc', last)
                if not utc(first) <= utc(a) < utc(b) <= utc(last):
                    raise ValueError('member coverage outside source interval')
                selected.append((a, b, m['sha256'], m['expected_rows']))
            if any(type(n) is not int or n < 0 for a,b,h,n in selected) or sum(n for a,b,h,n in selected) != source['expected_rows']:
                raise ValueError('source coverage row denominator differs')
            if not _complete(utc(first), utc(last), [(a,b) for a,b,h,n in selected]):
                raise ValueError('incomplete source member coverage')
        else:
            first = source['date']+'T00:00:00Z'
            last = stamp(utc(first)+timedelta(days=1))
            selected = [(first,last,source['sha256'],source['expected_rows'])]
        for a,b,h,n in selected:
            require_hash(h)
            if h in seen:
                raise ValueError('duplicate source member across partitions')
            seen.add(h)
            if not _complete(utc(a), utc(b), plan['coverage']):
                raise ValueError('source interval outside graph coverage')
            members.append({'start_utc':a,'end_utc':b,'sha256':h,'expected_rows':n,
                            'source_input':name,'source_manifest_sha256':digest(raw)})
        sources.append((source,digest(raw)))
    intervals = [(m['start_utc'],m['end_utc']) for m in members]
    if any(not _complete(utc(a),utc(b),intervals) for a,b in plan['coverage']):
        raise ValueError('incomplete source partition coverage')
    return sources, members



def _verify_graph_coverage(proof, graph, manifest_sha):
    required = {'schema_version','asset','week','end_utc','graph_config_hash',
                'graph_manifest_sha256','members','claim_sha256','plan_sha256'}
    if (not isinstance(proof,dict) or set(proof) != required or proof['schema_version'] != 1
            or proof['asset'] != graph.asset or proof['week'] != graph.start_utc
            or proof['end_utc'] != graph.end_utc or proof['graph_config_hash'] != graph.graph_config_hash
            or proof['graph_manifest_sha256'] != manifest_sha):
        raise ValueError('graph coverage proof identity differs')
    require_hash(proof['claim_sha256']); require_hash(proof['plan_sha256'])
    members = proof['members']
    if not isinstance(members,list) or not members:
        raise ValueError('graph coverage proof has no sources')
    hashes = []
    intervals = []
    for member in members:
        if set(member) != {'start_utc','end_utc','sha256','expected_rows','source_input','source_manifest_sha256'}:
            raise ValueError('graph coverage member fields differ')
        require_hash(member['sha256']); require_hash(member['source_manifest_sha256'])
        a,b = utc(member['start_utc']),utc(member['end_utc'])
        if (not a < b or a >= utc(graph.end_utc) or b <= utc(graph.start_utc)
                or type(member['expected_rows']) is not int or member['expected_rows'] < 0):
            raise ValueError('graph coverage member interval/count differs')
        hashes.append(member['sha256']); intervals.append((member['start_utc'],member['end_utc']))
    if len(hashes) != len(set(hashes)) or not set(graph.source_hashes) <= set(hashes):
        raise ValueError('graph coverage source identities differ')
    if not _complete(utc(graph.start_utc),utc(graph.end_utc),intervals):
        raise ValueError('incomplete graph source coverage')


def produce_registered_graphs(run, plan_input):
    if not isinstance(run, ResearchRun):
        raise ValueError('admitted graph source run required')
    run._active(); run._check_source()
    plan, identity = _plan(run, plan_input)
    config = json.loads(run.read_input(plan['graph_config_input']))
    if config.get('week_anchor') != 'MON':
        raise ValueError('graph week anchor differs')
    source_ids = [f'source-{i:06d}' for i in range(len(plan.get('source_inputs', [])))]
    graph_ids = ['graph-'+week[:10] for week in plan['expected_weeks']]
    ids = source_ids + graph_ids
    if run.admission.experiment['cells'] != ids:
        raise ValueError('registered graph/source denominator differs')
    root = run.admission.root
    directory = root/PREFIX/run.admission.experiment_id
    durable_mkdir(directory.parent); directory.mkdir(exist_ok=False); sync_directory(directory.parent)
    _immutable(directory/'intent.json', {'plan_sha256': identity, 'source_commit': run.admission.source,
        'claim_sha256': run._claim_sha256, 'graph_config_hash': cache_key(config),
        'cells': ids, 'validation_scope': 'whole registered stream; unobserved chain history not verified'})
    scratch = directory/'scratch'; durable_mkdir(scratch)
    workspace = directory/'aggregation'
    rows = {}; graphs = {}; iterator = None; reason = None; source_inventory = []; coverage_members = []

    def record(row):
        _immutable(directory/(row['id']+'.json'), row)
        rows[row['id']] = row

    if plan['mode'] == 'reuse':
        from ..admission import local_path
        from .graph_store import load_graph
        from .btc_store import load_btc_graph
        for week, cell in zip(plan['expected_weeks'], graph_ids, strict=True):
            try:
                reference = plan['graphs'][week]
                raw = run.read_input(reference['input'])
                path = local_path(root, run.admission.inputs[reference['input']]['path'])
                value = (load_graph if plan['asset'] == 'ETH' else load_btc_graph)(path, digest(raw))
                graph = value if plan['asset'] == 'ETH' else value.graph
                end = utc(week)+timedelta(days=7)
                if utc(graph.end_utc) != end or utc(graph.available_at) < end+timedelta(days=1):
                    raise ValueError('reused graph interval/availability differs')
                if (graph.asset != plan['asset'] or graph.start_utc != week
                        or graph.graph_config_hash != cache_key(config)
                        or list(graph.source_hashes) != reference['source_hashes']):
                    raise ValueError('reused graph identity/source membership differs')
                coverage_raw = run.read_input(reference['coverage_input'])
                _verify_graph_coverage(json.loads(coverage_raw),graph,digest(raw))
                coverage_path = local_path(root,run.admission.inputs[reference['coverage_input']]['path'])
                ref = {'manifest_path': str(path.relative_to(root)), 'manifest_sha256': digest(raw),
                       'raw_count': graph.raw_count, 'admitted_count': graph.admitted_count,
                       'exclusion_counts': dict(graph.exclusion_counts),
                       'source_hashes': list(graph.source_hashes), 'reused': True,
                       'coverage_path': str(coverage_path.relative_to(root)), 'coverage_sha256':digest(coverage_raw)}
                record({'id': cell, 'status': 'complete', **ref})
                graphs[week] = ref
                del graph, value
            except Exception as error:
                record({'id': cell, 'status': 'unavailable', 'reason': type(error).__name__+': '+str(error)})
        summary = {'asset': plan['asset'], 'plan_sha256': identity, 'graph_config_hash': cache_key(config),
            'expected_weeks': plan['expected_weeks'], 'graphs': graphs, 'workspace': None,
            'financial_run_admitted': False,
            'qualification': 'verified reuse only; no decoding and no new cross-graph transaction validation; later source/population admission required'}
        _immutable(directory/'result.json', summary)
        return [rows[cell] for cell in ids], summary, directory

    def events():
        seen = set()
        if plan['asset'] == 'ETH':
            from .eth_source import decode_eth
            schema = json.loads(run.read_input(plan['decoder']['schema_input']))
        else:
            from .btc_source import decode_parquet
        for cell, name, (source, source_sha) in zip(source_ids, plan['source_inputs'], source_inventory, strict=True):
            total = 0
            if plan['asset'] == 'ETH':
                if (source.get('status') != 'complete' or not source.get('members')
                        or source.get('expected_members') != len(source['members'])
                        or sum(m['expected_rows'] for m in source['members']) != source['expected_rows']):
                    raise ValueError('source inventory status/count differs')
                if not _complete(utc(source['start_utc']), utc(source['end_utc']), plan['coverage']):
                    raise ValueError('source interval outside graph coverage')
                for member in source['members']:
                    sha = member['sha256']
                    if sha in seen:
                        raise ValueError('duplicate source member across partitions')
                    seen.add(sha)
                    single = {**source, 'members': [member], 'expected_members': 1,
                              'expected_rows': member['expected_rows'], 'scratch': str(scratch)}
                    count = 0
                    for event in decode_eth(single, schema):
                        yield event; count += 1
                    # Verify the underlying member after decoder exhaustion too.
                    if file_hash(Path(member['path'])) != sha:
                        raise ValueError('source member changed during decoding')
                    yield SourceBoundary(sha, count)
                    total += count
            else:
                sha = source['sha256']
                if sha in seen:
                    raise ValueError('duplicate source member across partitions')
                seen.add(sha)
                for event in decode_parquet(source, **plan['decoder']):
                    yield event; total += 1
                yield SourceBoundary(sha, total)
            record({'id': cell, 'status': 'complete', 'rows': total,
                    'manifest_sha256': source_sha, 'input': name})

    try:
        source_inventory, coverage_members = _source_inventory(run, plan)
        _immutable(directory/'source-coverage.json', {'plan_sha256':identity,'members':coverage_members})
        if plan['asset'] == 'ETH':
            from .graph_store import save_graph
            iterator = build_weekly(events(), config, coverage=plan['coverage'], scratch=scratch, workspace=workspace)
        else:
            from .btc_weekly import build_btc_weekly
            from .btc_store import save_btc_graph
            iterator = build_btc_weekly(events(), config, coverage=plan['coverage'], scratch=scratch, workspace=workspace)
        for value in iterator:
            graph = value if plan['asset'] == 'ETH' else value.graph
            week = graph.start_utc
            if graph.asset != plan['asset'] or week not in plan['expected_weeks'] or week in graphs:
                raise ValueError('produced graph outside registered denominator')
            path = (save_graph if plan['asset'] == 'ETH' else save_btc_graph)(directory/('graph-'+week[:10]), value)
            ref = {'manifest_path': str(path.relative_to(root)), 'manifest_sha256': file_hash(path),
                   'raw_count': graph.raw_count, 'admitted_count': graph.admitted_count,
                   'exclusion_counts': dict(graph.exclusion_counts), 'source_hashes': list(graph.source_hashes)}
            proof = {'schema_version':1,'asset':graph.asset,'week':week,'end_utc':graph.end_utc,
                'graph_config_hash':graph.graph_config_hash,'graph_manifest_sha256':ref['manifest_sha256'],
                'claim_sha256':run._claim_sha256,'plan_sha256':identity,
                'members':[m for m in coverage_members if utc(m['start_utc']) < utc(graph.end_utc) and utc(m['end_utc']) > utc(week)]}
            _verify_graph_coverage(proof,graph,ref['manifest_sha256'])
            coverage_path = path.parent/'coverage.json'
            _immutable(coverage_path,proof)
            ref.update(coverage_path=str(coverage_path.relative_to(root)),coverage_sha256=file_hash(coverage_path))
            record({'id': 'graph-'+week[:10], 'status': 'complete', **ref})
            graphs[week] = ref
        if set(graphs) != set(plan['expected_weeks']):
            raise ValueError('produced graph denominator incomplete')
    except Exception as error:
        reason = type(error).__name__+': '+str(error)
    finally:
        if iterator is not None:
            iterator.close()
    for cell in ids:
        if cell not in rows:
            record({'id': cell, 'status': 'unavailable', 'reason': reason or 'no durable graph/source disposition'})
    summary = {'asset': plan['asset'], 'plan_sha256': identity, 'graph_config_hash': cache_key(config),
        'expected_weeks': plan['expected_weeks'], 'graphs': graphs, 'reason': reason,
        'workspace': str(workspace.relative_to(root)), 'financial_run_admitted': False,
        'qualification': 'whole supplied stream validated; canonical chain and unobserved prevouts remain source dependent; outputs require later explicit admission'}
    _immutable(directory/'result.json', summary)
    return [rows[cell] for cell in ids], summary, directory
