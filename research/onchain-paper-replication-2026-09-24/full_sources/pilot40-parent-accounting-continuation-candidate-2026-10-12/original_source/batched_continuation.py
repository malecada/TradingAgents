"""Opt-in durable complete-batch import; admission remains genuine caller-owned.

No directory scan guesses a prefix. Every recovered body is a registered input
and the caller must validate the reviewed parent/allowance/recovery authority.
"""
from dataclasses import dataclass, fields
from weakref import WeakKeyDictionary
import hashlib
import json
import os
import struct
from .batched_journal import HEADER, RECORD, MAGIC, STATUS, body, digest, require
from . import batched_numeric_execution as numeric_format

POLICY = 'completed-prefix-v1'
_VERIFIED = WeakKeyDictionary()
_READERS = WeakKeyDictionary()
_USED = WeakKeyDictionary()
MAX_MANIFEST_BYTES = 32*1024**2
SUFFIXES = ('.pending.json', '.records.bin', '.complete.json')

@dataclass(frozen=True, eq=False)
class CompletedBatch:
    score_bodies: tuple
    origins: bytes
    summary: bytes
    commit: bytes
    records: tuple
    legacy: bool = False

@dataclass(frozen=True, eq=False)
class CompletedPrefix:
    parent_experiment: str
    successor_experiment: str
    workflow_identity: str
    graph_hash: str
    next_ordinal: int
    batches: tuple
    origin_sha256: str
    score_sha256: str
    numerical_contract_sha256: str
    spent_counters: tuple
    manifest_sha256: str
    descriptors: tuple = ()
    verification_counters: tuple = ()


def _json(raw):
    value = json.loads(raw)
    require(body(value) == raw, 'continuation canonical JSON required')
    return value


def commit_batch(journal, numeric, contract_sha256):
    """Last durable publication, after score + numeric closure, before retirement."""
    require(type(contract_sha256) is str and len(contract_sha256)==64 and all(c in '0123456789abcdef' for c in contract_sha256), 'continuation contract digest required')
    index = journal.batch - 1
    require(index >= 0 and numeric.batch == journal.batch and numeric.ordinal == journal.cells and not numeric.buffer, 'score/numeric complete boundary differs')
    require(not numeric.poisoned and not numeric.closed, 'numeric continuation unavailable')
    journal.read_complete(index)
    blobs = tuple(journal._read(f'{index:08d}'+suffix)[0] for suffix in SUFFIXES)
    summary, _ = numeric_format.read_file(numeric.batches_fd, f'{index:012d}.json', numeric_format.SUMMARY_LIMIT)
    s = _json(summary)
    numeric._origin_current()
    origins = os.pread(numeric.origins_fd, 9*(s['stop']-s['start']), 9*s['start'])
    require(digest(origins)==s['origin_sha256'] and s['stop']==journal.cells, 'continuation origin join differs')
    prior=getattr(numeric,'imported_costs',{})
    value = {'policy':POLICY, 'batch':index, 'start':s['start'], 'stop':s['stop'],
             'contract_sha256':contract_sha256, 'cost_epoch_start':getattr(numeric,'continuation',{}).get('imported_cells',0), 'score_sha256':[digest(b) for b in blobs],
             'origin_sha256':digest(origins), 'summary_sha256':digest(summary),
             'counters':s['counters'], 'checkpoint_attempts':numeric.memo.executor.checkpoints+prior.get('checkpoint_attempts',0),
             'checkpoint_reserved_bytes':numeric.memo.executor.reserved_bytes+prior.get('checkpoint_reserved_bytes',0),
             'operation_counters':{k:getattr(numeric.memo.executor,k)+prior.get(k,0) for k in ('completed_operations','advance_calls','abandoned_call_operation_limit')}}
    raw = body(value)
    name = f'{index:08d}.prefix.json'
    journal._write(name, raw, journal.max_body)
    return raw


