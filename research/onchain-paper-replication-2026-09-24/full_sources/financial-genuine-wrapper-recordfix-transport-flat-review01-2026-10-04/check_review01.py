"""Independent opaque source/scope/pipeline review, with inherited fatal witness."""
import ast,copy,hashlib,importlib.util,itertools,json,os,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent;checks=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,TypeError,KeyError,OSError):ok(n,True);return
 raise AssertionError('accepted '+n)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
def write(n,o):(D/n).write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
expected={'remote':('54b5b7028a1fb22fcffa9f24bf77314d042aa106a5f78a97f3021b13286a210f','78c07fcf2b96fba04573bfeb097b7cbc3b55260f7d8703e5a37043329fd0d56a','recover01.py'),'flat':('b5c775a24e19c97cf0ef032a7598347689b8dfc27de5e273bccbe5710d9d519d','ea35a2f4baf6014a333d620d26d7695ad82c80ea3ff7584cf4fa1509e3229b37','restore01.py')}
for kind,(sourcepin,manifestpin,source) in expected.items():
 P=B/('financial-genuine-wrapper-recordfix-'+kind+'-preparation01-2026-10-04');S=D/(kind+'-source');ok(kind+' exact source',sha(S/source)==sourcepin);ok(kind+' manifest',sha(P/'MANIFEST01.json')==manifestpin)
 m=json.loads((P/'MANIFEST01.json').read_text());ok(kind+' full members',{p.relative_to(P).as_posix() for p in P.rglob('*') if p!=P/'MANIFEST01.json'}=={r['path'] for r in m['members']})
 for row in m['members']:
  p=P/row['path'];q=S/row['path'];s=p.lstat();valid=stat.S_IMODE(s.st_mode)==row['mode']==stat.S_IMODE(q.lstat().st_mode)
  if row['kind']=='file':valid=valid and stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and sha(p)==sha(q)==row['sha256']
  else:valid=valid and p.is_dir() and q.is_dir()
  ok(kind+' manifest '+row['path'],valid)
 text=(S/source).read_text();inverse=text;edits=json.loads((S/'INVERSE01.json').read_text())['edits']
 for i,e in enumerate(reversed(edits)):
  if kind=='flat':ok('flat inverse offset '+str(i),inverse[e['new_start']:e['new_end']]==e['new']);inverse=inverse[:e['new_start']]+e['old']+inverse[e['new_end']:]
  else:ok('remote inverse unique '+str(i),inverse.count(e['new'])==1);inverse=inverse.replace(e['new'],e['old'])
 old=S/('original-remote04.py' if kind=='remote' else 'original-restore04.py');ok(kind+' complete byte inverse',inverse==old.read_text());ok(kind+' complete AST inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old.read_text())))
sys.path.insert(0,str(D/'flat-source'));F=load('independent_flat',D/'flat-source/restore01.py');M=load('independent_remote',D/'remote-source/recover01.py');R=F.R
for n,h in F.PINS.items():ok('genuine unchanged R4 '+n,sha(D/'flat-source'/n)==h)
capture=B/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04';body={n:(capture/n).read_bytes() for n in F.EXPECTED}
for n,pin in F.EXPECTED.items():ok('actual frozen capture bytes '+n,len(body[n])==pin['bytes'] and hashlib.sha256(body[n]).hexdigest()==pin['sha256'] and M.REQUIRED[F.REL+'/'+n]==pin)
m,a,t=F.joins(body);ok('whole current metadata986713',len(m['members'])==986 and sum(r['kind']=='file' for r in m['members'])==713);ok('full source3253248',len(a['git_entries'])==325 and a['selected']==324 and len(a['role_hashes'])==8)
by={r['path']:r for r in m['members']};ok('all325 tracked in full manifest',set(a['git_entries'])<=set(by))
for n,(mode,oid) in a['git_entries'].items():ok('tracked mode in captured metadata '+n,by[n]['kind']=='file' and mode in ('100644','100755') and bool(by[n]['mode']&0o111)==(mode=='100755'))
for n,pin in a['role_hashes'].items():ok('all eight actual input manifest hashes '+n,by[n]['sha256']==pin)
for file,key,val in [('terminal.json','status','FAILED'),('terminal.json','runtime_bodies',True),('terminal.json','scientific_credit',1),('terminal.json','external_recovery',True),('terminal.json','error_type','OSError'),('terminal.json','observed_free_bytes',[0]*4),('source-authentication.json','tracked',324),('source-authentication.json','selected',323),('source-authentication.json','implementation',193),('source-authentication.json','package',148),('source-authentication.json','runtime_record_metadata_count',250),('source-authentication.json','changed',[]),('ACTUAL_TERMINAL02.json','actual_exit',1),('ACTUAL_TERMINAL02.json','native_or_numerical_claim_started',True)]:
 changed=dict(body);v=json.loads(changed[file]);v[key]=val;changed[file]=R.encode(v);refuse('capture contradiction '+file+'/'+key,lambda changed=changed:F.joins(changed))
q=json.loads((D/'remote-source/SELECTION_DRAFT01.json').read_text());M.validate_fixed_selection(q);ok('six required rows and unbound commit',len(q['rows'])==6 and q['remote_commit'] is None)
for i in range(6):
 for key,val in [('bytes',0),('sha256','0'*64),('path','research/wrong')]:
  z=copy.deepcopy(q);z['rows'][i][key]=val;refuse('required row mutation '+str(i)+'/'+key,lambda z=z:M.validate_fixed_selection(z))
for path in ('../escape','/absolute','research//bad','research/a/../b','research/./x'):
 z=copy.deepcopy(q);z['rows'].append({'path':path,'bytes':1,'sha256':'a'*64});refuse('unsafe path '+path,lambda z=z:M.validate_fixed_selection(z))
z=copy.deepcopy(q);z['rows'].append(z['rows'][0]);refuse('duplicate row',lambda:M.validate_fixed_selection(z))
for count in (506,507):
 z=copy.deepcopy(q);z['rows'] += [{'path':'research/opaque/'+str(i),'bytes':0,'sha256':hashlib.sha256(b'').hexdigest()} for i in range(count-6)]
 if count==506:M.validate_fixed_selection(z);ok('506 count fits1023 ops',11+2*count==1023)
 else:refuse('507 exceeds calls bound',lambda:M.validate_fixed_selection(z))
for value in (-1,True,M.FILE+1):
 z=copy.deepcopy(q);z['rows'][0]['bytes']=value;refuse('perbody extent '+repr(value),lambda z=z:M.validate_fixed_selection(z))
request=json.loads((D/'flat-source/REQUEST_TEMPLATE01.json').read_text());refuse('flat null request refused',lambda:F.validate_request(request));ok('all future authority null',all(request[k] is None for k in ('remote_root','remote_receipt_sha256','review','release')))
# Exact existing primitives, fresh opaque utility tree with the complete shape denominator.
owned=D/'owned01';owned.mkdir();src=owned/'source';src.mkdir()
for i in range(273):(src/('d'+str(i).zfill(3))).mkdir(mode=0o700)
for i in range(713):
 p=src/('d'+str(i%273).zfill(3))/('f'+str(i).zfill(4));p.write_bytes(('opaque independent body '+str(i)).encode());p.chmod(0o600 if i%2 else 0o640)
tiny=R.scan(src);ok('owned full-shape986713',len(tiny['members'])==986 and sum(r['kind']=='file' for r in tiny['members'])==713);info=R.pack(src,tiny,owned/'opaque.tar.gz');dest=owned/'flat';dest.mkdir(mode=0o700);result=R.restore(owned/'opaque.tar.gz',info,tiny,dest);ok('complete713 plus metadata714 files',result['members']==986 and result['regular_bodies']==713 and len(list(dest.iterdir()))==714 and result['instantiated_posix_tree'] is False)
metadata=json.loads(R.read(dest,result['metadata_file']));ok('all modes and directories retained',metadata['manifest']==tiny and len(metadata['flat_members'])==713)
for name,leaf in metadata['flat_members'].items():ok('opaque recovered '+name,R.read(dest,leaf)==R.read(src,name) and stat.S_IMODE((dest/leaf).stat().st_mode)==0o600)
refuse('fresh output required',lambda:R.restore(owned/'opaque.tar.gz',info,tiny,dest))
empty=owned/'wrong-binding';empty.mkdir(mode=0o700);refuse('archive hash corrupt',lambda:R.restore(owned/'opaque.tar.gz',dict(info,sha256='0'*64),tiny,empty));ok('pre-binding refusal remains empty',not list(empty.iterdir()))
bad=copy.deepcopy(tiny);bad['members'][0]['mode']=0o755;empty2=owned/'wrong-mode';empty2.mkdir(mode=0o700);refuse('manifest mode binding corrupt',lambda:R.restore(owned/'opaque.tar.gz',info,bad,empty2))
link=owned/'redirect';link.symlink_to(src,target_is_directory=True);refuse('source redirect refused',lambda:R.scan(link))
# Inherited remote failure-journal wrapper loses primary fatal on real O_EXCL failure.
# Only its exact exception handler is executed; main is a raising callback, no transport.
module=ast.parse((D/'remote-source/recover01.py').read_text());mainif=next(n for n in module.body if isinstance(n,ast.If) and ast.unparse(n.test)=="__name__ == '__main__'");witness=[]
for cls in (MemoryError,KeyboardInterrupt,SystemExit):
 root=owned/('fatal-'+cls.__name__);root.mkdir();(root/'FAILED01.json').write_bytes(b'owned existing failure marker\n');primary=cls('original primary')
 def original_failure():raise primary
 seen=None
 try:exec(compile(ast.Module(body=mainif.body,type_ignores=[]),'<exact remote top-level handler>','exec'),{'main':original_failure,'write':M.write,'encode':M.encode,'HERE':root,'CALLS':[]})
 except BaseException as e:seen=e
 ok('TF1 exact inherited fatal replaced '+cls.__name__,isinstance(seen,FileExistsError) and seen is not primary and seen.__context__ is primary)
 witness.append({'primary':cls.__name__,'observed':type(seen).__name__,'primary_retained_only_as_context':seen.__context__ is primary,'original_marker_unchanged':(root/'FAILED01.json').read_bytes()==b'owned existing failure marker\n'})
ok('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','pandas','scipy')))
write('TF1_WITNESS01.json',{'finding':'inherited top-level failure-journal write replaces first fatal','candidate':'remote recover01.py','witnesses':witness,'transport_operations':0,'actual_source_restores':0,'actual_receipts_fabricated':False})
write('CHECKS01.json',{'count':len(checks),'checks':checks,'verdict':'WITHHELD_REMOTE_TF1_FLAT_SOURCE_CHECKS_PASSED','actual_source_restores':0,'network_operations':0,'native_jobs':0,'actual_future_authority':None,'owned_pipeline':{'logical_members':986,'opaque_bodies':713,'flat_private_files':714},'scope':'Opaque synthetic full-shape utility pipeline; no Source325 archive restored, no Git receipt fabricated.'});print(json.dumps({'count':len(checks),'verdict':'WITHHELD_REMOTE_TF1_FLAT_SOURCE_CHECKS_PASSED'}))
