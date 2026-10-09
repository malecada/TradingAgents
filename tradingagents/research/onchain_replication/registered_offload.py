"""Actual typed View preserve/recover/retire calls; refuses unselected schema2.

No alternate transport injection or synthetic Owner construction is exposed.
"""
from pathlib import Path
from . import typed_payload_policy as policy,typed_payload_operations as typed
from . import batched_offload_semantics as semantic,preservation
require=policy.require
KIND='mcm-batched-bundle-v3'

def _selected(owner,stage):
    require(owner is not None and stage is not None,'batched transport not genuinely selected')
    record=typed.selected(owner)
    require(record is not None,'batched transport not genuinely selected')
    require(record['policy']['schema_version']==2 and record['policy']['format']=='typed-payload-budget-v2','batched typed schema2 not selected')
    require(getattr(policy,'BATCHED_KIND',None)==KIND and hasattr(typed._Operation,'retire_batched_sources'),'batched source extensions not installed/selected')
    selected=policy.validate(record['policy'])
    require(stage.kind=='mcm' and stage.name.startswith('mcm-'),'actual MCM stage required')
    graph=stage.name[4:];require(graph in selected['graphs'] and KIND in selected['graphs'][graph]['kinds'],'batched graph/kind not selected')
    return selected['graphs'][graph]['kinds'][KIND]