def _decode_batch(blobs, index, start, batch_cells, cells, contract, *, legacy=False):
    require(type(blobs) is tuple and len(blobs)==6 and all(type(b) is bytes for b in blobs), 'six recovered bodies required')
    pending, payload, complete, origins, summary, commit = blobs
    p, m, s, c = map(_json, (pending,complete,summary,commit))
    stop = min(start+batch_cells,cells)
    require(p == {'schema':3,'kind':'engineering_pending','start':start,'stop':stop,'workload_sha256':contract['descriptor_sha256'],'disposition':'attempted_unknown_without_complete'}, 'prefix pending/order/config differs')
    require(len(payload)==HEADER.size+(stop-start)*RECORD.size, 'prefix score extent differs')
    require(m == {'schema':3,'kind':'engineering_complete','pending_sha256':digest(pending),'payload_sha256':digest(payload),'payload_bytes':len(payload),'record_bytes':RECORD.size,'purposes_sha256':m.get('purposes_sha256')}, 'prefix score commitment differs')
    require(HEADER.unpack_from(payload)==(MAGIC,RECORD.size,start,stop,bytes.fromhex(digest(pending)),bytes.fromhex(m['purposes_sha256'])), 'prefix score header differs')
    records=tuple(RECORD.iter_unpack(payload[HEADER.size:])); aggregate=hashlib.sha256()
    import math
    for ordinal,row in enumerate(records,start):
        require(row[0]==ordinal and math.isfinite(row[2]) and 0<=row[2]<=1 and row[4] in STATUS.values(), 'prefix score record differs')
        aggregate.update(row[1])
    require(aggregate.hexdigest()==m['purposes_sha256'], 'prefix purpose order differs')
    require(len(origins)==9*(stop-start) and s['format']==numeric_format.FORMAT and s['batch']==index and s['start']==start and s['stop']==stop and s['origin_sha256']==digest(origins), 'prefix numeric range/hash differs')
    computed=reused=0
    for ordinal,(mode,origin) in enumerate(numeric_format.RECORD.iter_unpack(origins),start):
        require((mode==0 and origin==ordinal) or (mode==1 and origin<ordinal), 'prefix origin order differs')
        computed+=mode==0;reused+=mode==1
    require(s['computed']==computed and s['reused']==reused and s['old_per_occurrence_execution_credit'] is False, 'prefix numeric counts differ')
    require(type(s['elapsed_seconds']) is float and math.isfinite(s['elapsed_seconds']) and s['elapsed_seconds']>=0
            and s['receipt_framing']=='u64be-length/canonical-json-newline' and type(s['receipt_sha256']) is str
            and len(s['receipt_sha256'])==64 and all(x in '0123456789abcdef' for x in s['receipt_sha256']), 'prefix receipt/timing differs')
    if 'phase_totals' in s:numeric_format.validate_phase_totals(s['phase_totals'])
    require(type(s['counters']) is dict and all(type(k) is str and type(v) is int and 0<=v<2**127 for k,v in s['counters'].items()), 'prefix counters invalid')
    expected={'policy':POLICY,'batch':index,'start':start,'stop':stop,'contract_sha256':contract.get('numerical_contract_sha256',digest(body(contract))), 'cost_epoch_start':c.get('cost_epoch_start'),'score_sha256':[digest(b) for b in blobs[:3]],'origin_sha256':digest(origins),'summary_sha256':digest(summary),'counters':s['counters'], 'checkpoint_attempts':c.get('checkpoint_attempts'),'checkpoint_reserved_bytes':c.get('checkpoint_reserved_bytes'),'operation_counters':c.get('operation_counters')}
    require(type(c.get('cost_epoch_start')) is int and 0<=c['cost_epoch_start']<=start, 'prefix cost epoch differs')
    if legacy:
        expected['policy']='legacy-recovered-prefix-v1'
    require(c==expected and all(type(c[k]) is int and 0<=c[k]<2**127 for k in ('checkpoint_attempts','checkpoint_reserved_bytes')), 'prefix durable commit differs')
    require(type(c['operation_counters']) is dict and set(c['operation_counters'])=={'completed_operations','advance_calls','abandoned_call_operation_limit'} and all(type(v) is int and 0<=v<2**127 for v in c['operation_counters'].values()), 'prefix operation counters unavailable')
    expected_batch=(blobs[:3],origins,summary,commit,records,legacy)
    result=CompletedBatch(*expected_batch)
    require(type(result) is CompletedBatch and tuple(getattr(result,f.name) for f in fields(result))==expected_batch,'batch constructor changed authenticated fields')
    return result


