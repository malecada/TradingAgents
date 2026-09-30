"""Registered failed-chain precheck; no allocation or numerical continuation.

This joins actual ResearchRun admission with the accepted death observer.
Numerical source compatibility, current worker lease, pair workload membership,
output integrity and orphan reconciliation remain separate mandatory checks.
"""
import importlib.util
import json
import os
from pathlib import Path
import re
import stat

from tradingagents.research.lifecycle import ResearchRun
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, file_hash

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SELF=str((HERE/'ancestry.py').relative_to(ROOT))
DEATH=str((HERE.parent/'pair-death-2026-09-30/death.py').relative_to(ROOT))
_spec=importlib.util.spec_from_file_location('accepted_pair_death',ROOT/DEATH)
death=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(death)
MAX_BYTES=2*1024**2
MAX_ANCESTORS=8


def require(value,message):
    if not value:raise ValueError(message)


def equal(a,b):return canonical_bytes(a)==canonical_bytes(b)


def _read(root,path,snapshots,expected=None):
    require(path.is_absolute() and path.is_relative_to(root) and path.resolve()==path,'metadata path containment differs')
    before=path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_dev==root.stat().st_dev
            and before.st_size<=MAX_BYTES,'metadata type/extent differs')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        require(death.signature(os.fstat(fd))==death.signature(before),'metadata changed before read')
        with os.fdopen(fd,'rb',closefd=False) as stream:raw=stream.read(MAX_BYTES+1)
        require(len(raw)<=MAX_BYTES and death.signature(os.fstat(fd))==death.signature(before)
                and death.signature(path.stat())==death.signature(before),'metadata changed during read')
    finally:os.close(fd)
    sha=digest(raw)
    require(expected is None or sha==expected,'metadata hash differs')
    require(path not in snapshots or snapshots[path]==death.signature(before),'metadata changed between reads')
    snapshots[path]=death.signature(before)
    return json.loads(raw),sha


