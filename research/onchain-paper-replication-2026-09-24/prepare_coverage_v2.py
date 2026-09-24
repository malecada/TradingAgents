"""Update traceability only after the exact expanded synthetic suite succeeds."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import hashlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
P = 'tradingagents/research/onchain_replication/'
T = 'tests/research/onchain_replication/'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    xml = HERE/'replay/expanded-synthetic-01.xml'
    guard = HERE/'replay/expanded-synthetic-01-guard/final.json'
    final = json.loads(guard.read_bytes())
    if final['phase'] != 'complete' or final['child_exit_code'] != 0 or final['cleanup_verified'] is not True:
        raise ValueError('expanded suite has no successful contained terminal')
    source_file = HERE/'replay/expanded-synthetic-01-source.json'
    snapshot = json.loads(source_file.read_bytes())
    if any(sha(ROOT/p) != value for p, value in snapshot.items()):
        raise ValueError('code/test source changed after expanded-suite freeze')
    root = ET.parse(xml).getroot()
    tests = {}
    counts = {'passed': 0, 'failed': 0, 'errors': 0, 'skipped': 0}
    for case in root.iter('testcase'):
        status = 'failed' if case.find('failure') is not None else 'errors' if case.find('error') is not None else 'skipped' if case.find('skipped') is not None else 'passed'
        counts[status] += 1
        path = case.attrib['classname'].replace('.', '/')+'.py'
        tests.setdefault(path, []).append({'test': case.attrib['name'], 'status': status})
    if counts['failed'] or counts['errors']:
        raise ValueError('expanded-suite failures remain')
    value = json.loads((HERE/'implementation-coverage-v1.json').read_bytes())
    additions = {
      'F01': (['btc_source','range_source','parquet_ranges','price_source'], ['btc_source','range_source','parquet_ranges']),
      'F02': (['btc_weekly','btc_store','graph_store'], ['btc_weekly','btc_store','weekly']),
      'F03': (['price_source'], ['price_source','prices']),
      'F09': (['feature_pipeline','registered_features','component_store','feature_journal'], ['feature_pipeline','registered_features','component_store','feature_journal']),
      'F14': (['run','evaluation','job','job_payload','journal_recovery'], ['run','evaluation','job','job_payload','journal_recovery']),
      'F17': (['feature_pipeline','registered_features','component_store','model_registry'], ['feature_pipeline','registered_features','graph_baselines','registry']),
      'F18': (['btc_subsets','btc_store'], ['btc_subsets','btc_store']),
      'F19': (['btc_subsets'], ['btc_subsets']),
      'F20': (['verification','comparison'], ['verification','comparison'])}
    limitations = {
      'F01':'ETH retained and BTC selected-column decoders/capture are integrated as components; real full-source body admission remains pending.',
      'F02':'ETH/BTC exact aggregation and store components pass fixtures; real raw-to-graph independent reconciliation and full history remain pending.',
      'F03':'Parser and bounded immutable capture software verified; actual price source capture/admission has not occurred.',
      'F04':'One real resource-pilot week sampled512 neighborhoods; full fold dictionary population not executed.',
      'F05':'One real resource-pilot week produced32 motifs from512 samples; full training-fold resource feasibility remains unproved.',
      'F09':'First real full-node MCM became unavailable at frozen10,000-node neighborhood ceiling; no truncation or larger cap used.',
      'F14':'Registered batch/payload/recovery integration verified synthetically; no real financial fit. Full-history source-to-population preparation/admission remains pending.',
      'F17':'Graph representation production/reuse and temporal assembly are integrated and synthetic-tested; full-size/history execution remains pending.',
      'F18':'ETH incident-value and BTC exact-rational incident sidecars/subset rebuilding implemented; empirical treatments remain unexecuted.'}
    for record in value['records']:
        rid = record['id']
        code = set(record['code'])
        files = set(record['tests'])
        if rid in additions:
            extra_code, extra_tests = additions[rid]
            code.update(P+n+'.py' for n in extra_code)
            files.update(T+'test_'+n+'.py' for n in extra_tests)
        # Never make a nonexistent planned module into apparent implementation evidence.
        absent = sorted(p for p in code if not (ROOT/p).is_file())
        if absent:
            raise ValueError('unimplemented code mapping: '+str(absent))
        record['code'] = {p: sha(ROOT/p) for p in sorted(code)}
        if not files <= set(tests):
            raise ValueError('coverage test module absent from expanded suite: '+str(sorted(files-set(tests))))
        record['tests'] = {p: tests[p] for p in sorted(files)}
        if code and not any(t['status'] == 'passed' for cases in record['tests'].values() for t in cases):
            raise ValueError('implemented record has no current passing test: '+rid)
        if rid in limitations:
            record['limitation'] = limitations[rid]
    by_id = {r['id']: r for r in value['records']}
    mapping = {'U01':'F01','U02':'F02','U03':'F01','U04':'F03','U05':'F14','U06':'F04','U07':'F07',
               'U08':'F11','U09':'F14','U10':'F14','U11':'F20','U12':'F19','U13':'F18','U14':'F08'}
    for unknown, implemented in mapping.items():
        row = by_id[unknown]
        row['implemented_choice_reference'] = implemented
        row['code'] = dict(by_id[implemented]['code'])
        row['tests'] = dict(by_id[implemented]['tests'])
        row['qualification'] = 'Links implement the declared assumption or refusal; they do not recover a missing published setting.'
    value['schema_version'] = 2
    value['scope'] = 'Current synthetic implementation traceability; no full empirical coverage or numerical agreement claim. Prior report retained unchanged.'
    value['previous_report'] = {'path': str((HERE/'implementation-coverage-v1.json').relative_to(ROOT)), 'sha256': sha(HERE/'implementation-coverage-v1.json')}
    value['validation'] = {**counts, 'path': str(xml.relative_to(ROOT)), 'sha256': sha(xml),
        'source_snapshot': str(source_file.relative_to(ROOT)), 'source_snapshot_sha256': sha(source_file),
        'guard': str(guard.relative_to(ROOT)), 'guard_sha256': sha(guard)}
    with (HERE/'implementation-coverage-v2.json').open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
    print(json.dumps({'records':len(value['records']), 'validation':value['validation']}, sort_keys=True))


if __name__ == '__main__':
    main()
