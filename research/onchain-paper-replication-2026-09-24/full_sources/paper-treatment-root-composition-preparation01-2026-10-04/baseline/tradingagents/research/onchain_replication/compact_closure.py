"""Current-owner full compact graph/calendar admission to a metadata binding.

No representation event, owner terminal seal, native dispatch or empirical fit
is authorized here. Saved graph tensors are loaded and released sequentially.
Payload allowance covers retained source/features plus one loaded graph; other
parent attributes, dictionary/samples, provenance scratch and RSS remain outside.
"""
import hashlib
import json

from . import compact_dictionary, compact_denominator, compact_graph_artifacts, compact_mcm, compact_features
from . import compact_owner, score_batches as io
from .cache import cache_key
from .neighborhoods import node_order_hash, graph_hash
from .provenance import canonical_bytes, freeze, thaw

require = io._require


def _edges(edges):
    h = hashlib.sha256(canonical_bytes({'shape':edges.shape,'dtype':str(edges.dtype)}))
    # Native admitted graph edges are contiguous; hash bounded zero-copy views.
    if edges.size:
        raw = memoryview(edges).cast('B')
        for offset in range(0,len(raw),262144):h.update(raw[offset:offset+262144])
    return h.hexdigest()


def _membership(dictionary,denominator,graphs):
    require(type(dictionary) is compact_dictionary.Produced and type(denominator) is compact_denominator.Receipt,
        'actual compact dictionary and denominator required')
    training = compact_mcm._training(dictionary); owner = dictionary._proof.owner
    require(denominator._training is training and denominator.record['owner'] == owner.identity,
        'compact closure denominator ancestry differs')
    required = tuple(training.descriptor['required_graphs'])
    require(tuple(denominator.record['denominator']['required_graphs']) == required,
        'compact closure calendar graph union differs')
    require(type(graphs) in (tuple,list) and len(graphs) == len(required)
        and all(type(p) is compact_graph_artifacts.Published for p in graphs),
        'actual complete compact graph artifact population required')
    keys = [p.record['graph_hash'] for p in graphs]
    require(sorted(keys) == list(required),'exact unique compact graph union required')
    require(all(p._features._mcm._dictionary is dictionary and compact_graph_artifacts._owner(p._features) is owner
        for p in graphs),'compact closure graph dictionary/owner differs')
    require(owner.active is None and not owner.closed and set(owner.stages) == set(owner.required)
        == {'dictionary',*('mcm-'+h for h in required)} and all(s.closed for s in owner.stages.values()),
        'compact closure required stages incomplete')
    return training,owner,{p.record['graph_hash']:p for p in graphs}


def _final(dictionary,denominator,graphs):
    training,owner,by_hash = _membership(dictionary,denominator,graphs)
    compact_owner.verify_current(owner)
    dictionary._proof._final(); dictionary._numeric(); dictionary._evidence()
    compact_denominator._original(training); denominator._integrity()
    owner._verified_stages()
    parent = None
    for p in graphs:
        compact_graph_artifacts._original(p._features); p._evidence()
        require(p.directory == compact_graph_artifacts.directory(p._features),'compact graph artifact path differs')
        require(parent is None or p.directory.parent == parent,'compact graph attempt parents differ')
        parent = p.directory.parent
    compact_owner.entries(parent,set(by_hash),required=set(by_hash))


class Receipt:
    __slots__ = ('_dictionary','_denominator','_graphs','_record','_pin')
    def __init__(self,dictionary,denominator,graphs,record):
        object.__setattr__(self,'_dictionary',dictionary);object.__setattr__(self,'_denominator',denominator)
        object.__setattr__(self,'_graphs',tuple(graphs));object.__setattr__(self,'_record',freeze(record))
        object.__setattr__(self,'_pin',cache_key(record))
    def __setattr__(self,name,value):raise AttributeError('compact closure receipt is immutable')
    record = property(lambda self:self._record)
    def _integrity(self):
        require(cache_key(thaw(self.record)) == self._pin,'compact closure record changed')
        require(self.record['dictionary_receipt_sha256'] == self._dictionary.receipt_sha256
            and self.record['denominator'] == self._denominator.record,'compact closure original evidence differs')
        require({p.record['graph_hash']:p.receipt_sha256 for p in self._graphs} == dict(self.record['graph_receipts']),
            'compact closure graph receipts changed')
    def lease(self):
        self._integrity();self._dictionary.lease();self._denominator.lease()
        for p in self._graphs:p.lease()
        self._integrity()
    def _check(self):
        self._dictionary.check();self._denominator._check()
        for p in self._graphs:p._check()
        self.lease();_final(self._dictionary,self._denominator,self._graphs)
    def check(self):
        owner = self._dictionary._proof.owner
        require(owner._transition.acquire(blocking=False),'concurrent compact closure check')
        try:self._check()
        finally:owner._transition.release()