def verify(run,*,representation,plan_input,producer,policy_input,continuation_input,death_input):
    require(isinstance(run,ResearchRun),'actual admitted ResearchRun required')
    run._active();run._check_source()
    ad=run.admission;root=ad.root;snapshots={}
    for name in (SELF,DEATH):
        require(name in ad.experiment['source_files'] and file_hash(ROOT/name)==ad.experiment['source_files'][name],
                'executed ancestry/death source is not admitted')
    def read(path,expected=None):return _read(root,path,snapshots,expected)[0]
    def inp(name):
        require(isinstance(name,str) and name in ad.inputs,'registered compact input required')
        info=ad.inputs[name]
        return read(root/info['path'],info['sha256'])
    execution=inp('execution_job')
    require(type(execution.get('schema_version')) is int and execution['schema_version']==1
            and execution.get('kind')=='fit','fit execution route required')
    selected=execution.get('payload',{}).get('representation_jobs',{}).get(representation)
    route={'operation':'produce','plan_input':plan_input,'producer':producer,'pair_checkpoint_input':policy_input,
           'continuation_input':continuation_input,'death_input':death_input}
    require(isinstance(selected,dict) and all(k in selected and equal(selected[k],v) for k,v in route.items()),
            'selected successor producer route differs')
    plan=inp(plan_input)
    require(type(plan.get('schema_version')) is int and plan['schema_version']==2,'explicit version2 plan required')
    item=plan.get('producers',{}).get(producer)
    require(isinstance(item,dict) and all(k in item and equal(item[k],route[k]) for k in
            ('pair_checkpoint_input','continuation_input','death_input')),'plan successor route differs')
    descriptor=item.get('descriptor')
    require(isinstance(descriptor,dict) and equal(descriptor,selected.get('descriptor'))
            and descriptor.get('arm')=='proposed','registered motif descriptor differs')
    required=descriptor.get('required_graphs')
    require(isinstance(required,list) and required and all(isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h) for h in required)
            and sorted(set(required))==required,'required graph set differs')
    require(policy_input in ad.inputs,'registered pair policy required')
    # Policy numerical/backend/schema admission belongs to the owner binding.
    inp(policy_input)
    identity=cache_key(descriptor);work=root/'research_artifacts/onchain_representations'/identity
    require(work.is_dir() and work.resolve()==work and work.stat().st_dev==root.stat().st_dev,'workflow root differs')
    parent_id=ad.experiment['parent']
    require(isinstance(parent_id,str) and parent_id!=ad.experiment_id,'registered failed parent required')
    info=ad.inputs.get(continuation_input)
    expected_path=work/parent_id/'failed.json'
    require(isinstance(info,dict) and root/info['path']==expected_path,'exact immediate continuation input required')
    document=inp(death_input)
    require(isinstance(document,dict) and set(document)=={'schema_version','ancestors'}
            and type(document['schema_version']) is int and document['schema_version']==1,'death ancestry schema differs')
    entries=document['ancestors']
    require(isinstance(entries,list) and 1<=len(entries)<=MAX_ANCESTORS,'bounded nonempty death ancestry required')
    proofs={}
    for entry in entries:
        require(isinstance(entry,dict) and set(entry)=={'experiment','proof'},'death ancestry entry differs')
        name=entry['experiment']
        require(isinstance(name,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,127}',name)
                and name not in proofs and name!=ad.experiment_id,'duplicate/invalid ancestor identity')
        proofs[name]=entry['proof']
    expected_dirs={work/name for name in proofs}
    def directory_inventory():
        require(set(work.iterdir())==expected_dirs,'omitted, foreign or current representation owner exists')
        for directory in expected_dirs:
            require(directory.is_dir() and directory.resolve()==directory and directory.stat().st_dev==root.stat().st_dev,
                    'ancestor directory containment differs')
            complete=directory/'complete.json'
            require(not complete.exists() and not complete.is_symlink(),'complete representation requires reuse')
            terminal=root/'research_runs'/directory.name/'complete.json'
            require(not terminal.exists() and not terminal.is_symlink(),'completed lifecycle ancestor refused')
            final=root/death.PREFIX/directory.name/'guard/final.json'
            require(not final.is_symlink() and final.exists()==('final' in proofs[directory.name]),
                    'ancestor final guard inventory changed')
    directory_inventory()
    current=expected_path;expected=info['sha256'];expected_owner=None;seen=set();ancestors=[]
    while current is not None:
        name=current.parent.name
        require(len(seen)<MAX_ANCESTORS and name in proofs and name not in seen
                and current==work/name/'failed.json','ancestry path, depth or cycle differs')
        seen.add(name)
        manifest=read(current,expected);owner=manifest.get('owner')
        require(isinstance(owner,dict) and set(owner)=={'experiment','source_commit','producer','workflow_identity'}
                and owner['experiment']==name and owner['producer']==producer and owner['workflow_identity']==identity,
                'ancestor representation owner differs')
        require(expected_owner is None or equal(owner,expected_owner),'parent reference owner differs')
        require(type(manifest.get('schema_version')) is int and manifest['schema_version']==1
                and manifest.get('status')=='failed' and equal(manifest.get('required_graphs'),required)
                and manifest.get('workflow_identity') in (None,identity),'ancestor manifest differs')
        events=manifest.get('events')
        require(isinstance(events,list) and all(isinstance(e,dict) and e.get('stage')!='representation_complete' for e in events),
                'completed representation cannot be continued')
        require(manifest['workflow_identity'] is not None or not events,'unidentified journal contains numerical events')
        require(equal(read(current.parent/'owner.json'),owner),'retained representation owner differs')
        start=read(current.parent/'start.json')
        require(type(start.get('schema_version')) is int and start['schema_version']==1 and equal(start.get('owner'),owner)
                and equal(start.get('required_graphs'),required) and equal(start.get('parent'),manifest.get('parent')),
                'ancestor journal start differs')
        claim=read(root/'research_runs'/name/'claim.json')
        require(claim.get('experiment_id')==name and claim.get('source')==owner['source_commit']
                and claim.get('program_id')==ad.spec['program_id']
                and equal(claim.get('experiment'),ad.spec['experiments'].get(name)), 'historical lifecycle claim differs')
        rep_claim=read(current.parent/'claim.json')
        required_claim={'owner':owner,'descriptor':descriptor,'plan_input':plan_input,'binding_output':item.get('binding_output'),
                        'registration_sha256':claim['registration_sha256'],'pair_checkpoint_input':policy_input,
                        'pair_checkpoint_policy_sha256':ad.inputs[policy_input]['sha256']}
        require(all(k in rep_claim and equal(rep_claim[k],v) for k,v in required_claim.items()),'historical representation claim differs')
        require(policy_input in claim['inputs'] and claim['inputs'][policy_input]['sha256']==ad.inputs[policy_input]['sha256'],
                'ancestor pair policy differs')
        # A hash-valid journal cannot erase an ancestor that its immutable
        # historical producer contract required, even if a directory is missing.
        def historical_input(input_name):
            require(isinstance(input_name,str) and input_name in claim['inputs'],'historical registered input required')
            binding=claim['inputs'][input_name]
            return read(root/binding['path'],binding['sha256'])
        prior_execution=historical_input('execution_job');prior_plan=historical_input(plan_input)
        require(type(prior_execution.get('schema_version')) is int and prior_execution['schema_version']==1
                and prior_execution.get('kind')=='fit' and type(prior_plan.get('schema_version')) is int
                and prior_plan['schema_version']==2,'historical producer schemas differ')
        prior_selected=prior_execution.get('payload',{}).get('representation_jobs',{}).get(representation)
        prior_item=prior_plan.get('producers',{}).get(producer)
        require(isinstance(prior_selected,dict) and isinstance(prior_item,dict),'historical producer missing')
        for key,value in {'operation':'produce','plan_input':plan_input,'producer':producer,
                          'pair_checkpoint_input':policy_input,'descriptor':descriptor}.items():
            require(key in prior_selected and equal(prior_selected[key],value),'historical selected producer differs')
        for key in ('descriptor','pair_checkpoint_input','continuation_input','death_input'):
            require(key in prior_item and key in prior_selected and equal(prior_item[key],prior_selected[key]),
                    'historical plan route differs')
        require(prior_item.get('binding_output')==item.get('binding_output')
                and prior_item.get('journal_output')==item.get('journal_output'),'historical output route differs')
        parent=manifest.get('parent');prior_continuation=prior_item['continuation_input']
        if prior_continuation is None:
            require(parent is None and prior_item['death_input'] is None,'first producer has unexplained parent')
        else:
            require(isinstance(parent,dict) and set(parent)=={'path','sha256','owner'},'registered historical parent omitted')
            parent_name=claim['experiment']['parent']
            require(isinstance(parent_name,str) and parent_name in proofs and parent_name not in seen
                    and len(seen)<MAX_ANCESTORS,'historical parent membership/depth differs')
            pinned=claim['inputs'].get(prior_continuation)
            fixed=work/parent_name/'failed.json'
            require(isinstance(pinned,dict) and root/pinned['path']==fixed and parent['path']==str(fixed)
                    and parent['sha256']==pinned['sha256'],'historical continuation path/hash differs')
            require(isinstance(prior_item['death_input'],str) and prior_item['death_input'] in claim['inputs'],
                    'historical death route missing')
        proof=proofs[name]
        observation=death.verify(root,{'experiment':name,'source_commit':owner['source_commit']},proof)
        # Capture every observed metadata signature for a final whole-chain check.
        for reference in proof.values():read(root/reference['path'],reference['sha256'])
        require(observation['claim_sha256']==file_hash(root/'research_runs'/name/'claim.json'),'observed ancestor claim differs')
        ancestors.append({'experiment':name,'source_commit':owner['source_commit'],
                          'manifest_sha256':expected,'claim_sha256':observation['claim_sha256'],
                          'observer_sha256':observation['observer_sha256']})
        if parent is None:
            require(start.get('workflow_identity') is None,'first journal inherited unexplained workflow')
            current=None
        else:
            require(isinstance(parent,dict) and set(parent)=={'path','sha256','owner'},'exact journal parent reference required')
            current=Path(parent['path']);expected=parent['sha256'];expected_owner=parent['owner']
            require(claim['experiment']['parent']==current.parent.name,'lifecycle and representation parent differ')
            parent_manifest=read(current,expected)
            require(equal(start.get('workflow_identity'),parent_manifest.get('workflow_identity')),'inherited workflow differs')
    require(seen==set(proofs) and [x['experiment'] for x in ancestors]==[x['experiment'] for x in entries],
            'death evidence must cover exact ordered ancestry')
    run._active();run._check_source()
    for ancestor in ancestors:
        death.verify(root,{'experiment':ancestor['experiment'],'source_commit':ancestor['source_commit']},proofs[ancestor['experiment']])
    directory_inventory()
    for path,before in snapshots.items():
        require(path.resolve()==path and death.signature(path.stat())==before,'ancestry evidence changed at final observation')
    return {'schema_version':1,'experiment':ad.experiment_id,'source_commit':ad.source,
            'claim_sha256':run._claim_sha256,'workflow_identity':identity,'ancestors':ancestors,
            'continuation_admitted':False,'arrays_read':False,'numerical_compatibility_verified':False,
            'outputs_verified':False,'qualification':'Registered failed-chain and death precheck only; current lease, numerical compatibility, workload, checkpoint integrity and orphan recovery remain required.'}
