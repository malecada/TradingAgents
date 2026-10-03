"""Prospective original-dictionary evidence capability; no numerical stage fiction.

Stdlib validator and a distinct current-Binding metadata capability. Not a
compact_dictionary.Produced, and not accepted by compact_mcm. No file publication,
claims, sampling, clustering, array construction or numeric permission occurs.
The current owner/MCM import-stage route remains a separately reviewed integration.
"""
from dataclasses import dataclass
import hashlib
import json
import math
from datetime import datetime, timedelta
from threading import Lock

ROLES=frozenset(('dictionary','samples','dictionary_config','matching_config','graph_manifest',
    'claim','terminal','gate','dictionary_intent','sample_intent','dictionary_result'))
POLICY=frozenset(('schema_version','kind','original_claim','original_source','week','dictionary_identity',
    'sample_identity','sample_config','seed','sample_count','motif_count','required_graphs',
    'max_json_bytes','max_total_json_bytes','max_total_nodes','max_total_edges','refs'))

def require(value,message):
    if not value:raise ValueError(message)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def sha(raw):return hashlib.sha256(raw).hexdigest()

def _pairs(items):
    out={}
    for k,v in items:
        require(k not in out,'duplicate JSON key');out[k]=v
    return out

def parse(raw):
    require(type(raw) is bytes,'exact bytes required')
    value=json.loads(raw,object_pairs_hook=_pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
    canonical(value);return value

def _hash(value):return type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)

def _positive(value):return type(value) is int and 0<value<2**63

def _utc(value):
    require(type(value) is str,'UTC timestamp must be text')
    try:result=datetime.fromisoformat(value.replace('Z','+00:00'))
    except (ValueError,TypeError) as error:raise ValueError('UTC timestamp invalid') from error
    require(result.tzinfo is not None and result.utcoffset()==timedelta(0),'explicit UTC required')
    return result

def _availability(metadata,sample_config):
    start=_utc(sample_config['train_start']);end=_utc(sample_config['train_end'])
    graph_start=_utc(metadata['start_utc']);available=_utc(metadata['available_at'])
    require(start<end and graph_start==start and graph_start<=available<end,'original graph unavailable inside sampling interval')
    if 'end_utc' in metadata:
        graph_end=_utc(metadata['end_utc'])
        require(graph_start<graph_end<=available,'original graph chronology differs')

def policy_check(p):
    require(type(p) is dict and set(p)==POLICY,'import control fields differ')
    require(type(p['schema_version']) is int and p['schema_version']==1 and p['kind']=='original-dictionary-import-v1','import schema differs')
    for name in ('sample_count','motif_count','max_json_bytes','max_total_json_bytes','max_total_nodes','max_total_edges'):
        require(_positive(p[name]),'positive finite capacity required')
    require(p['max_json_bytes']<=2*1024**2 and p['max_total_json_bytes']<=16*1024**2,'metadata outer ceiling exceeded')
    require(p['sample_count']<=512 and p['motif_count']<=32 and p['motif_count']<=p['sample_count'],'import cardinality ceiling exceeded')
    require(type(p['seed']) is int and p['seed']>=0,'seed invalid')
    require(_hash(p['dictionary_identity']) and _hash(p['sample_identity']),'semantic hash invalid')
    require(type(p['original_source']) is str and len(p['original_source'])==40 and all(c in '0123456789abcdef' for c in p['original_source']),'original source invalid')
    require(type(p['original_claim']) is str and p['original_claim'] and type(p['week']) is str,'original identity invalid')
    required=p['required_graphs'];require(type(required) is list and required and len(required)<=9 and required==sorted(set(required)) and all(_hash(x) for x in required),'required graph denominator invalid')
    require(type(p['refs']) is dict and set(p['refs'])==ROLES,'exact original evidence roles required')
    for ref in p['refs'].values():
        require(type(ref) is dict and set(ref)=={'input','original_path','sha256'} and _hash(ref['sha256']) and type(ref['input']) is str and ref['input'] and type(ref['original_path']) is str and ref['original_path'].startswith('/'),'original input reference invalid')
    require(len({x['input'] for x in p['refs'].values()})==len(ROLES),'original inputs must be distinct')

