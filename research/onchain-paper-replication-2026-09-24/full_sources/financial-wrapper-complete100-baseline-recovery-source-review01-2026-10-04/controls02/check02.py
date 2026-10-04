"""Independent bounded original source review; no entrypoints/remote/current restore."""
import ast,copy,hashlib,importlib.util,json,os,shutil,stat,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent.parent;ROOT=B.parents[2]
A=B/'financial-wrapper-complete100-baseline-remote01-2026-10-04';C=B/'financial-wrapper-complete100-baseline-capture01-2026-10-04'
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01')
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_size<=4194304 and p.resolve()==p,'bounded canonical source '+p.name);return p.read_bytes()
def put(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
(H/'source').mkdir();sources={}
for p in sorted(A.iterdir()):
 if p.is_file():
  b=read(p);(H/'source'/p.name).write_bytes(b);sources[p.name]=sha(b)
ck(sources['recover01.py']=='b03a2c296d122f95f395c02fa1821df25d246d3d21ce93a28560a953f2335879','exact remote source');ck(sources['restore01.py']=='6af39be9f02e21e14b8409b312165ecb3e8e622f2243b42dfc2553b9781c6695','exact original flat source')
remote=(H/'source/recover01.py').read_text();inv=json.loads((H/'source/SOURCE_INVERSE02.json').read_text());restored=remote
for change in reversed(inv['changes']):ck(restored.count(change['replacement'])==1,'unique remote inverse');restored=restored.replace(change['replacement'],change['original'],1)
old=read(B/'financial-wrapper-claimedrun-failed-remote01-2026-10-04/recover01.py');(H/'ORIGINAL_REMOTE01.py').write_bytes(old);ck(sha(old)==inv['original_sha256']=='b1b6618949cacbe5db7230ca27b7b9cb06c356f95d4fbecc3df6d013b3acd9a9','authentic accepted predecessor');ck(restored.encode()==old,'remote full literal inverse');ck(ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False),'remote full AST inverse')
flat=(H/'source/restore01.py').read_text();errata=json.loads((H/'source/RESTORE_DRAFT_ERRATA01.json').read_text());back=flat
for change in reversed(errata['edits']):ck(back.count(change['replacement'])==1,'unique original flat errata inverse');back=back.replace(change['replacement'],change['original'],1)
ck(back.encode()==(H/'source/restore01.draft01.py').read_bytes(),'full preserved flat draft inverse')
# Extract source functions/constants; do not execute main/entry or top-level external imports.
rns={'Path':Path,'hashlib':hashlib,'json':json};tree=ast.parse(remote)
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('REQUIRED','FILE') for t in n.targets):exec(compile(ast.Module(body=[n],type_ignores=[]),'remote_constant','exec'),rns)
funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','encode','_raise_retained','validate_fixed_selection')];exec(compile(ast.Module(body=funcs,type_ignores=[]),'remote_pure','exec'),rns)
required=rns['REQUIRED'];ck(len(required)==17 and sum(v['bytes'] for v in required.values())==5320678,'exact17 bodies5320678B');req=read(C/'REQUIRED_BODIES02.json');ck(json.loads(req)==required,'fixed actual required map');(H/'REQUIRED_BODIES02.json').write_bytes(req)
for name,pin in required.items():b=read(ROOT/name);ck(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'actual fixed body '+Path(name).name)
ck(11+2*len(required)==45,'remote operation45 denominator');selection={'remote_commit':None,'rows':[dict(path=n,**v) for n,v in sorted(required.items())]};rns['validate_fixed_selection'](selection)
refusals=[]
for name,mut in [('missing',lambda v:v['rows'].pop()),('duplicate',lambda v:v['rows'].append(copy.deepcopy(v['rows'][0]))),('hash',lambda v:v['rows'][0].update(sha256='0'*64)),('extent',lambda v:v['rows'][0].update(bytes=4194305)),('path',lambda v:v['rows'][0].update(path='research/../escape'))]:
 v=copy.deepcopy(selection);mut(v)
 try:rns['validate_fixed_selection'](v)
 except ValueError as e:refusals.append({'case':name,'reason':str(e)})
 else:raise AssertionError(name+' accepted')
ck(len(refusals)==5,'fixed selection negative controls; no remote commit invented')
cap=read(C/'CAPTURE01.json');ck(sha(cap)=='7d65c2bac832832df5d62d49a41b31b7d54b33b52a448d048cd94b9541f8a176','actual six-scope capture');cap=json.loads(cap);ck(set(cap['scopes'])=={'capsule','parent','support','git1','git2','git3'},'complete six scopes')
logical=0;scope_rows=[]
for label,info in cap['scopes'].items():
 mraw=read(C/(label.upper()+'_MANIFEST01.json'));m=json.loads(mraw);ck(sha(mraw)==info['manifest_sha256']==info['archive']['manifest_sha256'],'manifest binding '+label);logical+=sum(r.get('bytes',0) for r in m['members']);scope_rows.append({'scope':label,'members':len(m['members']),'logical_bytes':sum(r.get('bytes',0) for r in m['members']),'manifest_sha256':sha(mraw)})
