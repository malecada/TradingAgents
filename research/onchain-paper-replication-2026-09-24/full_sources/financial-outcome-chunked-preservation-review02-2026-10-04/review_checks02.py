"""Independent opaque controls. Source AST scheduling is explicit, not a timed race."""
import ast,copy,hashlib,importlib.util,json,os,shutil,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'authenticated-source';P=D.parent/'financial-outcome-chunked-preservation-preparation02-2026-10-04';T=D/'owned02';T.mkdir();sys.path.insert(0,str(S))
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,S/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
N=load('review_new','chunk_archive01.py');O=load('review_old','baseline-chunk_archive01.py');checks=[];witness=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(n,v,detail=None):
 if not v:raise AssertionError(n)
 checks.append({'name':n,'detail':detail})
def refuse(n,f):
 try:f()
 except (ValueError,TypeError,KeyError,OSError) as e:check(n,True,{'type':type(e).__name__,'message':str(e)});return e
 raise AssertionError('unexpected acceptance: '+n)
def dump(n,o):(D/n).write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
check('declared candidate manifest pin',sha(P/'MANIFEST02.json')=='1f75f48e5f7dcfd5cfcfafff98ec4e7a94308ca6461d533af8e952b751208b92')
check('declared candidate source pin',sha(S/'chunk_archive01.py')=='c7ea8fe3c92e42b78a06412fee6cb88bd5323099fd28ebf54e0f195e7eaa53c8')
manifest=json.loads((P/'MANIFEST02.json').read_text());actual={p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST02.json'}
check('complete candidate manifest membership',actual=={r['path'] for r in manifest['entries']})
for r in manifest['entries']:
 p=P/r['path'];s=p.lstat();good=stat.S_IMODE(s.st_mode)==r['mode']
 if r['type']=='file':good=good and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p)==r['sha256']
 elif r['type']=='directory':good=good and stat.S_ISDIR(s.st_mode)
 elif r['type']=='symlink':good=good and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
 else:good=False
 check('candidate member '+r['path'],good)
for r in json.loads((S/'ORIGINS02.json').read_text()):check('actual origin '+r['path'],sha(Path(r['path']))==r['sha256'])
helper=json.loads((S/'HELPER_PINS01.json').read_text())
for name,pin in helper['unchanged_helpers'].items():
 check('helper exact actual '+name,sha(S/name)==pin==sha(P/name)==sha(Path(helper['original_directory'])/name))
