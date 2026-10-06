"""Fixed May30 maintenance: verified local copy, then separately released retirement."""
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,stat,time,subprocess
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
ID='real-pilot-may30-ledger-relocation-20261006-01'
GRAPH='eth-paper-real-pilot-graph-20220530-20261005-01'
CONSUMER='eth-paper-real-pilot-may30-ledger-continuation-20261006-01'
DATA=Path('/home/malecada/Data');TARGET=DATA/'onchain-pilot-retained-ledgers'/GRAPH/'ledger.sqlite'
BYTES=3189231616;SHA='e870a85f607afdfe44338f1e6f38a57c347a26a9c9385d8482ec92a2fd321bf3'
BASE='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-fifth-graph-failed-get-duplicates-retirement-preparation01-2026-10-06'
PIN='2899e5f24c545224514a2eb53d4ad7591e388bdb39f5655204b541c8dc338705'
GIB=1024**3;CHUNK=1024**2

def need(v,m):
    if not v:raise ValueError(m)
def sig(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
def base():
    p=ROOT/BASE/'retire01.py';raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==PIN,'reviewed recovery source differs')
    spec=importlib.util.spec_from_file_location('prior_failed_recovery',p);m=importlib.util.module_from_spec(spec);exec(compile(raw,str(p),'exec'),vars(m));return m

def syncdir(p):
    fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
def publish(p,value):
    with p.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    syncdir(p.parent)
def failure(here,name,error):
    try:publish(here/name,{'identity':ID,'error_type':type(error).__name__,'message':str(error),'no_retry':True,'partials_retained':True})
    except BaseException as secondary:error.add_note('Failure receipt unavailable: '+repr(secondary))

def validate(c):
    need(c['identity']==ID and c['schema_version']==1 and c['data_floor_bytes']==c['root_floor_bytes']==10*GIB
        and c['wall_seconds']==14400 and c['chunk_bytes']==CHUNK,'fixed ordinary limits differ')
    need(c['target']=={'path':str(TARGET),'device':66307,'bytes':BYTES,'sha256':SHA},'fixed target differs')
    m=base();e=c['recovery_selection'];m.recovery(ROOT,e)
    row=e['rows'][0]['original'];need(row['bytes']==BYTES and row['sha256']==SHA and row['stat_identity'][0]==66310,'original ledger identity differs')
    for item in e['rows']:m.current(ROOT,item['original'])
    need(DATA.resolve(strict=True)==DATA and DATA.stat().st_dev==66307 and ROOT.stat().st_dev==66310,'distinct canonical physical stores required')
    return m,row

def room(c,remaining=0):
    for p,floor,extra in [(ROOT,c['root_floor_bytes'],64*1024**2),(DATA,c['data_floor_bytes'],remaining+64*1024**2)]:
        s=os.statvfs(p);need(s.f_bavail*s.f_frsize>=floor+extra,'fresh physical volume floor/scratch unavailable')

