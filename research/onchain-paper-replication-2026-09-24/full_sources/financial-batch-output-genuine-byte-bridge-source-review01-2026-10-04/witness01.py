"""Actual opaque IO witness for the bridge tail's stat-only codec recheck.
No genuine _encode, Owner, ResearchRun, Target or produced handle is simulated.
"""
import ast,hashlib,json,os,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;P=D.parent/'financial-batch-output-genuine-byte-bridge-preparation01-2026-10-04';sys.path.insert(0,str(P))
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as R,owned_io as IO
root=D/'post-verify-close-corruption';root.mkdir(mode=0o700);dest=root/'codec';dest.mkdir(mode=0o700)
raw=bytes(range(256));d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'score-batches','dtype':'<f8','shape':[1,32],'order':'C','scope':{k:hashlib.sha256(k.encode()).hexdigest()for k in C.SCOPE},'motifs':32,'spent_samples':512}
cur=B.Cursor([('original',256,B.digest(raw))],8,lambda n,o,c:raw[o:o+c],lambda:None)
state={'injected':False};original_close=os.close
with L.LocalStore(dest)as store:
 pin=C.encode_stream(cur,d,store.put);proof=store.verify(pin,d);done=cur.completion();assert done['sha256']==proof['raw_sha256']
 chunk=dest/'chunk-00000.bin';before=chunk.read_bytes();complete=root/'complete.json'
 body=B.canonical({'kind':'opaque-tail-witness-not-genuine-bridge-proof','prior_codec_terminal':pin})
 def close(fd):
  s=os.fstat(fd)
  match=complete.exists() and (s.st_dev,s.st_ino)==(complete.stat().st_dev,complete.stat().st_ino)
  original_close(fd)
  if match and not state['injected']:
   state['injected']=True
   with chunk.open('r+b')as f:
    f.seek(C.HEADER.size);f.write(bytes([before[C.HEADER.size]^1]));f.flush();os.fsync(f.fileno())
 os.close=close
 try:B._write(R,IO,complete,body)
 finally:os.close=original_close
 store.check() # exact operation used at end of genuine boundary(), only stat/accounting
 assert state['injected'] and complete.read_bytes()==body and chunk.read_bytes()!=before
 try:C.verify_stream(lambda n:R.read(dest,n),pin,d)
 except ValueError as e:failure=str(e)
 else:raise AssertionError('independent codec verification unexpectedly passed')
 tree=ast.parse((P/'byte_bridge01.py').read_bytes());enc=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_encode');boundary=next(n for n in ast.walk(enc)if isinstance(n,ast.FunctionDef)and n.name=='boundary')
 codec_checks=[{'line':n.lineno,'source':ast.unparse(n)}for n in ast.walk(enc)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='store'and n.func.attr in ['verify','check']]
 out={'schema_version':1,'finding':'BB1_POST_VERIFICATION_CODEC_BYTES_NOT_REJOINED','candidate_sha256':B.digest((P/'byte_bridge01.py').read_bytes()),'actual_tail_utility_only':True,'genuine_bridge_executed':False,'real_summary_fd_close_then_single_corruption':state['injected'],'same_extent':len(before)==chunk.stat().st_size,'summary_write_readback_passed':True,'final_exact_store_check_passed':True,'independent_codec_refusal':failure,'old_frame_sha256':B.digest(before),'current_frame_sha256':B.digest(chunk.read_bytes()),'source_store_checks':codec_checks,'boundary_source':ast.unparse(boundary),'qualification':'A deterministic owned close hook after the actual summary fd close, not a wall-clock race or fake Owner. All other genuine authority/source checks are source-inspected, not executed.'}
 with (D/'WITNESS01.json').open('x')as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps({k:v for k,v in out.items()if k!='boundary_source'}))
