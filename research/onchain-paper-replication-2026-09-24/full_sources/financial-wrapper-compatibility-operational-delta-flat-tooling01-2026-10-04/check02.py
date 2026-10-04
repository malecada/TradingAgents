import importlib.util,json,os,hashlib,ast,copy
from pathlib import Path
P=Path(__file__).absolute().parent
s=importlib.util.spec_from_file_location('delta02',P/'restore01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
R=M.R;O=P/'owned02';O.mkdir(mode=0o700);checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,FileNotFoundError,FileExistsError,NotADirectoryError,KeyError,TypeError,EOFError):ck(n,True)
 else:raise AssertionError(n+' accepted')
# Full source re-execution of successful fixed archive route after final namespace check change.
bundle=P.parent/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';c,m=M.load_capture(bundle)
bounds=[]
def boundary():bounds.append(M.W.census(O))
r=M.restore_delta(bundle,c,m,O,boundary);ck('complete-real-frozen-roundtrip',r['regular_bodies']==33)
# Framing tests use tiny opaque original byte pack and unchanged PAX decoder.
t=O/'tree';t.mkdir(mode=0o700);(t/'byte').write_bytes(b'only opaque byte\x00\xff')
tm=R.scan(t);a=O/'good.tar.gz';ai=R.pack(t,tm,a);raw=a.read_bytes()
for name,changed in [('truncated',raw[:-5]),('corrupt',bytes([raw[0]^1])+raw[1:]),('trailing',raw+b'extra')]:
 ar=O/(name+'.tar.gz');ar.write_bytes(changed);dest=O/name;dest.mkdir(mode=0o700)
 info=dict(ai,bytes=len(changed),sha256=R.digest(changed))
 try:R.restore(ar,info,tm,dest)
 except BaseException as e:
  ck('framing:'+name,isinstance(e,Exception));(O/(name+'-error.json')).write_text(json.dumps({'type':type(e).__name__,'failure_retained':True})+'\n')
 else:raise AssertionError(name+' accepted')
# Wrong metadata hash/mode are refused even with archive bytes unchanged.
for kind in ['manifest-hash','member-mode']:
 dest=O/kind;dest.mkdir(mode=0o700);mm=copy.deepcopy(tm);info=copy.deepcopy(ai)
 if kind=='manifest-hash':info['manifest_sha256']='0'*64
 else:mm['members'][0]['mode']^=0o100;info['manifest_sha256']=R.digest(R.encode(mm))
 refuse(kind,lambda:R.restore(a,info,mm,dest))
# Complete fixed reader lexical refusal: never creates output for absent actual pins.
for name,pin in [('null',None),('bad','G'*64)]:refuse('futurepin:'+name,lambda pin=pin:M.run(pin,'0'*64))
# Finite actual floor and allocated policy exist unchanged and current owned root is measured.
ck('fixed-policy',M.W.POLICY=={'logical':67108864,'allocated':100663296,'members':32768,'depth':32,'file':4194304,'sample_seconds':5,'floor':10737418240,'samples':8192})
ck('sampled-all-owned',bounds[-1]['logical_bytes']>=943578)
ck('no-original-modified',R.digest(R.read(bundle,'CAPTURE01.json'))==M.CAPTURE)
(P/'CONTROLS02.json').write_text(json.dumps({'checks':len(checks),'names':checks,'actual_remote_entry_executed':False,'actual_local_roundtrip':r,'observations':bounds},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'status':'passed'}))