def stream_copy(source,target,row,*,tick,chunk=CHUNK):
    """Finite copy + independent fresh destination readback; never unlinks anything."""
    need(0<chunk<=CHUNK and row['bytes']>0,'bounded copy required')
    need(source.resolve(strict=True)==source and target.parent.resolve(strict=True)==target.parent,'canonical copy paths required')
    expected=row['stat_identity'];before=source.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==row['mode'] and [before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns]==expected,'source stat differs')
    need(not os.path.lexists(target),'exclusive target required')
    with os.fdopen(os.open(source,os.O_RDONLY|os.O_NOFOLLOW),'rb') as src:
        fcntl.flock(src.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        need(sig(os.fstat(src.fileno()))==sig(before),'opened source differs')
        fd=os.open(target,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w+b') as dst:
            fcntl.flock(dst.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            h=hashlib.sha256();n=0
            while n<row['bytes']:
                tick(row['bytes']-n);part=src.read(min(chunk,row['bytes']-n));need(bool(part),'short original source')
                need(dst.write(part)==len(part),'short destination write');h.update(part);n+=len(part)
            need(src.read(1)==b'' and h.hexdigest()==row['sha256'],'source length/hash differs')
            os.fchmod(dst.fileno(),row['mode']);dst.flush();os.fsync(dst.fileno());syncdir(target.parent)
            need(sig(source.lstat())==sig(before)==sig(os.fstat(src.fileno())),'source drift during copy')
            copied=sig(os.fstat(dst.fileno()));need(copied==sig(target.lstat()) and copied[2]==1,'destination changed')
            # New descriptor reads every byte; the write handle stays locked and open.
            with os.fdopen(os.open(target,os.O_RDONLY|os.O_NOFOLLOW),'rb') as readback:
                need(sig(os.fstat(readback.fileno()))==copied,'readback descriptor differs')
                d=hashlib.sha256();n=0
                while n<row['bytes']:
                    tick(0);part=readback.read(min(chunk,row['bytes']-n));need(bool(part),'short destination readback');d.update(part);n+=len(part)
                need(readback.read(1)==b'' and d.hexdigest()==row['sha256'],'destination readback hash differs')
                need(sig(os.fstat(readback.fileno()))==copied==sig(target.lstat()),'readback drift')
            need(sig(source.lstat())==sig(before)==sig(os.fstat(src.fileno())),'source drift after readback')
    return {'path':str(target),'device':copied[0],'bytes':row['bytes'],'sha256':row['sha256'],'stat_identity':copied}

def inactive_worker(m,own_unit):
    need(type(own_unit) is str and own_unit.startswith('onchain-replication-') and own_unit.endswith('.service'),'actual native unit required')
    text=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True)
    need(all(line.split()[0]==own_unit for line in text.splitlines() if line.strip()),'another native producer active')
    for claim in (ROOT/'research_runs').glob('*/claim.json'):
        if claim.with_name('complete.json').exists() or claim.with_name('failed.json').exists():continue
        j=json.loads(m.metadata(ROOT,str(claim.relative_to(ROOT))))
        need(j.get('program_id')!='onchain-paper-replication-2026-09-24','active replication claim')
        for ref in j.get('experiment',{}).get('inputs',{}).values():
            q=(ROOT/ref['path']).resolve()
            need(not q.is_relative_to(ROOT/m.ORIGINAL_PARENT) and not q.is_relative_to(TARGET.parent),'active consumer references retained store')

def copy(root,here,c,guard):
    need(root==ROOT,'fixed Main root required');m,row=validate(c);own=guard();inactive_worker(m,own['unit']);room(c,BYTES)
    for name in ('copy-attempt01.json','copy-complete01.json','copy-failed01.json'):need(not os.path.lexists(here/name),'copy identity already spent')
    need(not os.path.lexists(TARGET.parent),'target namespace must be entirely new')
    parent=TARGET.parent.parent
    if parent.exists():need(parent.resolve(strict=True)==parent and parent.stat().st_dev==66307,'canonical Data store parent required')
    start=time.monotonic();publish(here/'copy-attempt01.json',{'identity':ID,'source':row,'target':c['target'],'no_retry':True})
    try:
        if not parent.exists():parent.mkdir();syncdir(DATA)
        TARGET.parent.mkdir();syncdir(parent)
        last=[0.0]
        def tick(remaining):
            now=time.monotonic();need(now-start<c['wall_seconds'],'copy deadline')
            if now-last[0]>=1:guard();room(c,remaining);last[0]=now
        target=stream_copy(ROOT/row['path'],TARGET,row,tick=tick)
        guard();room(c);inactive_worker(m,own['unit'])
        need(target['device']==66307 and set(p.name for p in TARGET.parent.iterdir())=={'ledger.sqlite'},'exact Data sole-body store required')
        for item in c['recovery_selection']['rows']:m.current(ROOT,item['original'])
        record={'schema_version':1,'identity':ID,'predecessor':GRAPH,'original_claim_sha256':'63e94692f690373cc238bbb7d7c7e5147129f145c8df18b650a1040736b50a76','original_source':'14414c1637256dd286eafbe92391129dee3d29bf','original':row,'target':target,'copy_readback_verified':True,'external_byte_recovery_verified':True,'original_retired':False,'two_partial_arrays_retained':True,'typed_name_mode_verified':target['path']==str(TARGET) and target['stat_identity'][6]==row['mode'],'recovery_review':c['recovery_selection']['recovery_basis']['outcome_review'],'source_retired':False}
        publish(here/'copy-complete01.json',record)
    except BaseException as error:failure(here,'copy-failed01.json',error);raise
    return record

def retire(root,here,c,release):
    need(root==ROOT,'fixed Main root required');m,row=validate(c);m.inactive();room(c)
    need(release['decision']=='accepted' and release['phase']=='retire' and release['identity']==ID,'separate exact retirement release required')
    def bound(ref):return json.loads(m.metadata(ROOT,ref['path'],ref['sha256']))
    copy_ref=release['copy_receipt'];record=bound(copy_ref);review=bound(release['copy_review'])
    need(review['decision']=='accepted' and review['identity']==ID and review['copy_receipt_sha256']==copy_ref['sha256'] and review['full_destination_readback_verified'] is True,'actual independent copy acceptance required')
    need(record['identity']==ID and record['original']==row and record['copy_readback_verified'] is True and record['original_retired'] is False and record['typed_name_mode_verified'] is True,'actual copy receipt differs')
    target=record['target'];need({k:target[k] for k in ('path','device','bytes','sha256')}==c['target'],'copy target differs')
    need(TARGET.resolve(strict=True)==TARGET and set(p.name for p in TARGET.parent.iterdir())=={'ledger.sqlite'} and sig(TARGET.lstat())==target['stat_identity'],'copy currentness differs')
    for name in ('retire-attempt01.json','retire-complete01.json','retire-failed01.json','relocation-receipt01.json'):need(not os.path.lexists(here/name),'retirement identity already spent')
    publish(here/'retire-attempt01.json',{'identity':ID,'copy_receipt':copy_ref,'copy_review':release['copy_review'],'no_retry':True})
    attempted=[];removed=[];stage='opening-held-descriptors'
    try:
        with os.fdopen(os.open(ROOT/row['path'],os.O_RDONLY|os.O_NOFOLLOW),'rb') as src, os.fdopen(os.open(TARGET,os.O_RDONLY|os.O_NOFOLLOW),'rb') as dst:
            for handle in (src,dst):fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            need(m.identity(os.fstat(src.fileno()))==row['stat_identity'] and sig(os.fstat(dst.fileno()))==target['stat_identity'],'held source/destination differs')
            m.inactive();m.current(ROOT,row);need(sig(TARGET.lstat())==target['stat_identity'],'destination drift before unlink')
            stage='unlink-original';attempted.append(row['path'])
            (ROOT/row['path']).unlink();removed.append(row['path'])
            stage='sync-original-parent';syncdir((ROOT/row['path']).parent)
            stage='verify-post-unlink-disposition'
            need(not os.path.lexists(ROOT/row['path']) and sig(TARGET.lstat())==target['stat_identity'],'retirement disposition differs')
            stage='close-held-descriptors'
        stage='verify-retained-partial-arrays'
        for item in c['recovery_selection']['rows'][1:]:m.current(ROOT,item['original'])
        evidence={'identity':ID,'original':row,'target':target,'source_retired':True,'original_retired':True,'copy_receipt':copy_ref,'copy_review':release['copy_review'],'two_partial_arrays_retained':True,'original_parent_status':'failed','no_retry':True}
        stage='publish-retirement-complete'
        publish(here/'retire-complete01.json',evidence)
        ref={'path':str((here/'retire-complete01.json').relative_to(ROOT)),'sha256':hashlib.sha256((here/'retire-complete01.json').read_bytes()).hexdigest()}
        final={'schema_version':1,'kind':'closed-ledger-cross-volume-relocation','identity':CONSUMER,'predecessor':GRAPH,'original_claim_sha256':record['original_claim_sha256'],'original_source':record['original_source'],'original':{k:row[k] for k in ('path','bytes','sha256')},'target':target,'copy_readback_verified':True,'external_byte_recovery_verified':True,'original_retired':True,'retirement_evidence':ref}
        stage='publish-consumer-bridge'
        publish(here/'relocation-receipt01.json',final)
    except BaseException as error:
        # Successful unlink return is evidence even if fsync/close/publication then fails.
        # An attempted unlink without a successful return remains ambiguous, never coerced to success.
        disposition={'identity':ID,'error_type':type(error).__name__,'message':str(error),
            'stage':stage,'unlink_attempted':attempted,'removed':removed,
            'ambiguous_attempts':[p for p in attempted if p not in removed],
            'source_retired':True if row['path'] in removed else (None if attempted else False),
            'original':row,'target':target,'copy_receipt':copy_ref,'copy_review':release['copy_review'],
            'original_parent_status':'failed','no_retry':True,'partials_retained':True}
        try:publish(here/'retire-failed01.json',disposition)
        except BaseException as secondary:error.add_note('Retirement failure disposition unavailable: '+repr(secondary))
        raise
    return final
