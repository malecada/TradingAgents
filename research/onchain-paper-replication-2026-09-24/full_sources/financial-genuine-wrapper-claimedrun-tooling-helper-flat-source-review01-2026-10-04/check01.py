import ast,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];ROOT=B/'financial-genuine-wrapper-root-claimedrun-tooling-helper-flat01-2026-10-04';checks=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
s=(ROOT/'restore_scopes01.py').read_bytes();ok(sha(s)=='8dd3640ea7e5bd58f30de1c091f68c0272205be9a20ed36f8bb322841f9c8880','exact candidate')
for n,h in {'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():ok(sha((ROOT/n).read_bytes())==h,'unchanged primitive '+n)
sys.path.insert(0,str(ROOT));import recovery04 as R
qraw=(ROOT/'REQUEST_DRAFT01.json').read_bytes();q=json.loads(qraw);ok(qraw==R.encode(q),'canonical draft');ok(q['actual_execution'] is False and q['remote_commit'] is None and q['remote_receipt_sha256'] is None,'actual future pins unavailable')
ns={'__file__':str(ROOT/'restore_scopes01.py'),'__name__':'source_only'};exec(compile(s,'candidate source','exec'),ns);out=ROOT/'flat-eight-scopes01';ok(not os.path.lexists(out),'actual output absent before')
argv=sys.argv;sys.argv=['source-only','--request',str(ROOT/'REQUEST_DRAFT01.json'),'--sha256',sha(qraw)]
try:ns['main']()
except ValueError as e:ok(str(e)=='released fixed eight ordinary scopes','genuine draft early refusal')
else:raise AssertionError('draft accepted')
finally:sys.argv=argv
ok(not os.path.lexists(out),'no actual output reservation after')
# Actual unchanged FlatOutput API on a minimal owned directory, no archive restoration.
owned=H/'tiny-owned';owned.mkdir(mode=0o700);missing=owned/'scope-00';obj=R.FlatOutput(missing)
try:obj.begin()
except FileNotFoundError as e:refusal={'type':type(e).__name__,'errno':e.errno,'filename':e.filename,'message':str(e)};ok(not missing.exists(),'genuine absent destination refusal')
else:raise AssertionError('missing destination accepted')
finally:obj.close()
missing.mkdir(mode=0o700);obj=R.FlatOutput(missing)
try:obj.begin();ok(obj.fd is not None,'existing0700 precondition accepted');obj.finish();ok(list(missing.iterdir())==[],'control writes no archive bodies')
finally:obj.close()
# Complete actual source/draft body joins; no remote receipt fabricated.
rows=[];whole=0
for scope in q['scopes']:
 mf=MAIN/scope['manifest']['path'];ar=MAIN/scope['archive']['path'];mb=mf.read_bytes();ab=ar.read_bytes();m=json.loads(mb);R.validate(m)
 for ref,body in [(scope['manifest'],mb),(scope['archive'],ab)]:ok(len(body)==ref['bytes']<=4194304 and sha(body)==ref['sha256'],'actual original manifest/archive pin')
 ok(len(m['members'])==scope['ordinary_members'],'full original scope denominator');logical=sum(r.get('bytes',0) for r in m['members']);whole+=logical
 meta=next(r for r in m['members'] if r['path']=='CAPTURE_ORIGINAL_TREE01.json');ok(meta['sha256']==scope['original_metadata_sha256'],'per-tree actual metadata hash')
 auth=json.loads((ar.parent/'UNION_AUTHENTICATION01.json').read_bytes());key=scope['label'].split('/')[-1];ok(auth['archives'][key]['archive']['sha256']==scope['archive']['sha256'] and auth['archives'][key]['manifest']['sha256']==scope['manifest']['sha256'],'actual capture auth join')
 rows.append({'label':scope['label'],'logical_bytes':logical,'members':len(m['members']),'archive_sha256':sha(ab),'manifest_sha256':sha(mb)})
ok(len(rows)==8 and len({r['label'] for r in rows})==8 and whole==52444730 and whole<64*1024**2,'exact8 scopes/whole logical bound')
# Source explicitly invokes restore without creating per-scope destination.
tree=ast.parse(s);calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='mkdir'];ok(len(calls)==1 and isinstance(calls[0].args[0],ast.Name) and calls[0].args[0].id=='out','only outer directory created')
for n in ['restore_scopes01.py','SOURCE_DRAFT01_344e.py','REQUEST_DRAFT01.json','PREPARATION_CORRECTION01.json','ROOT_ADOPTION01.json','recovery04.py','owned_io.py','bounded_git01.py']:
 with (H/('ORIGINAL_'+n)).open('xb') as f:f.write((ROOT/n).read_bytes())
result={'status':'WITHHELD_TF_DESTINATION01','checks':len(checks),'check_names':checks,'candidate_sha256':sha(s),'draft_sha256':sha(qraw),'finding':{'source_line':28,'primitive_begin_line':144,'message':'No scope-XX directory is created before R.restore/FlatOutput.begin requires existing0700 destination. First actual valid request would reserve outer output then fail before recovering scope0.','actual_owned_absent_precondition':refusal,'existing_private_directory_control_passed':True},'whole_logical_bytes':whole,'scopes':rows,'actual_Root_restore':False,'actual_Root_output_absent':True,'actual_remote_receipt':None,'numerical_authority':False}
with (H/'READBACK01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'readback':sha((H/'READBACK01.json').read_bytes()),'draft_sha256':sha(qraw)}))
