"""Registered first/failed pair-journal owner join; no numerical allocation.

Every admitted failed representation ancestor must have an exact failed pair
journal and binding certificate. Missing/partial owners and pending reservations
require separate reconciliation. This does not implement physical quotas,
workload execution, complete-representation reuse or empirical admission.
"""
import copy
import importlib.util
from pathlib import Path

from tradingagents.research.lifecycle import _lock
from tradingagents.research.onchain_replication import matching_owner as owner
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.provenance import file_hash, thaw, durable_mkdir

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
route=load('pair_owner_workload_route',HERE.parent/'pair-workload-route-2026-09-30/route.py')
journal=load('pair_owner_journal',HERE/'journal.py')
SOURCES=tuple(str(Path(p).relative_to(ROOT)) for p in (__file__,route.__file__,journal.__file__))
# Prepay the maximum certificates for the supported eight-ancestor chain so the
# derived journal policy remains identical across successors. This conservative
# logical reservation is not a measurement of filesystem allocation.
CERTIFICATE_RESERVE=(owner.ancestry.MAX_ANCESTORS+1)*journal.LIMIT

def require(value,message):
    if not value:raise ValueError(message)

def certificate(record,control_input,control_sha256):
    return {'schema_version':1,'binding':thaw(record),'control_input':control_input,'control_sha256':control_sha256}

def sources(workload):
    ad=workload.bound._run.admission
    for name in SOURCES:
        require(name in ad.experiment['source_files'] and file_hash(ROOT/name)==ad.experiment['source_files'][name],
            'pair owner implementation is not admitted')

def directory(path,root):
    require(path.is_dir() and path.resolve()==path and path.stat().st_dev==root.stat().st_dev,'pair directory containment/device differs')

def root_for(workload):
    return workload.bound._run.admission.root/'research_artifacts/onchain_pair_workflows'/workload.bound.record['workflow_identity']

def history(root,parent,initial,allowed,names,workflow,policy,ad_root,snapshots):
    """Recheck immutable compact ancestry, including its exact directory inventory."""
    for path,sha in snapshots.items():owner.ancestry._read(ad_root,path,{},expected=sha)
    if parent is None:return
    directory(root,ad_root);directory(root/'pairs',ad_root)
    for name in names:
        d=root/name;directory(d,ad_root)
        terminal,_=owner.ancestry._read(ad_root,d/'failed.json',{},expected=snapshots[d/'failed.json'])
        expected={d/'binding.json',d/'start.json',d/'failed.json',
            *(d/f'event-{i:06d}.json' for i in range(len(terminal['events'])))}
        require(set(d.iterdir())==expected,'historical pair inventory changed')
    require(owner.equal(journal.load(root,parent,workflow,policy),initial),'inherited pair state changed')
    observed={p.name for p in (root/'pairs').iterdir()}
    require(allowed<=observed,'inherited pair session disappeared')
    for name in allowed:directory(root/'pairs'/name,ad_root)

