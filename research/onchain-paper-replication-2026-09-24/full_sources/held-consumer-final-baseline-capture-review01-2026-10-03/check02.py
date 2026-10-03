from pathlib import Path,PurePosixPath
import gzip,hashlib,io,json,os,stat,tarfile,time
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-final-baseline-root-capture01-2026-10-03';B=R.parent/'held-consumer-final-composition-root-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());E=lambda v:(json.dumps(v,sort_keys=True,indent=2)+'\n').encode();FILE=4194304
qraw=(A/'REQUEST01.json').read_bytes();assert H(qraw)=='3d5481584c69034d696276431465064d01788e0fd651bdc8fe7df203bc52bf71';q=json.loads(qraw);assert E(q)==qraw
craw=(A/'bundle01/capture.json').read_bytes();assert H(craw)=='b9f1d20bedb3e9eff6ca7390684c439de29f5eaab062663e8419f2a3b7a40227';c=json.loads(craw);assert E(c)==craw and c['request_sha256']==H(qraw) and c['source']==q['source']=='d443208795f59292c156c5b81b687594efacea4d'
assert q['capsule_manifest']==J(B/'CAPSULE_BASELINE_OBSERVATION01.json') and q['external_manifest']==J(B/'ACTUAL_PARENT_BASELINE01.json')
assert set(p.name for p in (A/'bundle01').iterdir())=={'capture.json','capsule.tar.gz','external.tar.gz','capsule-manifest.json','external-manifest.json'}
receipt=J(A/'ACTUAL_CAPTURE_RECEIPT01.json');assert receipt['actual_exit_code']==0 and receipt['actual_tool_chunk']=='a9e19a' and receipt['archives']==c['archives'] and receipt['capture_sha256']==H(craw) and receipt['request_sha256']==H(qraw)
for row in receipt['capture_body_members']:
 p=A/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==row['mode'];raw=p.read_bytes();assert len(raw)==row['bytes']<=FILE and H(raw)==row['sha256']
