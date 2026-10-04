import ast,copy,hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
import chunk_archive01 as N
D=Path(__file__).resolve().parent;T=D/'correction04';T.mkdir();checks=[];witness=[]
spec=importlib.util.spec_from_file_location('archive_old',D/'baseline-chunk_archive01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,OSError):checks.append(n);return
 raise AssertionError(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=T/'source';source.mkdir();(source/'directory').mkdir()
for i in range(130):(source/('empty-%03d'%i)).write_bytes(b'')
(source/'directory/opaque').write_bytes(b'z'*(N.CHUNK+19))
roots={'r':str(source)};oldcap=T/'old-archive';newcap=T/'new-archive';old_result=O.capture(roots,oldcap);new_result=N.capture(roots,newcap);check('full old/new capture framing byte-identical',old_result['index_sha256']==new_result['index_sha256'])
for p in oldcap.iterdir():check('unchanged archive artifact '+p.name,p.read_bytes()==(newcap/p.name).read_bytes())
indexhash=new_result['index_sha256'];flat=T/'flat';receipt=N.restore(newcap,indexhash,flat);check('two member and mapping pages',len(json.loads((flat/'index.json').read_bytes())['pages'])==2 and len(receipt['mapping_pages'])==2);check('standalone complete flat verifies',N.verify_flat(flat,indexhash)==receipt)
oldflat=T/'old-flat';O.restore(oldcap,indexhash,oldflat)
for p in oldflat.iterdir():check('unchanged valid flat body '+p.name,p.read_bytes()==(flat/p.name).read_bytes())
mutations={'version':('schema_version',2),'boolversion':('schema_version',True),'kind':('kind','unknown'),'authority':('native_or_research_authority',True),'cap':('reserved_whole_bytes',N.TOTAL+1),'negativecap':('reserved_whole_bytes',-1),'underreserve':('reserved_whole_bytes',1),'boolcount':('member_count',True),'wrongfilecount':('file_count',0),'qualification':('git_qualification','verified Git'),'rootanchorbool':None,'extrafield':None}
for label,edit in mutations.items():
 bad=T/('flat-'+label);shutil.copytree(flat,bad);index=json.loads((bad/'index.json').read_bytes())
 if label=='rootanchorbool':index['roots']['r']['anchor']['inode']=True
 elif label=='extrafield':index['unexpected']='not allowed'
 else:index[edit[0]]=edit[1]
 (bad/'index.json').write_bytes(N.encode(index));newhash=sha(bad/'index.json');r=json.loads((bad/'recovery.json').read_bytes());r['source_index_sha256']=newhash;r['roots']=index['roots'];(bad/'recovery.json').write_bytes(N.encode(r))
 old_outcome='accepted'
 try:O.verify_flat(bad,newhash)
 except (ValueError,KeyError,TypeError,OSError):old_outcome='refused'
 if label in ('version','kind','authority','cap'):check('CA1 RED original accepts '+label,old_outcome=='accepted')
 refuse('CA1 GREEN strict flat refuses '+label,lambda bad=bad,newhash=newhash:N.verify_flat(bad,newhash))
 refuse('CA1 shared archive policy refuses '+label,lambda index=index:N._index(index,N.encode(index)))
 witness.append({'id':'CA1','mutation':label,'old_result':old_outcome,'new_result':'refused','new_opaque_index_sha256':newhash,'qualification':'newly pinned synthetic counterexample; not a real external pin bypass'})
# Flat bodies also reproduce exact original chunk hashes, not just whole-file hashes.
bad=T/'flat-rehashed-chunk';shutil.copytree(flat,bad);idx=json.loads((bad/'index.json').read_bytes());page=idx['pages'][0];rows=json.loads((bad/page['name']).read_bytes());file_row=next(r for r in rows if r.get('chunks'));file_row['chunks'][0]['sha256']='0'*64;(bad/page['name']).write_bytes(N.encode(rows));page.update(bytes=(bad/page['name']).stat().st_size,sha256=sha(bad/page['name']));(bad/'index.json').write_bytes(N.encode(idx));newhash=sha(bad/'index.json');r=json.loads((bad/'recovery.json').read_bytes());r['source_index_sha256']=newhash;(bad/'recovery.json').write_bytes(N.encode(r))
check('CA1 RED original accepts freshly pinned wrong chunk hash',O.verify_flat(bad,newhash)['status']=='complete-flat-byte-recovery')
refuse('CA1 GREEN flat bytes enforce exact chunk hash',lambda:N.verify_flat(bad,newhash))
# Shared metadata framing gives both readers identical source-index/member checks.
validindex=json.loads((newcap/'index.json').read_bytes());pages=[json.loads(N.read_record(newcap,p)) for p in validindex['pages']]
for label,change in [('extra-page',lambda ps:ps.append([])),('missing-member',lambda ps:ps[-1].pop()),('duplicate-member',lambda ps:ps[0].__setitem__(1,copy.deepcopy(ps[0][0]))),('bad-mode',lambda ps:ps[0][0].update(mode=True)),('extra-field',lambda ps:ps[0][0].update(extra=1)),('traversal',lambda ps:ps[0][0].update(path='../escape'))]:
 altered=copy.deepcopy(pages);change(altered);refuse('shared member '+label,lambda altered=altered:N._members(validindex,altered))
# Explicit scheduling between exact source operations, not a timed race claim.
def schedule(module,name,stage):
 text=Path(module.__file__).read_text();fn=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='fresh');fn=copy.deepcopy(fn);fn.name='scheduled_fresh'
 callback=ast.Expr(value=ast.Call(func=ast.Name(id='switch_owned_parent',ctx=ast.Load()),args=[],keywords=[]))
 if module is O:
  pos=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='mkdir');fn.body.insert(pos,callback)
 else:
  tr=next(n for n in fn.body if isinstance(n,ast.Try))
  if stage=='before-traversal':tr.body.insert(0,callback)
  else:
   pos=next(i for i,n in enumerate(tr.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='mkdir');tr.body.insert(pos,callback)
 root=T/name;root.mkdir();parent=root/'parent';parent.mkdir();redirect=root/'redirect';redirect.mkdir();moved=root/'original-parent';target=parent/'child'
 def switch():parent.rename(moved);parent.symlink_to(redirect,target_is_directory=True)
 ns=dict(vars(module));ns['switch_owned_parent']=switch;exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'scheduled-exact-source-operations','exec'),ns)
 before=set(os.listdir('/proc/self/fd'));outcome='accepted'
 try:ns['scheduled_fresh'](parent,target)
 except (ValueError,OSError):outcome='refused'
 after=set(os.listdir('/proc/self/fd'));check('owned descriptor cleanup '+name,before==after)
 record={'id':'CA2','case':name,'stage':stage,'outcome':outcome,'redirected_child_exists':(redirect/'child').exists(),'original_owned_child_exists':(moved/'child').exists(),'qualification':'explicit scheduling of source operations on owned paths; no timing/active-root claim'};witness.append(record);return record
