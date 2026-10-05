"""Optional labels-free metadata projection; never scientific feature authority.

Only publish_projection uses ResearchRun. Pure helpers accept metadata, not
capabilities; component shapes are explicitly unverified metadata declarations.
"""
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime,timedelta
from pathlib import Path

DOC_LIMIT=16*1024**2
POLICY_LIMIT=512*1024
OUTPUT_LIMIT=4*1024**2
MAX_ROWS=4096
MAX_GRAPHS=1024
BATCH=16
LOOKBACK=28
EXAMPLE_FIELDS={'decision_at','label_start','label_end','max_input_available_at','input_dates','input_prices','graph_hashes','graph_available_at','target_price','up'}
SOURCES=('tradingagents/research/onchain_replication/population_batch_projection.py','tradingagents/research/onchain_replication/population_assembly.py','tradingagents/research/onchain_replication/environment.py')

def require(value,message):
    if not value:raise ValueError(message)

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def valid_hash(value):return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None

def encode(value,limit=DOC_LIMIT):
    # Incremental encoder refuses before accumulating a document above its bound.
    parts=[];count=0
    for text in json.JSONEncoder(sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).iterencode(value):
        raw=text.encode();count+=len(raw);require(count<=limit,'JSON byte bound exceeded');parts.append(raw)
    return b''.join(parts)

def parse(raw,limit=DOC_LIMIT):
    require(type(raw) is bytes and len(raw)<=limit,'bounded JSON bytes required')
    def pairs(items):
        result={}
        for k,v in items:require(k not in result,'duplicate JSON field');result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def clock(value):
    require(type(value) is str and len(value)<=40,'explicit UTC timestamp required')
    try:v=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError:raise ValueError('invalid UTC timestamp') from None
    require(v.tzinfo is not None and v.utcoffset()==timedelta(0),'explicit UTC timestamp required');return v

def _list(value,limit,message):require(type(value) is list and len(value)<=limit,message)

def component(value,graph_hash):
    require(type(value) is dict and set(value)=={'schema_version','context','tree','arrays'} and type(value['schema_version']) is int and value['schema_version']==1,'original component schema differs')
    require(type(value['context']) is dict and value['context'].get('graph_hash')==graph_hash,'original component graph differs')
    def scalar(v):return {'kind':'scalar','value':v}
    tree={'kind':'dict','items':[[scalar('feature'),{'kind':'dict','items':[[scalar('mcm'),{'kind':'array','member':'array-000000.npy'}],[scalar('edge_index'),{'kind':'array','member':'array-000001.npy'}]]}],[scalar('aligned_vectors'),scalar(None)]]}
    require(value['tree']==tree and type(value['arrays']) is dict and set(value['arrays'])=={'array-000000.npy','array-000001.npy'},'original component membership differs')
    sizes=[]
    for name,dtype,width in [('array-000000.npy','float32',4),('array-000001.npy','int64',8)]:
        d=value['arrays'][name]
        require(type(d) is dict and set(d)=={'shape','dtype','bytes','sha256'} and d['dtype']==dtype and valid_hash(d['sha256']),'component descriptor differs')
        shape=d['shape'];require(type(shape) is list and len(shape)==2 and all(type(n) is int and 0<=n<=2**40 for n in shape),'component shape differs')
        require((shape[0]>0 and shape[1]==32) if dtype=='float32' else shape[0]==2,'complete MCM32/edge shape required')
        size=shape[0]*shape[1]*width
        require(type(d['bytes']) is int and size<d['bytes']<=size+65536,'component declared header extent differs');sizes.append(size)
    return {'status':'declared_metadata_only','nodes':value['arrays']['array-000000.npy']['shape'][0],
        'edges':value['arrays']['array-000001.npy']['shape'][1],'fixed_tensor_bytes':sum(sizes),
        'manifest_sha256':digest(encode(value)),'body_header_owner_terminal_verified':False}

