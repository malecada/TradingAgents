"""Exclusive durable representation event, with explicit prefix-to-tail handoff.

The journal stays active/unsealed. This does not publish ResearchRun outputs,
perform sealed/historical reuse, or admit a fit. Snapshot signatures are local
drift checks; their proof is not a portable replacement for content validation.
"""
import importlib.util
import os
from pathlib import Path
import stat
from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest,file_hash,thaw,durable_mkdir,sync_directory

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('publication_representation_closure',HERE.parent/'representation-closure-route-2026-10-01/closure.py')
closure=importlib.util.module_from_spec(spec);spec.loader.exec_module(closure)
saved=closure.saved;reader=closure.reader;producer=saved.producer
SOURCES=tuple(sorted(set(closure.SOURCES)|{str(Path(__file__).relative_to(ROOT))}))
require=saved.require;equal=saved.equal

def component_manifest(payload,context):
    def encode(value):
        if type(value) is dict:return {'kind':'dict','items':[[encode(k),encode(v)] for k,v in value.items()]}
        if type(value) in (tuple,list):return {'kind':'tuple' if type(value) is tuple else 'list','items':[encode(x) for x in value]}
        require(value is None or type(value) in (bool,str,int,float),'representation metadata payload required')
        canonical_bytes(value);return {'kind':'scalar','value':value}
    return {'schema_version':1,'context':context,'tree':encode(payload),'arrays':{}}

class Snapshot:
    """Bounded inventory plus admitted content hashes, bracketed by leases."""
    def __init__(self,root,directories,cap,*,expected_files):
        require(type(cap) is int and cap>0,'positive snapshot allowance required')
        require(type(expected_files) is dict and bool(expected_files),'explicit admitted snapshot hashes and extents required')
        self.root=root;self.files={};self.dirs={};self.expected={p:dict(v) for p,v in expected_files.items()};count=0
        for path in sorted(set(directories)):
            require(path.resolve()==path and path.is_relative_to(root),'snapshot directory containment differs')
            value=path.lstat();require(stat.S_ISDIR(value.st_mode) and value.st_dev==root.stat().st_dev,'snapshot directory type/device differs')
            count+=1;require(count<=cap,'snapshot entry allowance exceeded')
            children=set()
            for child in path.iterdir():
                count+=1;require(count<=cap,'snapshot entry allowance exceeded')
                info=self.expected.get(child)
                require(type(info) is dict and set(info)=={'sha256','bytes'} and type(info['bytes']) is int and info['bytes']>=0,'snapshot file extent is not admitted')
                sha=info['sha256']
                require(type(sha) is str and len(sha)==64 and all(c in '0123456789abcdef' for c in sha),'snapshot file hash is not admitted')
                with reader.opened(child,root) as (stream,sig):
                    require(sig[2]==info['bytes'],'snapshot declared extent differs')
                    require(reader.digest_stream(stream,info['bytes'])==sha,'snapshot content hash differs')
                    self.files[child]=sig
                children.add(child)
            self.dirs[path]=((value.st_dev,value.st_ino),children)
        require(set(self.files)==set(self.expected),'snapshot admitted file membership differs')
        self.check()
    def check(self):
        for path,(identity,files) in self.dirs.items():
            value=path.lstat()
            require(path.resolve()==path and stat.S_ISDIR(value.st_mode) and (value.st_dev,value.st_ino)==identity,'snapshot directory changed')
            reader.inventory(path,files)
        for path,sig in self.files.items():
            with reader.opened(path,self.root,sig) as (stream,current):
                info=self.expected[path]
                require(current[2]==info['bytes'],'snapshot declared extent differs')
                require(reader.digest_stream(stream,info['bytes'])==info['sha256'],'snapshot content hash differs')
    def record(self):
        return {'files':{str(p):{'signature':list(s),'sha256':self.expected[p]['sha256'],'bytes':self.expected[p]['bytes']} for p,s in sorted(self.files.items())},
            'directories':{str(p):{'identity':list(v[0]),'members':sorted(str(x) for x in v[1])} for p,v in sorted(self.dirs.items())}}

def attempt_directory(owned):
    b=owned.workload.bound;return b._run.admission.root/'research_artifacts/onchain_representation_publications'/b.record['workflow_identity']/b.record['experiment']

