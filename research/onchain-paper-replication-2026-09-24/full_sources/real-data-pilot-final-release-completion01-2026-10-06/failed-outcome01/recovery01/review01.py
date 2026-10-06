"""One returned archive stream; original archive proof reused, no transport."""
from pathlib import Path
import hashlib,io,json,stat,tarfile

R=Path.cwd()
BASE=Path('research/onchain-paper-replication-2026-09-24')
F=BASE/'full_sources'
OLD=F/'real-data-pilot-final-release-completion01-2026-10-06/failed-outcome01'
H=OLD/'recovery01'
I='real-pilot-first-resource-failed-preservation-20261006-01'
N='eth-paper-real-data-end-to-end-resource-20261005-01'
S=BASE/'storage'/I
CAP=F/'real-data-pilot-first-resource-failed-increment01-2026-10-06'
ORIGINAL=CAP/'failed-increment02.tar'
cache={};read_counts={}
def raw(p):
    p=Path(p);assert p!=ORIGINAL
    if p not in cache:
        q=R/p;s=q.lstat()
        assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
        b=q.read_bytes();z=q.lstat()
        assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
        cache[p]=b;read_counts[str(p)]=read_counts.get(str(p),0)+1
    return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(name,value):
    p=H/name
    with p.open('x') as f:f.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return p

