import ast,json,os,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;P=D.parent/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P))
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as R
enc=next(n for n in ast.parse((P/'byte_bridge01.py').read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='_encode');tr=next(n for n in enc.body if isinstance(n,ast.Try));code=compile(ast.Module(body=tr.body[-6:-1],type_ignores=[]),'<exact population bracket tail>','exec');out=[]
for case in ['missing','extra','replace','mode','extent','mtime','hardlink','root-alias','root-mode']:
 base=D/('population-'+case);base.mkdir(mode=0o700);root=base/'codec';root.mkdir(mode=0o700);raw=b'x'*256;d={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'score-batches','dtype':'<f8','shape':[1,32],'order':'C','scope':{k:B.digest(k.encode())for k in C.SCOPE},'motifs':32,'spent_samples':512}
 cur=B.Cursor([('raw',256,B.digest(raw))],8,lambda n,o,c:raw[o:o+c],lambda:None)
 with L.LocalStore(root)as store:
  pin=C.encode_stream(cur,d,store.put);proof=store.verify(pin,d);done=cur.completion();p=root/'chunk-00000.bin'
  def boundary():
   if case=='missing':p.rename(base/'retained-original')
   elif case=='extra':(root/'unexpected').write_bytes(b'x')
   elif case=='replace':
    b=p.read_bytes();p.rename(base/'retained-original');p.write_bytes(b);p.chmod(0o600)
   elif case=='mode':p.chmod(0o640)
   elif case=='extent':
    with p.open('ab')as f:f.write(b'x')
   elif case=='mtime':
    s=p.stat();os.utime(p,ns=(s.st_atime_ns,s.st_mtime_ns+1000000))
   elif case=='hardlink':os.link(p,base/'literal-hardlink')
   elif case=='root-alias':root.rename(base/'retained-codec');root.symlink_to(base/'retained-codec',target_is_directory=True)
   elif case=='root-mode':root.chmod(0o750)
  try:exec(code,{'store':store,'terminal':pin,'descriptor':d,'proof':proof,'done':done,'require':B.require,'_codec_population':B._codec_population,'R':R,'boundary':boundary})
  except BaseException as e:out.append({'case':case,'refusal':type(e).__name__+': '+str(e)})
  else:raise AssertionError('population mutation accepted '+case)
with (D/'POPULATION01.json').open('x')as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print('9 concrete population mutations refused; all original inode bodies retained')