def _authority(run, m):
    """Admitted parent, immutable terminal evidence and two recovered inventories."""
    ad=run.admission
    run._active();run._check_source()
    require(ad.experiment['parent']==m['parent_experiment'] and ad.effective_attempt_budget>0,
            'registered continuation parent/allowance differs')
    parent=ad.root/'research_runs'/m['parent_experiment']
    require(not os.path.lexists(parent/'complete.json'), 'COMPLETE parent refused')
    def registered(ref):
        require(type(ref) is dict and set(ref)=={'role','sha256'}, 'authority registered reference required')
        raw=_bounded_input(run,ref['role'],max_bytes=MAX_MANIFEST_BYTES)
        require(len(raw)<=MAX_MANIFEST_BYTES and digest(raw)==ref['sha256'], 'authority body differs')
        return raw
    claim_raw=registered(m['parent_claim']);failed_raw=registered(m['parent_failed'])
    claim=json.loads(claim_raw);failed=json.loads(failed_raw)
    require(ad.root/ad.inputs[m['parent_claim']['role']]['path']==parent/'claim.json'
            and ad.root/ad.inputs[m['parent_failed']['role']]['path']==parent/'failed.json',
            'registered original parent terminal paths required')
    require(failed['status']=='failed' and failed['experiment_id']==m['parent_experiment']
            and failed['claim_sha256']==digest(claim_raw) and claim['experiment_id']==m['parent_experiment']
            and claim['program_id']==ad.spec['program_id'] and claim['family']['mechanism_id']==ad.family['mechanism_id'],
            'FAILED parent claim/family differs')
    review=json.loads(registered(m['review']))
    require(review['policy']==POLICY and review['decision']=='accepted'
            and review['parent_claim_sha256']==digest(claim_raw) and review['parent_failed_sha256']==digest(failed_raw)
            and review['successor_experiment']==ad.experiment_id
            and review['contract_sha256']==digest(body(m['contract']))
            and review['batches_sha256']==digest(body(m['batches']))
            and review['descriptors_sha256']==digest(body(m.get('descriptors',{})))
            and review['spent_counters_sha256']==digest(body(m['spent_counters'])), 'reviewed continuation joins differ')
    recovered={}
    for kind in ('score_offload','numeric_origin'):
        receipt_raw=registered(m['recoveries'][kind])
        receipt=json.loads(receipt_raw)
        require(review['recoveries'][kind]==digest(receipt_raw) and receipt['status']=='recovered'
                and receipt['parent_experiment']==m['parent_experiment'] and receipt['scope']==kind,
                'required recovered scope differs')
        originals=receipt['original_evidence']
        require(type(originals) is list and 0<len(originals)<=16, 'bounded original external recovery evidence required')
        for original in originals:registered(original)
        require(review['original_evidence'][kind]==digest(body(originals)), 'original recovery evidence join differs')
        recovered[kind]=set(receipt['body_sha256'])
    for refs in m['batches']:
        require(all(ref['sha256'] in recovered['score_offload'] for ref in refs[:3])
                and all(ref['sha256'] in recovered['numeric_origin'] for ref in refs[3:]), 'missing required recovered scope body')
    accounting_raw=registered(m['parent_accounting'])
    require(digest(accounting_raw) in failed['output_sha256'].values()
            and review['parent_accounting_sha256']==digest(accounting_raw), 'actual parent spent output required')
    accounting=json.loads(accounting_raw)
    require(accounting['parent_experiment']==m['parent_experiment']
            and accounting['spent_counters']==m['spent_counters']
            and type(accounting['retained_partial_work']) is dict
            and all(type(v) is int and v>=0 for v in accounting['retained_partial_work'].values()), 'parent spent/partial accounting differs')
    return accounting