def project(population,binding,assembly,components):
    require(type(population) is dict and set(population)=={'schema_version','examples','scaler'} and type(population['schema_version']) is int and population['schema_version']==1,'population schema differs')
    e=population['examples'];require(type(e) is dict and set(e)=={'train','test','exclusions','train_hash','test_mask_hash','source_hashes','fold_hash'},'example manifest schema differs')
    for k in ('train','test','exclusions'):_list(e[k],MAX_ROWS,'row bound exceeded')
    require(len(e['train'])+len(e['test'])<=MAX_ROWS,'total eligible row bound exceeded')
    _list(e['source_hashes'],MAX_GRAPHS,'source membership bound exceeded')
    require(bool(e['source_hashes']) and len(set(e['source_hashes']))==len(e['source_hashes']) and all(valid_hash(x) for x in e['source_hashes']),'source hashes differ')
    require(all(valid_hash(e[k]) for k in ('train_hash','test_mask_hash','fold_hash')),'population hashes differ')
    require(type(binding) is dict and set(binding)=={'train_hash','test_mask_hash','test_examples_hash','source_hashes','fold_hash','scaler'},'binding schema differs')
    require(binding=={'train_hash':e['train_hash'],'test_mask_hash':e['test_mask_hash'],'test_examples_hash':digest(encode(e['test'])),'source_hashes':e['source_hashes'],'fold_hash':e['fold_hash'],'scaler':population['scaler']},'original binding differs')
    require(digest(encode(e['train']))==e['train_hash'] and digest(encode([r['decision_at'] for r in e['test']]))==e['test_mask_hash'],'original row hashes differ')
    require(population['scaler']['train_hash']==e['train_hash'],'scaler membership differs')
    require(type(assembly) is dict and set(assembly)=={'schema_version','weeks','decision_count','provenance'} and type(assembly['schema_version']) is int and assembly['schema_version']==1,'assembly schema differs')
    require(type(assembly['decision_count']) is int and assembly['decision_count']==len(e['train'])+len(e['test'])+len(e['exclusions']),'decision denominator differs')
    provenance=assembly['provenance'];require(digest(encode(provenance['source_admission']))==provenance['source_admission_hash'],'source admission hash differs')
    require(set(e['source_hashes']) <= (set(provenance['source_admission']['source_hashes']) | {provenance['source_admission']['price_source_hash']}) and provenance['source_admission']['price_source_hash'] in e['source_hashes'] and provenance['fold']['member_hash']==e['fold_hash'],'assembly source/fold differs')
    require(type(provenance['calendar']['lookback_days']) is int and provenance['calendar']['lookback_days']==LOOKBACK,'registered lookback differs')
    rows=[];batches=[];all_graphs=[];decisions=set()
    for partition in ('train','test'):
        part=[];previous=None
        for ordinal,row in enumerate(e[partition]):
            require(type(row) is dict and set(row)==EXAMPLE_FIELDS,'example row fields differ')
            decision=clock(row['decision_at']);require(previous is None or previous<decision,'eligible rows not ordered');previous=decision
            require(decision not in decisions,'duplicate decision');decisions.add(decision)
            for key in ('input_dates','graph_hashes','graph_available_at'):
                require(type(row[key]) in (list,tuple) and len(row[key])==LOOKBACK,'complete28 positions required')
            expected=[(decision-timedelta(days=LOOKBACK-j)).date().isoformat() for j in range(LOOKBACK)]
            require(list(row['input_dates'])==expected,'input date sequence differs')
            for date,h,available in zip(expected,row['graph_hashes'],row['graph_available_at'],strict=True):
                require(valid_hash(h),'graph hash differs');require(clock(available)<=clock(date+'T00:00:00Z')+timedelta(days=1),'late graph in eligible row')
                if h not in all_graphs:all_graphs.append(h);require(len(all_graphs)<=MAX_GRAPHS,'graph count bound exceeded')
            record={'partition':partition,'ordinal':ordinal,'decision_at':row['decision_at'],'input_dates':list(row['input_dates']),'graph_hashes':list(row['graph_hashes']),'graph_available_at':list(row['graph_available_at'])}
            rows.append(record);part.append(record)
        for start in range(0,len(part),BATCH):
            selected=part[start:start+BATCH];union=[];counts={}
            for row in selected:
                for h in row['graph_hashes']:
                    if h not in counts:union.append(h);counts[h]=0
                    counts[h]+=1
            batches.append({'partition':partition,'ordinals':list(range(start,start+len(selected))),
                'graph_hashes':union,'multiplicity':[counts[h] for h in union]})
    exclusions=[]
    for row in e['exclusions']:
        require(type(row) is dict and set(row)=={'decision_at','reason','partition'} and row['partition'] in ('train','test') and type(row['reason']) is str and 0<len(row['reason'])<=128,'exclusion schema differs')
        d=clock(row['decision_at']);require(d not in decisions,'duplicate/excluded eligible decision');decisions.add(d);exclusions.append(dict(row))
    require(type(components) is dict and set(components)<=set(all_graphs),'unexpected component join')
    joins={}
    for h in all_graphs:
        if h not in components:joins[h]={'status':'missing_registered_component'};continue
        v=components[h]
        require(type(v) is dict,'component disposition required')
        if v.get('status')=='unavailable':
            require(set(v)=={'status','reason','evidence_hashes'} and type(v['reason']) is str and 0<len(v['reason'])<=512,'unavailable disposition differs')
            _list(v['evidence_hashes'],64,'unavailable evidence bound');require(bool(v['evidence_hashes']) and all(valid_hash(x) for x in v['evidence_hashes']),'unavailable evidence hashes differ');joins[h]=json.loads(encode(v))
        else:joins[h]=component(v,h)
    value={'schema_version':1,'kind':'population-batch-projection-v1','batch_size':BATCH,'lookback_days':LOOKBACK,
        'rows':rows,'batches':batches,'exclusions':exclusions,'components':joins,
        'membership':{k:e[k] for k in ('train_hash','test_mask_hash','source_hashes','fold_hash')},
        'scientific_feature_admission':False,'array_bodies_or_labels_emitted':False}
    require(len((json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())<=OUTPUT_LIMIT,'projection output bound exceeded')
    return value

def _run_class():
    from ..lifecycle import ResearchRun
    return ResearchRun

def _runtime(root):
    from . import environment
    require(Path(environment.__file__).resolve()==root/SOURCES[2],'loaded runtime inventory outside admitted root')
    return environment.inventory(root,include_torch=False)

def _sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def _read(path,limit):
    path=Path(path)
    require(path.is_absolute() and path.resolve()==path,'direct immutable metadata path required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC);primary=None
    try:
        before=os.fstat(fd);pin=_sig(before)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit and pin==_sig(path.lstat()),'bounded single-link metadata required')
        parts=[];count=0
        while True:
            block=os.read(fd,min(65536,limit-count+1))
            if not block:break
            count+=len(block);require(count<=limit,'metadata grew beyond bound');parts.append(block)
        require(count==before.st_size and _sig(os.fstat(fd))==_sig(path.lstat())==pin and path.resolve()==path,'metadata inode/bytes changed')
        return b''.join(parts)
    except BaseException as error:primary=error;raise
    finally:
        try:os.close(fd)
        except BaseException as later:
            # No optional formatting/notes/cause assignment can mask an actual fatal.
            if primary is None or (isinstance(primary,Exception) and not isinstance(primary,MemoryError)):raise

def _name(name):
    require(type(name) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',name) is not None and name not in ('.','..'),'registered flat name required');return name

def _input(run,name,limit=DOC_LIMIT):
    _name(name);require(name in run.admission.inputs,'registered projection input missing')
    ref=run.admission.inputs[name];rel=Path(ref['path'])
    require(not rel.is_absolute() and '..' not in rel.parts and not any(p.lower() in {'keys','apis','.env','hf_token.txt'} for p in rel.parts),'direct noncredential input path required')
    raw=_read(run.admission.root/rel,limit)
    require(valid_hash(ref['sha256']) and digest(raw)==ref['sha256'],'projection input hash differs')
    require(run.read_input(name)==raw,'registered projection input changed');return parse(raw,limit)

def _context(run):
    require(type(run) is _run_class(),'genuine ResearchRun required')
    run._active();run._check_source();run._check_inputs();ad=run.admission
    require(type(ad.source) is str and re.fullmatch('[0-9a-f]{40}',ad.source) is not None and valid_hash(ad.registration_sha256) and valid_hash(run._claim_sha256),'run source/claim identity differs')
    own=Path(__file__).resolve();require(own==ad.root/SOURCES[0],'loaded projection source outside admitted root')
    loaded=sys.modules.get(__package__+'.population_assembly')
    require(loaded is not None and Path(loaded.__file__).resolve()==ad.root/SOURCES[1],'loaded producer source outside admitted root')
    pins={}
    for name in SOURCES:
        expected=ad.experiment['source_files'].get(name);require(valid_hash(expected),'projection source not registered')
        require(digest(_read(ad.root/name,DOC_LIMIT))==expected,'projection source bytes changed');pins[name]=expected
    return {'source':ad.source,'registration_sha256':ad.registration_sha256,'experiment':ad.experiment_id,
        'claim_sha256':run._claim_sha256,'run_directory':str(run.directory),'inputs':json.loads(encode(ad.inputs)),
        'registered_outputs':list(ad.experiment['outputs']),'source_files':pins,'runtime_hashes':json.loads(encode(ad.experiment['runtime_hashes']))}

def publish_projection(run,plan_input,plan,result):
    """Actual optional producer boundary; output is metadata, never admission.

    Original output files remain untouched even when this selected publication
    fails. The enclosing genuine worker must retain/fail the whole run normally.
    """
    initial=_context(run)
    require(_input(run,plan_input,POLICY_LIMIT)==plan,'registered population plan changed')
    outputs=plan['outputs'];require(set(outputs)=={'population','binding','assembly','projection'} and len(set(outputs.values()))==4,'projection output names differ')
    for name in outputs.values():_name(name);require(name in run.admission.experiment['outputs'],'projection output not registered')
    require(outputs['projection'] not in run._published_outputs and not (run.directory/'outputs'/outputs['projection']).exists(),'projection output already born')
    policy=_input(run,plan['projection_input'],POLICY_LIMIT)
    fields={'schema_version','kind','environment_input','model_input','training_input','components_input'}
    require(type(policy) is dict and set(policy)==fields and type(policy['schema_version']) is int and policy['schema_version']==1 and policy['kind']=='population-batch-projection-v1','projection policy differs')
    names=[policy[k] for k in ('environment_input','model_input','training_input','components_input')]
    require(len(set(names))==4,'projection policy inputs overlap')
    environment=_input(run,policy['environment_input']);require(environment==_runtime(run.admission.root),'projection runtime inventory differs')
    model=_input(run,policy['model_input']);training=_input(run,policy['training_input'])
    require(type(training.get('batch_size')) is int and training['batch_size']==BATCH and type(model.get('lookback_days')) is int and model['lookback_days']==LOOKBACK and type(model.get('mcm_input')) is int and model['mcm_input']==32,'original model/batch configuration differs')
    inventory=_input(run,policy['components_input'])
    require(type(inventory) is dict and set(inventory)=={'schema_version','graphs'} and type(inventory['schema_version']) is int and inventory['schema_version']==1 and type(inventory['graphs']) is dict and len(inventory['graphs'])<=MAX_GRAPHS,'component inventory differs')
    components={}
    for h,ref in inventory['graphs'].items():
        require(valid_hash(h) and type(ref) is dict and set(ref)=={'status','input'} and ref['status'] in ('metadata','unavailable'),'registered component reference differs')
        value=_input(run,ref['input'])
        if ref['status']=='unavailable':require(type(value) is dict and value.get('status')=='unavailable','registered unavailable evidence differs')
        else:component(value,h)
        components[h]=value
    assembly={k:v for k,v in result.items() if k not in ('population','binding')}
    original_values={'population':result['population'],'binding':result['binding'],'assembly':assembly}
    def original_outputs():
        values={};refs={}
        for role,value in original_values.items():
            name=outputs[role];raw=_read(run.directory/'outputs'/name,DOC_LIMIT)
            require(run._published_outputs.get(name)==digest(raw),'original published output hash differs')
            decoded=parse(raw);require(encode(decoded)==encode(value),'original published output differs from assembled result')
            values[role]=decoded;refs[role]={'output':name,'sha256':digest(raw)}
        return values,refs
    values,refs=original_outputs()
    projected=project(values['population'],values['binding'],values['assembly'],components)
    projected['provenance']={k:initial[k] for k in ('source','registration_sha256','experiment','claim_sha256','source_files','runtime_hashes')}
    projected['provenance'].update(original_outputs=refs,plan_input=plan_input,
        plan_sha256=run.admission.inputs[plan_input]['sha256'],
        projection_policy_sha256=run.admission.inputs[plan['projection_input']]['sha256'],
        input_hashes={name:run.admission.inputs[name]['sha256'] for name in names},
        component_input_hashes={v['input']:run.admission.inputs[v['input']]['sha256'] for v in inventory['graphs'].values()})
    require(len((json.dumps(projected,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())<=OUTPUT_LIMIT,'projection final output bound exceeded')
    require(_context(run)==initial and _runtime(run.admission.root)==environment,'projection authority/runtime changed')
    require(original_outputs()[1]==refs,'original outputs changed before projection')
    run.write_json(outputs['projection'],projected)
    require(_context(run)==initial and _runtime(run.admission.root)==environment,'projection authority/runtime changed after publication')
    require(original_outputs()[1]==refs,'original outputs changed after projection')
    raw=_read(run.directory/'outputs'/outputs['projection'],OUTPUT_LIMIT)
    require(digest(raw)==run._published_outputs.get(outputs['projection']) and encode(parse(raw))==encode(projected),'published projection changed')
    return projected
