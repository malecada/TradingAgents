"""Write prospective graph08 gate only after independent preservation closure.

Metadata-only preparation. Does not commit, admit, launch, or read source bodies.
The exact generated gate still needs independent release review.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from preservation_requirement import STORAGES, REQUIRED, verify_chain as verify
from previous_graph_requirement import verify as verify_previous_graph, VERIFY as PREVIOUS_VERIFY

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
OLD = HERE.with_name('graph-successor-07-2026-09-30')
NEW_ID = 'eth-paper-graph-resource-20260930-08'
OLD_ID = 'eth-paper-graph-resource-20260930-07'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path':str(path.relative_to(ROOT)), 'sha256':sha(path)}


def write_new(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def main():
    preservation = verify(ROOT)
    previous_graph = verify_previous_graph(ROOT)
    for name in ('gate.json','verification-reuse.json'):
        if (HERE/name).exists():
            raise FileExistsError('Preparation identity already exists; review retained bytes')
    g = json.loads((OLD/'gate.json').read_bytes())
    old = g['experiments'][OLD_ID]
    e = copy.deepcopy(old)
    e['charter'] = ref(HERE/'CHARTER.md')
    e['question'] = 'Complete the next chronologically unfinished original stress-week ETH graph, 2024-08-05 through 2024-08-12, under unchanged graph semantics and finite local limits.'
    e['windows'][0].update(start='2024-08-05T00:00:00Z', end='2024-08-12T00:00:00Z')
    e['cells'][-1] = 'graph-2024-08-05'
    for key, info in list(e['inputs'].items()):
        if key.startswith(('source_', 'mapping_')):
            del e['inputs'][key]
        elif Path(info['path']).parent == OLD.relative_to(ROOT):
            e['inputs'][key] = {**ref(HERE/Path(info['path']).name), 'dataset':'eth'}
    for i in range(7):
        wrapper = HERE/f'source-{i:02d}.json'
        e['inputs'][f'source_{i:02d}'] = {**ref(wrapper),'dataset':'eth'}
        for j, member in enumerate(json.loads(wrapper.read_bytes())['members']):
            mapping = Path(member['path'])
            if sha(mapping) != member['sha256']:
                raise ValueError('source mapping differs')
            e['inputs'][f'mapping_{i:02d}_{j:02d}'] = {**ref(mapping),'dataset':'eth'}
    for i, storage in enumerate(STORAGES):
        for name in (*REQUIRED, 'closure-review.json'):
            key = f'preservation_chain_{i}_'+name.replace('/','_').replace('.','_')
            e['inputs'][key] = {**ref(ROOT/storage/name),'dataset':'eth'}
    previous_run = ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/OLD_ID
    previous_ledger = ROOT/'research_runs'/OLD_ID
    prerequisites = [previous_ledger/'claim.json', previous_ledger/'complete.json',
                     previous_run/'owner.json', previous_run/'observer.json', previous_run/'guard/final.json',
                     OLD/'empirical-closure01.json', OLD/'CLOSURE_REVIEW.md']
    prerequisites += [ROOT/PREVIOUS_VERIFY/n for n in ('result.json','guard01/final.json','closure01.json','CLOSURE_REVIEW.md','closure-review.json')]
    for i,p in enumerate(prerequisites):
        e['inputs'][f'previous_graph_{i:02d}'] = {**ref(p),'dataset':'eth'}
    e['source_files'] = {}
    for name, expected in old['source_files'].items():
        p = ROOT/name
        if p.parent == OLD:
            p = HERE/p.name
        elif sha(p) != expected:
            raise ValueError('previous verified source changed: '+name)
        e['source_files'][str(p.relative_to(ROOT))] = sha(p)
    for name in ('preservation_requirement.py', 'prepare_registration.py', 'previous_graph_requirement.py'):
        p = HERE/name
        e['source_files'][str(p.relative_to(ROOT))] = sha(p)
    e['cumulative_budget_extension'] = {'extension':ref(HERE/'extension.proposed.json'), 'review':ref(HERE/'extension-review.json')}
    g['experiments'][NEW_ID] = e
    from tradingagents.research.onchain_replication.job import required_sources
    if not required_sources() <= set(e['source_files']):
        raise ValueError('required source coverage incomplete')
    prior = ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/registered-hub-edges-2026-09-30'
    bindings = json.loads((prior/'source-bindings02.json').read_bytes())
    for name, expected in bindings['files'].items():
        if sha(ROOT/name) != expected:
            raise ValueError('old offline verification no longer reusable: '+name)
    reuse = {'current_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
             'verification_head':bindings['head'], 'bindings':ref(prior/'source-bindings02.json'),
             'terminal':ref(prior/'closure-check02.json'), 'unchanged_files_verified':len(bindings['files']),
             'new_experiment_source_pins':len(e['source_files']), 'new_experiment_inputs':len(e['inputs']),
             'preservation_prerequisite':preservation,'previous_graph_prerequisite':previous_graph,
             'qualification':'Identical prior full-suite bound bytes; new registration/preflight/helper require separate review. No empirical admission, body read, or launch.'}
    write_new(HERE/'verification-reuse.json',reuse)
    write_new(HERE/'gate.json',g)
    print(json.dumps(reuse,indent=2))

if __name__=='__main__':
    main()