def _graph(g):
    require(type(g) is dict and set(g)=={'node_ids','node_features','edge_index','edge_features','edge_width','parent_hash','center_id'},'attributed graph schema differs')
    ids=g['node_ids'];nf=g['node_features'];ei=g['edge_index'];ef=g['edge_features']
    require(type(ids) is list and ids and all(type(x) is str and x for x in ids) and len(set(ids))==len(ids),'node identities invalid')
    require(g['center_id'] in ids and _hash(g['parent_hash']),'center/parent invalid')
    require(type(g['edge_width']) is int and g['edge_width']==2,'edge width differs')
    require(type(nf) is list and len(nf)==len(ids) and all(type(row) is list and len(row)==4 for row in nf),'node feature dimensions differ')
    require(type(ei) is list and len(ei)==2 and all(type(row) is list for row in ei) and len(ei[0])==len(ei[1]),'edge dimensions differ')
    require(all(type(v) is int and 0<=v<len(ids) for row in ei for v in row),'edge index invalid')
    require(type(ef) is list and len(ef)==len(ei[0]) and all(type(row) is list and len(row)==2 for row in ef),'edge features dimensions differ')
    require(all(type(v) in (int,float) and math.isfinite(v) for row in nf+ef for v in row),'nonfinite/boolean feature')
    return len(ids),len(ef)

@dataclass(frozen=True,slots=True)
class OriginalEvidence:
    """Immutable original JSON evidence, deliberately not a numerical Dictionary."""
    dictionary_identity:str
    sample_identity:str
    representative_indices:tuple
    original_terminal:str
    original_claim:str
    _dictionary_bytes:bytes
    _bundle_sha256:str
    def dictionary_record(self):return parse(self._dictionary_bytes)
    @property
    def bundle_sha256(self):return self._bundle_sha256

def validate(policy,blobs):
    policy_check(policy);p=parse(canonical(policy))
    require(type(blobs) is dict and set(blobs)==ROLES,'exact original body membership required')
    require(all(type(v) is bytes and len(v)<=p['max_json_bytes'] for v in blobs.values()),'metadata per-file capacity')
    require(sum(map(len,blobs.values()))<=p['max_total_json_bytes'],'metadata aggregate capacity')
    require(all(sha(v)==p['refs'][k]['sha256'] for k,v in blobs.items()),'original body hash differs')
    v={k:parse(raw) for k,raw in blobs.items()};d=v['dictionary'];s=v['samples'];claim=v['claim'];terminal=v['terminal']
    require(claim['experiment_id']==p['original_claim'] and claim['source']==claim['design_source']==p['original_source'],'original claim/source differs')
    require(claim['registration_sha256']==sha(blobs['gate']),'original registration hash differs')
    require(v['gate']['experiments'].get(p['original_claim'])==claim['experiment'],'original selected experiment differs')
    require(terminal['experiment_id']==claim['experiment_id'] and terminal['claim_sha256']==sha(blobs['claim']) and terminal['status'] in ('complete','failed'),'original terminal join differs')
    for role,phase in [('dictionary_intent','dictionary'),('sample_intent','neighborhoods')]:
        intent=v[role];require(intent['phase']==phase and intent['week']==p['week'] and intent['source_commit']==p['original_source'],'original phase/source differs')
    def join(intent,role):
        require(v[intent]['bindings'].get(p['refs'][role]['original_path'])==sha(blobs[role]),'original intermediate binding differs: '+role)
    for role in ('samples','dictionary_config','matching_config'):join('dictionary_intent',role)
    for role in ('graph_manifest','dictionary_config'):join('sample_intent',role)
    require(set(d)=={'representatives','memberships','sample_hash','training_graph_hashes','config','matching_config_hash','identity','hierarchy'},'dictionary schema differs')
    require(set(s)=={'graphs','records','source_hashes','rng_state','seed','identity'},'sample schema differs')
    require(d['config']==v['dictionary_config'] and d['config']['size']==p['motif_count'] and d['config']['sample_count']==p['sample_count'],'original dictionary configuration differs')
    require(d['matching_config_hash']==sha(canonical(v['matching_config'])),'original matching configuration differs')
    gh=v['graph_manifest']['graph_hash'];require(_hash(gh) and s['source_hashes']==d['training_graph_hashes']==[gh],'original training population differs')
    require(p['sample_config']==d['config']|{'train_start':v['graph_manifest']['metadata']['start_utc'],'train_end':p['sample_config']['train_end']},'original sample configuration differs')
    _availability(v['graph_manifest']['metadata'],p['sample_config'])
    require(s['seed']==p['seed'] and type(s['seed']) is int and s['rng_state']['bit_generator']=='PCG64','original RNG differs')
    require(type(s['graphs']) is list and type(s['records']) is list and len(s['graphs'])==len(s['records'])==p['sample_count'],'sample cardinality differs')
    totals=[0,0]
    for graph,record in zip(s['graphs'],s['records'],strict=True):
        n,e=_graph(graph);totals[0]+=n;totals[1]+=e
        require(totals[0]<=p['max_total_nodes'] and totals[1]<=p['max_total_edges'],'original graph metadata capacity')
        require(graph['parent_hash']==record['graph_hash']==gh and graph['center_id']==record['center_id'] and record['node_count']==n and record['edge_count']==e,'sample graph record differs')
        require(type(record['center_index']) is int and record['center_index']>=0 and type(record['probability']) in (int,float) and 0<record['probability']<=1,'sample draw record invalid')
    require(len({(x['graph_hash'],x['center_index']) for x in s['records']})==p['sample_count'],'repeated sampled center')
    sample_hash=sha(canonical({'training_graphs':s['source_hashes'],'config':p['sample_config'],'seed':s['seed'],'records':s['records'],'rng_state':s['rng_state']}))
    require(sample_hash==p['sample_identity']==s['identity']==d['sample_hash'],'original sample semantic identity differs')
    reps=d['representatives'];groups=d['memberships'];require(type(reps) is list and type(groups) is list and len(reps)==len(groups)==p['motif_count'],'dictionary cardinality differs')
    require(all(type(group) is list and all(type(j) is int for j in group) for group in groups) and sorted(j for group in groups for j in group)==list(range(p['sample_count'])),'membership partition differs')
    indices=[]
    for g,group in zip(reps,groups,strict=True):
        matches=[j for j,x in enumerate(s['graphs']) if canonical(x)==canonical(g)]
        require(len(matches)==1 and matches[0] in group,'representative is not unique original sample member');indices.append(matches[0])
    require(len(set(indices))==len(indices),'repeated representative')
    scientific={'graphs':[{'nodes':g['node_ids'],**{k:g[k] for k in ('node_features','edge_index','edge_features','parent_hash','center_id')}} for g in reps],
      'sample_hash':d['sample_hash'],'training_graph_hashes':d['training_graph_hashes'],'config':d['config'],'matching_hash':d['matching_config_hash'],'memberships':groups,'hierarchy':d['hierarchy']}
    require(sha(canonical(scientific))==d['identity']==p['dictionary_identity'],'original dictionary semantic identity differs')
    result=v['dictionary_result'];require(result['status']=='complete' and result['phase']=='dictionary' and result['week']==p['week'] and result['details']['identity']==d['identity'] and result['details']['motifs']==p['motif_count'] and result['details']['resource_only'] is True,'original dictionary component result differs')
    return OriginalEvidence(d['identity'],s['identity'],tuple(indices),terminal['status'],claim['experiment_id'],blobs['dictionary'],sha(canonical({'policy':p,'bodies':{k:sha(raw) for k,raw in blobs.items()}})))

