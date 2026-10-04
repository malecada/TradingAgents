import gzip,hashlib,io,json,os,stat,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;ns={'__name__':'metadata','__file__':str(H/'capture_helpers01.py')};exec(compile((H/'capture_helpers01.py').read_text(),'candidate','exec'),ns)
measurements=[]
for scope,root in sorted(ns['SCOPES'].items()):
 members=[];files={};virtual=[]
 def visit(p,rel):
  st=p.lstat();row={'path':rel,'mode':stat.S_IMODE(st.st_mode)}
  if stat.S_ISLNK(st.st_mode):row.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(st.st_mode):
   row['kind']='directory'
   if rel!='.':virtual.append({'path':rel,'mode':448,'kind':'directory'})
   for c in sorted(p.iterdir()):visit(c,c.name if rel=='.' else rel+'/'+c.name)
  else:
   assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=4194304
   b=p.read_bytes();h=hashlib.sha256(b).hexdigest();row.update(kind='file',bytes=len(b),sha256=h,union_path=scope+'/'+rel);files[rel]=p;virtual.append({'path':rel,'mode':384,'kind':'file','bytes':len(b),'sha256':h})
  members.append(row)
 visit(root,'.');members.sort(key=lambda r:r['path']);tree={'scope':scope,'original_root':str(root),'members':members};metadata=ns['encoded']({'schema_version':1,'original_tree':tree,'source_commit':'0a2e7639b42b9423b90743feadcda4078aa21816','links_followed_or_extracted':False,'research_authority':False});assert 'CAPTURE_ORIGINAL_TREE01.json' not in files
 virtual.append({'path':'CAPTURE_ORIGINAL_TREE01.json','mode':384,'kind':'file','bytes':len(metadata),'sha256':hashlib.sha256(metadata).hexdigest()});virtual.sort(key=lambda r:r['path'])
 sink=io.BytesIO();gz=gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0);tar=tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT)
 for r in virtual:
  t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
  if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
  else:
   body=metadata if r['path']=='CAPTURE_ORIGINAL_TREE01.json' else files[r['path']].read_bytes();assert len(body)==r['bytes'] and hashlib.sha256(body).hexdigest()==r['sha256'];t.size=len(body);tar.addfile(t,io.BytesIO(body))
 tar.close();gz.close();raw=sink.getvalue();inflated=gzip.decompress(raw);assert len(raw)<=4194304
 offset=0;pending=False;cutoff_slashes=0
 while any(inflated[offset:offset+512]):
  header=inflated[offset:offset+512];info=tarfile.TarInfo.frombuf(header,'utf-8','strict');offset+=512
  if pending and info.type==tarfile.REGTYPE and header[:100].split(b'\0',1)[0].endswith(b'/'):cutoff_slashes+=1
  pending=info.type==tarfile.XHDTYPE;offset+=((info.size+511)//512)*512
 measurements.append({'scope':scope,'canonical_PAX_cutoff_slash_headers':cutoff_slashes,'original_members':len(members),'original_regular_bodies':len(files),'original_regular_bytes':sum(r.get('bytes',0) for r in members),'ordinary_members':len(virtual),'metadata_bytes':len(metadata),'exact_canonical_simulated_archive_bytes':len(raw),'exact_canonical_simulated_archive_sha256':hashlib.sha256(raw).hexdigest(),'actual_tar_bytes_including_headers_PAX_padding':len(inflated),'read_only_measurement_not_capture':True})
(H/'FEASIBILITY01.json').write_text(json.dumps(measurements,indent=2)+'\n');print(json.dumps(measurements))