def precheck(workload,parent_input):
    require(type(workload) is route.Route,'actual admitted workload route required')
    workload.bound.check();workload.lease();sources(workload)
    bound=workload.bound;run=bound._run;ad=run.admission;record=bound.record
    policy=thaw(workload.control['journal_limits'])
    policy['max_reserved_bytes']-=CERTIFICATE_RESERVE;journal.policy(policy)
    root=root_for(workload);snapshots={};signatures={}
    def read(path,expected=None):
        value,sha=owner.ancestry._read(ad.root,path,signatures,expected=expected)
        snapshots[path]=sha;return value
    def registered(claim,name):
        require(isinstance(name,str) and name in claim['inputs'],'registered historical pair input required')
        info=claim['inputs'][name]
        return read(ad.root/info['path'],info['sha256'])
    control_input=workload.descriptor['pair_workload']['input']
    control_sha=workload.descriptor['pair_workload']['sha256']
    own_claim=read(run.directory/'claim.json',run._claim_sha256)
    own_rep_claim=read(Path(record['journal_directory'])/'claim.json')
    plan_input=own_rep_claim['plan_input']
    def routes(claim):
        plan=registered(claim,plan_input);execution=registered(claim,'execution_job')
        item=plan.get('producers',{}).get(record['producer'])
        selected=execution.get('payload',{}).get('representation_jobs',{}).get(record['representation'])
        require(isinstance(item,dict) and isinstance(selected,dict),'pair producer route missing')
        for value in (item,selected):
            require(value.get('pair_workload_input')==control_input
                and owner.equal(value.get('descriptor'),workload.descriptor),'historical workload route differs')
        require('pair_journal_parent_input' in item and 'pair_journal_parent_input' in selected
            and item['pair_journal_parent_input']==selected['pair_journal_parent_input'],'explicit pair-parent route differs')
        require(control_input in claim['inputs'] and claim['inputs'][control_input]['sha256']==control_sha,'historical workload control differs')
        registered(claim,control_input)
        return item['pair_journal_parent_input']
    require(routes(own_claim)==parent_input,'selected pair parent differs')
    args=bound._ancestry_arguments
    if args is None:
        require(parent_input is None,'first pair owner cannot inherit a parent')
        ancestors=[]
    else:
        require(isinstance(parent_input,str),'failed pair parent required')
        ancestors=owner.ancestry.verify(run,**args,current_journal=Path(record['journal_directory']))['ancestors']
    names=[row['experiment'] for row in ancestors]
    references=[];parent=None
    if ancestors:
        directory(root,ad.root);directory(root/'pairs',ad.root)
        info=ad.inputs.get(parent_input)
        require(isinstance(info,dict) and ad.root/info['path']==root/names[0]/'failed.json','exact immediate pair parent required')
        parent={'path':str(root/names[0]/'failed.json'),'sha256':info['sha256']}
        current=parent
        for i,ancestor in enumerate(ancestors):
            name=ancestor['experiment'];d=root/name;directory(d,ad.root)
            claim=read(ad.root/'research_runs'/name/'claim.json',ancestor['claim_sha256'])
            historical_parent=routes(claim)
            expected_binding=thaw(record)|{'experiment':name,'source_commit':ancestor['source_commit'],
                'claim_sha256':ancestor['claim_sha256'],'registration_sha256':claim['registration_sha256'],
                'journal_directory':str(Path(record['journal_directory']).parent/name)}
            expected=certificate(expected_binding,control_input,control_sha)
            require(owner.equal(read(d/'binding.json'),expected),'historical pair binding differs from admitted owner')
            require(current['path']==str(d/'failed.json'),'pair ancestry order differs')
            terminal=read(d/'failed.json',current['sha256'])
            require(terminal.get('status')=='failed' and not ((d/'complete.json').exists() or (d/'complete.json').is_symlink()),'failed pair owner required')
            require(terminal.get('start',{}).get('path')==str(d/'start.json'),'pair start path differs')
            start=read(d/'start.json',terminal['start']['sha256'])
            require(start.get('owner')==cache_key(expected) and start.get('workflow')==record['workflow_identity']
                and owner.equal(start.get('policy'),policy),'pair start owner/workflow/quota differs')
            next_reference=None
            if i+1<len(names):
                require(isinstance(historical_parent,str) and historical_parent in claim['inputs'],'historical pair ancestor omitted')
                info=claim['inputs'][historical_parent];fixed=root/names[i+1]/'failed.json'
                require(ad.root/info['path']==fixed,'historical pair parent path differs')
                next_reference={'path':str(fixed),'sha256':info['sha256']}
            else:require(historical_parent is None,'unaccounted historical pair ancestor')
            require(owner.equal(start.get('parent'),next_reference),'pair ancestry pointer differs')
            references.append(current);current=next_reference
        require(set(root.iterdir())=={root/'pairs',*(root/name for name in names)},'foreign or omitted pair owner')
    else:
        require(not root.exists() and not root.is_symlink(),'pair workflow already reserved')
    # All pair certificates are joined to admitted claims before journal replay.
    state=journal.empty() if parent is None else journal.load(root,parent,record['workflow_identity'],policy)
    require(state['pending'] is None,'pair reservation requires reconciliation')
    allowed=set()
    for reference in references:
        terminal=read(Path(reference['path']),reference['sha256'])
        for ref in terminal['events']:
            event=read(Path(ref['path']),ref['sha256'])
            if event['kind']=='reserve':allowed.add(event['payload']['artifact_owner'])
            elif event['kind']=='publish':read(Path(event['payload']['path']),event['payload']['sha256'])
    if ancestors:
        require({p.name for p in (root/'pairs').iterdir()}==allowed,'foreign or missing pair session')
        for name in allowed:directory(root/'pairs'/name,ad.root)
    candidate=copy.deepcopy(state);candidate['reserved_bytes']+=2*journal.LIMIT;journal.quota(candidate,policy)
    cert=certificate(record,control_input,control_sha)
    require(len(journal.encode(cert))<=journal.LIMIT,'pair binding metadata bound exceeded')
    history(root,parent,state,allowed,names,record['workflow_identity'],policy,ad.root,snapshots)
    workload.lease()
    return root,policy,parent,state,allowed,snapshots,cert,names