# Parser-only format reconstruction; never creates a numerical Dictionary.
import struct
import sys

def motif_record_identity(g):
    require(sys.byteorder=='little','registered little-endian numeric encoding required')
    result=hashlib.sha256(b'matching-local-v1\0');extent=0
    def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    def frame(raw):result.update(len(raw).to_bytes(8,'big'));result.update(raw)
    frame(encoded({'parent_hash':g['parent_hash'],'center_id':g['center_id'],'node_count':len(g['node_ids'])}))
    for start in range(0,len(g['node_ids']),1024):frame(encoded(g['node_ids'][start:start+1024]))
    specs=[('node_features','<f8',[len(g['node_ids']),4],'d'),('edge_index','<i8',[2,len(g['edge_index'][0])],'q'),('edge_features','<f8',[len(g['edge_index'][0]),2],'d')]
    for name,dtype,shape,fmt in specs:
        count=shape[0]*shape[1];extent+=8*count
        frame(encoded({'name':name,'dtype':dtype,'shape':shape,'bytes':8*count}))
        for row in g[name]:
            for value in row:result.update(struct.pack('<'+fmt,value))
    return result.hexdigest(),extent

def expected_numeric(policy,blobs):
    evidence=validate(policy,blobs);dictionary=evidence.dictionary_record()
    hashes=[];extent=0
    for g in dictionary['representatives']:
        identity,size=motif_record_identity(g);hashes.append(identity);extent+=size
    return {'original_dictionary':evidence.dictionary_identity,'original_matching':dictionary['matching_config_hash'],
      'representative_sample_indices':list(evidence.representative_indices),'ordered_motifs':hashes,
      'bundle_sha256':evidence.bundle_sha256,'numeric_bytes':extent,'owner_stage_completed':False,'mcm_execution_admitted':False}