def admit(dictionary,denominator,graphs,*,input_name):
    training,owner,by_hash = _membership(dictionary,denominator,graphs)
    require(owner._transition.acquire(blocking=False),'concurrent compact closure admission')
    try:
        dictionary.check();denominator._check();_final(dictionary,denominator,graphs)
        run = owner.bound._run; bound = owner.bound.record
        selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound['representation']]
        item = json.loads(run.read_input(selected['plan_input']))['producers'][bound['producer']]
        require(type(input_name) is str and input_name in run.admission.inputs
            and item.get('compact_closure_input') == selected.get('compact_closure_input') == input_name,
            'selected compact closure policy differs')
        policy = json.loads(run.read_input(input_name))
        fields = {'schema_version','max_graphs','max_record_bytes','max_numeric_payload_bytes'}
        require(type(policy) is dict and set(policy) == fields and type(policy['schema_version']) is int
            and policy['schema_version'] == 1 and all(type(policy[k]) is int and 0 < policy[k] < 2**63
            for k in fields-{'schema_version'}) and policy['max_record_bytes'] <= 2*1024**2,
            'compact closure policy differs')
        require(0 < len(by_hash) <= policy['max_graphs'],'compact closure graph count bound exceeded')
        sizes = [p.record['numeric_payload_bytes'] for p in graphs]
        reserved = 2*sum(sizes)+max(sizes)
        require(reserved <= policy['max_numeric_payload_bytes'],'compact closure numeric payload allowance exceeded')
        # Pin selected policies and component receipts before sequential readback.
        receipts = {h:by_hash[h].receipt_sha256 for h in sorted(by_hash)}
        for h in sorted(by_hash):
            loaded = by_hash[h]._load();loaded.lease();del loaded
            _final(dictionary,denominator,graphs)
        feature_hashes = {h:by_hash[h].record['feature_hash'] for h in sorted(by_hash)}
        lineage = {}; charge = 0
        originals = {graph_hash(g):g for g in training.graphs}
        for h in sorted(set(by_hash)|set(dictionary.dictionary.training_graph_hashes)):
            g = originals[h]
            value = {'input_graph_hash':h,'asset':g.asset,'source_hashes':list(g.source_hashes),
                'start_utc':g.start_utc,'end_utc':g.end_utc,'available_at':g.available_at,
                'node_order_hash':node_order_hash(g.node_ids),'edge_index_hash':_edges(g.edge_index)}
            charge += len(canonical_bytes(value))+len(h)+8
            require(charge <= policy['max_record_bytes'],'compact closure lineage metadata allowance exceeded')
            lineage[h] = value
        descriptor = training.descriptor; examples = training._examples; fold = training._fold
        binding = {'schema_version':3,'workflow_identity':bound['workflow_identity'],'representation':'motif_mcm',
            'asset':originals[sorted(by_hash)[0]].asset,'fold_id':fold.id,'fold_hash':examples.fold_hash,
            'train_hash':examples.train_hash,'seed':training.seed,'dictionary_hash':dictionary.dictionary.identity,
            'dictionary_training_graph_hashes':list(dictionary.dictionary.training_graph_hashes),
            'configuration_hash':cache_key({'dictionary':thaw(training.settings),
                'matching':thaw(descriptor['configs']['matching']),'baselines':thaw(descriptor['configs']['baselines'])}),
            'feature_hashes':feature_hashes,'lineage':lineage,'alignment_order':[],
            'alignment_order_policy':'available_at,start_utc,graph_hash; start at earliest required event week'}
        record = {'schema_version':1,'owner':owner.identity,'policy':{'input':input_name,
            'sha256':run.admission.inputs[input_name]['sha256']},'binding':binding,
            'dictionary_receipt_sha256':dictionary.receipt_sha256,'denominator':thaw(denominator.record),
            'graph_receipts':receipts,'reserved_numeric_payload_bytes':reserved,
            'empirical_admission_verified':False,'representation_published':False}
        require(len(canonical_bytes(record)) <= policy['max_record_bytes'],'compact closure record allowance exceeded')
        result = Receipt(dictionary,denominator,graphs,record)
        result.lease();_final(dictionary,denominator,graphs)
        return result
    finally:owner._transition.release()