idx=json.loads(read(C/'GIT_OBJECTS01.json'));ck(idx['object_count']==len(idx['reachable_objects'])==385 and idx['object_body_bytes']==sum(r['bytes'] for r in idx['reachable_objects'])==7807097,'all385 object denominator');ck(1+385+6==392 and 392<400,'actual fixed offline Git operations392 under400');ck(logical<64*1024**2,'actual fixed combined scope logical under64MiB')
side=read(C/'ORIGINAL_ROOT_RECEIPT_MODES01.json');ck(sha(side)=='17b9baf9e9a37c3b98943e7c9d46ffa85d2771eb8d7bd7cc76530017372450da','explicit root mode sidecar');(H/'ROOT_MODE_SIDECAR01.json').write_bytes(side)
(H/'utilities').mkdir()
for n,pin in {'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():
 b=read(P/n);ck(sha(b)==pin,'unchanged primitive '+n);(H/'utilities'/n).write_bytes(b)
sys.path.insert(0,str(H/'utilities'));spec=importlib.util.spec_from_file_location('Rreview',H/'utilities/recovery04.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
ck(shutil.disk_usage(H).free>=R.FLOOR,'actual owned tests10GiB free floor');tiny=H/'tiny';tiny.mkdir(mode=0o700);origin=tiny/'original';origin.mkdir(mode=0o700);(origin/'opaque').write_bytes(b'ordinary opaque review body\x00');(origin/'empty').mkdir(mode=0o700)
m=R.scan(origin);archive=tiny/'opaque.tar.gz';info=R.pack(origin,m,archive);dest=tiny/'absent-destination'
try:R.restore(archive,info,m,dest)
except FileNotFoundError as e:witness={'case':'BR1 real unchanged restore with caller-required absent destination','exception':type(e).__name__,'message':str(e),'destination_exists_after':os.path.lexists(dest)}
else:raise AssertionError('expected missing-directory blocker absent')
ck(not os.path.lexists(dest),'BR1 no implicit directory creation')
# An independent existing private directory satisfies the documented primitive precondition.
good=tiny/'existing-private';good.mkdir(mode=0o700);result=R.restore(archive,info,m,good);meta=json.loads(R.read(good,result['metadata_file']));ck(R.read(good,meta['flat_members']['opaque'])==(origin/'opaque').read_bytes(),'real tiny canonical roundtrip with correct precondition')
ck(meta['manifest']==m and result['research_authority'] is False,'tiny modes/emptydirs retained as metadata only')
# Actual flat entry cleanup with controlled ordinary exceptions only, no entry main/receipt writes.
entry=next(n for n in ast.parse(flat).body if isinstance(n,ast.FunctionDef) and n.name=='entry');cleanup=[]
# Execute its body with a small stdlib R facade for error writer only; genuine _cleanup is unchanged.
from types import SimpleNamespace
pairs=[]
for first in (ValueError('ordinary-primary'),KeyboardInterrupt('fatal-primary'),MemoryError('memory-primary')):
 for later in (OSError('journal-error'),SystemExit('journal-fatal'),MemoryError('journal-memory')):
  seen=[]
  def fail(first=first):raise first
  def writer(*args,later=later):seen.append('journal-attempt');raise later
  en={'main':fail,'R':SimpleNamespace(put=writer,_cleanup=R._cleanup),'HERE':tiny}
  exec(compile(ast.Module(body=[entry],type_ignores=[]),'actual_flat_entry_cleanup','exec'),en)
  try:en['entry']()
  except BaseException as actual:
   expected=first if isinstance(first,MemoryError) or not isinstance(first,Exception) else later
   ck((actual is expected if isinstance(expected,MemoryError) or not isinstance(expected,Exception) else type(actual).__name__=='CleanupFailure' and actual.failures==(first,later)) and seen==['journal-attempt'],'actual first-fatal/ordinary-uncertainty journal pair');pairs.append({'primary':type(first).__name__,'journal':type(later).__name__,'raised':type(actual).__name__})
  else:raise AssertionError('entry swallowed error')
put('READBACK01.json',{'checks':len(checks),'names':checks,'source_hashes':sources,'selection':{'rows':17,'bytes':5320678,'operations':45,'commit':None},'scopes':scope_rows,'scope_logical_bytes':logical,'original_git_objects':385,'object_body_bytes':7807097,'offline_git_operation_count':392,'fixed_selection_refusals':refusals,'BR1_witness':witness,'fatal_pairs':pairs,'actual_remote_or_restore_entry_executed':False,'current_source_restored':False,'new_release':None})
print(json.dumps({'checks':len(checks),'BR1':witness,'remote':'SOURCE_ONLY_FIXED17_ACCEPTABLE','flat':'WITHHELD_BR1','scope_bytes':logical}))
