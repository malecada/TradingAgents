"""Static prospective metadata checks only; no workload, admission or readiness."""
import ast
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OLD=HERE.parent/'neural-resource-memory-3_75gib-2026-10-02'

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def check_ref(value):assert sha(ROOT/value['path'])==value['sha256'],value['path']

def main():
    population=read(HERE/'population01.json');allocation=read(HERE/'allocation.json');extension=read(HERE/'extension.json');review=read(HERE/'review.proposal.json')
    assert len(population['current_claims'])==len(population['prior_claims'])==17
    assert population['total_spent']==allocation['consumed_before']==extension['consumed_before']==34
    assert allocation['cumulative_ceiling']==extension['cumulative_ceiling']==63
    assert 63==34+sum(allocation['pending_allocation'].values())
    assert allocation['pending_allocation']=={'missing_body_batches':12,'financial_fit_batches':15,'neural_resource_only':1,'remaining_graph_matching_mcm_resource':1}
    assert extension['claims']==population['current_claims']
    assert set(extension)=={'schema_version','program_id','base_family','cumulative_ceiling','consumed_before','initial_experiment','allocation','claims','reason'}
    assert extension['base_family']==read(OLD/'extension.json')['base_family']
    assert set(review)=={'schema_version','decision','extension_sha256','reviewer','scope'}
    assert review['decision']=='pending_independent_review' and review['extension_sha256']==sha(HERE/'extension.json')
    check_ref(extension['allocation']);check_ref(allocation['resource_amendment']);check_ref(allocation['population'])
    for row in extension['claims']:
        claim=ROOT/'research_runs'/row['experiment']/'claim.json';terminal=claim.parent/(row['terminal_status']+'.json')
        assert sha(claim)==row['claim_sha256'] and sha(terminal)==row['terminal_sha256']
        assert read(terminal)['claim_sha256']==row['claim_sha256']
    for row in population['prior_claims']:check_ref(row['claim']);check_ref(row['terminal'])
    new=read(HERE/'execution-job.json');old=read(OLD/'execution-job.json')
    changed={k for k in new['resources'] if new['resources'][k]!=old['resources'][k]}
    assert changed=={'memory_high_bytes'} and new['resources']['memory_high_bytes']==new['resources']['memory_max_bytes']==4026531840
    adjusted=read(HERE/'execution-job.json');adjusted['resources']['memory_high_bytes']=old['resources']['memory_high_bytes'];assert adjusted==old
    policy=read(HERE/'launch_scheduling.json');prior=read(OLD/'launch_scheduling.json');policy['qualification']=prior['qualification'];assert policy==prior
    assert (HERE/'readiness.py').read_bytes()==(OLD/'readiness.py').read_bytes()
    caller=ast.parse((HERE/'launch_once.draft.py').read_text());before=ast.parse((OLD/'launch_once.py').read_text())
    mainfn=next(n for n in caller.body if isinstance(n,ast.FunctionDef) and n.name=='main');assert isinstance(mainfn.body[0],ast.Raise);mainfn.body.pop(0)
    identity=next(n for n in caller.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPERIMENT' for t in n.targets))
    assert identity.value.value=='eth-paper-neural-resource-20261002-03';identity.value.value='eth-paper-neural-resource-20261002-02'
    assert ast.dump(caller)==ast.dump(before),'Only identity and fail-closed draft blocker may differ from corrected caller'
    g=read(HERE/'gate.draft.json');selected=g['experiments']['eth-paper-neural-resource-20261002-03']
    assert selected['parent']=='eth-paper-neural-resource-20261002-02'
    assert selected['source_files']=={'UNRESOLVED_COMPLETE_FINAL_SOURCE_CLOSURE':None}
    assert len(selected['runtime_hashes'])==7 and set(selected['runtime_hashes'].values())=={None}
    previous=read(OLD/'gate.json')['experiments']['eth-paper-neural-resource-20261002-02']
    for k in ('cells','windows','outputs','selection','reuse','stage','family'):assert selected[k]==previous[k]
    for key in ['model','neural_plan',*('graph_'+w.replace('-','_') for w in ('2022-01-03','2022-06-13','2022-07-25','2022-11-07','2023-06-05','2024-01-01','2024-03-11','2024-08-05','2024-12-23'))]:assert selected['inputs'][key]==previous['inputs'][key]
    name=selected['parent'];count=0
    while name is not None:
        actual=read(ROOT/'research_runs'/name/'claim.json')['experiment'];assert g['experiments'][name]==actual
        name=actual['parent'];count+=1
    assert count==3
    for name in ('gate.json','review.json','launch_once.py'):assert not (HERE/name).exists(),'No executable final selected objects in draft directory'
    print(json.dumps({'status':'static_metadata_checks_passed','current_claims':17,'prior_claims':17,'spent':34,'prospective_ceiling':63,'historical_ancestors_exact':3,'caller_AST_difference':'identity03 + failclosed draft blocker only','resource_difference':'memory_high_bytes only','helper_byte_identical':True,'final_source_resolved':False,'machine_review_accepted':False,'admission_or_readiness_executed':False},indent=2))
if __name__=='__main__':main()