def verify_prefix(run, registered_input, *, expected_contract):
    """A parser result is not authority; only a genuine admitted run returns it."""
    from tradingagents.research.lifecycle import ResearchRun
    require(type(run) is ResearchRun, 'genuine continuation admission required')
    manifest_raw=_bounded_input(run,registered_input,max_bytes=MAX_MANIFEST_BYTES)
    require(len(manifest_raw)<=MAX_MANIFEST_BYTES, 'prefix manifest extent exceeded')
    m=_json(manifest_raw)
    require(m['policy']==POLICY and m.get('provenance_mode','durable-commit') in ('durable-commit','legacy-recovered-prefix-v1') and m['contract']==expected_contract, 'prefix exact contract differs')
    required={'source_sha256','config_sha256','dictionary_sha256','graph_hash','node_order_hash','descriptor_sha256','workflow_identity','cells','batch_cells'}
    require(required<=set(expected_contract), 'prefix numerical contract incomplete')
    require(type(expected_contract['batch_cells']) is int and 0<expected_contract['batch_cells']<=4096
            and type(expected_contract['cells']) is int and 0<expected_contract['cells']<2**63, 'prefix finite bounds required')
    require(m['successor_experiment']==run.admission.experiment_id and m['parent_experiment']!=m['successor_experiment'] and m['parent_status']=='FAILED', 'fresh successor/FAILED parent required')
    require(m['successor_experiment'] not in m['ancestor_experiments'] and m['parent_experiment'] in m['ancestor_experiments'], 'continuation identity reused')
    require((m['contract']['workflow_identity'],m['contract']['graph_hash']) not in _USED.get(run,set()),'continuation already consumed by successor')
    descriptors=_descriptors(m.get('descriptors',{}),expected_contract)
    accounting=_authority(run,m)
    batches=[];start=0;last_costs={};origin_cache=None;origin_reads=0;last_summary=None;last_epoch=None;oh=hashlib.sha256();sh=hashlib.sha256()
    require(type(m['batches']) is list and 0<len(m['batches'])<=65536, 'bounded nonempty prefix required')
    for index,refs in enumerate(m['batches']):
        require(type(refs) is list and len(refs)==6, 'prefix registered body roster differs')
        refs=_references(refs)
        batch=_registered_batch(run,refs,index,expected_contract,m.get('provenance_mode')=='legacy-recovered-prefix-v1',descriptors)
        commit_value=_json(batch.commit);summary_value=_json(batch.summary)
        epoch=commit_value['cost_epoch_start']
        require((index==0 and epoch==0) or epoch==last_epoch or epoch==start, 'prefix memo reset boundary differs')
        if last_summary is not None and epoch==last_epoch:
            require(set(summary_value['counters'])==set(last_summary)
                    and all(v>=last_summary[k] for k,v in summary_value['counters'].items() if k!='accounted_cache_bytes'),
                    'prefix cumulative numeric counters decreased')
        last_summary=summary_value['counters'];last_epoch=epoch
        costs=_costs(batch.commit)
        require(all(costs[k]>=last_costs.get(k,0) for k in costs), 'prefix spent counters decreased')
        last_costs=costs
        for record,(mode,origin) in zip(batch.records,numeric_format.RECORD.iter_unpack(batch.origins),strict=True):
            if mode:
                origin_batch,offset=divmod(origin,expected_contract['batch_cells'])
                if origin_batch==index:source=batch
                else:
                    if origin_cache is None or origin_cache[0]!=origin_batch:
                        origin_reads+=1
                        origin_cache=(origin_batch,_registered_batch(run,batches[origin_batch],origin_batch,expected_contract,m.get('provenance_mode')=='legacy-recovered-prefix-v1',descriptors))
                    source=origin_cache[1]
                require(record[2:]==source.records[offset][2:]
                        and numeric_format.RECORD.unpack_from(source.origins,offset*9)==(0,origin),
                        'reused origin score/status differs')
        batches.append(refs);start+=len(batch.records);oh.update(batch.origins);sh.update(batch.score_bodies[1])
    require(start==m['next_ordinal'] and start<=expected_contract['cells'] and (start==expected_contract['cells'] or start%expected_contract['batch_cells']==0), 'partial/finished prefix refused')
    require(type(m['spent_counters']) is dict and all(type(k) is str and type(v) is int and 0<=v<2**127 for k,v in m['spent_counters'].items()), 'spent accounting required')
    _check_spent(m['spent_counters'],accounting['retained_partial_work'],last_costs)
    require(_bounded_input(run,registered_input,max_bytes=MAX_MANIFEST_BYTES)==manifest_raw, 'prefix changed during verification')
    _authority(run,m)
    expected=(m['parent_experiment'],m['successor_experiment'],expected_contract['workflow_identity'],expected_contract['graph_hash'],start,tuple(batches),oh.hexdigest(),sh.hexdigest(),expected_contract.get('numerical_contract_sha256',digest(body(expected_contract))),tuple(sorted(m['spent_counters'].items())),digest(manifest_raw),tuple(sorted(descriptors.items())),(('verified_batches',len(batches)),('prior_origin_batch_reads',origin_reads),('max_decoded_batches_retained',2)))
    result=CompletedPrefix(*expected)
    require(type(result) is CompletedPrefix and tuple(getattr(result,f.name) for f in fields(result))==expected, 'prefix constructor changed authenticated fields')
    _VERIFIED[result]=expected
    _READERS[result]=(run,body(expected_contract),m.get('provenance_mode')=='legacy-recovered-prefix-v1',registered_input)
    return result


