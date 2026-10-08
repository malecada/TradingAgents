"""Reference the accepted diagnostic heartbeat without copying core bodies."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
F = HERE.parent


def ref(path):
    return {'path': str(path.relative_to(ROOT)),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def verify(row):
    path = ROOT / row['path']
    if ref(path) != row:
        raise ValueError('immutable reference changed: ' + str(path))
    return path


def main():
    previous = F / 'real-data-pilot-startup-composition04-2026-10-08/COMPOSITION04.json'
    result = json.loads(previous.read_bytes())
    review = F / 'real-data-pilot-diagnostic-heartbeat-review01-2026-10-08/SOURCE_REVIEW01.json'
    accepted = json.loads(review.read_bytes())
    if accepted['decision'] != 'accepted-source-only':
        raise ValueError('heartbeat source review refused')
    name = 'real_pilot_partial_progress.py'
    if result['files'][name]['sha256'] != accepted['baseline_sha256']:
        raise ValueError('heartbeat composition baseline mismatch')
    candidate = F / 'real-data-pilot-diagnostic-heartbeat01-2026-10-08' / name
    if ref(candidate)['sha256'] != accepted['candidate_sha256']:
        raise ValueError('accepted heartbeat body changed')
    result['files'][name] = {'source': str(candidate.relative_to(ROOT)),
                             'sha256': accepted['candidate_sha256']}
    result['prior_composition'] = ref(previous)
    result['inherited_reviews'].append(ref(review))
    for row in result['inherited_reviews'] + result['entry_helper_reviews'] + [result['actual_original_metadata_check']]:
        verify({'path': row['path'], 'sha256': row['sha256']})
    for name, row in result['files'].items():
        path = verify({'path': row['source'], 'sha256': row['sha256']})
        ast.parse(path.read_text(), filename=name)
    result['scope'] = ('Ten exact reviewed core bodies; replaces only the diagnostic '
                       'with bounded post-callback heartbeat. No copies, installation, '
                       'registration or numerical execution.')
    result['heartbeat'] = {'sampled_interval_seconds': 60, 'max_automatic_writes': 480,
                           'blocking_callback_refresh_guaranteed': False,
                           'mandatory_writes_unchanged': True}
    with (HERE / 'COMPOSITION05.json').open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'core_sources': len(result['files']),
                      'manifest': ref(HERE / 'COMPOSITION05.json'),
                      'status': result['status']}, sort_keys=True))


if __name__ == '__main__':
    main()