def preserve_and_retire(owner,stage,*,journal,batch,tokens,work):
    """Generated NEW journal files only. Success includes actual deletion code.

    Caller must anchor returned history/manifest/binding in stage completion.
    Old receipts/currentness booleans cannot authorize this operation.
    """
    budget=_selected(owner,stage);work=Path(work)
    artifact=owner.bound._run.admission.root/'research_artifacts'
    require(work.is_absolute() and work.parent.resolve()==work.parent and work.is_relative_to(artifact),'actual owned scratch path required')
    rows=semantic.current(journal,batch,tokens)
    require(journal.root.is_relative_to(stage.root) and journal.root.name=='matching','only selected stage generated journal sources')
    source=[]
    for index,suffix in enumerate(semantic.SUFFIXES):
        dev,ino,size,digest=semantic.TOKEN.unpack_from(tokens,index*semantic.TOKEN.size)
        path=journal.root/(f'{batch:08d}'+suffix);s=path.stat()
        source.append({'source_path':str(path),'resolved_path':str(path),'bytes':size,'mtime_ns':s.st_mtime_ns,'expected_sha256':digest.hex()})
    bound=((sum(512+((x['bytes']+511)//512)*512 for x in source)+1024+10239)//10240)*10240
    require(bound<=budget['chunk_bytes'],'selected archive part allowance exceeded')
    work.mkdir(exist_ok=False)
    manifest=preservation.build_bundle(source,work/'bundle.tar',allowed_roots=[journal.root],start_index=batch*3)
    require(manifest['archive_bytes']==bound,'archive extent differs')
    typed._write(work/'manifest.json',manifest)
    binding=semantic.binding(journal,batch,tokens,manifest)
    with typed.operation(owner,stage,kind=KIND,binding=binding,payload_bytes=bound,chunk_count=1) as op:
        receipt=op.preserve(work/'bundle.tar',expected_sha256=manifest['archive_sha256'],expected_bytes=bound,index=0,attempt=work/'preserve')
        op.retire_batched_sources(receipt,manifest=manifest,journal=journal,batch=batch,tokens=tokens,attempt=work/'recover',semantic_root=work/'semantic')
        op.retire_source(work/'bundle.tar',expected_sha256=manifest['archive_sha256'],expected_bytes=bound)
    result={'schema_version':1,'format':'registered-batched-offload-v1','batch':batch,'start':rows[0][0],'stop':rows[-1][0]+1,'binding':binding,'manifest':manifest,'history':op.history(),'receipt':receipt,'retired_files':3}
    typed._write(work/'offload.json',result);return result

def _consume_recovered(journal,evidence,batch,directory,consume):
    # Actual recovered files, exact same registered journal class. This
    # is a read-only handle; no journal birth or authority is invented.
    reader=object.__new__(type(journal));reader.root=directory/'tree'
    reader.pin=tuple(evidence['root_pin']);reader.batch_cells=4096
    reader.max_cells=2**63;reader.max_body=1024**2
    import os
    reader.fd=os.open(reader.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        rows=reader._read_complete(batch)
        consume(batch,rows)
        require(rows==reader._read_complete(batch),'recovered records changed during consumer')
        reader._root()
    finally:os.close(reader.fd)

def fresh_recover(owner,stage,*,record,journal,work,consume=None):
    """Caller must anchor exact record hash; fresh transport retrieval always runs."""
    _selected(owner,stage);work=Path(work)
    require(record['format']=='registered-batched-offload-v1','batched offload record required')
    batch=record['batch'];tokens=bytes.fromhex(record['binding']['source_tokens']);manifest=record['manifest']
    require(semantic.binding(journal,batch,tokens,manifest)==record['binding'],'historical source binding differs')
    parts=list(typed.iter_history_parts(record['history'],binding=record['binding'],kind=KIND))
    require(len(parts)==1 and parts[0]['receipt']==record['receipt'],'actual typed preserved part differs')
    work.mkdir(exist_ok=False)
    with typed.operation(owner,stage,kind=KIND,binding=record['binding'],payload_bytes=0,chunk_count=0) as op:
        data=op.recover(record['receipt'],attempt=work/'recover')
        evidence=semantic.recover(data,manifest,journal,batch,tokens,work/'semantic')
        require(evidence['start']==record['start'] and evidence['stop']==record['stop'],'fresh recovered coverage differs')
        if consume is not None:_consume_recovered(journal,evidence,batch,work/'semantic',consume)
        semantic.dispose_recovery(work/'semantic',manifest,batch,tokens)
    result={'schema_version':1,'format':'registered-batched-fresh-recovery-v1','original_history':record['history'],'history':op.history(),'source_binding':record['binding'],'start':evidence['start'],'stop':evidence['stop']}
    typed._write(work/'complete.json',result);return result

def finalize(owner,stage,*,records,batch_count,journal,work,consume=None):
    """Fresh full sweep of externally anchored (record_path, SHA256) entries."""
    import hashlib
    _selected(owner,stage);require(type(batch_count) is int and 0<batch_count<=stage.pairs,'finite final batch count required')
    work=Path(work);work.mkdir(exist_ok=False);iterator=iter(records);aggregate=hashlib.sha256();cursor=0
    for batch in range(batch_count):
        try:path,expected=next(iterator)
        except StopIteration as error:raise ValueError('short final offload roster') from error
        encoded=typed._read(path)
        require(policy.sha(encoded)==expected,'anchored offload record differs')
        import json
        record=json.loads(encoded)
        require(record['batch']==batch and record['start']==cursor,'final offload coverage order differs')
        fresh=fresh_recover(owner,stage,record=record,journal=journal,work=work/f'{batch:08d}',consume=consume)
        require(typed._read(path)==encoded,'offload record changed during final recovery')
        aggregate.update(bytes.fromhex(expected));aggregate.update(bytes.fromhex(policy.sha(policy.raw(fresh))));cursor=fresh['stop']
    sentinel=object();require(next(iterator,sentinel) is sentinel and cursor==stage.pairs,'extra/missing final cells')
    result={'schema_version':1,'format':'registered-batched-final-coverage-v1','owner':owner.identity,'stage':stage.name,'stage_intent_sha256':stage.intent_sha256,'cells':cursor,'batches':batch_count,'original_and_fresh_history_aggregate_sha256':aggregate.hexdigest(),'historical_not_future_availability':True}
    typed._write(work/'accepted-coverage.json',result);return result
