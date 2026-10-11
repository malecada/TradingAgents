import ast,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'pilot34-linux-memfd-compatibility-probe01-2026-10-11';refs={};checks=[]
def read(path):
 b=path.read_bytes();assert len(b)<2*1024**2;name=str(path.relative_to(R)) if path.is_relative_to(R) else str(path);refs[name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def ck(v,n):checks.append({'check':n,'pass':bool(v)});assert v,n
receipt=json.loads(read(D/'ACTUAL_TOOL_RECEIPTS01.json'));source=read(D/'ACTUAL_INLINE_PROBE_SOURCE01.py').decode();headers=json.loads(read(D/'ACTUAL_HEADER_READBACK01.json'));result=json.loads(read(D/'PROBE01.json'))
ck(receipt['not_a_prelaunch_source_freeze'] is True and receipt['probe']['tool_chunk']=='a5dd44' and receipt['probe']['exit_code']==0,'original Root tool association and explicit postexecution retention')
ck(json.loads(receipt['probe']['output'])==result,'retained actual stdout exactly equals probe result')
feature=json.loads(receipt['feature_observation']['output'].splitlines()[-1]);ck(receipt['feature_observation']['tool_chunk']=='1641bd' and receipt['feature_observation']['exit_code']==0 and feature['interpreter']=='3.13.13' and feature['fcntl_origin']=='built-in' and not feature['memfd_available'] and all(v is None for v in feature['fcntl_constants'].values()) and all(v is None for v in feature['os_constants'].values()),'actual feature observation explains missing Python bindings')
tree=ast.parse(source);body=ast.literal_eval(next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets)))
ck(len(body)==result['bytes']==41 and hashlib.sha256(body).hexdigest()==result['sha256'],'exact finite probe payload length/hash')
ck(all(s in source for s in ['ctypes.CDLL(None,use_errno=True)','create.argtypes=[ctypes.c_char_p,ctypes.c_uint]','create.restype=ctypes.c_int','fcntl.fcntl(fd,1033,15)','fcntl.fcntl(fd,1034)','os.pread(fd,len(body)+1,0)==body','assert e.errno==errno.EPERM','finally:\n if fd is not None and fd>=0:os.close(fd)',"(D/'PROBE01.json').open('x')"]),'retained typed libc/seal/readback/EPERM/close/exclusive source sequence')
ck(headers['postprobe_current_header_readback'] is True,'header receipt explicitly postprobe')
for h in headers['headers']:
 b=read(Path(h['original_path']));ck(len(b)==h['bytes'] and hashlib.sha256(b).hexdigest()==h['sha256'],'current public header hash '+h['original_path']);ck(all(line in b.decode().splitlines() for line in h['relevant_lines']),'retained relevant UAPI lines '+h['original_path'])
lines='\n'.join(line for h in headers['headers'] for line in h['relevant_lines']);ck(all(s in lines for s in ['F_LINUX_SPECIFIC_BASE\t1024','F_ADD_SEALS\t(F_LINUX_SPECIFIC_BASE + 9)','F_GET_SEALS\t(F_LINUX_SPECIFIC_BASE + 10)','F_SEAL_SEAL\t0x0001','F_SEAL_SHRINK\t0x0002','F_SEAL_GROW\t0x0004','F_SEAL_WRITE\t0x0008','MFD_CLOEXEC\t\t0x0001U','MFD_ALLOW_SEALING\t0x0002U']),'literal Linux UAPI constants agree with1033/1034/15/3')
out={'decision':'ACCEPT_RETAINED_FINITE_LINUX_COMPATIBILITY_OBSERVATION','checks':checks,'references':refs,'actual_feature_observation':feature,'probe_source_executed_by_reviewer':False,'limitations':['Trusted Root actual tool references and original retained stdout support the observation; postexecution source file alone is not cryptographic execution attestation.','Current header readback occurred after probe and is not a prelaunch freeze.','Finite41-byte libc memfd/seal test only, no native extension loading, numerical proof, capacity or general compatibility guarantee.','No probe retry or scientific module import.']}
with (P/'PROBE_REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':len(checks)}))
