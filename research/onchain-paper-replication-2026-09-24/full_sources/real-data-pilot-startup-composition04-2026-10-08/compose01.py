"""Join already-reviewed sources without copying or installing them."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
F = HERE.parent


def ref(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def verify(value):
    path = ROOT/value['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != value['sha256']:
        raise ValueError('immutable reference changed: '+str(path))
    return path


def main():
    previous = F/'real-data-pilot-startup-composition03-2026-10-08/COMPOSITION03.json'
    body = json.loads(previous.read_bytes())
    files = dict(body['files'])
    event_review = F/'real-data-pilot-event-timing-review01-2026-10-08/SOURCE_REVIEW01.json'
    accepted = json.loads(event_review.read_bytes())
    if accepted['decision'] != 'accepted-source-only':
        raise ValueError('event timing source review refused')
    for name, row in accepted['files'].items():
        candidate = row['candidate']
        verify(candidate)
        baseline = row['baseline']
        verify(baseline)
        if name in files and files[name]['sha256'] != baseline['sha256']:
            raise ValueError('composition baseline mismatch: '+name)
        files[name] = {'source': candidate['path'], 'sha256': candidate['sha256']}
    for name, value in files.items():
        path = verify({'path':value['source'], 'sha256':value['sha256']})
        ast.parse(path.read_text(), filename=str(ROOT/'tradingagents/research/onchain_replication'/name))
    reviews = list(body['inherited_reviews'])+[ref(event_review)]
    for row in reviews:
        verify(row)
    root_review = F/'real-data-pilot-storage-root-review01-2026-10-08/SOURCE_REVIEW01.json'
    metadata_review = root_review.parent/'metadata-review01/SOURCE_REVIEW01.json'
    original_metadata_check = F/'real-data-pilot-storage-metadata-check01-2026-10-08/CHECK01.json'
    result = {'status':'SOURCE_ONLY_NOT_INSTALLED_NOT_ENTRY_RELEASED',
              'prior_composition':ref(previous), 'files':files,
              'inherited_reviews':reviews,
              'entry_helper_reviews':[ref(root_review),ref(metadata_review)],
              'actual_original_metadata_check':ref(original_metadata_check),
              'scope':'Ten exact core sources with reused independent reviews. Adds inclusive event-publication timing to constructor/preparation reuse, startup/retention timing and explicit identity forwarding. Referenced bodies remain in their immutable candidate directories; no additional copies, source integration, registration or launch.',
              'static_reduction':body['static_reduction'],
              'syntactic_compilation':len(files),
              'limitations':['No measured savings or whole-pilot capacity follows.',
                             'Current21 must close and its complete declared outcome be recovered before dependent integration/entry.',
                             'Fresh entry, metadata templates, bindings, runtime/source pins and cumulative allowance remain required.']}
    for row in result['entry_helper_reviews']+[result['actual_original_metadata_check']]:
        verify(row)
    with (HERE/'COMPOSITION04.json').open('x') as stream:
        json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({'core_sources':len(files),'manifest':ref(HERE/'COMPOSITION04.json'),'status':result['status']},sort_keys=True))


if __name__ == '__main__':
    main()
