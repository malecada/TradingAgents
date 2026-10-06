"""Concrete May9 metadata-only successor. Parent FAILED remains immutable."""
import hashlib,importlib.util,json,os,stat
from pathlib import Path
ID='real-pilot-second-graph-preservation-metadata-20261006-01'
PARENT='real-pilot-second-graph-preservation-20261006-01'
STUDY='research/onchain-paper-replication-2026-09-24'
OLD=STUDY+'/storage/'+PARENT
DEST=STUDY+'/storage/'+ID
OLD_SELECTION_SHA='96f5605613d4d9c537d4d130917d3af04f9a8005cc385b5a0576c60cf673c43a'
BASE=STUDY+'/storage/cold-offload-2026-09-29-03/offload.py'
BASE_SHA='0d507711644d962e494e659987ba0a6d479304af7092ba15315630d0b68e1a84'
LIMIT=4*1024**2
GIB=1024**3
QUALIFICATION='BYTE recovery composition with original restoration names/modes. Parent remains FAILED. Original body gets are reviewed historical recoveries; current remote body availability, executed POSIX restoration and runtime/environment reconstruction are not established. No retirement or paper-trial authority.'
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def identity(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def path(root,name):
    p=Path(name);need(not p.is_absolute() and '..' not in p.parts and str(p)==name,'canonical relative path required')
    p=root/p;need(p.resolve(strict=True)==p,'redirected source/evidence refused');return p
def raw(root,name,digest):
    p=path(root,name);s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=LIMIT,'bounded single-link metadata required')
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC),'rb') as f:
        need(identity(os.fstat(f.fileno()))==identity(s),'metadata open identity differs');b=f.read(LIMIT+1)
        need(identity(os.fstat(f.fileno()))==identity(s),'metadata changed while reading')
    need(identity(p.lstat())==identity(s) and len(b)==s.st_size and sha(b)==digest,'metadata hash/currentness differs: '+name);return b
def doc(root,ref):return json.loads(raw(root,ref['path'],ref['sha256']))
def current(root,name,pin,mode):
    s=path(root,name).lstat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and identity(s)==pin and stat.S_IMODE(s.st_mode)==mode,'inherited body stat/mode differs: '+name)
def bind_primitives(root):
    b=raw(root,BASE,BASE_SHA);p=root/BASE;s=importlib.util.spec_from_file_location('metadata_successor_cold03',p);m=importlib.util.module_from_spec(s);exec(compile(b,str(p),'exec'),vars(m));return m

