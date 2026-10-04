from pathlib import Path
import ast,json,hashlib,stat,os,importlib.util,sys,io,gzip,tarfile,copy
O=Path(__file__).resolve().parent;F=O.parent;T=F/'financial-wrapper-compatibility-operational-delta-flat-tooling01-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());checks=[]
def ck(n,v):
 assert v,n;checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,KeyError,TypeError,FileExistsError,FileNotFoundError,EOFError):checks.append(n)
 else:raise AssertionError(n)
man=J(T/'MANIFEST01.json');ck('author-seal',h((T/'MANIFEST01.json').read_bytes())=='13d6a12f3f57659416c4c189a39cebdfe0f3f1c0d438d78bb267fe147d2da30f')
expected=set()
for x in man['members']:
 p=T/x['path'];s=p.lstat();expected.add(x['path']);ck('mode:'+x['path'],stat.S_IMODE(s.st_mode)==x['mode'])
 if x['kind']=='file':ck('body:'+x['path'],stat.S_ISREG(s.st_mode) and s.st_nlink==x['nlink'] and s.st_size==x['bytes'] and h(p.read_bytes())==x['sha256'])
 elif x['kind']=='directory':ck('dir:'+x['path'],stat.S_ISDIR(s.st_mode))
 else:ck('literal-link:'+x['path'],stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target'])
actual={p.relative_to(T).as_posix() for p in T.rglob('*')};ck('complete-author-members',actual==expected|{'MANIFEST01.json'})
raw=(T/'restore01.py').read_text();ck('source-pin',h(raw.encode())=='b8c16007f3945e30d1a1a4889504f1ed5cfc77256f4c03f7cbd8a4a7ac28659d');inv=J(T/'SOURCE_INVERSE01.json');old=(T/'ORIGINAL_restore01.py').read_text();reb=raw
for e in reversed(inv['edits']):
 ck('inverse-segment',reb[e['new_start']:e['new_end']]==e['new']);reb=reb[:e['new_start']]+e['old']+reb[e['new_end']:]
ck('byte-AST-inverse',reb==old and ast.dump(ast.parse(reb))==ast.dump(ast.parse(old)))
spec=importlib.util.spec_from_file_location('independent_delta_flat',T/'restore01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
for n,pin in M.PINS.items():ck('dependency:'+n,h((T/n).read_bytes())==pin)
q={'remote_commit':'0'*40,'rows':[dict(path=n,**p) for n,p in sorted(M.REQUIRED.items())]};M.selection_rows(q)
for label,mut in [('missing',lambda q:q['rows'].pop()),('extra',lambda q:q['rows'].append(q['rows'][0])),('reorder',lambda q:q['rows'].reverse()),('hash',lambda q:q['rows'][0].update(sha256='0'*64)),('commit',lambda q:q.update(remote_commit=None))]:
 z=copy.deepcopy(q);mut(z);refuse('selection-'+label,lambda z=z:M.selection_rows(z))
refuse('absent-real-receipt',lambda:M.validate_remote({},q,'0'*64));refuse('null-hash',lambda:M.hexpin(None))
bundle=F/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';cap,m=M.load_capture(bundle);owned=O/'opaque03';owned.mkdir(mode=0o700);samples=[]
def boundary():samples.append(M.W.census(owned))
result=M.restore_delta(bundle,cap,m,owned,boundary);dest=owned/M.OUTPUT;meta=M.verify_flat(dest,result,cap,m,boundary);ck('actual-local41-33',len(m['members'])==41 and result['regular_bodies']==33)
buf=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=buf,mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as t:
  for x in m['members']:
   a=tarfile.TarInfo(x['path']);a.mode=x['mode'];a.uid=a.gid=a.mtime=0;a.uname=a.gname=''
   if x['kind']=='directory':a.type=tarfile.DIRTYPE;t.addfile(a)
   else:b=(dest/meta['flat_members'][x['path']]).read_bytes();ck('recovered-body:'+x['path'],len(b)==x['bytes'] and h(b)==x['sha256']);a.size=len(b);t.addfile(a,io.BytesIO(b))
ck('canonical-actual-flat-reencoding',buf.getvalue()==(bundle/'operational-delta01.tar.gz').read_bytes());refuse('fresh-output-replay',lambda:M.restore_delta(bundle,cap,m,owned,boundary))
# Extra private body cannot pass complete final mapping; remains retained.
(dest/'unexpected').write_bytes(b'opaque extra');refuse('extra-flat-body',lambda:M.verify_flat(dest,result,cap,m,boundary))
# Real FD cleanup is independently exercised against the pinned primitive.
for i,(primary,secondary) in enumerate([(ValueError('p'),MemoryError('c')),(MemoryError('p'),SystemExit('c')),(SystemExit('p'),MemoryError('c'))]):
 p=owned/f'fd-{i}';fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 def close(fd=fd,e=secondary):os.close(fd);raise e
 try:
  M.R._cleanup((close,),primary=primary)
  raise primary
 except BaseException as e:ck('fatal-fd:'+str(i),e is (primary if isinstance(primary,MemoryError) or not isinstance(primary,Exception) else secondary))
 else:raise AssertionError('fatal accepted')
 try:os.fstat(fd)
 except OSError:checks.append('fd-closed:'+str(i))
 else:raise AssertionError('fd retained')
# Tiny cap and malformed framing controls; no actual provenance receipt generated.
tiny=owned/'tiny';tiny.mkdir(mode=0o700);(tiny/'opaque').write_bytes(b'opaque\x00\xff');tm=M.R.scan(tiny);arc=owned/'tiny.gz';ai=M.R.pack(tiny,tm,arc);b=arc.read_bytes()
for label,body in [('truncated',b[:-4]),('trailing',b+b'x'),('magic',b'X'+b[1:])]:
 p=owned/(label+'.gz');p.write_bytes(body);d=owned/label;d.mkdir(mode=0o700);info=dict(ai,bytes=len(body),sha256=h(body))
 try:M.R.restore(p,info,tm,d)
 except Exception as e:checks.append('framing-'+label);(owned/(label+'-error.txt')).write_text(type(e).__name__+'\n')
 else:raise AssertionError(label)
read={'schema_version':1,'check_count':len(checks),'checks':checks,'source_sha256':h(raw.encode()),'author_manifest_sha256':h((T/'MANIFEST01.json').read_bytes()),'actual_local_archive_roundtrip':result,'observations':samples,'remote_receipt_created':False,'helper_entry_executed':False,'qualifications':['Actual owned local opaque41/33 roundtrip only','Byte/AST inverse verifies all changes; orchestration is new, not unchanged algorithm','Old385 plus failed-byte171 recovery remains separate mandatory composition','Sampled currentness/resource boundaries; no continuous quota or numerical authority']};(O/'FLAT_READBACK01.json').write_text(json.dumps(read,indent=2)+'\n');print('PASS',len(checks),'independent flat source/domain/refusal controls')