def restore_prefix(prefix, journal, numeric, consumer):
    """Copy only authenticated complete batches into a fresh successor namespace."""
    require(type(prefix) is CompletedPrefix and _VERIFIED.pop(prefix,None)==tuple(getattr(prefix,f.name) for f in fields(prefix)), 'verified unused prefix required')
    require(journal.cells==journal.batch==numeric.ordinal==numeric.batch==0, 'fresh prefix destination required')
    require(not journal.closed and not journal.poisoned and callable(consumer), 'prefix destination unavailable')
    try:
        reader=_READERS.get(prefix)
        if reader is not None:
            run,_,_,role=reader
            key=(prefix.workflow_identity,prefix.graph_hash)
            used=_USED.setdefault(run,set())
            require(key not in used,'continuation already consumed by successor')
            used.add(key)
            manifest=_bounded_input(run,role,max_bytes=MAX_MANIFEST_BYTES)
            require(digest(manifest)==prefix.manifest_sha256,'prefix admission changed before restoration')
            _authority(run,_json(manifest))
        for index in range(len(prefix.batches)):
            batch=_load_batch(prefix,index)
            for suffix,raw in zip(SUFFIXES,batch.score_bodies,strict=True):
                journal._write(f'{index:08d}'+suffix,raw,max(journal.max_body,HEADER.size+journal.batch_cells*RECORD.size))
            require(tuple(journal.read_complete(index))==batch.records, 'restored score differs')
            numeric.import_completed_batch(batch.origins,batch.summary)
            suffix='.legacy-prefix-counter.json' if batch.legacy else '.prefix.json'
            journal._write(f'{index:08d}'+suffix,batch.commit,journal.max_body)
            journal.cells+=len(batch.records);journal.batch+=1
            for row in batch.records:
                ordinal=row[0];center,motif=divmod(ordinal,32)
                consumer(ordinal,center,motif,struct.pack('<f',row[2]))
        require(journal.cells==numeric.ordinal==prefix.next_ordinal, 'restored prefix cursor differs')
        numeric.imported_costs={k:dict(prefix.spent_counters).get(k,v) for k,v in _costs(batch.commit).items()}
        numeric.memo.restore_ordinal(prefix.next_ordinal)
        numeric.continuation={'policy':POLICY,'manifest_sha256':prefix.manifest_sha256,'parent_experiment':prefix.parent_experiment,'imported_cells':prefix.next_ordinal,'imported_computed':numeric.computed,'imported_reused':numeric.reused,'spent_counters':dict(prefix.spent_counters),'memo_reset_count':1}
    except BaseException:
        journal.poisoned=True;numeric._poison();raise


