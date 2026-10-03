"""Read-only registered workload join, not a pair owner or empirical release.

No pair allocation, journal creation, sampling or fitting occurs here. Actual
graph/sample checks currently require resident GraphSnapshot objects; mapped
population ownership and whole-workflow physical accounting remain separate.
"""
from dataclasses import asdict
import math
from pathlib import Path

from tradingagents.research.lifecycle import ResearchRun
from tradingagents.research.onchain_replication import matching_owner as owner, matching_pair as pair
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.dataset import ExampleManifest
from tradingagents.research.onchain_replication.neighborhoods import graph_hash, SampleManifest, NeighborhoodIndex
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.registered_features import representation_descriptor
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, file_hash, freeze, thaw, utc

ROOT=Path(__file__).resolve().parents[4]
SELF=str(Path(__file__).resolve().relative_to(ROOT))

def require(value,message):
    if not value:raise ValueError(message)

def positive(value):return type(value) is int and value>0

def control_schema(control):
    require(isinstance(control,dict) and set(control)=={'schema_version','max_entries','operations_per_checkpoint',
        'max_checkpoints','journal_limits','example_manifest_sha256'},'workload control schema differs')
    pair.hash_string(control['example_manifest_sha256'])
    require(type(control['schema_version']) is int and control['schema_version']==1,'workload control version differs')
    require(all(positive(control[k]) for k in ('max_entries','operations_per_checkpoint','max_checkpoints')),'positive workload schedule required')
    limits=control['journal_limits']
    require(isinstance(limits,dict) and set(limits)=={'max_reserved_bytes','max_reservations','max_events'}
        and all(positive(v) for v in limits.values()),'positive workload journal quotas required')

class Route:
    def __init__(self,bound,descriptor,control,graphs,settings,snapshots):
        self.bound=bound;self.descriptor=freeze(descriptor);self.control=freeze(control)
        self.record=freeze({'owner':thaw(bound.record),'control_sha256':descriptor['pair_workload']['sha256']})
        self._graphs=dict(graphs);self.settings=freeze(settings);self._snapshots=dict(snapshots)
    def lease(self):
        self.bound.lease()
        root=self.bound._run.admission.root
        for path,expected in self._snapshots.items():
            owner.ancestry._read(root,path,{},expected=expected)
        require(file_hash(ROOT/SELF)==self.bound._run.admission.experiment['source_files'][SELF],
            'imported workload source changed')
        self.bound.lease()
    def sample_scope(self,samples):
        """Check actual induced sample graphs and derive the exact dictionary scope.

        Does not re-run the weighted RNG draw or authorize pair allocation.
        Sampler/journal provenance is still required from the outer producer.
        """
        self.lease()
        require(isinstance(samples,SampleManifest),'actual sample manifest required')
        cfg=thaw(self.settings);seed=self.descriptor['seed']
        require(type(samples.seed) is int and samples.seed==seed,'sample seed differs')
        # Rehash current resident parents once at this numerical boundary.
        training=[]
        for h,g in self._graphs.items():
            require(graph_hash(g)==h,'admitted graph changed')
            if utc(g.start_utc)>=utc(cfg['train_start']) and utc(g.available_at)<utc(cfg['train_end']):training.append((h,g))
        training.sort(key=lambda item:(item[1].start_utc,item[1].asset,item[0]))
        hashes=tuple(h for h,g in training)
        require(tuple(samples.source_hashes)==hashes,'sample training population differs')
        require(len(samples.graphs)==len(samples.records)==cfg['sample_count'],'sample count differs')
        expected=cache_key({'training_graphs':hashes,'config':cfg,'seed':seed,'records':samples.records,'rng_state':samples.rng_state})
        require(samples.identity==expected,'sample configuration/order identity differs')
        typed=[];seen=set();active=None;index=None
        for local,record in zip(samples.graphs,samples.records,strict=True):
            require(set(record)=={'graph_hash','center_id','center_index','probability','node_count','edge_count'},'sample record schema differs')
            h=record['graph_hash'];center=record['center_index'];probability=record['probability']
            require(h in hashes and type(center) is int and 0<=center<len(self._graphs[h].node_ids),'sample center membership differs')
            require((h,center) not in seen,'duplicate sampled center');seen.add((h,center))
            require(type(probability) in (float,int) and math.isfinite(probability) and 0<probability<=1,'sample probability differs')
            require(local.parent_hash==h and local.center_id==record['center_id']==self._graphs[h].node_ids[center]
                and type(record['node_count']) is int and record['node_count']==len(local.node_ids)
                and type(record['edge_count']) is int and record['edge_count']==local.edge_index.shape[1],'sample graph/record differs')
            if active!=h:index=NeighborhoodIndex(self._graphs[h]);active=h
            identity=graph_identity(local)
            require(identity==graph_identity(index.neighborhood(center,cfg)),'sample is not the actual induced neighborhood')
            typed.append(identity)
        result=cache_key({'schema_version':1,'kind':'dictionary','workflow':self.bound.record['workflow_identity'],
            'backend':pair.BACKEND,'sample':samples.identity,'typed_sample_graphs':typed,
            'matching':self.descriptor['configs']['matching'],'dictionary':cfg,'seed':seed})
        self.lease();return result