assert receipt['disk_free_bytes']>=receipt['disk_floor_bytes']==10737418240
# Independent raw framing: validate extension size BEFORE payload, bounded gzip reads,
# then canonical archive re-encoding; no tar extraction or decoded numeric input.
def inspect(role):
 m=q[role+'_manifest'];mb=(A/'bundle01'/(role+'-manifest.json')).read_bytes();assert mb==E(m) and H(mb)==q[role+'_manifest_sha256']==c['archives'][role]['manifest_sha256']
 raw=(A/'bundle01'/(role+'.tar.gz')).read_bytes();assert len(raw)==c['archives'][role]['bytes']<=FILE and H(raw)==c['archives'][role]['sha256']
 source=Path(q[role+'_root']);assert source.resolve()==source and stat.S_IMODE(source.lstat().st_mode)==m['root_mode'];expected={r['path']:r for r in m['members']};assert len(expected)==len(m['members'])
 allnames=[]
 for p,ds,fs in os.walk(source,followlinks=False):allnames.extend(str((Path(p)/n).relative_to(source)) for n in ds+fs)
 assert set(allnames)==set(expected)
 out=io.BytesIO();enc=gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0);tw=tarfile.open(fileobj=enc,mode='w|',format=tarfile.PAX_FORMAT)
 inflated=0;headers=0;seen=[];pending=None;total=0;started=time.monotonic();pax_count=0
 with gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb') as gz:
  def take(n):
   nonlocal inflated
   assert 0<=n<=FILE
   pieces=[]
   while n:
    b=gz.read(min(n,65536));assert b;pieces.append(b);n-=len(b);inflated+=len(b);assert inflated<=192*1024**2
   return b''.join(pieces)
  while True:
   assert time.monotonic()-started<60
   head=take(512);headers+=1;assert headers<=65538
   if head==bytes(512):
    assert pending is None and take(512)==bytes(512)
    while True:
     tail=gz.read(65536)
     if not tail:break
     inflated+=len(tail);assert inflated<=192*1024**2 and not any(tail)
    break
   t=tarfile.TarInfo.frombuf(head,'utf-8','strict');assert t.size>=0
   if t.type==tarfile.XHDTYPE:
    assert pending is None and t.name=='././@PaxHeader' and t.size<=8192
    b=take(t.size);assert not any(take((-t.size)%512));pos=0;values={}
    while pos<len(b):
     sp=b.index(b' ',pos);assert sp-pos<=8 and b[pos:sp].isdigit();n=int(b[pos:sp]);assert n>sp-pos+3 and pos+n<=len(b)
     rec=b[sp+1:pos+n];assert rec.endswith(b'\n');k,v=rec[:-1].split(b'=',1);assert k==b'path' and k not in values;values[k]=v.decode('utf8');pos+=n
    assert set(values)=={b'path'};pending=values[b'path'];pax_count+=1;continue
   assert t.type in (tarfile.REGTYPE,tarfile.DIRTYPE)
   name=t.name if pending is None else pending;pending=None
   # USTAR directories have one canonical terminal slash, absent from manifest paths.
   if t.isdir() and name.endswith('/'):
    name=name[:-1]
   pp=PurePosixPath(name);assert name==pp.as_posix() and not pp.is_absolute() and all(x not in ('','.','..') for x in pp.parts) and len(name.encode())<=2048 and len(pp.parts)<=32
   assert name in expected and name not in seen;row=expected[name];seen.append(name);assert t.uid==t.gid==0 and t.uname==t.gname=='' and t.mtime==0 and t.linkname=='' and t.mode==row['mode']
   p=source/name;s=p.lstat();assert p.resolve()==p and stat.S_IMODE(s.st_mode)==row['mode']
   if row['kind']=='directory':assert t.isdir() and t.size==0 and stat.S_ISDIR(s.st_mode);payload=b''
   else:
    assert t.isfile() and t.size==row['bytes']<=FILE and stat.S_ISREG(s.st_mode) and s.st_nlink==1
    payload=take(t.size);assert H(payload)==row['sha256'] and p.read_bytes()==payload;total+=len(payload)
   assert not any(take((-t.size)%512))
   nt=tarfile.TarInfo(name);nt.mode=row['mode'];nt.uid=nt.gid=0;nt.uname=nt.gname='';nt.mtime=0;nt.type=tarfile.DIRTYPE if row['kind']=='directory' else tarfile.REGTYPE;nt.size=len(payload);tw.addfile(nt,None if nt.isdir() else io.BytesIO(payload))
 tw.close();enc.close();assert out.getvalue()==raw
 assert seen==[r['path'] for r in m['members']] and set(seen)==set(expected)
 assert sum(r.get('bytes',0) for r in m['members'])==total
 return {'members':len(seen),'files':sum(r['kind']=='file' for r in m['members']),'directories_excluding_root':sum(r['kind']=='directory' for r in m['members']),'root_mode_metadata':m['root_mode'],'logical_body_bytes':total,'inflated_framing_bytes':inflated,'raw_headers':headers,'path_only_pax_headers':pax_count,'compressed_bytes':len(raw),'sha256':H(raw),'canonical_reencoding_exact':True,'complete_current_original_names_modes_body_hashes':True}
result={r:inspect(r) for r in ('capsule','external')};assert result['capsule']['members']==925 and result['external']['members']==12
assert sum(v['logical_body_bytes'] for v in result.values())<=128*1024**2
p=Path(q['external_root']);assert not os.path.lexists(p/'attempt')
cap=Path(q['capsule_root'])
for identity in ('original-import-held-success-20261003-01','original-import-held-publication-failure-20261003-01'):
 for prefix in ('research_runs','fixture_outer','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not os.path.lexists(cap/prefix/identity)
selected=[]
for d in Path('/proc').iterdir():
 if not d.name.isdecimal() or int(d.name)==os.getpid():continue
 try:args=(d/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if b'tradingagents.research.onchain_replication.job' in args or any(Path(a.decode('utf8','replace')).name in ('outer_controller01.py','launch_success01.py') for a in args if a):selected.append(int(d.name))
assert not selected
out={'schema_version':1,'decision':'accepted_local_baseline_capture_only','request_sha256':H(qraw),'capture_sha256':H(craw),'archives':result,'selected_process_pids':selected,'actual_remote_origin_verified':False,'fresh_recovered_git_verified':False,'native_or_claim':False,'qualification':'Independent bounded framing and byte-identical canonical re-encoding, original body/mode/full membership joins only. Root mode is manifest metadata, not a TAR member. No extraction, numerical decoding, capture rerun, remote recovery or native approval.'}
(R/'READBACK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('PASS local capture:925capsule+12external members complete;bounded raw gzip/TAR/path-onlyPAX;exact canonical compressed bytes;all original bodies/modes;no attempt/selected process. No extraction/remote/Git reconstruction/native.')