def _costs(commit):
    value=_json(commit)
    return dict(checkpoint_attempts=value['checkpoint_attempts'],checkpoint_reserved_bytes=value['checkpoint_reserved_bytes'],**value['operation_counters'])


def verify_purposes(prefix,tasks):
    """Compare authentic reconstructed graph/motif purposes before sink import."""
    require(type(prefix) is CompletedPrefix and prefix in _VERIFIED,'verified prefix required')
    # The driver supplies a factory for authentic parent operational descriptors.
    # A plain iterator remains the bounded parser-fixture interface.
    for index in range(len(prefix.batches)):
        batch=_load_batch(prefix,index)
        owned=callable(tasks)
        iterator=tasks(batch,_descriptor_for(prefix,batch)) if owned else tasks
        try:
            for record in batch.records:
                purpose,a,b=next(iterator)
                require(purpose['ordinal']==record[0] and hashlib.sha256(body(purpose)).digest()==record[1],
                        'restored graph/motif purpose differs')
                del a,b,purpose
        finally:
            if owned:iterator.close()


def _references(refs):
    require(type(refs) is list and len(refs)==6,'six registered references required')
    result=[]
    for ref in refs:
        require(type(ref) is dict and set(ref)=={'role','sha256'}
                and type(ref['role']) is str and 0<len(ref['role'])<=128
                and ref['role'].isascii() and all(x.isalnum() or x in '_-.' for x in ref['role'])
                and type(ref['sha256']) is str and len(ref['sha256'])==64
                and all(c in '0123456789abcdef' for c in ref['sha256']), 'prefix recovered reference differs')
        result.append((ref['role'],ref['sha256']))
    require(len({role for role,_ in result})==6,'distinct registered prefix roles required')
    return tuple(result)


def _registered_batch(run,refs,index,contract,legacy,descriptors=None):
    names=tuple(role for role,_ in refs)
    values=run.read_inputs(names,max_each_bytes=1024**2,max_total_bytes=4*1024**2)
    blobs=tuple(values[role] for role,_ in refs)
    require(all(digest(raw)==sha for raw,(_,sha) in zip(blobs,refs,strict=True)), 'recovered prefix body changed')
    if descriptors:
        pending=_json(blobs[0]);key=pending['workload_sha256']
        require(key in descriptors,'unreviewed parent descriptor')
        contract={**contract,'descriptor_sha256':key}
    return _decode_batch(blobs,index,index*contract['batch_cells'],contract['batch_cells'],contract['cells'],contract,legacy=legacy)


def _load_batch(prefix,index):
    reader=_READERS.get(prefix)
    if reader is None:
        # Only internal parser tests install such a grant. verify_prefix always
        # retains immutable role/hash references and a genuine ResearchRun.
        batch=prefix.batches[index]
        require(type(batch) is CompletedBatch,'registered prefix reader missing')
        return batch
    run,contract,legacy,_=reader
    return _registered_batch(run,prefix.batches[index],index,_json(contract),legacy,dict(prefix.descriptors))


