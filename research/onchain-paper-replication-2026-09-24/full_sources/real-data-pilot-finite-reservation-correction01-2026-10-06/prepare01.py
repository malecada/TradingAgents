"""Finite policy metadata from the accepted seven-count preparation; no launch."""
import copy,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
FS=HERE.parent

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

successor=load(FS/'real-data-pilot-packed-feature-successor03-2026-10-06/successor02.py','packed_successor')
b=successor.load('builder')

def fill(envelope,mcm,rows,import_stage):
    e,m=copy.deepcopy(envelope),copy.deepcopy(mcm)
    b.need(len(rows)==7 and all(type(n) is int and n>0 for n in rows.values()),'seven authenticated graph counts required')
    pairs=[n*32 for n in rows.values()];maximum=max(pairs);stage=e['stage_policy'];log=stage['log'];schedule=stage['schedule']
    b.need(log['max_events']==2*maximum+schedule['max_total_checkpoints'],'existing event/checkpoint envelope differs')
    def assign(value,key,number):
        b.positive(number);b.need(value[key] is None or value[key]==number,'refuse replacing a different finite declaration: '+key);value[key]=number
    assign(log,'max_pairs',maximum)
    assign(log,'max_logical_bytes',log['max_events']*168+2*8192)
    retained=stage['restart_retention']['max_live_bytes'] if 'restart_retention' in stage else schedule['max_total_checkpoint_bytes']
    def capacity(n):
        chunks=(n+stage['score_chunk_cells']-1)//stage['score_chunk_cells']
        return log['max_logical_bytes']+retained+88*n+(4*chunks+4)*8192
    assign(stage,'max_retained_logical_bytes',capacity(maximum))
    assign(e,'max_workflow_retained_logical_bytes',2*65536+import_stage['max_stage_bytes']+sum(capacity(n)+2*8192 for n in pairs))
    assign(m,'max_entries',maximum)
    assign(m['numeric'],'max_output_bytes',4*maximum)
    assign(m['numeric'],'max_numeric_bytes',4*maximum+m['numeric']['max_buffer_bytes'])
    return e,m

def prepare():
    prior=FS/'real-data-pilot-final02-2026-10-06/PREPARATION_RESULT05.json'
    spec=json.loads(prior.read_bytes())['builder03_spec'];refs=spec['references']
    graphs=b.graphs(ROOT,spec['graphs'])
    original={k:b.metadata(ROOT,refs[k]) for k in ('compact_policy','mcm_policy','original_import_stage')}
    e,m=fill(original['compact_policy'],original['mcm_policy'],{k:g['rows'] for k,g in graphs.items()},original['original_import_stage'])
    out=HERE/'metadata01';out.mkdir(exist_ok=False)
    generated={}
    for role,value in [('compact_policy',e),('mcm_policy',m)]:
        path=out/(role+'.json');body=b.raw(value);path.write_bytes(body)
        generated[role]={'path':str(path.relative_to(ROOT)),'bytes':len(body),'sha256':b.sha(body)}
    updated=copy.deepcopy(spec);updated['references'].update(generated)
    result=b.build(ROOT,updated)
    (out/'PREPARATION_RESULT01.json').write_bytes(b.raw({'status':'METADATA_ONLY_NOT_ADMITTED_OLD02_CONTEXT_NEVER_REOPEN','builder03_spec':updated,'builder03_result':result,'prior_preparation_sha256':b.sha(prior.read_bytes()),'qualification':'Only seven formerly-null declaration fields filled; no identity, resource or scientific policy change. Root fresh03 preparation required.'}))
    (out/'INPUT_REPLACEMENTS01.json').write_bytes(b.raw({'before':{k:refs[k] for k in generated},'candidate':generated}))
    return result
if __name__=='__main__':prepare()
