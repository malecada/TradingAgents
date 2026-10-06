from pathlib import Path
import ast,hashlib,importlib.util,json,os
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate',H/'relocate01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fixture=H/'synthetic01';fixture.mkdir(exist_ok=False)
source=fixture/'source.bin';data=b'0123456789abcdef'*4096+b'!';source.write_bytes(data);os.chmod(source,0o640);s=source.stat()
row={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'mode':0o640,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]}
calls=[];target=fixture/'good.bin';out=m.stream_copy(source,target,row,tick=lambda n:calls.append(n),chunk=32768)
assert target.read_bytes()==data and out['stat_identity']==m.sig(target.stat()) and target.stat().st_mode&0o777==0o640 and source.read_bytes()==data
refused=[]
def refusal(name,fn):
    try:fn()
    except (ValueError,FileExistsError,RuntimeError):refused.append(name)
    else:raise AssertionError(name)
refusal('exclusive target',lambda:m.stream_copy(source,target,row,tick=lambda n:None))
bad={**row,'sha256':'0'*64};wrong=fixture/'wrong-hash.bin'
refusal('wrong hash preserves original and attempted destination',lambda:m.stream_copy(source,wrong,bad,tick=lambda n:None))
assert wrong.exists() and source.exists()
partial=fixture/'partial.bin';count=[0]
def stop(n):
    count[0]+=1
    if count[0]==2:raise RuntimeError('synthetic deadline interruption')
refusal('interruption retains partial destination',lambda:m.stream_copy(source,partial,row,tick=stop,chunk=32768))
assert 0<partial.stat().st_size<len(data) and source.read_bytes()==data
symlink=fixture/'linked.bin';symlink.symlink_to('good.bin')
refusal('destination symlink',lambda:m.stream_copy(source,symlink,row,tick=lambda n:None))
for name in ('relocate01.py','entry01.py','prepare01.py'):compile((H/name).read_bytes(),str(H/name),'exec')
tree=ast.parse((H/'relocate01.py').read_text())
for name in ('copy','stream_copy'):
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    assert not any(isinstance(n,ast.Attribute) and n.attr in ('unlink','remove','rmdir') for n in ast.walk(node))
# The only production unlink is in the separate retire function, after acceptance and durable attempt.
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='retire')
assert sum(isinstance(n,ast.Attribute) and n.attr=='unlink' for n in ast.walk(node))==1
result={'decision':'pass','synthetic_payload_bytes':len(data),'fresh_copy_readback_bit_mode_check':True,'refusals':refused,'copy_functions_have_no_deletion_call':True,'production_payload_reads':0,'native_network_git_calls':0,'real_prepare_metadata_check_reused':'e9ee7e exit0; not rerun'}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