def parent_state(root,binding):
    """Authenticate compact proof/receipts, stat ONLY the36 original/get bodies."""
    root=Path(root);need(root.resolve(strict=True)==root,'canonical root required')
    need(set(binding)=={'review','metadata','outcome'},'exact failed-parent proof bindings required')
    review=doc(root,binding['review'])
    need(review['decision']=='accepted-failed-parent-partial-byte-evidence' and review['identity']==PARENT and review['parent_status']=='failed' and review['full_scope_byte_recovery'] is False and review['retirement_release'] is False and review['authenticated_body_get_count']==36 and review['complete_row_metadata_get_count']==35,'independent exact failed-parent review required')
    need(review['metadata_check']==binding['metadata'] and review['outcome_check']==binding['outcome'],'exact reviewed proof refs required')
    payload_ref=review['recovered_payload_hash'];need(review['evidence'].get(payload_ref['path'])==payload_ref['sha256'],'body hash proof not anchored');payload=doc(root,payload_ref)
    need(payload['decision']=='pass-six-recovered-payload-bytes' and len(payload['files'])==6,'independent six-body byte pass required')
    for ref in (binding['metadata'],binding['outcome']):need(review['evidence'].get(ref['path'])==ref['sha256'],'partial proof not anchored by review')
    meta=doc(root,binding['metadata']);outcome=doc(root,binding['outcome'])
    need(outcome['decision']=='accepted-failed-parent-partial-byte-evidence' and outcome['actual_parent_outcome']=='failed' and outcome['actual_root_exit']==1 and outcome['guard_cleanup_verified'] is True and outcome['original_guard_child_exit'] is None and outcome['separate_worker_exit']==-15 and outcome['global_complete_or_metadata_full_recovery'] is False,'original failure/null/cleanup disposition differs')
    need(outcome['body_gets_independently_authenticated']==36 and outcome['complete_row_metadata_gets']==35 and outcome['no_retirement_release'] is True,'exact partial scope differs')
    evidence=meta['evidence']
    def old(name):
        relative=OLD+'/'+name;need(relative in evidence,'original receipt absent from reviewed evidence: '+name);return json.loads(raw(root,relative,evidence[relative]))
    need(evidence[OLD+'/selection01.json']==OLD_SELECTION_SHA,'original selection anchor differs')
    selection=old('selection01.json');need(selection['identity']==PARENT and selection['count']==36 and len(selection['files'])==36,'original36 membership required')
    terminal=old('ROOT_TERMINAL01.json');outer=old('outer-exit01.json');guard=old('guard01/final.json')
    need(terminal['identity']==PARENT and terminal['actual_current_cgroup_absent'] is True and terminal['actual_root_tool_exit_code']==1 and terminal['full_scope_complete'] is False,'genuine failed cleanup observation differs')
    need(outer['entry_selected_exit_code']==1 and outer['guard_child_exit_code'] is None and outer['cleanup_verified'] is True and guard['phase']=='failed' and guard['child_exit_code'] is None and guard['cleanup_verified'] is True,'original outer/native failure changed')
    absent=['complete.json','completion-candidate.json','recovered-complete.json','failed.json','35-kept.json','35-verified.json','35-recovered-restore.json','35-recovered-restore.json.transport.json']
    need(all(not os.path.lexists(root/OLD/name) for name in absent),'old failed namespace changed')
    rows=meta['rows'];need(len(rows)==36 and [r['index'] for r in rows]==list(range(36)),'complete ordered36-body proof required')
    for item in payload['files']:
        r=rows[item['index']];need(item['sha256']==r['sha256'] and item['bytes']==r['bytes'] and item['original_path']==r['original_path'] and item['recovered_path']==r['recovered_path'] and item['stat_identity']==r['recovered_stat_identity'],'six-body proof row join differs')
    records=[]
    for i,(r,s) in enumerate(zip(rows,selection['files'])):
        need(r['original_path']==s['path'] and r['sha256']==s['sha256'] and r['bytes']==s['bytes'] and r['original_stat_identity']==s['stat_identity'] and r['original_mode']==s['mode'] and r['body_get_complete'] is True,'body proof/original row differs')
        need(r['recovered_path']==OLD+f'/{i:02d}-recovered.bin','original body get name differs')
        current(root,s['path'],r['original_stat_identity'],r['original_mode']);current(root,r['recovered_path'],r['recovered_stat_identity'],r['recovered_mode'])
        get=old(f'{i:02d}-recovered.bin.transport.json');need(get['status']=='complete' and get['returncode']==0 and get['expected_bytes']==get['received_bytes']==s['bytes'],'original successful body-get receipt differs')
        restore=old(f'{i:02d}-restore.json')
        need(all(restore[k]==v for k,v in s.items()) and restore['remote_object']==selection['remote']+f'/{i:02d}.bin' and restore['remote_restore']==selection['remote']+f'/{i:02d}-restore.json' and restore['body_roundtrip_verified'] is True,'original restoration join differs')
        if i<35:
            need(r['restoration_metadata_get_complete'] is True and r['kept_marker_present'] is True,'old successful metadata scope differs')
            rec=old(f'{i:02d}-kept.json');need(rec==old(f'{i:02d}-verified.json') and all(rec[k]==v for k,v in restore.items()) and rec['original_retained'] is True and rec['recovered_body_retained'] is True,'old kept proof differs')
            need(old(f'{i:02d}-recovered-restore.json')==restore,'old recovered metadata differs')
            get=old(f'{i:02d}-recovered-restore.json.transport.json');need(get['status']=='complete' and get['returncode']==0 and get['expected_bytes']==get['received_bytes']==(root/OLD/f'{i:02d}-restore.json').stat().st_size,'old metadata transport differs');records.append(rec)
        else:need(r['restoration_metadata_get_complete'] is False and r['kept_marker_present'] is False,'final increment is no longer missing')
    need(sum(r['bytes'] for r in rows)==selection['total_bytes']==outcome['body_bytes'],'full36 byte denominator differs')
    for d in selection['directories']:
        s=path(root,d['path']).lstat();need(stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==d['mode'],'original directory name/mode differs')
    return selection,rows,records