def produce(owned,journal,*,examples,fold,denominator_input,dictionary_ticket,closure_input,output_input):
    saved.actual_owner(owned,journal);route=owned.workload;bound=route.bound;ad=bound._run.admission;owner=thaw(bound.record)
    directory=Path(owner['journal_directory']);attempt=attempt_directory(owned);prefix=thaw(journal.records);index=len(prefix)
    metadata=producer.Metadata(ad.root);written={};published=False;snapshot=None;date_receipt=None;component_state=None
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'representation publication source differs')
    sources()
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered representation output input required')
        info=ad.inputs[name];return metadata.read(ad.root/info['path'],info['sha256'])
    claim=metadata.read(directory/'claim.json');plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(owner['producer']);selected=job.get('payload',{}).get('representation_jobs',{}).get(owner['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('representation_output_input')==selected.get('representation_output_input')==output_input,'selected representation output differs')
    policy=registered(output_input)
    require(isinstance(policy,dict) and set(policy)=={'schema_version','max_metadata_bytes','max_manifest_bytes','max_attempt_bytes','max_snapshot_entries','max_journal_events'}
        and type(policy['schema_version']) is int and policy['schema_version']==1
        and all(type(v) is int and v>0 for k,v in policy.items() if k!='schema_version')
        and max(policy['max_metadata_bytes'],policy['max_manifest_bytes'])<=reader.MANIFEST_LIMIT,'representation output policy differs')
    cap=policy['max_metadata_bytes'];reserve=4*cap+policy['max_manifest_bytes']
    require(reserve<=policy['max_attempt_bytes'] and index<policy['max_journal_events'],'representation output allowance exceeded')
    require(not attempt.exists() and not attempt.is_symlink(),'representation output attempt already reserved')
    require(not any(e['stage']=='representation_complete' for e in prefix),'representation already completed')
    pin=saved.ticket_lease(dictionary_ticket,owned,journal)
    artifact=registered(pin['inputs']['artifact']['input']);control=registered(closure_input)
    graph_output=registered(control['graph_admission']['output_input']);mcm_output=registered(control['graph_admission']['mcm_output_input'])
    require(index<artifact['max_journal_events'],'upstream journal allowance exceeded')
    closure.snapshot_events(metadata,directory,prefix,artifact_cap=artifact['max_manifest_bytes'],mcm_cap=mcm_output['max_metadata_bytes'],graph_cap=graph_output['max_metadata_bytes'])
    event_path=directory/f'event-{index:06d}.json';component=directory/f'checkpoint-{index:06d}/manifest.json'
    require(not event_path.exists() and not component.parent.exists(),'representation completion slot reserved')
    expected_owner={k:owner[k] for k in ('experiment','source_commit','producer','workflow_identity')}
    def lease():
        owned.lease();sources();metadata.lease();saved.ticket_lease(dictionary_ticket,owned,journal)
        require(journal.directory==directory and equal(journal.owner,expected_owner) and journal.parent is None and not journal.sealed
            and journal.identity==owner['workflow_identity'] and journal.required==sorted(route.descriptor['required_graphs'])
            and len(journal.records)==index+int(published) and equal(journal.records[:index],prefix),'representation publication journal changed')
        if date_receipt is not None:date_receipt.lease()
        if snapshot is not None:snapshot.check()
        if written:
            reader.inventory(attempt,set(written))
            for path,sha in written.items():metadata.read(path,sha,cap)
        if component_state is not None:
            signatures,files=component_state;reader.inventory(component.parent,files)
            for path,sig in signatures.items():
                with reader.opened(path,ad.root,sig):pass
    lease();require(attempt.resolve()==attempt and attempt.is_relative_to(ad.root),'representation output containment differs')
    durable_mkdir(attempt.parent);lease();attempt.mkdir(exist_ok=False);sync_directory(attempt.parent)
    require(attempt.stat().st_dev==ad.root.stat().st_dev,'representation output device differs')
    def write(name,value):
        raw=canonical_bytes(value);require(len(raw)<=cap,'representation metadata allowance exceeded')
        path=attempt/name
        with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        sync_directory(attempt);sha=file_hash(path);written[path]=sha;metadata.read(path,sha,cap)
        return {'path':str(path),'sha256':sha}
    try:
        start=write('start.json',{'schema_version':1,'status':'reserved','resumable':False,'owner':owner,'event_index':index,
            'closure_input':closure_input,'denominator_input':denominator_input,'output_input':output_input,
            'output_policy_sha256':ad.inputs[output_input]['sha256'],'reserved_encoded_bytes':reserve,
            'sources':{name:ad.experiment['source_files'][name] for name in SOURCES}})
        receipt=closure.admit(owned,journal,examples=examples,fold=fold,denominator_input=denominator_input,
            dictionary_ticket=dictionary_ticket,policy_input=closure_input)
        receipt.lease();record=thaw(receipt.record);payload=record['binding']
        date_receipt=closure.denominator.admit(owned,examples=examples,fold=fold,policy_input=denominator_input)
        directories=[];expected_files={}
        def pin_metadata(path,sha,cap):
            value=metadata.read(path,sha,cap)
            expected_files[path]={'sha256':sha,'bytes':metadata.snapshots[path][1][2]}
            return value
        def pin_component(ref,limits):
            path=Path(ref['path'])
            manifest=pin_metadata(path,ref['sha256'],limits['max_manifest_bytes'])
            directories.append(path.parent)
            for name,info in manifest['arrays'].items():
                require(Path(name).name==name,'snapshot member path differs')
                expected_files[path.parent/name]={'sha256':info['sha256'],'bytes':info['bytes']}
        dictionary_output=registered(pin['inputs']['dictionary_output']['input'])
        pin_component(pin['record']['component'],dictionary_output)
        pin_component(pin['record']['sample_provenance']['sample_artifact']['component'],artifact)
        for graph in record['graphs'].values():
            mcm=graph['feature_provenance']['mcm_provenance']
            for entry,proof_key,limits in ((graph,'graph_proof',graph_output),(mcm,'mcm_proof',mcm_output)):
                ref=entry[proof_key];path=Path(ref['path'])
                proof=pin_metadata(path,ref['sha256'],limits['max_metadata_bytes'])
                start_ref=proof['start'];start_path=path.parent/'start.json'
                require(start_ref['path']==str(start_path),'snapshot start reference differs')
                pin_metadata(start_path,start_ref['sha256'],limits['max_metadata_bytes'])
                directories.append(path.parent)
                pin_component(entry['component'],limits)
        snapshot=Snapshot(ad.root,directories,policy['max_snapshot_entries'],expected_files=expected_files)
        receipt.lease();snapshot.check()
        context={'workflow_identity':owner['workflow_identity'],'binding_hash':closure.cache_key(payload),'storage':'native_motif_representation_v1',
            'closure_hash':digest(canonical_bytes(record)),'output_input':output_input,'output_policy_sha256':ad.inputs[output_input]['sha256']}
        binding={'owner':expected_owner,'stage':'representation_complete','context':context}
        manifest=component_manifest(payload,binding);component_hash=digest(canonical_bytes(manifest));size=len(canonical_bytes(manifest))
        event={'stage':'representation_complete','context':context,'path':str(component.relative_to(directory)),'sha256':component_hash,'binding':binding}
        event_bytes=len(producer.lifecycle._encode(event))
        require(size<=policy['max_manifest_bytes'] and event_bytes<=min(cap,artifact['max_manifest_bytes']),'representation component/event allowance exceeded')
        snapshot_record=snapshot.record()
        proof_template={'schema_version':1,'status':'complete','resumable':False,'journal_sealed':False,'owner':owner,'start':start,
            'event_index':index,'closure':record,'predecessor_snapshot':snapshot_record,'output_input':output_input,
            'output_policy_sha256':ad.inputs[output_input]['sha256'],'encoded_artifact_bytes':size,'encoded_event_bytes':event_bytes,
            'event':{'path':str(event_path),'sha256':'0'*64},'component':{'path':str(component),'sha256':component_hash}}
        require(len(canonical_bytes(proof_template))<=cap,'representation completion proof allowance exceeded')
        # Explicit handoff: the old full-prefix closure lease is checked for the
        # final time here. It is not relaxed, called after append, or bypassed.
        receipt.lease();lease();del receipt
        journal('representation_complete',context,payload);published=True;lease()
        event_sha=file_hash(event_path)
        require(equal(metadata.read(event_path,event_sha,cap),event) and equal(journal.records[index],event),'representation event/content differs')
        actual,signatures,_,files=reader.inspect_component(component,component_hash,binding,ad.root,policy['max_manifest_bytes'],policy['max_manifest_bytes'],1)
        require(equal(actual,manifest) and set(signatures)=={component} and signatures[component][2]==size,'representation component content/size differs')
        component_state=(signatures,files)
        # Content identity, not stat clocks, protects the new scalar manifest
        # during completion-proof publication and the final lease.
        metadata.read(component,component_hash,policy['max_manifest_bytes'])
        proof=write('complete.json',proof_template|{'event':{'path':str(event_path),'sha256':event_sha}})
        lease();return proof
    except BaseException as error:
        try:write('failed.json',{'schema_version':1,'status':'failed','resumable':False,'owner':owner,'reason_type':type(error).__name__,'reason':str(error)[:500]})
        except BaseException:pass
        raise
