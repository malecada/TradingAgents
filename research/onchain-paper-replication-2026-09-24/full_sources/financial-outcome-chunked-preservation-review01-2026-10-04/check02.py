"""Independent whole-pipeline opaque byte checks; no monkeypatch or live sources."""
import ast,copy,hashlib,importlib.util,json,os,shutil,stat,sys
from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'financial-outcome-chunked-preservation-preparation01-2026-10-04';REPO=B.parents[3];checks=[];witnesses=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def refuse(fn,label):
 try:fn()
 except (ValueError,FileNotFoundError,FileExistsError,NotADirectoryError,KeyError,TypeError):checks.append(label);return
 raise AssertionError('not refused: '+label)
def put(p,obj):p.write_bytes(m.encode(obj))
ok(sha(P/'MANIFEST01.json')=='fa7a9440bce0a81c38d8634e7738757d774412d225738d0fa3303870a37c2485','exact candidate manifest')
doc=json.loads((P/'MANIFEST01.json').read_text());entries=doc['entries'];ok({e['path'] for e in entries}=={p.relative_to(P).as_posix() for p in P.rglob('*')}-{'MANIFEST01.json'},'complete candidate membership')
for e in entries:
 p=P/e['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==e['mode'],'candidate member mode');ok(s.st_nlink==e['nlink'] if 'nlink' in e else True,'declared link count')
 if e['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==e['bytes'] and sha(p)==e['sha256'],'candidate body hash/extent')
 elif e['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'candidate directory')
 elif e['kind']=='symlink':ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==e['target'],'candidate symlink')
 else:raise AssertionError('unknown type')
pins=json.loads((P/'HELPER_PINS01.json').read_text())
for name,pin in pins['unchanged_helpers'].items():ok(sha(P/name)==pin and (P/name).read_bytes()==(REPO/pins['original_directory']/name).read_bytes(),'unchanged actual primitive '+name)
ok(sha(P/'chunk_archive01.py')=='315f3a3246bf196531c93b90c55041d806f9e4908cd12b72b8ae39228aad7e00','exact source pin')
sys.path.insert(0,str(P));spec=importlib.util.spec_from_file_location('review_chunk_archive',P/'chunk_archive01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ok((m.FILE,m.CHUNK,m.TOTAL,m.FLOOR,m.ENTRIES,m.PAGE,m.SECONDS)==(4*1024**2,1024**2,1024**3,10*1024**3,32768,128,1800),'fixed bounds unchanged')
root=B/'owned01';root.mkdir(mode=0o700);a=root/'source-a';a.mkdir(mode=0o750);b=root/'source-b';b.mkdir(mode=0o700)
(a/'empty').write_bytes(b'');(a/'empty-dir').mkdir();(a/'.git').mkdir();(a/'.git/HEAD').write_bytes(b'opaque Git bytes; not an object/ref proof\n');(a/'hidden').mkdir();(a/'hidden/.body').write_bytes(b'\x00\xffopaque\n')
payload=bytes(range(256))*4097;(a/'multi-chunk.bin').write_bytes(payload);os.chmod(a/'multi-chunk.bin',0o640)
for i in range(130):(b/('member-%03d'%i)).write_bytes(('opaque %d\n'%i).encode())
expected={label:{p.relative_to(path).as_posix():{'kind':'directory' if p.is_dir() else 'file','mode':stat.S_IMODE(p.lstat().st_mode),**({} if p.is_dir() else {'bytes':p.stat().st_size,'sha256':sha(p)})} for p in path.rglob('*')} for label,path in [('a',a),('b',b)]}
archive=root/'archive';captured=m.capture({'a':str(a),'b':str(b)},archive);index_hash=captured['index_sha256'];index,members=m.validate_archive(archive,index_hash,m.Bounds());ok(len(index['pages'])==2,'actual paged member manifest')
actual={label:{r['path']:{k:v for k,v in r.items() if k not in ('root','path')} for r in members if r['root']==label} for label in expected};ok(actual==expected,'complete independent root/file/directory/mode/hash reconstruction')
flat=root/'flat';receipt=m.restore(archive,index_hash,flat);ok(m.verify_flat(flat,index_hash)==receipt,'whole capture restore verify-flat success')
maprows=[r for p in receipt['mapping_pages'] for r in json.loads((flat/p['name']).read_bytes())];ok(len(receipt['mapping_pages'])==2,'actual paged flat mapping')
for r in maprows:ok((flat/r['body']).read_bytes()==({'a':a,'b':b}[r['root']]/r['path']).read_bytes(),'actual opaque source/flat byte equality')
page_rows=[r for p in index['pages'] for r in json.loads((archive/p['name']).read_bytes())];multi=next(r for r in page_rows if r['path']=='multi-chunk.bin');ok([r['bytes'] for r in multi['chunks']]==[m.CHUNK,256],'exact full 1MiB segmentation and final extent');ok(b''.join((archive/r['name']).read_bytes() for r in multi['chunks'])==payload,'ordered complete chunk reconstruction')
# Same complete index pin; flat verification does not need originals or archive.
a.rename(root/'source-a-retained');b.rename(root/'source-b-retained');archive.rename(root/'archive-retained');archive=root/'archive-retained';ok(m.verify_flat(flat,index_hash)==receipt,'fresh flat proves bytes independently of source/archive names')
# Existing destination, direct overlap and partial directory identities refuse.
refuse(lambda:m.capture({'a':str(root/'source-a-retained')},archive),'capture destination cannot reopen')
refuse(lambda:m.restore(archive,index_hash,flat),'restore destination cannot reopen')
refuse(lambda:m.capture({'a':str(root/'source-a-retained')},root/'source-a-retained'/'recursive'),'source-recursive destination refused')
partial=root/'partial';partial.mkdir();(partial/'intent.json').write_bytes(b'{}');refuse(lambda:m.validate_archive(partial,index_hash,m.Bounds()),'partial archive without index refused')
# Exact pinned archive mutation controls, restoring each owned opaque byte afterward.
for name in ('chunk-00000000.bin',index['pages'][0]['name'],'intent.json'):
 p=archive/name;original=p.read_bytes();p.write_bytes(original+b'x');refuse(lambda:m.validate_archive(archive,index_hash,m.Bounds()),'corrupt archive member '+name);p.write_bytes(original)
p=archive/'chunk-00000000.bin';temp=archive/'withheld-byte';p.rename(temp);refuse(lambda:m.validate_archive(archive,index_hash,m.Bounds()),'missing chunk refused');temp.rename(p)
(archive/'extra').write_bytes(b'opaque');refuse(lambda:m.validate_archive(archive,index_hash,m.Bounds()),'unexpected archive body refused');(archive/'extra').unlink()
# Changed self-consistent envelopes use NEW test pins only: no genuine pin is replaced.
original_index=(flat/'index.json').read_bytes();original_receipt=(flat/'recovery.json').read_bytes()
for key,value in [('reserved_whole_bytes',m.TOTAL+1),('kind','not-a-complete-index'),('native_or_research_authority',True),('schema_version',999)]:
 mutated=copy.deepcopy(index);mutated[key]=value;newraw=m.encode(mutated);newpin=m.sha(newraw);changed=copy.deepcopy(receipt);changed['source_index_sha256']=newpin;(flat/'index.json').write_bytes(newraw);put(flat/'recovery.json',changed)
 try:result=m.verify_flat(flat,newpin)
 except (ValueError,KeyError,TypeError):outcome='refused'
 else:outcome='accepted'
 cases={'mutated_field':key,'value':value,'index_hash_changed':True,'actual_status':outcome,'scope':'opaque caller-supplied new pin; no Root source/recovery pin or scientific authority'}
 if outcome=='accepted':witnesses.append({'id':'CA1','line':187,'detail':cases})
 (flat/'index.json').write_bytes(original_index);(flat/'recovery.json').write_bytes(original_receipt)
# Body/mapping corruption and extra failure marker refuse even after published receipt.
body=flat/maprows[0]['body'];original=body.read_bytes();body.write_bytes(original+b'x');refuse(lambda:m.verify_flat(flat,index_hash),'flat body extent/hash corruption');body.write_bytes(original)
(flat/'restore-failure.json').write_bytes(b'{"status":"failed"}');refuse(lambda:m.verify_flat(flat,index_hash),'post-completion failure marker refuses validation');(flat/'restore-failure.json').unlink()
# Fresh destination ownership step reconstruction, no monkeypatch: swap owned parent
# after exact anchored checks, before actual path-based mkdir from fresh().
parent=root/'fresh-parent';parent.mkdir();redirect=root/'redirect-parent';redirect.mkdir();target=parent/'destination';anchor=m.anchor(parent)
parent.rename(root/'fresh-parent-retained');parent.symlink_to('redirect-parent',target_is_directory=True)
try:
 target.mkdir();ok((redirect/'destination').is_dir(),'CA2 exact mkdir side effect redirected before parent recheck')
 refuse(lambda:m.check_anchor(parent,anchor),'CA2 later anchor check refuses after foreign-target creation')
 witnesses.append({'id':'CA2','line':86,'detail':'Actual path-based mkdir created destination in a different owned root after anchored parent rename/symlink substitution; subsequent anchor check refused only after side effect. Exact fresh() operations scheduled explicitly, not a timed full-call race or monkeypatch.'})
finally:parent.unlink()
# Bounded write gate can be exercised with real opaque bytes, no numerical arrays.
owned=root/'write-bound';owned.mkdir();bounds=m.Bounds();bounds.anchors[owned]=m.anchor(owned);refuse(lambda:m._write(owned,'over.bin',b'x'*(m.FILE+1),bounds),'4MiB output limit before file creation');ok(not (owned/'over.bin').exists(),'no oversized partial output')
# IO helper callback semantics, without patching its accepted implementation.
from owned_io import _cleanup,CleanupFailure
for primary_type in (OSError,MemoryError,KeyboardInterrupt,SystemExit):
 for cleanup_type in (OSError,MemoryError,KeyboardInterrupt,SystemExit):
  primary=primary_type('primary');secondary=cleanup_type('cleanup');calls=[]
  def bad():calls.append(1);raise secondary
  try:
   try:raise primary
   finally:_cleanup((bad,lambda:calls.append(2)))
  except BaseException as got:
   expected=primary if isinstance(primary,(MemoryError,KeyboardInterrupt,SystemExit)) else secondary if isinstance(secondary,(MemoryError,KeyboardInterrupt,SystemExit)) else None
   ok((got is expected) if expected is not None else isinstance(got,CleanupFailure),'accepted primitive first-fatal/uncertainty semantics')
  ok(calls==[1,2],'all primitive cleanup callbacks attempted')
# No mutation to source/helper constants or files.
for name,pin in pins['unchanged_helpers'].items():ok(sha(P/name)==pin,'helper remained unchanged '+name)
(B/'candidate-source.py').write_bytes((P/'chunk_archive01.py').read_bytes())
(B/'CHECKS02.json').write_text(json.dumps({'status':'controls-completed-with-source-blockers','checks':len(checks),'labels':checks,'witnesses':witnesses,'actual_capture':captured,'actual_flat_receipt':receipt,'not_authority':True,'scope':'Actual whole pipeline on owned opaque bytes; no live outcome/native/numerical/Git/network/Run. CA1 explicitly changes test pin; CA2 exact operation scheduling, not observed uninstrumented concurrency.'},sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'witnesses':witnesses}))
