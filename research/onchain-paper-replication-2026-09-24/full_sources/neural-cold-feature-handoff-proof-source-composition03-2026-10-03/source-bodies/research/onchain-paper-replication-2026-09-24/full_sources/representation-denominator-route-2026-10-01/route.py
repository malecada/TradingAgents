"""Current registered owner/calendar/coverage join for the full date denominator.

Resident graph population only. No graph feature loading, fitting, completion
publication, price revalidation or empirical release. A receipt's lease must be
checked at use; these objects are in-process contracts, not a security boundary.
"""
from dataclasses import asdict
import importlib.util
from pathlib import Path
from tradingagents.research.onchain_replication import calendar,dataset
from tradingagents.research.onchain_replication.contracts import Fold,GraphSnapshot
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest,file_hash,freeze,thaw

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
graphs=load('denominator_saved_graphs',HERE.parent/'graph-feature-artifact-route-2026-10-01/route.py')
denominator=load('denominator_metadata',HERE.parent/'representation-denominator-2026-10-01/denominator.py')
# Use the same real owner class as the following saved-graph admission route.
ownership=graphs.saved.producer.artifacts.consumer.ownership
SOURCES=tuple(sorted(set(graphs.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in
    (__file__,denominator.__file__,calendar.__file__,dataset.__file__)}))
require=graphs.require;equal=graphs.equal

class Receipt:
    __slots__=('_record','_lease')
    def __init__(self,record,lease):
        object.__setattr__(self,'_record',freeze(record));object.__setattr__(self,'_lease',lease)
    def __setattr__(self,name,value):raise AttributeError('denominator receipt is immutable')
    @property
    def record(self):return self._record
    def lease(self):self._lease()

def manifest_hash(examples):
    return digest(canonical_bytes({**vars(examples),'train':[asdict(r) for r in examples.train],
        'test':[asdict(r) for r in examples.test]}))

def admit(owned,*,examples,fold,policy_input):
    require(type(owned) is ownership.OwnedJournal,'actual denominator owner required')
    route=owned.workload;bound=route.bound;bound.check();owned.lease()
    require(bound._ancestry_arguments is None,'historical denominator admission requires separate admission')
    ad=bound._run.admission;owner=thaw(bound.record)
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'denominator source differs')
    sources();metadata=graphs.saved.producer.Metadata(ad.root)
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered denominator input required')
        info=ad.inputs[name];return metadata.read(ad.root/info['path'],info['sha256'])
    claim=metadata.read(Path(owner['journal_directory'])/'claim.json')
    plan=registered(claim['plan_input']);execution=registered('execution_job')
    item=plan.get('producers',{}).get(owner['producer'])
    selected=execution.get('payload',{}).get('representation_jobs',{}).get(owner['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('denominator_input')==selected.get('denominator_input')==policy_input,'selected denominator policy differs')
    policy=registered(policy_input)
    require(isinstance(policy,dict) and set(policy)=={'schema_version','calendar_input','coverage_input','max_calendar_days'}
        and type(policy['schema_version']) is int and policy['schema_version']==1
        and type(policy['max_calendar_days']) is int and policy['max_calendar_days']>0,'denominator policy differs')
    config=registered(policy['calendar_input']);coverage=registered(policy['coverage_input'])
    require(isinstance(config,dict) and type(config.get('lookback_days')) is int and config['lookback_days']>0
        and isinstance(config.get('folds'),list) and bool(config['folds']) and isinstance(coverage,dict),'registered calendar configuration differs')
    require(type(fold) is Fold and type(examples) is dataset.ExampleManifest,'actual denominator fold/examples required')
    admitted_folds=calendar.build_folds(config,coverage)
    matches=[f for f in admitted_folds if f.id==fold.id]
    require(len(matches)==1 and equal(asdict(matches[0]),asdict(fold))
        and equal(asdict(fold),route.descriptor['fold']),'registered fold fields/coverage differ')
    for selected_route in (item,selected):
        require(equal(selected_route.get('descriptor'),route.descriptor),'registered denominator descriptor differs')
    expected=route.control['example_manifest_sha256']
    require(equal(examples.train_hash,route.descriptor['train_hash']),'registered denominator training membership differs')
    snapshots=dict(route._graphs)
    def graph_check():
        require(set(route._graphs)==set(snapshots),'denominator graph population changed')
        for h,g in snapshots.items():
            require(type(g) is GraphSnapshot and route._graphs.get(h) is g and graph_hash(g)==h,'denominator graph source changed')
    graph_check()
    graph_metadata=tuple(dataset.CalendarGraph(g.asset,g.start_utc,g.end_utc,g.available_at,g.source_hashes,h) for h,g in snapshots.items())
    result=denominator.validate(graph_metadata,examples,fold,lookback_days=config['lookback_days'],
        max_calendar_days=policy['max_calendar_days'],expected_manifest_sha256=expected,
        expected_population=thaw(route.descriptor['graph_population']),expected_required=thaw(route.descriptor['required_graphs']))
    descriptor=thaw(route.descriptor);control=thaw(route.control)
    def lease():
        require(owned.workload is route and route.bound is bound and equal(bound.record,owner),'denominator owner replaced')
        bound.check();owned.lease();metadata.lease();sources()
        require(equal(route.descriptor,descriptor) and equal(route.control,control),'denominator route replaced')
        require(manifest_hash(examples)==expected and equal(asdict(fold),descriptor['fold']),'denominator examples/fold changed')
        graph_check();metadata.lease()
    def reference(name):return {'input':name,'sha256':ad.inputs[name]['sha256']}
    record={'schema_version':1,'owner':owner,'policy':reference(policy_input),'calendar':reference(policy['calendar_input']),
        'coverage':reference(policy['coverage_input']),'descriptor_sha256':digest(canonical_bytes(descriptor)),
        'denominator':result,'graph_completion_validated':False}
    receipt=Receipt(record,lease);receipt.lease();return receipt
