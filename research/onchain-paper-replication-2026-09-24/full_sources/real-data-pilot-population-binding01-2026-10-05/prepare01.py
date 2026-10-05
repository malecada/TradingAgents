"""Emit metadata plans to stdout; never inspect numeric price/graph arrays."""
import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timedelta
from real_pilot_population import WEEKS,DECISIONS,SCOPE,require


def prepare(refs):
    require(type(refs) is dict and set(refs)==set(WEEKS), 'all seven actual graph references required')
    graph_inputs={};by_week={};roles={}
    for i,w in enumerate(WEEKS):
        ref=refs[w]
        require(type(ref) is dict and set(ref)=={'path','sha256'},'exact graph body reference required')
        path=Path(ref['path']);require(path.suffix=='.json' and path.stat().st_size<=65536,'bounded graph metadata required')
        raw=path.read_bytes();require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'graph metadata body differs')
        value=json.loads(raw);require(value['metadata']['start_utc']==w and value['metadata']['asset']=='ETH','actual graph week differs')
        role='pilot_graph_%02d'%i;h=value['graph_hash'];require(h not in graph_inputs,'distinct original graphs required')
        graph_inputs[h]=role;by_week[w]=h;roles[role]=ref
    sequences=[]
    for decision in DECISIONS:
        row=[];d=datetime.fromisoformat(decision.removesuffix('Z'))
        for i in range(28,0,-1):
            day=d-timedelta(days=i);end=day-timedelta(days=day.weekday());week=end-timedelta(days=7)
            row.append(by_week[week.isoformat()+'Z'])
        sequences.append(row)
    pilot={'schema_version':2,'population_scope':SCOPE,'kind':'real-data-import-training-pilot-v1','asset':'ETH','seed':11,'batch_size':16,'lookback_days':28,'cell_id':'real-eth-one-update','graph_inputs':graph_inputs,'indices':None,'decisions':DECISIONS,'graph_sequences':sequences,'population_plan_input':'resource_population_plan','model_input':'model','training_input':'training','model_execution':None,'max_checkpoint_bytes':4194304,'outputs':{'summary':'pilot-summary.json','ledger':'cell-ledger.json','binding':'resource-binding.json','journal':'resource-journal.json'}}
    population={'schema_version':1,'population_scope':SCOPE,'financial_fit_complete':False,'fold':'2024','scope_input':'resource_population_scope','calendar_input':'calendar','price_panel_input':'price_panel','graphs':{w:graph_inputs[by_week[w]] for w in WEEKS},'outputs':{'resource_population':'resource-population.json','binding':'resource-population-binding.json'}}
    return {'status':'metadata-source-candidate-not-registered','pilot_plan':pilot,'population_plan':population,'graph_roles':roles,'other_input_roles':['resource_population_scope','calendar','price_panel','model','training','resource_population_plan'],'numeric_eligibility_and_scaler':None,'full_fold_population':False}


if __name__=='__main__':print(json.dumps(prepare(json.loads(Path(sys.argv[1]).read_bytes())),sort_keys=True,indent=2))
