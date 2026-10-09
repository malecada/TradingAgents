"""Genuine grouped typed operations; original per-batch route is unchanged."""
from pathlib import Path
import hashlib,json,os,stat
from . import registered_offload as original,typed_payload_operations as typed
from . import grouped_offload_semantics as semantic,preservation
require=semantic.require;KIND=original.KIND

def preserve_and_retire(owner,stage,*,journal,items,work):
    budget=original._selected(owner,stage);items=semantic.roster(items);work=Path(work)
    require(hasattr(typed._Operation,'retire_batched_group'),'grouped retirement source not selected')
    artifact=owner.bound._run.admission.root/'research_artifacts'
    require(work.is_absolute() and work.parent.resolve()==work.parent and work.is_relative_to(artifact),'actual owned group scratch required')
    require(journal.root==stage.root/'matching','actual stage group namespace')
    coverage=semantic.current(journal,items);rows=semantic.source_rows(journal,items);bound=semantic.archive_bound(rows)
    require(bound<=budget['chunk_bytes'],'group exceeds actual selected part allowance')
    work.mkdir(exist_ok=False);manifest=preservation.build_bundle(rows,work/'bundle.tar',allowed_roots=[journal.root],start_index=3*items[0][0])
    require(manifest['archive_bytes']==bound,'group archive extent changed');typed._write(work/'manifest.json',manifest)
    binding=semantic.binding(journal,items,manifest)
    with typed.operation(owner,stage,kind=KIND,binding=binding,payload_bytes=bound,chunk_count=1) as op:
        receipt=op.preserve(work/'bundle.tar',expected_sha256=manifest['archive_sha256'],expected_bytes=bound,index=0,attempt=work/'preserve')
        op.retire_batched_group(receipt,manifest=manifest,journal=journal,items=items,attempt=work/'recover',semantic_root=work/'semantic')
        op.retire_source(work/'bundle.tar',expected_sha256=manifest['archive_sha256'],expected_bytes=bound)
    result={'schema_version':1,'format':'registered-grouped-offload-v1',**coverage,'binding':binding,'manifest':manifest,'history':op.history(),'receipt':receipt,'retired_files':3*len(items),'resume_supported':False}
    require(len(semantic.raw(result))<=131072,'group offload record extent');typed._write(work/'offload.json',result);return result

def fresh_recover(owner,stage,*,record,journal,work,consume=None):
    original._selected(owner,stage);require(record['format']=='registered-grouped-offload-v1' and record['resume_supported'] is False,'explicit grouped record required')
    items=semantic.from_binding(record['binding']);manifest=record['manifest'];require(semantic.binding(journal,items,manifest)==record['binding'],'group historical binding differs')
    parts=list(typed.iter_history_parts(record['history'],binding=record['binding'],kind=KIND));require(len(parts)==1 and parts[0]['receipt']==record['receipt'],'actual group preservation proof differs')
    work=Path(work);work.mkdir(exist_ok=False)
    with typed.operation(owner,stage,kind=KIND,binding=record['binding'],payload_bytes=0,chunk_count=0) as op:
        data=op.recover(record['receipt'],attempt=work/'recover')
        evidence=semantic.recover(data,manifest,journal,items,work/'semantic',consume=consume)
        require(evidence['start']==record['start'] and evidence['stop']==record['stop'],'group fresh coverage differs')
        semantic.dispose_recovery(work/'semantic',manifest,items)
    result={'schema_version':1,'format':'registered-grouped-fresh-recovery-v1','original_history':record['history'],'history':op.history(),'source_binding':record['binding'],'start':evidence['start'],'stop':evidence['stop'],'first_batch':items[0][0],'batches':len(items)}
    typed._write(work/'complete.json',result);return result

def finalize(owner,stage,*,records,group_count,batch_count,journal,work,spool_fd):
    """Fresh full recovery with the unchanged float64 -> float32 spool comparison."""
    original._selected(owner,stage);require(type(group_count) is int and type(batch_count) is int and 0<group_count<=batch_count<=stage.pairs ,'finite grouped final coverage required')
    import numpy as np
    spool=stage.root/'stream/scores.f32';pin=semantic.batched_journal.sig(os.fstat(spool_fd));st=os.fstat(spool_fd)
    require(stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and st.st_size==4*stage.pairs and pin==semantic.batched_journal.sig(spool.lstat()),'actual original spool identity/extent')
    def consume(batch,rows):
        with np.errstate(over='raise',invalid='raise'):
            expected=np.asarray([row[2] for row in rows],dtype='<f8').astype('<f4').tobytes()
        require(os.pread(spool_fd,len(expected),4*rows[0][0])==expected and semantic.batched_journal.sig(os.fstat(spool_fd))==pin==semantic.batched_journal.sig(spool.lstat()),'fresh grouped records differ from original spool')
    work=Path(work);work.mkdir(exist_ok=False);iterator=iter(records);aggregate=hashlib.sha256();cursor=next_batch=0
    for group in range(group_count):
        try:path,expected=next(iterator)
        except StopIteration as error:raise ValueError('short grouped offload roster') from error
        body=typed._read(path);require(semantic.sha(body)==expected,'anchored grouped record changed');record=json.loads(body)
        require(record['first_batch']==next_batch and record['start']==cursor,'group order/coverage differs')
        fresh=fresh_recover(owner,stage,record=record,journal=journal,work=work/f'{group:08d}',consume=consume)
        require(typed._read(path)==body,'group original record changed during recovery')
        aggregate.update(bytes.fromhex(expected));aggregate.update(bytes.fromhex(semantic.sha(semantic.raw(fresh))));cursor=fresh['stop'];next_batch+=fresh['batches']
    sentinel=object();require(next(iterator,sentinel) is sentinel and cursor==stage.pairs and next_batch==batch_count,'grouped final denominator differs')
    require(semantic.batched_journal.sig(os.fstat(spool_fd))==pin==semantic.batched_journal.sig(spool.lstat()),'final grouped spool changed')
    result={'schema_version':1,'format':'registered-grouped-final-coverage-v1','owner':owner.identity,'stage':stage.name,'stage_intent_sha256':stage.intent_sha256,'cells':cursor,'batches':next_batch,'groups':group_count,'original_and_fresh_history_aggregate_sha256':aggregate.hexdigest(),'historical_not_future_availability':True,'resume_supported':False}
    typed._write(work/'accepted-coverage.json',result);return result
