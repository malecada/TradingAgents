"""Independent actual950 scope capture bytes/framing; no capture/restore/network/native."""
import gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'held-consumer-final-released-scope-root-capture01-2026-10-03';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(U));s=importlib.util.spec_from_file_location('io_validators_only',U/'recovery04.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a);sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];bodypins=[]
def ck(v,msg):
 assert v,msg
 checks.append(msg)
def doc(p,pin=None):
 raw=a.read(p.parent,p.name);ck(pin is None or sha(raw)==pin,'pin '+p.name);v=json.loads(raw);ck(a.encode(v)==raw,'canonical '+p.name);bodypins.append({'path':str(p),'bytes':len(raw),'sha256':sha(raw),'mode':stat.S_IMODE(p.lstat().st_mode)});return v
q=doc(P/'REQUEST01.json','660a715bc4da9bfd93e4076cee4d82730301024b9fa95668c8182a48d9ac2061');a.request(q);receipt=doc(P/'bundle01/capture.json','122706bfcd5cf8eaaecc31b7230a0553d804606fad4db4d86a74f136dbe27408');terminal=doc(P/'ACTUAL_TERMINAL01.json');pre=doc(P/'PRECAPTURE_SCOPE01.json');ck(receipt['request_sha256']==sha(a.encode(q)) and receipt['source']==q['source']==a.SOURCE and set(receipt['archives'])=={'capsule','external'},'exact capture chain');ck(terminal['exit']==0 and terminal['capture_sha256']==sha(a.encode(receipt)) and terminal['genuine_run_or_native_started'] is False and terminal['free_bytes']>=a.FLOOR,'actual terminal capture-only/floor');ck('--launch' not in terminal['argv'] and terminal['argv'][terminal['argv'].index('--mode')+1]=='capture' and terminal['argv'][-1]==sha(a.encode(q)),'exact nonnative capture command');ck(sha((U/'recovery04.py').read_bytes())=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','actual accepted source04')
for stream in ('stdout','stderr'):ck(a.read(P,'CAPTURE01.'+stream)==b'','empty capture '+stream)
old=doc(F/'held-consumer-final-baseline-root-capture01-2026-10-03/REQUEST01.json','3d5481584c69034d696276431465064d01788e0fd651bdc8fe7df203bc52bf71');ck(q['capsule_manifest']==old['capsule_manifest'],'entire unchanged925 capsule');oldparent={r['path']:r for r in old['external_manifest']['members']};newparent={r['path']:r for r in q['external_manifest']['members']};ck(all(newparent.get(n)==r for n,r in oldparent.items()) and len(oldparent)==12 and len(newparent)==25,'all original12 preserved in25');added=set(newparent)-set(oldparent);ck(added==set(pre['added_files']) and len(added)==13 and all(newparent[n]['kind']=='file' and newparent[n]['mode']==0o600 for n in added),'exact13new regular600 bodies')
# Independent bounded raw framing, not tarfile extension iteration/extractall.
def decode(raw,manifest):
 stream=gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb');total=0;headers=0;pax=None;members=[];bodies={};pax_count=0
 def take(n):
  nonlocal total
  ck(type(n) is int and 0<=n<=a.FILE,'bounded requested bytes');parts=[]
  while n:
   b=stream.read(min(n,65536));ck(bool(b),'nontruncated frame');total+=len(b);ck(total<=192*1024**2,'inflated192MiB');parts.append(b);n-=len(b)
  return b''.join(parts)
 try:
  while True:
   header=take(512);headers+=1;ck(headers<=65538,'finite raw headers')
   if header==bytes(512):
    ck(pax is None and take(512)==bytes(512),'two block termination/no pendingPAX')
    while True:
     b=stream.read(65536)
     if not b:break
     total+=len(b);ck(total<=192*1024**2 and not any(b),'zero bounded final framing')
    break
   t=tarfile.TarInfo.frombuf(header,'utf-8','strict');kind=header[156:157];rawname=header[:100].split(b'\0')[0];ck(t.size>=0,'nonnegative body')
   if kind==tarfile.XHDTYPE:
    ck(t.name=='././@PaxHeader' and pax is None and t.size<=8192,'only one local bounded PAX');b=take(t.size);ck(not any(take((-t.size)%512)),'zeroPAXpadding');offset=0;fields={}
    while offset<len(b):
     end=b.find(b' ',offset);ck(offset<end<=offset+8 and b[offset:end].isdigit(),'PAXlength syntax');n=int(b[offset:end]);ck(n>end-offset+3 and offset+n<=len(b),'PAXlength bound');record=b[end+1:offset+n];ck(record.endswith(b'\n') and b'=' in record,'PAXfield frame');k,v=record[:-1].split(b'=',1);ck(k==b'path' and k not in fields,'unique path-onlyPAX');fields[k]=v.decode('utf-8');offset+=n
    ck(set(fields)=={b'path'},'PAX path exists');pax=fields[b'path'];pax_count+=1;continue
   ck(kind in (tarfile.REGTYPE,tarfile.AREGTYPE,tarfile.DIRTYPE) and t.type==kind,'only exact raw selected regular/directory type');name=pax if pax is not None else t.name;pax=None
   if kind==tarfile.DIRTYPE:
    ck(not rawname.endswith(b'//'),'raw directory no repeated terminal slash')
    if name.endswith('/'):name=name[:-1]
    ck(not name.endswith('/') and t.size==0,'one directory slash/zero body')
   else:ck(not rawname.endswith(b'/') and not name.endswith('/') and t.size<=a.FILE,'regular slash/extent')
   a.path_name(name);ck(name not in bodies,'no duplicate archive member');b=take(t.size);ck(not any(take((-t.size)%512)),'memberzero padding');r={'path':name,'kind':'directory' if kind==tarfile.DIRTYPE else 'file','mode':t.mode}
   if r['kind']=='file':r.update(bytes=len(b),sha256=sha(b))
   members.append(r);bodies[name]=b
  ck(members==manifest['members'],'entire ordered typed original manifest');return bodies,{'inflated_bytes':total,'headers':headers,'pax_headers':pax_count}
 finally:stream.close()
def recode(manifest,bodies):
 output=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in manifest['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:b=bodies[r['path']];t.size=len(b);tar.addfile(t,io.BytesIO(b))
 return output.getvalue()
results={};external_bodies=None
for role in ('capsule','external'):
 root=Path(q[role+'_root']);manifest=q[role+'_manifest'];ck(a.scan(root)==manifest,'complete original scope before '+role);saved=doc(P/'bundle01'/(role+'-manifest.json'),q[role+'_manifest_sha256']);ck(saved==manifest,'actual savedmanifest '+role);raw=a.read(P/'bundle01',role+'.tar.gz');info=receipt['archives'][role];ck(set(info)=={'bytes','sha256','manifest_sha256'} and len(raw)==info['bytes']<=a.FILE and sha(raw)==info['sha256'] and info['manifest_sha256']==q[role+'_manifest_sha256'],'archive receipt body '+role);bodies,stats=decode(raw,manifest)
 for r in manifest['members']:
  p=root/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'original member mode '+r['path'])
  if r['kind']=='file':ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and a.read(root,r['path'])==bodies[r['path']],'every original opaque body '+r['path'])
  else:ck(stat.S_ISDIR(s.st_mode),'original directory '+r['path'])
 ck(stat.S_IMODE(root.stat().st_mode)==manifest['root_mode'],'original rootmode '+role);ck(recode(manifest,bodies)==raw,'exact entire canonical compressedarchive '+role);ck(a.scan(root)==manifest,'complete original scope after '+role);results[role]={'manifest_sha256':q[role+'_manifest_sha256'],'archive_sha256':sha(raw),'compressed_bytes':len(raw),'members':len(manifest['members']),'regular_bodies':sum(r['kind']=='file' for r in manifest['members']),'logical_bytes':sum(r.get('bytes',0) for r in manifest['members']),'root_mode':manifest['root_mode'],**stats}
 if role=='external':external_bodies=bodies
ck(sum(r['members'] for r in results.values())==950,'full950 actualmembers');ck(sum(r['logical_bytes'] for r in results.values())<=a.BASE,'combined128MiBbound');ck(sha(external_bodies['request-final01.json'])=='bc482b1196e691d8a0a06e3c866a11877b8cf8556ef407e5d3da72743412e4d4' and sha(external_bodies['release-final01.json'])=='eeac08eef932caccea1346149ec8a7f7473de03e774e0285634a74ae71b8774f','exact current final request/release archived')
for row in pre['new13bodies']:
 ck(len(external_bodies[row['path']])==row['bytes'] and sha(external_bodies[row['path']])==row['sha256'],'newbody actualpin '+row['path'])
 if row['source'].startswith('research/'):
  p=Path.cwd()/row['source'];ck(a.read(p.parent,p.name)==external_bodies[row['path']],'exact independent sourcebody copy '+row['path'])
ck(set(p.name for p in (P/'bundle01').iterdir())=={'capture.json','capsule-manifest.json','external-manifest.json','capsule.tar.gz','external.tar.gz'},'exact five captured bundlefiles');ck(not any(n.split('.')[0] in {'numpy','torch','scipy'} for n in sys.modules),'no numerical imports')
r={'decision':'ACCEPTED_ACTUAL_NEW_FULL950_LOCAL_CAPTURE_ONLY','request_sha256':sha(a.encode(q)),'capture_sha256':sha(a.encode(receipt)),'actual_terminal_exit':terminal['exit'],'actual_elapsed_seconds':terminal['elapsed_seconds'],'capture':results,'new_parent_regular_bodies':13,'old_parent_members_preserved':12,'checks':len(checks),'final_request_sha256':pre['actual_final_request_sha256'],'final_release_sha256':pre['actual_final_release_sha256'],'ROOT_LAUNCH_HOLD':terminal['ROOT_LAUNCH_HOLD'],'restoration':False,'external_recovery':False,'native_or_research_authority':False};(O/'READBACK01.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');(O/'PINS01.json').write_text(json.dumps(bodypins,sort_keys=True,indent=2)+'\n');print(json.dumps(r,indent=2))
