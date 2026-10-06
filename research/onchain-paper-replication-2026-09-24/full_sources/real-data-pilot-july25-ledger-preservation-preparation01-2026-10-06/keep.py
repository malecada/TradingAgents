"""One-use preservation primitives. Entry supplies genuine release/native guard; no launcher."""
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil
ID='real-pilot-july25-ledger-preservation-20261006-01'
BASE='research/onchain-paper-replication-2026-09-24/storage/cold-offload-2026-09-29-03/offload.py'
BASE_SHA='0d507711644d962e494e659987ba0a6d479304af7092ba15315630d0b68e1a84'
def bind_primitives(root):
    p=Path(root)/BASE
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=BASE_SHA:raise ValueError('cold03 source changed')
    spec=importlib.util.spec_from_file_location('preservation_cold03',p)
    module=importlib.util.module_from_spec(spec);exec(compile(raw,str(p),'exec'),vars(module))
    return module

def keep_one(root, here, row, number, remote, transport, *, primitives):
    validate_source=primitives.validate_source;identity=primitives.identity;sha=primitives.sha;publish=primitives.publish;sync_directory=primitives.sync_directory
    source = root / row['path']
    if source.resolve(strict=True)!=source or here.resolve(strict=True)!=here or source.is_relative_to(here):
        raise ValueError('canonical original outside preservation directory required')
    validate_source(source, row)
    verified = here / f'{number:02d}-verified.json'
    if any((here/f'{number:02d}-{suffix}').exists() for suffix in ('verified.json','recovered.bin','restore.json','recovered-restore.json','kept.json')):
        raise FileExistsError('identity already attempted; reconcile instead of repeating')
    body = remote + f'/{number:02d}.bin'
    recovery = here / f'{number:02d}-recovered.bin'
    metadata = here / f'{number:02d}-restore.json'
    recovered_metadata = here / f'{number:02d}-recovered-restore.json'
    with os.fdopen(os.open(source, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as retained:
        fcntl.flock(retained, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if identity(os.fstat(retained.fileno())) != row['stat_identity']:
            raise ValueError('opened file identity differs')
        transport.put(source, body)
        transport.get(body, recovery)
        if recovery.stat().st_size != row['bytes'] or sha(recovery) != row['sha256']:
            raise ValueError('body round-trip mismatch; original retained')
        validate_source(source, row)
        record = {**row, 'remote_object':body, 'remote_restore':remote+f'/{number:02d}-restore.json',
                  'body_roundtrip_verified':True,
                  'restoration':'Download remote_object to a new temporary file; verify bytes and SHA-256; restore original path only when absent. Never launch the old job.'}
        publish(metadata, record)
        transport.put(metadata, record['remote_restore'])
        transport.get(record['remote_restore'], recovered_metadata)
        if sha(metadata) != sha(recovered_metadata):
            raise ValueError('restoration metadata round-trip mismatch; original retained')
        validate_source(source, row)
        if identity(os.fstat(retained.fileno())) != row['stat_identity']:
            raise ValueError('opened source drifted')
        for recovered in (recovery,recovered_metadata):
            with recovered.open('rb') as checked:os.fsync(checked.fileno())
        sync_directory(here)
        record.update(original_retained=True,recovered_body_retained=True)
        publish(verified, record)
    publish(here / f'{number:02d}-kept.json', record)
    sync_directory(here)
    return record


GIB=1024**3
def preserve_selected(root,here,c,transport,guard):
    """Called only by released entry; guard is its real assert_guarded_worker closure."""
    root=Path(root);here=Path(here);guard()
    if root.resolve(strict=True)!=root or here.resolve(strict=True)!=here or not here.is_relative_to(root):raise ValueError('canonical preservation roots required')
    if c['identity']!=ID or c['schema_version']!=1:raise ValueError('wrong preservation selection')
    rows=c['files']
    if type(rows) is not list or not 1<=len(rows)<=4096 or len(rows)!=c['count']:raise ValueError('finite exact row count required')
    if any(type(r['bytes']) is not int or r['bytes']<0 for r in rows):raise ValueError('invalid row size')
    if sum(r['bytes'] for r in rows)!=c['total_bytes'] or max(r['bytes'] for r in rows)!=c['max_body_bytes']:raise ValueError('exact byte denominator differs')
    if c['disk_floor_bytes']!=10*GIB or c['transport_payload_budget_bytes']!=8*GIB or c['owned_tree_limit_bytes']!=5*GIB:raise ValueError('fixed finite envelope differs')
    if transport.remaining!=8*GIB or c['total_bytes']+16*1024**2>5*GIB:raise ValueError('fresh transport or retained scratch budget differs')
    paths=[]
    for r in rows:
        p=Path(r['path']);source=root/p
        if p.is_absolute() or '..' in p.parts or str(p)!=r['path'] or source.resolve(strict=True)!=source or source.is_relative_to(here):raise ValueError('canonical original selection required')
        if type(r['sha256']) is not str or len(r['sha256'])!=64 or any(v not in '0123456789abcdef' for v in r['sha256']):raise ValueError('exact original SHA required')
        if type(r['stat_identity']) is not list or len(r['stat_identity'])!=5 or r['stat_identity'][2]!=r['bytes']:raise ValueError('original stat denominator differs')
        paths.append(str(p))
    if len(set(paths))!=len(paths):raise ValueError('duplicate original path')
    primitives=bind_primitives(root)
    # Exclusive intent reserves this local identity even when remote mkdir fails.
    primitives.publish(here/'intent.json',{'identity':ID,'selection':c,'no_automatic_retry':True})
    records=[];attempts=[];number=None
    try:
        if shutil.disk_usage(here).free<c['disk_floor_bytes']+c['total_bytes']+16*1024**2:raise ValueError('floor plus all retained recoveries unavailable')
        if transport.available()<c['total_bytes']+16*1024**2:raise ValueError('remote capacity unavailable')
        transport.mkdir(c['remote'])
        for number,row in enumerate(rows):
            guard()
            remaining=sum(r['bytes'] for r in rows[number:])
            if shutil.disk_usage(here).free<c['disk_floor_bytes']+remaining+16*1024**2:raise ValueError('retained recovery floor unavailable')
            primitives.publish(here/f'{number:02d}-attempted.json',{'number':number,'row':row})
            attempts.append(number)
            records.append(keep_one(root,here,row,number,c['remote'],transport,primitives=primitives))
        guard()
        result={'identity':ID,'selection':c,'files':records,'count':len(records),'bytes_preserved':sum(r['bytes'] for r in records),'originals_retained':True,'recoveries_retained':True,'no_automatic_retry':True}
        primitives.finish(here,result,c['remote'],transport)
        return result
    except BaseException as error:
        try:
            primitives.publish(here/'failed.json',{'identity':ID,'error':type(error).__name__+': '+str(error),'attempted':attempts,'verified':[i for i in range(len(records))],'failed_row':number if number is not None and number>=len(records) else None,'skipped':[i for i in range(len(rows)) if i not in attempts],'no_automatic_retry':True,'originals_never_unlinked':True,'reconcile_all_receipts_and_partial_recoveries':True})
        except BaseException as evidence_error:
            try:error.add_note('Preservation failure evidence unavailable: '+repr(evidence_error))
            except BaseException:pass
        raise