class OwnedJournal:
    def __init__(self,workload,j,initial,allowed,snapshots,cert_reference,names,parent):
        self.workload=workload;self.journal=j;self.initial=copy.deepcopy(initial)
        self.allowed=set(allowed);self.snapshots=dict(snapshots);self.cert_reference=cert_reference;self.names=tuple(names);self.parent=copy.deepcopy(parent)
    @property
    def reserved_bytes(self):return CERTIFICATE_RESERVE+self.journal.reserved_bytes
    def lease(self):
        self.workload.lease();sources(self.workload);j=self.journal;j.active()
        ad=self.workload.bound._run.admission
        history(j.root,self.parent,self.initial,self.allowed,self.names,j.workflow,j.policy,ad.root,self.snapshots)
        cert,_=owner.ancestry._read(ad.root,Path(self.cert_reference['path']),{},expected=self.cert_reference['sha256'])
        require(cache_key(cert)==j.owner,'current pair binding differs')
        start,_=owner.ancestry._read(ad.root,Path(j.start['path']),{},expected=j.start['sha256'])
        require(start['owner']==j.owner and start['workflow']==j.workflow and owner.equal(start['policy'],j.policy),'current pair start differs')
        require(not any((j.directory/n).exists() or (j.directory/n).is_symlink() for n in ('complete.json','failed.json')),'current pair owner is terminal')
        directory(j.root,ad.root);directory(j.root/'pairs',ad.root)
        require(set(j.root.iterdir())=={j.root/'pairs',j.directory,*(j.root/name for name in self.names)},'pair owner inventory changed')
        state=copy.deepcopy(self.initial);state['reserved_bytes']+=2*journal.LIMIT
        allowed=set(self.allowed);previous=j.start['sha256']
        require(sorted(p.name for p in j.directory.glob('event-*.json'))==[f'event-{i:06d}.json' for i in range(len(j.records))],'current pair event inventory differs')
        for i,ref in enumerate(j.records):
            require(ref['path']==str(j.directory/f'event-{i:06d}.json'),'current event path differs')
            event,_=owner.ancestry._read(ad.root,Path(ref['path']),{},expected=ref['sha256'])
            require(event['previous']==previous,'current event predecessor differs')
            state=journal.apply(state,event,j.directory,j.owner,j.workflow,j.policy);previous=ref['sha256']
            if event['kind']=='reserve':allowed.add(event['payload']['artifact_owner'])
        require(owner.equal(state,j.state) and previous==j.previous,'current pair journal state differs')
        observed={p.name for p in (j.root/'pairs').iterdir()}
        require(self.allowed<=observed<=allowed,'missing inherited or unreserved pair session')
        for path in (j.root/'pairs').iterdir():directory(path,ad.root)
        self.workload.lease()
    def seal(self,status):
        self.lease();return self.journal.seal(status)

def open_journal(workload,*,parent_input=None):
    checked=precheck(workload,parent_input)
    run=workload.bound._run
    with _lock(run.admission.root):
        # Recheck exact metadata/ownership under the exclusive lifecycle lock.
        workload.lease();sources(workload)
        root,policy,parent,initial,allowed,snapshots,cert,names=checked
        def before_create():
            history(root,parent,initial,allowed,names,workload.bound.record['workflow_identity'],policy,run.admission.root,snapshots)
            require(set(root.iterdir())=={root/'pairs',*(root/name for name in names)},'pair owner appeared before creation')
            require({p.name for p in (root/'pairs').iterdir()}==allowed,'pair session appeared before creation')
            workload.lease()
        history(root,parent,initial,allowed,names,workload.bound.record['workflow_identity'],policy,run.admission.root,snapshots)
        if parent is None:
            existing=root.parent
            while not existing.exists():existing=existing.parent
            directory(existing,run.admission.root)
            require(root.resolve()==root,'pair root path differs')
            workload.lease()
            durable_mkdir(root.parent);root.mkdir(exist_ok=False);journal.sync(root.parent)
            (root/'pairs').mkdir();journal.sync(root)
        else:
            require(set(root.iterdir())=={root/'pairs',*(root/name for name in names)},'pair owner appeared before creation')
        j=journal.Journal(root,run.admission.experiment_id,cache_key(cert),workload.bound.record['workflow_identity'],policy,parent=parent,before_create=before_create)
        ref=journal.write(j.directory/'binding.json',cert)
        owned=OwnedJournal(workload,j,initial,allowed,snapshots,ref,names,parent)
        owned.lease()
        return owned
