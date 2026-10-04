import ast,copy,hashlib,json,os,stat,sys,types
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-recordfix-remote-correction02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
mraw=(P/'MANIFEST02.json').read_bytes();ck(sha(mraw)=='c2cd422d4aeb9e1f4185cfdf482767be4c56405553773326fb4c9247abc9f2db','exact candidate manifest');m=json.loads(mraw);ck({p.name for p in P.iterdir()}=={r['path'] for r in m['members']}|{'MANIFEST02.json'},'complete candidate membership')
for r in m['members']:
 p=P/r['path'];st=p.lstat();ck(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==r['mode'] and st.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'all candidate mode/type/bytes')
new=(P/'recover01.py').read_text();old=(P/'original-recover01.py').read_text();ck(sha(new.encode())=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','actual correction source');inverse=json.loads((P/'INVERSE02.json').read_bytes());back=new
for edit in reversed(inverse['edits']):ck(back.count(edit['new'])==1,'unique exact source inverse region');back=back.replace(edit['new'],edit['old'],1)
ck(back==old,'full byte inverse only declared correction')
nt=ast.parse(new);ot=ast.parse(old);nf={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)};of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)}
for n in ['git','main','validate_fixed_selection','require','digest','encode']:ck(ast.dump(nf[n],include_attributes=False)==ast.dump(of[n],include_attributes=False),'unchanged complete function AST '+n)
required=ast.literal_eval(next(n.value for n in nt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in n.targets)))
for name,pin in required.items():
 p=Path.cwd()/name;ck(p.is_file() and p.stat().st_size==pin['bytes'] and sha(p.read_bytes())==pin['sha256'],'all actual fixed capture bodies')
owned=O/'owned';owned.mkdir(mode=0o700)
def load(tree,new):
 names={'require','encode','write','_raise_retained','entry','validate_fixed_selection'};body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];g={'os':os,'json':json,'Path':Path,'FILE':4*1024**2,'HERE':owned,'CALLS':[],'REQUIRED':required};exec(compile(ast.Module(body=body,type_ignores=[]),'<exact extracted transport source>','exec'),g)
 if not new:
  block=next(n for n in tree.body if isinstance(n,ast.If));fun=ast.FunctionDef(name='entry',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=block.body,decorator_list=[]);exec(compile(ast.fix_missing_locations(ast.Module(body=[fun],type_ignores=[])),'<exact original entry>','exec'),g)
 return g
G=load(nt,True);OLD=load(ot,False);collision=owned/'FAILED01.json';collision.write_bytes(b'original reserved evidence');red=[]
for cls in [MemoryError,KeyboardInterrupt,SystemExit]:
 primary=cls('original fatal')
 def fail(primary=primary):raise primary
 for label,g in [('original',OLD),('corrected',G)]:
  g['main']=fail
  try:g['entry']()
  except BaseException as observed:
   expected=isinstance(observed,FileExistsError) if label=='original' else observed is primary;ck(expected,label+' real O_EXCL fatal witness '+cls.__name__);red.append({'source':label,'primary':cls.__name__,'observed':type(observed).__name__,'same_original':observed is primary})
  else:raise AssertionError('fatal swallowed')
ck(collision.read_bytes()==b'original reserved evidence','actual original collision bytes preserved')
classes=[ValueError,OSError,MemoryError,KeyboardInterrupt,SystemExit,BaseException];pairs=[]
for i,A in enumerate(classes):
 for j,B in enumerate(classes):
  primary=A('body');secondary=B('close');expected=primary if (isinstance(primary,MemoryError) or not isinstance(primary,Exception)) else secondary if (isinstance(secondary,MemoryError) or not isinstance(secondary,Exception)) else primary
  closed=[]
  def failwrite(fd,body):raise primary
  def close(fd):os.close(fd);closed.append(fd);raise secondary
  proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in ['O_WRONLY','O_CREAT','O_EXCL','O_NOFOLLOW','open','fsync']},write=failwrite,close=close);g=load(nt,True);g['os']=proxy
  try:g['write'](owned/('pair-'+str(i)+'-'+str(j)),b'x')
  except BaseException as observed:ck(observed is expected,'write exact fatal/ordinary identity '+str((i,j)))
  else:raise AssertionError('write error lost')
  ck(len(closed)==1,'actual FD close once')
  try:os.fstat(closed[0])
  except OSError:ck(True,'actual FD is closed')
  else:raise AssertionError('FD leaked')
  def main():raise primary
  def journal(path,body):raise secondary
  g=load(nt,True);g['main']=main;g['write']=journal
  try:g['entry']()
  except BaseException as observed:ck(observed is expected,'entry exact fatal/ordinary identity '+str((i,j)))
  else:raise AssertionError('entry error lost')
  pairs.append([A.__name__,B.__name__,type(expected).__name__])
g=load(nt,True);success=owned/'success';g['write'](success,b'opaque');ck(success.read_bytes()==b'opaque' and stat.S_IMODE(success.stat().st_mode)==0o600,'real successful write/readback0600')
errors=[]
valid={'remote_commit':'0'*40,'rows':[dict(path=n,**pin) for n,pin in sorted(required.items())]};g['validate_fixed_selection'](valid)
for label,change in [('missing_required',lambda q:q['rows'].pop()),('duplicate',lambda q:q['rows'].append(q['rows'][0])),('boolean_extent',lambda q:q['rows'][0].update(bytes=True)),('unsafe_path',lambda q:q['rows'][0].update(path='research/../bad')),('uppercase_hash',lambda q:q['rows'][0].update(sha256='A'*64)),('extra_schema',lambda q:q.update(extra=1))]:
 q=copy.deepcopy(valid);change(q)
 try:g['validate_fixed_selection'](q)
 except ValueError as error:errors.append({'case':label,'message':str(error)});ck(True,label+' actual schema refuses')
 else:raise AssertionError('schema admitted '+label)
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_NARROW_REMOTE_FATAL_CORRECTION_SOURCE_ONLY','checks':len(checks),'source_sha256':sha(new.encode()),'original_source_sha256':sha(old.encode()),'candidate_manifest_sha256':sha(mraw),'full_byte_inverse':True,'unchanged_git_main_selection_AST':True,'actual_collision_witness':red,'actual_write_and_entry_exception_pairs':pairs,'refusals':errors,'network_or_actual_recovery':False,'native_or_numerical_authority':False,'qualification':'Real exceptions and tiny actual owned FDs only. Allocation/OOM equivalence and runtime/capacity are not proved; unchanged Git kill/reap semantics reviewed as source, not a new actual process receipt.'}
(O/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['actual_write_and_entry_exception_pairs']},indent=2))