assert sha(OLD/'ARCHIVE_REVIEW01.json')=='cadfc44c78f0bb1d74f14e32abc37e29138109476e7c83a7829730f78eb21bb0'
assert sha(OLD/'BODY_REVIEW01.json')=='03e91fe321fafa7c66d50a155a3157be5105709e1870ae6a32a64229ec1b5d53'
assert sha(OLD/'OUTCOME_REVIEW01.json')=='9941387f26b7e3fe79f60848eac3a967b740700142d290ecbc83679d571466a4'
archive_proof=read(OLD/'ARCHIVE_REVIEW01.json');body=read(OLD/'BODY_REVIEW01.json');capture=read(CAP/'CAPTURE02.json')
assert archive_proof['decision']==body['decision']=='accepted'
assert archive_proof['capture_sha256']==sha(CAP/'CAPTURE02.json')
selection=read(S/'selection01.json');complete=read(S/'complete.json');verified=read(S/'00-verified.json');restored=read(S/'00-recovered-restore.json')
root=read(S/'ROOT_TERMINAL01.json');outer=read(S/'outer-exit01.json');guard=read(S/'guard01/final.json')
assert complete['identity']==selection['identity']==root['identity']==outer['identity']==I
assert complete['selection']==selection and complete['files']==[verified]
assert complete['count']==selection['count']==1 and complete['bytes_preserved']==491520
assert complete['originals_retained'] is True and complete['recoveries_retained'] is True and complete['no_automatic_retry'] is True
assert sha(S/'complete.json')==sha(S/'completion-candidate.json')==sha(S/'recovered-complete.json')
assert sha(S/'00-recovered-restore.json')==sha(S/'00-restore.json')
assert sha(S/'00-verified.json')==sha(S/'00-kept.json')
assert {k:v for k,v in verified.items() if k not in ('original_retained','recovered_body_retained')}==restored
assert verified['original_retained'] is True and verified['recovered_body_retained'] is True and verified['body_roundtrip_verified'] is True
row=selection['files'][0]
assert all(verified[k]==v for k,v in row.items())
assert verified['remote_object']==selection['remote']+'/00.bin' and verified['remote_restore']==selection['remote']+'/00-restore.json'
assert read(S/'00-attempted.json')=={'number':0,'row':row}
assert read(S/'intent.json')['selection']==selection
assert row['path']==str(ORIGINAL) and row['bytes']==491520 and row['sha256']==archive_proof['archive']['sha256']==capture['archive']['sha256']
s=ORIGINAL.lstat()
assert (R/ORIGINAL).resolve(strict=True)==R/ORIGINAL and stat.S_ISREG(s.st_mode) and s.st_nlink==row['nlink']==1
assert stat.S_IMODE(s.st_mode)==row['mode'] and row['stat_identity']==[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
assert not (S/'failed.json').exists()

returned=S/'00-recovered.bin'
b=raw(returned)
assert len(b)==491520 and hashlib.sha256(b).hexdigest()==row['sha256']
files={v['path']:v for v in body['files']};dirs={v['path']:v for v in body['directories']}
members={v['path']:v for v in capture['members']}
assert len(files)==38 and len(dirs)==10 and len(members)==48
assert set(members)==set(files)|set(dirs)
verified_members=[]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:') as tf:
    seen=set()
    for member in tf.getmembers():
        p=member.name.rstrip('/')
        assert p in members and p not in seen and not Path(p).is_absolute() and '..' not in Path(p).parts
        seen.add(p);expected=members[p]
        assert member.mode==expected['mode']
        if expected['kind']=='directory':
            assert member.isdir() and member.size==0 and dirs[p]['mode']==member.mode
            verified_members.append({'path':p,'kind':'directory','mode':member.mode})
        else:
            assert member.isfile() and not member.issym() and not member.islnk()
            assert member.size==expected['bytes']==files[p]['bytes'] and files[p]['mode']==member.mode
            with tf.extractfile(member) as stream:payload=stream.read(member.size+1)
            digest=hashlib.sha256(payload).hexdigest()
            assert len(payload)==member.size and digest==expected['sha256']==files[p]['sha256']
            verified_members.append({'path':p,'kind':'regular','mode':member.mode,'bytes':member.size,'sha256':digest})
    assert seen==set(members)
assert sum(v.get('bytes',0) for v in verified_members)==399493
assert read_counts[str(returned)]==1 and str(ORIGINAL) not in read_counts

transport_receipts={}
selected_pids=set()
for name,size in (('00-recovered.bin',491520),('00-recovered-restore.json',931),('recovered-complete.json',2770)):
    p=S/(name+'.transport.json');receipt=read(p)
    assert receipt['status']=='complete' and receipt['returncode']==0 and receipt['error_type'] is None
    assert receipt['expected_bytes']==receipt['received_bytes']==size
    selected_pids.add(receipt['pid'])
    transport_receipts[name]={'receipt':ref(p),'expected_bytes':size,'received_bytes':size,'returncode':0,'pid':receipt['pid']}
assert root['original_outer']==outer
assert root['root_actual_exit']=={'exit_code':0,'invoke_chunk':'0270f6','session':18284,'terminal_chunk':'e58442'}
assert outer['entry_selected_exit_code']==outer['guard_child_exit_code']==guard['child_exit_code']==0
assert outer['guard_phase']==guard['phase']=='complete' and outer['cleanup_verified'] is True and guard['cleanup_verified'] is True
assert outer['fatal_type'] is None
assert root['actual_native']['elapsed_seconds']==guard['elapsed_seconds']==4.817551178000031
assert root['actual_native']['optional_memory_telemetry']==guard['optional_memory_telemetry']
assert guard['cleanup_stop_returncode']==5
assert guard['cleanup_unit_properties']['ControlGroup']=='' and guard['cleanup_unit_properties']['ActiveState']=='inactive'
assert guard['cleanup_unit_properties']['ExecMainStatus']=='0' and guard['cleanup_unit_properties']['Result']=='success'
assert not Path(guard['cgroup']).exists()
assert guard['owner_identity'] is None
child=read(S/'guard01/child_exit.json');cpu=read(S/'guard01/cpu_ready.json')
assert child['exit_code']==0
selected_pids.update((guard['monitor_pid'],child['workload_pid'],cpu['pid']))
assert all(type(pid) is int and pid>0 and not Path('/proc',str(pid)).exists() for pid in selected_pids)
for p,pin in root['evidence'].items():assert sha(Path(p))==pin
preflight=read(S/'preflight01.json')
assert preflight==read(S/'launch-attempt01.json') and preflight['head']==root['source']=='c677f0a79082584176e8a99c5720714299a3aa72'
assert preflight['envelope_sha256']==sha(S/'envelope01.json')=='652290a8786f0b801ea06528d35ccfb7e4b779a1ee128246522f622c72185c45'
assert sha(S/'RELEASE_REVIEW01.json')=='f4e5ffa46af888621c71acb6626e8a00a01b9eb23268de22a3342fb732e6bdbc'

member_proof={'schema_version':1,'decision':'accepted','identity':I,'returned_archive':ref(returned),
    'original_archive_proof_reused':ref(OLD/'ARCHIVE_REVIEW01.json'),'capture':ref(CAP/'CAPTURE02.json'),
    'body_review':ref(OLD/'BODY_REVIEW01.json'),'returned_archive_bytes':491520,
    'regular_count':38,'directory_count':10,'total_names':48,'original_regular_bytes':399493,
    'returned_archive_stream_count':1,'original_archive_stream_count':0,
    'members':verified_members,'qualification':'Actual returned archive BYTE/member/name/mode integrity; no filesystem extraction or POSIX reconstruction.'}
mp=write('RECOVERED_MEMBERS01.json',member_proof)
evidence={str(p):hashlib.sha256(v).hexdigest() for p,v in cache.items()}
evidence[str(mp)]=sha(mp)
review={'schema_version':1,'decision':'accepted','identity':I,'source':root['source'],
    'scope':'Actual complete external round trip of the exact failed-pilot increment archive and restoration/completion records; independent fresh returned archive/member byte verification.',
    'evidence':dict(sorted(evidence.items())),'complete_sha256':sha(S/'complete.json'),
    'original_failed_experiment':N,'original_failed_outcome_review':ref(OLD/'OUTCOME_REVIEW01.json'),
    'archive':{'original_path':str(ORIGINAL),'returned_path':str(returned),'sha256':row['sha256'],'bytes':491520,
       'regular_bodies':38,'directory_names_modes':10,'total_names':48,'unpacked_regular_bytes':399493,
       'actual_returned_members_review':ref(mp),'original_archive_current_stat_unchanged':True,
       'original_archive_hash_proof_reused':ref(OLD/'ARCHIVE_REVIEW01.json')},
    'actual_receipt_complete':True,'actual_returned_restore_matches':True,'actual_returned_completion_matches':True,
    'transport_receipts':transport_receipts,'root_actual_exit':root['root_actual_exit'],
    'native':{'phase':guard['phase'],'child_exit_code':guard['child_exit_code'],
       'elapsed_seconds':guard['elapsed_seconds'],'cleanup_verified':guard['cleanup_verified'],
       'cleanup_stop_returncode':guard['cleanup_stop_returncode'],'owner_identity':None,
       'cleanup_unit_properties':guard['cleanup_unit_properties'],
       'memory_events':guard['memory_events'],
       'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},
    'outer':outer,'current_cleanup':{'recorded_cgroup_absent':True,
       'selected_pid_exists':{str(pid):False for pid in sorted(selected_pids)},
       'qualification':'Six selected recorded PIDs and recorded cgroup absent at review. Unit terminal properties are original guard readbacks; no fresh native command or lifetime PID reconstruction.',
       'lifetime_process_history':None},
    'originals_retained':True,'returned_archive_retained':True,'deletion_authorized':False,
    'qualification':'BYTE recovery acceptance covers only38 metadata/log bodies399493bytes and10typed directory names/modes inside the491520-byte archive. It does not establish POSIX ownership/timestamps/xattrs reconstruction, installed runtime, older source/raw/graph stores or future remote availability. The original scientific FAILED/spent outcome and all nulls remain unchanged; no relaunch/refund/financial credit follows.',
    'not_tested':['No transport/network/native replay, extraction or deletion.',
       'No scientific payload decoding, numerical imports, fitting, financial claims or full-pilot capacity testing.',
       'No original archive/body re-stream; immutable accepted proof and unchanged original archive stat reused.']}
rp=write('RECOVERY_REVIEW01.json',review)
manifest=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','identity':I,'files':[ref(H/'review01.py'),ref(mp),ref(rp)]})
print(json.dumps({'review':ref(rp),'manifest':ref(manifest),'members':ref(mp),'decision':'accepted','regulars':38,'directories':10,'returned_archive_streams':1,'original_archive_streams':0},sort_keys=True))
