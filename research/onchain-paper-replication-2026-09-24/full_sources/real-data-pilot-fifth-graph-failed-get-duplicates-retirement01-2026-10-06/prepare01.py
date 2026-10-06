"""Metadata-only exact three-get draft; no payload reads, admission or retirement."""
from pathlib import Path
import hashlib, importlib.util, json, sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('failed_get_retirement_candidate',HERE/'retire01.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
ROOT=r.ROOT

def prepare(outcome_review=None,outcome_sha=None):
    evidence={}
    def add(path,pin=None):
        raw=r.metadata(ROOT,path,pin);evidence[path]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
    proof=add(r.BODY_PROOF,r.BODY_PROOF_SHA)
    for name in ('selection01.json','complete.json','recovered-complete.json','guard01/final.json','outer-exit01.json','ROOT_TERMINAL01.json'):
        add(r.BACKUP+'/'+name)
    for path in ('research_runs/'+r.GRAPH+'/failed.json',r.PARENT_RUN+'/postmortem-cells.json',r.PARENT_RUN+'/guard/final.json',r.PARENT_CALLER+'/ROOT_TERMINAL01.json',r.PARENT_CALLER+'/outer-exit01.json'):
        add(path)
    rows=[]
    for pr in proof['files']:
        n=pr['index'];kp=r.BACKUP+f'/{n:02d}-kept.json';kept=add(kp)
        original={k:kept[k] for k in ('path','bytes','sha256','stat_identity','mode')}
        recovered={k:pr[k] for k in ('bytes','sha256','stat_identity','mode')};recovered['path']=pr['recovered_path']
        rows.append({'index':n,'original':original,'recovered':recovered,'kept':kp})
    c={'schema_version':1,'identity':r.ID,'status':'DRAFT_NOT_RELEASED','count':3,'retire_bytes':3278655680,
       'rows':rows,'evidence':evidence,'recovery_basis':{'outcome_review':None,'recovered_body_proof':{'path':r.BODY_PROOF,'sha256':r.BODY_PROOF_SHA}},
       'remote_disposition':'Accepted historical full BYTE recovery; no current remote availability assertion. All three original failed payloads retained locally.',
       'original_parent_status':'failed','original_graph_status':'unavailable','original_source_rows':7507236,
       'release':None,'committed_source_and_release':None,'actual_remote_commit_readback':None}
    r.selected(ROOT,c)
    if outcome_review is not None:
        r.require(type(outcome_sha) is str and len(outcome_sha)==64,'exact review SHA required')
        add(outcome_review,outcome_sha)
        c['recovery_basis']['outcome_review']={'path':outcome_review,'sha256':outcome_sha}
        r.recovery(ROOT,c)
    return c

if __name__=='__main__':
    r.require(len(sys.argv) in (1,3),'optional exact outcome review relative path and SHA required')
    print(json.dumps(prepare(*sys.argv[1:]),indent=2))
