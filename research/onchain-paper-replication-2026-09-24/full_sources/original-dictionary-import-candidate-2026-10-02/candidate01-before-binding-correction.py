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
    require(v['graph_manifest']['metadata']['available_at']<p['sample_config']['train_end'],'original graph unavailable inside sampling interval')
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

class ImportedOriginal:
    """Current Binding-bound metadata capability, not a compact numerical view.

    Callback return is withheld until exact original inputs and live authority
    rejoin. This does not certify arbitrary callback side effects or graph arrays.
    """
    def __init__(self,policy,reader,lease,owner_identity):
        self._policy=canonical(policy);self._reader=reader;self._lease=lease
        self._identity=owner_identity;self._closed=False;self._lock=Lock()
        self._reader_pin=reader;self._lease_pin=lease;self._owner_pin=owner_identity
        self._initial=self._check().bundle_sha256
    def _check(self):
        require(not self._closed,'import capability closed')
        require(self._reader is self._reader_pin and self._lease is self._lease_pin and self._identity==self._owner_pin,'import authority changed')
        self._lease();p=parse(self._policy);policy_check(p)
        blobs={k:self._reader(p['refs'][k]['input']) for k in sorted(ROLES)}
        value=validate(p,blobs);self._lease()
        # Rejoin all originals after the final authority callback.
        final_blobs={k:self._reader(p['refs'][k]['input']) for k in sorted(ROLES)}
        require(final_blobs==blobs,'original bytes changed across authority callback')
        require(not hasattr(self,'_initial') or value.bundle_sha256==self._initial,'original import evidence changed')
        return value
    def check(self):
        require(self._lock.acquire(False),'concurrent import transition')
        try:return self._check()
        finally:self._lock.release()
    def with_evidence(self,action):
        require(self._lock.acquire(False),'concurrent import transition');primary=None;result=None
        try:
            value=self._check()
            try:result=action(value)
            except BaseException as error:primary=error
            try:self._check()
            except BaseException as error:
                fatal=lambda x:isinstance(x,MemoryError) or not isinstance(x,Exception)
                if primary is None:primary=error
                elif fatal(error) and not fatal(primary):error.__cause__=primary;primary=error
                else:primary.add_note('post-callback evidence/authority check failed: '+type(error).__name__)
            if primary is not None:raise primary
            return result
        finally:self._lock.release()
    def close(self):
        require(self._lock.acquire(False),'concurrent import transition')
        try:require(not self._closed,'import capability already closed');self._closed=True
        finally:self._lock.release()

def _bind_for_test(policy,reader,lease,owner_identity):
    """Explicit synthetic metadata boundary. Never an empirical admission API."""
    return ImportedOriginal(policy,reader,lease,owner_identity)

def _read_registered(run,name):
    """Bounded exact bytes via existing descriptor-relative storage reader."""
    from pathlib import Path
    import os
    import sys
    from tradingagents.research.onchain_replication import score_batches as io
    require(type(name) is str and name in run.admission.inputs,'registered import input required')
    root=run.admission.root.resolve();info=run.admission.inputs[name]
    path=root/info['path']
    require(path.is_relative_to(root) and path.resolve()==path,'registered import path redirected')
    parent,fd=io._open(path.parent)
    try:
        raw=io._read(fd,path.name,2*1024**2);io._root(parent,fd)
        require(sha(raw)==info['sha256'],'registered exact body hash differs')
        return raw
    finally:
        primary=sys.exception()
        try:os.close(fd)
        except BaseException as error:
            fatal=io.CleanupFailure('import metadata parent close unresolved')
            fatal.add_note(type(error).__name__)
            if primary is not None and (isinstance(primary,MemoryError) or not isinstance(primary,Exception)):
                primary.add_note('import metadata parent close unresolved');raise primary from error
            raise fatal from (primary if primary is not None else error)


def admit(bound,*,input_name,job_input='execution_job'):
    """Prospective typed Binding integration; frozen-source admission is mandatory.

    Uses existing bounded no-follow ancestry reader, not an invented filesystem
    writer. No capability is returned unless both selected job and plan agree.
    Existing job/descriptor schemas do not yet admit this route.
    """
    from tradingagents.research.onchain_replication import matching_owner
    from tradingagents.research.onchain_replication.provenance import thaw, file_hash
    from pathlib import Path
    require(type(bound) is matching_owner.Binding,'actual current matching Binding required')
    run=bound._run;ad=run.admission;original_bound=bound;original_run=run
    path=Path(__file__).resolve();root=ad.root.resolve()
    require(path.is_relative_to(root),'candidate source is not inside admitted source root')
    relative=str(path.relative_to(root));expected=ad.experiment['source_files'].get(relative)
    require(expected is not None and file_hash(path)==expected,'executed import source not admitted')
    control_pin=None;route_pin=None
    def reader(name):
        return _read_registered(run,name)
    def selection():
        selected=parse(reader(job_input))['payload']['representation_jobs'][bound.record['representation']]
        item=parse(reader(selected['plan_input']))['producers'][bound.record['producer']]
        require(selected.get('original_dictionary_input')==item.get('original_dictionary_input')==input_name,'explicit original import selector differs')
        require(selected.get('descriptor')==item.get('descriptor') and sha(canonical(selected['descriptor']))==bound.record['workflow_identity'],'original import descriptor differs')
        require(selected['descriptor'].get('original_dictionary_import')=={'input':input_name,'sha256':ad.inputs[input_name]['sha256']},'import descriptor input hash differs')
        return canonical({'selected':selected,'item':item})
    def lease():
        require(bound is original_bound and bound._run is original_run,'original live Binding changed')
        bound.lease()
        if control_pin is not None:require(reader(input_name)==control_pin,'import control changed')
        if route_pin is not None:require(selection()==route_pin,'import selection changed')
        require(file_hash(path)==expected,'import source changed')
    bound.check();route_pin=selection();control_pin=reader(input_name);policy=parse(control_pin);policy_check(policy)
    require(all(ad.inputs.get(ref['input'],{}).get('sha256')==ref['sha256'] for ref in policy['refs'].values()),'original body references not admitted')
    cap=ImportedOriginal(policy,reader,lease,sha(canonical(thaw(bound.record))))
    bound.check();cap.check();return cap
