from pathlib import Path
import ast,hashlib,json,types,os,subprocess
D=Path(__file__).resolve().parent;F=D.parent;P=F/'financial-wrapper-compatibility-coalesced-evidence-correction04-2026-10-04';O=F/'financial-wrapper-compatibility-coalesced-evidence-preparation03-2026-10-04';checks=[]
def h(b):return hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
old=(O/'copy_layout01.py').read_bytes();new=(P/'copy_layout01.py').read_bytes();inverse=json.loads((P/'SOURCE_INVERSE01.json').read_bytes());restored=new.decode()
for edit in reversed(inverse['literal_edits']):ok(restored.count(edit['new'])==1,'unique exact literal edit');restored=restored.replace(edit['new'],edit['old'],1)
ok(len(inverse['literal_edits'])==4 and restored.encode()==old,'full inverse literal old bytes');ok(ast.dump(ast.parse(restored))==ast.dump(ast.parse(old)),'whole inverse AST')
a=ast.parse(old);b=ast.parse(new);a.body=[n for n in a.body if not isinstance(n,ast.FunctionDef) or n.name!='namespace'];b.body=[n for n in b.body if not isinstance(n,ast.FunctionDef) or n.name!='namespace'];ok(ast.dump(a)==ast.dump(b),'all other complete AST identical');ok((P/'INPUTS01.json').read_bytes()==(O/'INPUTS01.json').read_bytes(),'entire input bytes unchanged')
M=types.ModuleType('actual04');M.__file__=str(P/'copy_layout01.py');exec(compile(new,M.__file__,'exec'),M.__dict__);ok([M.FILE,M.TOTAL,M.LOGICAL,M.ALLOCATED,M.FLOOR,M.SECONDS,M.MEMBERS]==[4194304,8388608,67108864,100663296,10737418240,120,256],'all actual unchanged constants')
T=D/'owned-extra04';T.mkdir(mode=0o700)
def refused(f,label):
 try:f()
 except ValueError as e:ok(True,label);return str(e)
 raise AssertionError('accepted '+label)
r=T/'257-members';r.mkdir(mode=0o700)
for k in range(257):(r/('%03d'%k)).touch(mode=0o600)
refused(lambda:M.namespace(r),'actual257member refused')
r2=T/'file-over4MiB';r2.mkdir(mode=0o700)
with (r2/'oversized').open('xb') as f:f.truncate(4194305)
refused(lambda:M.namespace(r2),'actual sparse oversized file refused')
r3=T/'logical-over64MiB';r3.mkdir(mode=0o700)
for k in range(17):
 with (r3/('%02d'%k)).open('xb') as f:f.truncate(4194304)
refused(lambda:M.namespace(r3),'actual17 sparse4MiB logical over64MiB refused')
# Exact 5.0 boundary at final resource check: simulated clock only, actual statvfs retained.
r4=T/'finalclock';r4.mkdir(mode=0o700);ro,rt=M.os,M.time;off=[0.0];proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)})
def fs(p):v=os.statvfs(p);off[0]=5.0;return v
proxy.statvfs=fs;M.os=proxy;M.time=types.SimpleNamespace(monotonic=lambda:off[0])
try:refused(lambda:M.namespace(r4),'exact5.0 final boundary refuses')
finally:M.os=ro;M.time=rt
# Final namespace cleanup observer mutates an earlier genuine owned input after Reader.finish.
r5=T/'lateinput';r5.mkdir(mode=0o700);p=r5/'original';p.write_bytes(b'opaque');p.chmod(0o600);spec={'rows':[{'original_path':str(p),'path':str(p),'destination':'body','bytes':6,'sha256':h(b'opaque'),'original_mode':0o600,'copy_mode':0o600,'output_mode':0o600,'role':'receipt'}]};calls=[0];real=M.namespace
def late(root):
 result=real(root)
 if (root/'DRAFT_LAYOUT01.json').exists():
  calls[0]+=1
  if calls[0]==2:p.write_bytes(b'CHANGED')
 return result
M.namespace=late
try:refused(lambda:M.copy_layout(spec,r5/'partial',M.PC.Reader()),'late final-observer original mutation refused');ok(calls[0]==2 and (r5/'partial/body').read_bytes()==b'opaque','late failure keeps partialbody')
finally:M.namespace=real
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_OPTIONAL_LOCKS='0');res=subprocess.run(['git','rev-parse','HEAD'],cwd=CAP,capture_output=True,timeout=10,env=env);ok(res.returncode==0 and res.stdout.strip()==b'32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41','unchanged genuine CAP source');ok(len(list((CAP/'research_runs').glob('*/claim.json')))==3 and not (CAP/'research_runs/financial-wrapper-classification-eager-complete100-compatibility-20261004-01').exists(),'3claims and no new claim');ok(not M.OUTPUT.exists(),'fixed Root output absent')
(D/'INDEPENDENT04.json').write_text(json.dumps({'checks':checks,'count':len(checks),'all_ast_except_namespace_unchanged':True,'literal_inverse_sha256':h(restored.encode()),'numerical_authority':False,'public_entry':False,'resource_controls':'actual metadata sparse file/member caps; finalclock is explicitly simulated'},indent=2)+'\n');print(len(checks))