check('original body actual equality',(S/'baseline-chunk_archive01.py').read_bytes()==(P.parent/'financial-outcome-chunked-preservation-preparation01-2026-10-04/chunk_archive01.py').read_bytes())
source=(S/'chunk_archive01.py').read_text();inverse=json.loads((S/'INVERSE03.json').read_text());restored=source
for e in reversed(inverse['edits']):check('inverse single seam '+str(len(checks)),restored.count(e['new'])==1);restored=restored.replace(e['new'],e['old'])
check('full exact byte inverse',restored.encode()==(S/'baseline-chunk_archive01.py').read_bytes())
check('full exact AST inverse',ast.dump(ast.parse(restored))==ast.dump(ast.parse((S/'baseline-chunk_archive01.py').read_text())))
for k in ('FILE','CHUNK','TOTAL','FLOOR','ENTRIES','PAGE','SECONDS','FINAL_REVIEW'):check('unchanged bounds/withheld '+k,getattr(N,k)==getattr(O,k))
# Entire two-page workload includes empty directories, zero-length files, modes,
# a 2MiB+18 body and opaque Git-like bytes without invoking Git.
r=T/'source';r.mkdir();(r/'empty-dir').mkdir();(r/'.git').mkdir();(r/'.git/opaque').write_bytes(b'not a Git object\n');(r/'data').mkdir()
for i in range(130):(r/'data'/('tiny-%03d'%i)).write_bytes(('opaque-%03d'%i).encode())
(r/'zero').write_bytes(b'');(r/'data/tiny-000').chmod(0o640);(r/'large').write_bytes(b'abcdef01'*(N.CHUNK//4)+b'opaque-last-block!')
roots={'opaque':str(r)};oc=T/'archive-old';nc=T/'archive-new';a=O.capture(roots,oc);b=N.capture(roots,nc)
check('valid actual old/new index equality',a['index_sha256']==b['index_sha256'])
for p in oc.iterdir():check('valid archive artifact equality '+p.name,p.read_bytes()==(nc/p.name).read_bytes())
of=T/'flat-old';nf=T/'flat-new';oldreceipt=O.restore(oc,a['index_sha256'],of);receipt=N.restore(nc,b['index_sha256'],nf)
check('full valid receipt equality',oldreceipt==receipt)
for p in of.iterdir():check('valid flat artifact equality '+p.name,p.read_bytes()==(nf/p.name).read_bytes())
check('new actual standalone verifier',N.verify_flat(nf,b['index_sha256'])==receipt)
idx=json.loads((nc/'index.json').read_bytes());pages=[json.loads((nc/p['name']).read_bytes()) for p in idx['pages']]
check('two member and mapping pages',len(pages)==2 and len(receipt['mapping_pages'])==2)
large=next(x for ps in pages for x in ps if x['path']=='large');check('exact 1MiB framing with tail', [c['bytes'] for c in large['chunks']]==[N.CHUNK,N.CHUNK,len(b'opaque-last-block!')])
for page in receipt['mapping_pages']:
 for row in json.loads((nf/page['name']).read_bytes()):check('independent original byte and logical mode '+row['path'],(nf/row['body']).read_bytes()==(r/row['path']).read_bytes() and row['mode']==stat.S_IMODE((r/row['path']).stat().st_mode))
r.rename(T/'preserved-source');nc.rename(T/'preserved-archive');check('standalone verifier after source/archive relocation',N.verify_flat(nf,b['index_sha256'])==receipt)
# Tiny complete trees for exact malformed-envelope paired readers.
s=T/'small-source';s.mkdir();(s/'dir').mkdir();(s/'dir/body').write_bytes(b'opaque');sc=T/'small-archive';sr=N.capture({'s':str(s)},sc);sf=T/'small-flat';N.restore(sc,sr['index_sha256'],sf)
si=json.loads((sc/'index.json').read_bytes());sp=[json.loads((sc/p['name']).read_bytes()) for p in si['pages']]
mutations={
 'version':lambda x:x.update(schema_version=2),'boolversion':lambda x:x.update(schema_version=True),'kind':lambda x:x.update(kind='other'),'authority':lambda x:x.update(native_or_research_authority=True),'nullauthority':lambda x:x.update(native_or_research_authority=None),'cap':lambda x:x.update(reserved_whole_bytes=N.TOTAL+1),'underreserve':lambda x:x.update(reserved_whole_bytes=0),'qualification':lambda x:x.update(git_qualification='verified Git objects'),'flatclaim':lambda x:x.update(flat_qualification='restored POSIX'),
 'rootempty':lambda x:x.update(roots={}), 'overroots':lambda x:x.update(roots={str(i):{'path':str(T/('absent'+str(i))),'anchor':{'device':0,'inode':0,'mode':0}} for i in range(5)}),'overlap':lambda x:x['roots'].update(other=copy.deepcopy(x['roots']['s'])),'rootrelative':lambda x:x['roots']['s'].update(path='relative'), 'rootanchorbool':lambda x:x['roots']['s']['anchor'].update(inode=True),'rootmode':lambda x:x['roots']['s']['anchor'].update(mode=0o10000),'extrafield':lambda x:x.update(extra=1),'pagehash':lambda x:x['pages'][0].update(sha256='z'*64),'pagetype':lambda x:x['pages'][0].update(bytes=True),'pageorder':lambda x:x['pages'][0].update(name='page-00001.json')}
for key in ('member_count','file_count','logical_bytes','reserved_whole_bytes','chunk_count','chunk_bytes'):
 mutations['bool-'+key]=lambda x,key=key:x.update({key:True})
 mutations['negative-'+key]=lambda x,key=key:x.update({key:-1})
for key in si:mutations['missing-'+key]=lambda x,key=key:x.pop(key)
for label,change in mutations.items():
 bad=copy.deepcopy(si);change(bad);ac=T/('malformed-archive-'+label);fl=T/('malformed-flat-'+label);shutil.copytree(sc,ac);shutil.copytree(sf,fl);raw=N.encode(bad);pin=N.sha(raw)
 for target in (ac,fl):(target/'index.json').write_bytes(raw)
 recovery=json.loads((fl/'recovery.json').read_bytes());recovery['source_index_sha256']=pin
 if 'roots' in bad:recovery['roots']=bad['roots']
 (fl/'recovery.json').write_bytes(N.encode(recovery))
 if label in ('version','kind','authority','cap'):
  check('CA1 exact RED old flat accepts '+label,O.verify_flat(fl,pin)['status']=='complete-flat-byte-recovery')
  witness.append({'case':'CA1 '+label,'old':'accepted','new':'refused','index_sha256':pin,'qualification':'fresh opaque pin, not authentic Root pin bypass'})
 refuse('shared archive malformed '+label,lambda ac=ac,pin=pin:N.validate_archive(ac,pin,N.Bounds()))
 refuse('shared flat malformed '+label,lambda fl=fl,pin=pin:N.verify_flat(fl,pin))
# Noncanonical raw framing must fail even though the supplied opaque pin matches.
for reader,original in (('archive',sc),('flat',sf)):
 bad=T/('noncanonical-'+reader);shutil.copytree(original,bad);raw=json.dumps(si,indent=3).encode();(bad/'index.json').write_bytes(raw)
 refuse('canonical framing '+reader,lambda bad=bad,reader=reader:N.validate_archive(bad,N.sha(raw),N.Bounds()) if reader=='archive' else N.verify_flat(bad,N.sha(raw)))
member_mutations={
 'unknownroot':lambda ps:ps[0][0].update(root='absent'),'traversal':lambda ps:ps[0][0].update(path='../x'),'modebool':lambda ps:ps[0][0].update(mode=True),'modeoverflow':lambda ps:ps[0][0].update(mode=0o10000),'duplicate':lambda ps:ps[0].__setitem__(1,copy.deepcopy(ps[0][0])),'order':lambda ps:ps[0].reverse(),'missingparent':lambda ps:ps[0][0].update(path='unused'),'extrafield':lambda ps:ps[0][1].update(extra=0),'fileoversize':lambda ps:ps[0][1].update(bytes=N.FILE+1),'filebool':lambda ps:ps[0][1].update(bytes=True),'chunkmissing':lambda ps:ps[0][1].update(chunks=[]),'chunkduplicate':lambda ps:ps[0][1]['chunks'].append(copy.deepcopy(ps[0][1]['chunks'][0])),'chunkname':lambda ps:ps[0][1]['chunks'][0].update(name='chunk-00000001.bin'),'chunkextent':lambda ps:ps[0][1]['chunks'][0].update(bytes=5),'chunkbool':lambda ps:ps[0][1]['chunks'][0].update(bytes=True),'hashmalformed':lambda ps:ps[0][1]['chunks'][0].update(sha256='A'*64)}
for label,change in member_mutations.items():
 pagesbad=copy.deepcopy(sp);change(pagesbad);refuse('pure complete member framing '+label,lambda pagesbad=pagesbad:N._members(si,pagesbad))
# Actual false chunk hash accepted by old flat but refused by both new readers.
for reader,original in (('archive',sc),('flat',sf)):
 bad=T/('false-chunk-'+reader);shutil.copytree(original,bad);bi=copy.deepcopy(si);bp=copy.deepcopy(sp);bp[0][1]['chunks'][0]['sha256']='0'*64;raw=N.encode(bp[0]);(bad/bi['pages'][0]['name']).write_bytes(raw);bi['pages'][0].update(bytes=len(raw),sha256=N.sha(raw));raw=N.encode(bi);(bad/'index.json').write_bytes(raw);pin=N.sha(raw)
 if reader=='flat':
  rr=json.loads((bad/'recovery.json').read_bytes());rr['source_index_sha256']=pin;(bad/'recovery.json').write_bytes(N.encode(rr));check('old false chunk RED',O.verify_flat(bad,pin)['status']=='complete-flat-byte-recovery');refuse('new flat false chunk GREEN',lambda:N.verify_flat(bad,pin))
 else:refuse('new archive false chunk GREEN',lambda:N.validate_archive(bad,pin,N.Bounds()))
# Missing and extra opaque artifacts, direct corruption, symlinks and oversize.
for label,mutate in [('missing',lambda p:(p/'body-00000000.bin').unlink()),('extra',lambda p:(p/'unclaimed').write_bytes(b'x')),('corrupt',lambda p:(p/'body-00000000.bin').write_bytes(b'changed')),('symlink',lambda p:((p/'body-00000000.bin').unlink(),(p/'body-00000000.bin').symlink_to(s/'dir/body')))]:
 bad=T/('artifact-'+label);shutil.copytree(sf,bad);mutate(bad);refuse('actual flat artifact '+label,lambda bad=bad:N.verify_flat(bad,sr['index_sha256']))
large_source=T/'oversize-source';large_source.mkdir()
with (large_source/'body').open('wb') as f:f.truncate(N.FILE+1)
refuse('oversized original source',lambda:N.capture({'opaque':str(large_source)},T/'oversize-archive'));check('oversize refuses before archive creation',not (T/'oversize-archive').exists())
out=T/'write-bounds';out.mkdir();bounds=N.Bounds();bounds.anchors[out]=N.anchor(out);refuse('oversized output',lambda:N._write(out,'oversize',b'x'*(N.FILE+1),bounds));check('oversize no partial file',not (out/'oversize').exists())
# Exact operation scheduling; no module monkeypatch or altered helper constants.
def function(module,name):return copy.deepcopy(next(n for n in ast.parse(Path(module.__file__).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name))
def compiled(fn,module,extras):
 ns=dict(vars(module));ns.update(extras);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<independent-exact-source-schedule>','exec'),ns);return ns[fn.name]
def event():return ast.Expr(value=ast.Call(func=ast.Name(id='review_event',ctx=ast.Load()),args=[],keywords=[]))
def fdcensus():return set(os.listdir('/proc/self/fd'))
for label,module,stage in [('old',O,'mkdir'),('new-before',N,'traverse'),('new-after',N,'mkdir')]:
 root=T/('rename-'+label);root.mkdir();parent=root/'parent';parent.mkdir();replacement=root/'replacement';replacement.mkdir();retained=root/'retained';fn=function(module,'fresh')
 seq=fn.body if module is O else next(n for n in fn.body if isinstance(n,ast.Try)).body
 pos=0 if stage=='traverse' else next(i for i,n in enumerate(seq) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='mkdir')
 seq.insert(pos,event())
 def switch():parent.rename(retained);parent.symlink_to(replacement,target_is_directory=True)
 f=compiled(fn,module,{'review_event':switch});before=fdcensus();refuse('CA2 namespace refusal '+label,lambda:f(parent,parent/'child'));check('CA2 all descriptor cleanup '+label,fdcensus()==before)
 expected=(label=='old',label=='new-after');observed=((replacement/'child').exists(),(retained/'child').exists());check('CA2 exact side-effect location '+label,observed==expected);witness.append({'case':'CA2 '+label,'redirected_child':observed[0],'retained_original_child':observed[1],'outcome':'refused','scheduling':'inserted event between exact source operations; no timed race claim'})
# Fresh actual descriptor cleanup for every body/close error pair. Each injected
# close executes os.close exactly once before raising; secondary errors are real.
classes=(OSError,MemoryError,KeyboardInterrupt,SystemExit)
for i,pc in enumerate(classes):
 for j,cc in enumerate(classes):
  parent=T/('fd-cleanup-%d-%d'%(i,j));parent.mkdir();primary=pc('review body');secondary=[];closed=[];fn=function(N,'fresh');tr=next(n for n in fn.body if isinstance(n,ast.Try));pos=next(i for i,n in enumerate(tr.body) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='fstat' and isinstance(n.value.args[0],ast.Name) and n.value.args[0].id=='child');tr.body.insert(pos,event())
  class Rewriter(ast.NodeTransformer):
   def visit_Call(self,node):
    node=self.generic_visit(node)
    if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='os' and node.func.attr=='close':node.func=ast.Name(id='review_close',ctx=ast.Load())
    return node
  fn=Rewriter().visit(fn)
  def throw():raise primary
  def close(fd):
   os.close(fd);closed.append(fd);error=cc('review close '+str(len(closed)));secondary.append(error);raise error
  f=compiled(fn,N,{'review_event':throw,'review_close':close});before=fdcensus();observed=None
  try:f(parent,parent/'child')
  except BaseException as e:observed=e
  fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
  expected=primary if fatal(primary) else secondary[0] if fatal(secondary[0]) else None
  check('first fatal precedence '+str((i,j)),observed is expected if expected else type(observed).__name__=='CleanupFailure')
  check('every fd attempted once '+str((i,j)),len(closed)==len(parent.parts)+1 and len(set(closed))==len(closed) and fdcensus()==before)
  check('actual partial child retained '+str((i,j)),(parent/'child').is_dir())
# Capture mutation immediately after actual intent write must leave failed partial
# evidence, never a complete index. Instrument only the exact caller statement.
changed=T/'changed-source';changed.mkdir();(changed/'body').write_bytes(b'initial opaque');fn=function(N,'capture');tr=next(n for n in fn.body if isinstance(n,ast.Try));position=next(i for i,n in enumerate(tr.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='_write');tr.body.insert(position+1,event())
def mutate_source():(changed/'body').write_bytes(b'actual changed opaque')
f=compiled(fn,N,{'review_event':mutate_source});failed=T/'changed-archive';refuse('actual source change after intent',lambda:f({'s':str(changed)},failed));check('failure receipt retained without complete index',(failed/'capture-failure.json').is_file() and (failed/'intent.json').is_file() and not (failed/'index.json').exists())
check('no numerical imports',not any(x in sys.modules for x in ('numpy','torch','scipy')))
dump('WITNESSES02.json',witness);dump('CHECKS02.json',{'count':len(checks),'checks':checks,'candidate_sha256':sha(S/'chunk_archive01.py'),'candidate_manifest_sha256':sha(P/'MANIFEST02.json'),'author_manifest_files':sum(r['type']=='file' for r in manifest['entries']),'author_manifest_bytes':sum(r.get('bytes',0) for r in manifest['entries']),'scope':'Independent actual opaque stdlib pipeline, metadata/schema mutations and explicitly scheduled extracted source operations; no numerical/native/network/Git execution','not_tested':['live outcome','100 epoch capacity','near bound storage behavior','concurrent uninstrumented race stress','POSIX/Git restoration','actual remote recovery'],'authority':None})
print(json.dumps({'checks':len(checks),'source':sha(S/'chunk_archive01.py'),'author_manifest_members':len(manifest['entries'])}))