def admit(run,*,representation,plan_input,producer,policy_input,control_input,journal_directory,
          graphs,examples,fold,seed,configs,continuation_input=None,death_input=None):
    require(isinstance(run,ResearchRun),'actual admitted ResearchRun required')
    run._active();ad=run.admission;snapshots={}
    require(SELF in ad.experiment['source_files'] and file_hash(ROOT/SELF)==ad.experiment['source_files'][SELF],
        'workload route source is not admitted')
    def read(name):
        require(isinstance(name,str) and name in ad.inputs,'registered workload input required')
        info=ad.inputs[name];path=ad.root/info['path']
        value,sha=owner.ancestry._read(ad.root,path,{},expected=info['sha256'])
        snapshots[path]=sha;return value
    control=read(control_input);control_schema(control)
    plan=read(plan_input);execution=read('execution_job')
    require(type(plan.get('schema_version')) is int and plan['schema_version']==2,'version2 plan required')
    item=plan.get('producers',{}).get(producer)
    selected=execution.get('payload',{}).get('representation_jobs',{}).get(representation)
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('pair_workload_input')==selected.get('pair_workload_input')==control_input,'selected workload route differs')
    descriptor=item['descriptor']
    expected_control={'input':control_input,'sha256':ad.inputs[control_input]['sha256']}
    require(descriptor.get('pair_workload')==expected_control,'descriptor workload identity differs')
    bound=owner.bind(run,representation=representation,plan_input=plan_input,producer=producer,policy_input=policy_input,
        journal_directory=journal_directory,continuation_input=continuation_input,death_input=death_input)
    bound.check()
    # All input/route/schedule/owner checks above precede actual graph iteration.
    require(type(seed) is int and seed>=0,'integer seed required')
    require(isinstance(examples,ExampleManifest) and examples.fold_hash==fold.member_hash,'actual example/fold membership required')
    actual_examples={**vars(examples),'train':[asdict(row) for row in examples.train],
        'test':[asdict(row) for row in examples.test]}
    require(digest(canonical_bytes(actual_examples))==control['example_manifest_sha256'],
        'actual example population differs from registration')
    require(examples.train_hash==digest(canonical_bytes([asdict(x) for x in examples.train]))
        and examples.test_mask_hash==digest(canonical_bytes([x.decision_at for x in examples.test])), 'actual example membership differs')
    graphs=tuple(graphs)
    require(bool(graphs) and all(type(g) is GraphSnapshot for g in graphs),'resident graph population required; mapped admission remains separate')
    actual=representation_descriptor(graphs,examples,fold,'proposed',seed,configs)
    actual.update(pair_execution={'backend':pair.BACKEND,'policy_sha256':ad.inputs[policy_input]['sha256']},pair_workload=expected_control)
    require(owner.equal(actual,descriptor),'actual graph/configuration descriptor differs')
    by_hash={graph_hash(g):g for g in graphs}
    require(len({g.asset for g in graphs})==1 and len({g.start_utc for g in graphs})==len(graphs),'mixed asset or duplicate week')
    require(all(set(g.source_hashes)<=set(examples.source_hashes) for g in graphs),'unbound actual graph source')
    refs=item.get('graphs')
    require(isinstance(refs,dict) and set(refs)==set(by_hash),'registered graph manifest population differs')
    for h,reference in refs.items():
        # First release supports existing registered graph inputs only. Same-run
        # outputs need a separately reviewed publication binding, not a fallback.
        require(isinstance(reference,dict) and set(reference)=={'input'},'exact registered graph input required')
        metadata=read(reference['input'])
        require(metadata.get('graph_hash')==h,'actual graph differs from admitted manifest')
    for partition,rows in [('train',examples.train),('test',examples.test)]:
        require(bool(rows),'empty declared example partition')
        for row in rows:
            require(len(row.graph_hashes)==len(row.graph_available_at) and bool(row.graph_hashes),'graph clock dimensions differ')
            require(utc(row.max_input_available_at)<=utc(row.decision_at),'future example input')
            if partition=='train':require(utc(fold.train_start)<=utc(row.decision_at)<utc(fold.train_end)
                and utc(row.label_end)<utc(fold.test_start),'training fold clocks differ')
            else:require(utc(fold.test_start)<=utc(row.decision_at)<utc(fold.test_end)
                and utc(row.label_end)<=utc(fold.test_end),'test fold clocks differ')
            for h,timestamp in zip(row.graph_hashes,row.graph_available_at,strict=True):
                require(h in by_hash and utc(by_hash[h].available_at)==utc(timestamp)
                    and utc(timestamp)<=utc(row.decision_at),'actual graph clock lineage differs')
    settings=dict(configs['dictionary'])|{'train_start':fold.train_start,'train_end':fold.train_end}
    route=Route(bound,descriptor,control,by_hash,settings,snapshots)
    route.lease();return route