def select(root,binding):
    original,rows,records=parent_state(root,binding)
    return {'schema_version':1,'status':'DRAFT_NOT_RELEASED','identity':ID,'parent':PARENT,'parent_status':'FAILED','binding':binding,'count':1,'total_bytes':2*LIMIT,'max_body_bytes':LIMIT,'files':[original['files'][35]],'missing_rows':[35],'body_transfer_count':0,'original_count':36,'original_total_bytes':original['total_bytes'],'directories':original['directories'],'remote':'research-backups/onchain-paper-replication-2026-09-24/'+ID,'disk_floor_bytes':10*GIB,'owned_tree_limit_bytes':5*GIB,'transport_payload_budget_bytes':8*GIB,'qualification':QUALIFICATION}

def preserve_selected(root,here,c,transport,guard):
    root=Path(root);here=Path(here);guard()
    need(here==root/DEST and here.resolve(strict=True)==here,'fixed fresh successor namespace required')
    expected=select(root,c['binding']);need(c==expected,'exact metadata-only selection changed')
    need(transport.remaining==8*GIB,'fresh unchanged finite transport required')
    p=bind_primitives(root);p.publish(here/'intent.json',{'identity':ID,'parent':PARENT,'parent_status':'FAILED','selection':c,'no_automatic_retry':True})
    try:
        need(transport.available()>=16*1024**2,'fresh remote metadata space unavailable');transport.mkdir(c['remote']);guard()
        original,rows,records=parent_state(root,c['binding']);record={**original['files'][35],'remote_object':original['remote']+'/35.bin','remote_restore':c['remote']+'/35-restore.json','body_roundtrip_verified':True,'body_recovery_origin':'reviewed-parent-failed-historical-full-get','parent_body_proof':c['binding']['metadata'],'original_retained':True,'recovered_body_retained':True,'restoration':'Freshly download original remote_object, authenticate exact bytes/SHA before use; restore original name/mode only under separately authorized POSIX restoration. Do not rerun old job.'}
        meta=here/'35-restore.json';recovered=here/'35-recovered-restore.json';p.publish(here/'35-attempted.json',{'number':35,'metadata_only':True,'body_transfer_count':0});p.publish(meta,record)
        need(meta.stat().st_size<=LIMIT,'finite metadata bound');transport.put(meta,record['remote_restore']);transport.get(record['remote_restore'],recovered)
        need(recovered.stat().st_size==meta.stat().st_size and meta.read_bytes()==recovered.read_bytes(),'new full metadata recovery differs')
        get_path=recovered.with_name(recovered.name+'.transport.json');need(get_path.stat().st_size<=LIMIT,'bounded new get receipt required');get=json.loads(get_path.read_bytes())
        need(get['status']=='complete' and get['returncode']==0 and get['expected_bytes']==get['received_bytes']==meta.stat().st_size,'new metadata get did not complete');guard()
        parent_state(root,c['binding']);p.publish(here/'35-verified.json',record);p.publish(here/'35-kept.json',record)
        records.append(record)
        result={'identity':ID,'parent':PARENT,'parent_status':'FAILED','parent_proof':c['binding'],'files':records,'count':36,'bytes_preserved':original['total_bytes'],'directories':original['directories'],'fresh_body_transfers':0,'fresh_restoration_metadata_rows':[35],'originals_retained':True,'recoveries_retained':True,'no_automatic_retry':True,'qualification':QUALIFICATION}
        need(len((json.dumps(result,indent=2)+'\n').encode())<=LIMIT,'combined completion exceeds finite metadata bound');guard();parent_state(root,c['binding']);p.finish(here,result,c['remote'],transport);return result
    except BaseException as error:
        p.publish(here/'failed.json',{'identity':ID,'parent':PARENT,'parent_status':'FAILED','error':type(error).__name__+': '+str(error),'no_automatic_retry':True,'originals_and_old_namespace_never_modified':True});raise
