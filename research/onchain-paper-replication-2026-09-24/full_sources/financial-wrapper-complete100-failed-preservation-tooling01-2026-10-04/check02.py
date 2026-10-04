from pathlib import Path
import ast,copy,hashlib,json,sys
D=Path(__file__).resolve().parent;F=D.parent;B=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';sys.path.insert(0,str(D));import restore01 as S
R=S.R;n=0;sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v):
 global n
 assert v;n+=1
def refuses(fn):
 try:fn()
 except (ValueError,KeyError,TypeError,FileNotFoundError):ok(True)
 else:raise AssertionError('expected refusal')
cap=json.loads((B/'CAPTURE01.json').read_bytes());scopes=S.load_scopes(B,cap);ok(len(scopes)==10);actual=[]
for label,scope in scopes.items():
 raw=(B/('complete-'+label+'01.tar.gz')).read_bytes();frames=list(R.framed_members(raw));m=scope['manifest'];ok(len(frames)==len(m['members']))
 for (name,t,b),row in zip(frames,m['members'],strict=True):
  ok(name==row['path'] and t.mode==row['mode'] and (t.isfile() if row['kind']=='file' else t.isdir()))
  if row['kind']=='file':ok(len(b)==row['bytes'] and sha(b)==row['sha256'])
 actual.append({'label':label,'frames':len(frames),'archive_sha256':sha(raw)})
for key,val in [('historical_native_started',False),('new_native_or_claim_started_by_capture',True),('permanent_disposition','COMPLETE'),('prior_failed_capture_permanently_withheld',False),('source','0'*40),('identity','other')]:
 c=copy.deepcopy(cap);c[key]=val;refuses(lambda:S.load_scopes(B,c))
for mutate in [lambda s:s['capsule01']['manifest']['members'].pop(),lambda s:s['capsule01']['manifest']['members'][0].update(mode=0),lambda s:s.pop('capsule08')]:
 sc=copy.deepcopy(scopes);mutate(sc);refuses(lambda:S.validate_union(B,cap,sc))
# Real owned ten-scope opaque utility, no receipt/claim/authority fabrication.
tiny=D/'tiny02';tiny.mkdir();bundle=tiny/'bundle';bundle.mkdir();out=tiny/'flat';out.mkdir();ss={}
for label in S.LABELS:
 src=tiny/('original-'+label);src.mkdir();(src/'empty').mkdir();(src/'opaque').write_bytes(b'opaque engineering '+label.encode());m=R.scan(src);arc=R.pack(src,m,bundle/('complete-'+label+'01.tar.gz'));ss[label]={'manifest':m,'archive':arc}
rest=S.restore_scopes(bundle,ss,out,lambda:None);ok(len(rest)==10)
for label,result in rest.items():
 md=json.loads((out/('flat-'+label+'01')/result['metadata_file']).read_bytes());ok((out/('flat-'+label+'01')/md['flat_members']['opaque']).read_bytes()==b'opaque engineering '+label.encode())
refuses(lambda:S.restore_scopes(bundle,ss,out,lambda:None))
# First-fatal cleanup helper inherited byte-exact, all nine fatal/ordinary pairs.
for primary in (KeyboardInterrupt('p'),MemoryError('p'),ValueError('p')):
 for secondary in (KeyboardInterrupt('s'),MemoryError('s'),OSError('s')):
  try:
   try:raise primary
   except BaseException:
    R._cleanup((lambda e=secondary:(_ for _ in ()).throw(e),),primary=primary)
    raise
  except BaseException as actualerror:
   expected=primary if isinstance(primary,(KeyboardInterrupt,MemoryError)) else secondary
   ok(actualerror is expected)
  else:raise AssertionError('fatal lost')
inv=json.loads((D/'SOURCE_INVERSE01.json').read_bytes())
for name,row in inv.items():
 s=(D/name).read_text()
 for e in reversed(row['edits']):ok(s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
 ok(s.encode()==(D/('ORIGINAL_'+name)).read_bytes());ok(ast.dump(ast.parse(s))==ast.dump(ast.parse((D/('ORIGINAL_'+name)).read_bytes())))
ok(len(inv['recover01.py']['edits'])==4)
(D/'CHECKS01.json').write_text(json.dumps({'checks':n,'actual_full_archive_frames':actual,'actual_restore':False,'tiny_owned_scopes':10,'source_only':True},indent=2)+'\n');print(json.dumps({'checks':n,'actual_archives':len(actual)}))
