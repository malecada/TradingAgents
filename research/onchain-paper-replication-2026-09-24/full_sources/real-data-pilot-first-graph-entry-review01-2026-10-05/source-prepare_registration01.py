"""Freeze the first whole-week pilot graph after actual storage acceptance.

Metadata only: never starts a claim, reads raw bodies, or generates outcomes.
"""
from pathlib import Path
import hashlib
import json

from tradingagents.research.admission import runtime_hashes
from tradingagents.research.onchain_replication.job import required_sources

ROOT=Path.cwd()
HERE=Path(__file__).resolve().parent
STUDY=Path('research/onchain-paper-replication-2026-09-24')
PREP=ROOT/STUDY/'full_sources/real-data-end-to-end-pilot-preparation01-2026-10-05'
STORAGE=ROOT/STUDY/'storage/closed-ledger-pilot-offload-2026-10-05-01'
BUDGET=ROOT/STUDY/'full_sources/real-data-pilot-allocation-review01-2026-10-05'
NAME='eth-paper-real-pilot-graph-20220502-20261005-01'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':str(path.relative_to(ROOT)),'sha256':sha(path)}
def write(path,value):
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n')


def main():
    for path in (HERE/'gate01.json',ROOT/'research_runs'/NAME,
                 ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,
                 ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME):
        if path.exists() or path.is_symlink():raise FileExistsError('fixed identity already generated or reserved: '+str(path))
    allocation=json.loads((PREP/'CUMULATIVE_ALLOCATION_PROPOSED71_01.json').read_bytes())
    extension=PREP/'EXTENSION_PROPOSED71_01.json'
    review=BUDGET/'review.accepted01.json'
    reviewed=json.loads(review.read_bytes())
    if reviewed['decision']!='accepted' or reviewed['extension_sha256']!=sha(extension):
        raise ValueError('exact cumulative extension review missing')
    closure=json.loads((STORAGE/'closure-review.json').read_bytes())
    if closure['decision']!='accepted':raise ValueError('actual storage outcome not independently accepted')
    for path,expected in closure['evidence'].items():
        if sha(ROOT/path)!=expected:raise ValueError('accepted storage evidence changed')
    complete=json.loads((STORAGE/'complete.json').read_bytes())
    final=json.loads((STORAGE/'guard01/final.json').read_bytes())
    if (complete['bytes_moved']!=3662934016 or final['phase']!='complete'
            or final['child_exit_code']!=0 or final['cleanup_verified'] is not True
            or Path(final['cgroup']).exists()):
        raise ValueError('storage completion/cleanup differs')
    case=json.loads((PREP/'GRAPH_STAGE_CASES_DRAFT01.json').read_bytes())['graph_cases'][0]
    if case['identity']!=NAME or case['parent'] is not None:raise ValueError('first fixed graph case differs')
    inputs=dict(case['inputs'])
    for name,path in {'environment':HERE/'environment01.json',
                      'execution_workspace':HERE/'workspace01.json',
                      'execution_job':HERE/'execution-job01.json',
                      'raw_extent':HERE/'RAW_EXTENT01.json',
                      'storage_projection':HERE/'STORAGE_PROJECTION_DRAFT01.json',
                      'storage_policy':HERE/'STORAGE_POLICY01.json',
                      'input_selection':PREP/'INPUT_SELECTION_DRAFT01.json',
                      'storage_closure_review':STORAGE/'closure-review.json',
                      'storage_complete':STORAGE/'complete.json',
                      'storage_native_final':STORAGE/'guard01/final.json',
                      'storage_restore':STORAGE/'00-restore.json',
                      'storage_recovered_restore':STORAGE/'00-recovered-restore.json',
                      'storage_recovered_complete':STORAGE/'recovered-complete.json'}.items():
        inputs[name]={**ref(path),'dataset':'eth'}
    weekly=json.loads((ROOT/inputs['weekly_source']['path']).read_bytes())
    for number,member in enumerate(weekly['members']):
        path=Path(member['path'])
        if sha(path)!=member['sha256']:raise ValueError('daily map changed')
        inputs[f'daily_map_{number:02d}']={**ref(path),'dataset':'eth'}
    pins={path:sha(ROOT/path) for path in required_sources()}
    for path in (HERE/'prepare_registration01.py',HERE/'preflight01.py',HERE/'launch01.py',HERE/'CHARTER01.md',
                 PREP/'CUMULATIVE_ALLOCATION_PROPOSED71_01.json',extension,review):
        pins.update({str(path.relative_to(ROOT)):sha(path)})
    item={'family':'paper','parent':None,'stage':'development','reuse':'exploratory',
          'question':'Build the complete preserved ETH May2–9,2022 graph for the fixed representative real-data pilot and measure whole-source throughput, peak charged memory and storage.',
          'charter':ref(HERE/'CHARTER01.md'),'selection':None,
          'source_files':dict(sorted(pins.items())),'runtime_hashes':runtime_hashes(),
          'windows':[{'dataset':'eth','start':'2022-05-02T00:00:00Z','end':'2022-05-09T00:00:00Z','availability':'existing'}],
          'inputs':inputs,'cells':case['cells'],'outputs':case['outputs'],
          'cumulative_budget_extension':{'extension':ref(extension),'review':ref(review)}}
    gate={'schema_version':1,'program_id':allocation['program_id'],
          'families':{'paper':allocation['base_family']},
          'datasets':{'eth':{'identity':'ethereum-native-top-level-transactions-chain-1',
                            'history_reference':str(STUDY/'history.json'),
                            'exposures':[{'start':'2022-01-01T00:00:00Z','end':'2025-01-01T00:00:00Z','state':'spent'}]}},
          'experiments':{NAME:item}}
    write(HERE/'gate01.json',gate)
    print(json.dumps({'identity':NAME,'source_pins':len(pins),'input_pins':len(inputs),
                      'gate_sha256':sha(HERE/'gate01.json'),'claim_started':False,
                      'qualification':'Concrete metadata registration generated only; commit, exact entry review and fresh native/resource checks remain mandatory.'}))


if __name__=='__main__':main()