old=schedule(O,'old-substitution','before-mkdir');check('CA2 RED old writes redirected root before refusal',old['outcome']=='refused' and old['redirected_child_exists'] and not old['original_owned_child_exists'])
new=schedule(N,'new-before-traversal','before-traversal');check('CA2 GREEN pre-open substitution creates nowhere',new['outcome']=='refused' and not new['redirected_child_exists'] and not new['original_owned_child_exists'])
new=schedule(N,'new-after-anchor','before-mkdir');check('CA2 GREEN descriptor never creates redirected root',new['outcome']=='refused' and not new['redirected_child_exists'] and new['original_owned_child_exists'])
# The last retained child belongs to the original verified inode, never the
# substituted target. Namespace uncertainty remains a failure, with bytes kept.
inverse=json.loads((D/'INVERSE03.json').read_text());s=(D/'chunk_archive01.py').read_text()
for e in reversed(inverse['edits']):check('single exact inverse',s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
check('full byte inverse',s.encode()==(D/'baseline-chunk_archive01.py').read_bytes());check('full AST inverse',ast.dump(ast.parse(s))==ast.dump(ast.parse((D/'baseline-chunk_archive01.py').read_bytes())))
for k in ('FILE','CHUNK','TOTAL','FLOOR','ENTRIES','PAGE','SECONDS'):check('fixed original bound '+k,getattr(O,k)==getattr(N,k))
check('no numerical import',not any(k in sys.modules for k in ('numpy','torch','scipy')))
(D/'WITNESS04.json').write_text(json.dumps(witness,indent=2)+'\n');(D/'CORRECTION_CHECKS04.json').write_text(json.dumps({'count':len(checks),'checks':checks,'scope':'owned opaque records/paths only; source preparation and exact scheduled operations'},indent=2)+'\n');print(len(checks),'passed')
