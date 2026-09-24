"""Prepare metadata only; no raw reads, claims or empirical execution."""
from pathlib import Path
import json
import ast
from tradingagents.research import runtime_hashes
from tradingagents.research.onchain_replication.provenance import file_hash
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;STUDY=HERE.parent

def main():
    index=json.loads((HERE/'source-index.json').read_bytes())
    paths=[HERE/'source-index.json',STUDY/'history.json',STUDY/'budget-amendment.proposed.json',STUDY/'protocol-freeze-v3.json',STUDY/'protocol-freeze-v2.json',STUDY/'protocol-freeze.json',HERE/'environment.json',ROOT/'uv.lock',ROOT/'pyproject.toml',*sorted((STUDY/'config').glob('*.json'))]
    paths.extend(Path(member['path']) for week in index['weeks'].values() for member in week['members'])
    paths.extend([STUDY/'protocol-freeze-v4.json',STUDY/'resource-cap-v4.md',HERE/'resource-contract-v4.json'])
    inputs={('source_index' if path==HERE/'source-index.json' else 'binding_'+str(i)):{'path':str(path.relative_to(ROOT)),'sha256':file_hash(path),'dataset':'eth'} for i,path in enumerate(paths)}
    cells=[phase+'-'+week for week in index['weeks'] for phase in ('decode_graph','neighborhoods','matching','neural_checkpoint','dictionary','mcm') if phase!='dictionary' or week=='2022-01-03']
    cells += ['source-'+member['start_utc'][:10] for week in index['weeks'].values() for member in week['members']]
    package=ROOT/'tradingagents/research/onchain_replication'
    names={'__init__','resources','provenance','eth_source','weekly','graph_store','neighborhoods','serialization','dictionary','matching','mcm','model','checkpoints','cache','environment'}
    pending=list(names)
    while pending:
        name=pending.pop()
        for node in ast.walk(ast.parse((package/(name+'.py')).read_text())):
            if isinstance(node,ast.ImportFrom) and node.level==1 and node.module:
                dependency=node.module.split('.')[0]
                if dependency not in names:names.add(dependency);pending.append(dependency)
    sources=[*(package/(name+'.py') for name in sorted(names)),*sorted(HERE.glob('*.py'))]
    gate={'schema_version':1,'program_id':'onchain-paper-replication-2026-09-24','families':{'paper':{'mechanism_id':'celik-sefer-transaction-graph-full-neural-replication','attempt_budget':51,'prior_attempts':17,'history_reference':str((STUDY/'history.json').relative_to(ROOT))+'; correlated earlier screen17claims included; explicit cumulative proposal budget-amendment.proposed.json; no fresh-sample assertion'}},'datasets':{'eth':{'identity':'ethereum-native-top-level-transactions-chain-1','history_reference':str((STUDY/'history.json').relative_to(ROOT)),'exposures':[{'start':'2022-01-01T00:00:00Z','end':'2025-01-01T00:00:00Z','state':'spent'}]}},'experiments':{'eth-paper-resource-pilot-20260924':{'family':'paper','parent':None,'charter':{'path':str((HERE/'CHARTER.md').relative_to(ROOT)),'sha256':file_hash(HERE/'CHARTER.md')},'question':'Measured full-graph implementation resource cost; synthetic labels only; no predictive outcome','stage':'development','reuse':'exploratory','windows':[{'dataset':'eth','start':'2022-01-01T00:00:00Z','end':'2025-01-01T00:00:00Z','availability':'existing'}],'inputs':inputs,'source_files':{str(p.relative_to(ROOT)):file_hash(p) for p in sources},'runtime_hashes':runtime_hashes(),'selection':None,'cells':cells,'outputs':['cell-ledger.json','artifact-index.json','capacity-forecast.json']}}}
    experiment=gate['experiments']['eth-paper-resource-pilot-20260924']
    experiment['charter']={'path':str((HERE/'CHARTER-v2.md').relative_to(ROOT)),'sha256':file_hash(HERE/'CHARTER-v2.md')}
    path=HERE/'gate-v3.json'
    if path.exists():raise FileExistsError('preserve prior registration; explicit revision required')
    path.write_text(json.dumps(gate,indent=2,sort_keys=True)+'\n')
    print(len(cells),'cells; proposed metadata only, commit and independent review required')

if __name__=='__main__':main()