def _bounded_input(run,name,*,max_bytes):
    """Source-checked registered metadata transaction, capped before allocation.

    This explicit continuation route permits a 32MiB manifest/inventory; the
    shared general-purpose 2MiB/4MiB role reader remains unchanged.
    """
    from tradingagents.research.lifecycle import _lock
    require(type(max_bytes) is int and 0<max_bytes<=MAX_MANIFEST_BYTES,'continuation metadata bound differs')
    with _lock(run.admission.root):
        run._active();run._check_source()
        require(type(name) is str and name in run.admission.inputs,'unregistered continuation input')
        info=run.admission.inputs[name];pin=(info['path'],info['sha256'])
        value=_registered_body(run,name,max_bytes)
        run._active();run._check_source()
        require(pin==(run.admission.inputs[name]['path'],run.admission.inputs[name]['sha256']), 'continuation input contract changed')
        require(_registered_body(run,name,max_bytes)==value,'continuation input changed during admission')
        run._active()
        return value


def _registered_body(run,name,limit):
    import stat
    from . import score_batches as io
    from .original_dictionary import _close_owned
    root=run.admission.root.resolve();info=run.admission.inputs[name];path=root/info['path']
    require(path.is_relative_to(root) and path.resolve()==path,'continuation input path redirected')
    parent,fd=io._open(path.parent);child=None
    try:
        io._root(parent,fd)
        child=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=fd)
        before=os.fstat(child)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_dev==root.stat().st_dev
                and 0<=before.st_size<=limit,'continuation metadata type/size/device differs')
        parts=[];size=0
        while True:
            block=os.read(child,min(65536,limit+1-size))
            if not block:break
            size+=len(block);require(size<=limit,'continuation metadata capacity exceeded');parts.append(block)
        value=b''.join(parts)
        require(len(value)==before.st_size and io._signature(before)==io._signature(os.fstat(child))
                ==io._signature(os.stat(path.name,dir_fd=fd,follow_symlinks=False)),'continuation input changed during read')
        io._root(parent,fd)
        require(path.resolve()==path and digest(value)==info['sha256'],'continuation registered body differs')
        return value
    finally:_close_owned((() if child is None else (child,))+(fd,),io)


def _descriptors(values,contract):
    require(type(values) is dict and len(values)<=1024,'bounded parent descriptor epochs required')
    result={}
    for key,value in values.items():
        require(type(value) is dict and set(value)=={'rows','cells','motifs','graph_hash','node_order_hash','workload_sha256','purpose_schema_version'}, 'parent descriptor schema differs')
        require(all(type(value[k]) is int and value[k]>0 for k in ('rows','cells','motifs','purpose_schema_version'))
                and all(type(value[k]) is str and len(value[k])==64 and all(c in '0123456789abcdef' for c in value[k])
                        for k in ('graph_hash','node_order_hash','workload_sha256')), 'parent descriptor types differ')
        encoded=body(value)
        require(digest(encoded)==key and value['graph_hash']==contract['graph_hash']
                and value['node_order_hash']==contract['node_order_hash'] and value['cells']==contract['cells']
                and value['rows']*32==value['cells'] and value['motifs']==32 and value['purpose_schema_version']==2,
                'parent descriptor scientific population differs')
        result[key]=encoded
    if values:require('numerical_contract_sha256' in contract,'stable scientific continuation contract required')
    return result


def _descriptor_for(prefix,batch):
    if not prefix.descriptors:return None
    key=_json(batch.score_bodies[0])['workload_sha256']
    values=dict(prefix.descriptors)
    require(key in values,'parent descriptor unavailable')
    return _json(values[key])


def _check_spent(spent,partial,completed):
    require(all(spent.get(k,-1)>=v+partial.get(k,0) for k,v in completed.items()),
            'parent spent counters refund completed or partial work')
