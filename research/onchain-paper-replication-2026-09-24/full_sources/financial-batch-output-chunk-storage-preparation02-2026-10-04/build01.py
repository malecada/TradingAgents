from pathlib import Path
import hashlib,json,ast
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-chunk-storage-preparation01-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((A/'codec01.py').read_bytes())=='00d06377c4567bd7880dd7ddbf396b613a78968a7317a565f7e034319c9ed4fe'
assert sha((A/'local_store01.py').read_bytes())=='2614242ebc8395f859e704db1971dd46172ff8ea9802fb4c77397c80970bdb52'
changes={}
for n in ('codec01.py','local_store01.py','owned_io.py','recovery04.py','bounded_git01.py'):
 old=(A/n).read_text();(H/('ORIGINAL_'+n)).write_text(old);new=old;edits=[]
 def edit(a,b):
  global new
  assert new.count(a)==1,(n,a);new=new.replace(a,b);edits.append({'before':a,'after':b})
 if n=='codec01.py':
  edit("start=time.monotonic();total=descriptor(expected);pin(terminal_pin)","start=time.monotonic();total=descriptor(expected);expected=parse(canonical(expected));pin(terminal_pin)")
 if n=='local_store01.py':
  edit('FLOOR=10*1024**3','''FLOOR=10*1024**3
# Conservative ENGINEERING reservation, not a filesystem quota theorem.
# No filesystem scratch is written; headroom reserves bounded IO transient space.
BLOCK=65536
DIRECTORY_HEADROOM=1024**2
SCRATCH_HEADROOM=4*1024**2
ENTRY_HEADROOM=BLOCK

def project(reserved,logical,size,limit=LIMIT):
 C.require(all(type(x)is int for x in (reserved,logical,size,limit)) and reserved>=0 and logical>=0 and 0<size<=C.FILE,'reservation integers')
 cost=((size+BLOCK-1)//BLOCK)*BLOCK+ENTRY_HEADROOM
 C.require(logical+size<=limit and reserved+cost<=limit,'pre-write no-refund whole reservation')
 return reserved+cost,logical+size
''')
  edit('self.names=set();self.total=0;self.begin=time.monotonic()','self.names=set();self.total=0;self.reserved=0;self.reserved_logical=0;self.begin=time.monotonic()')
  edit("C.require(stat.S_IMODE(s.st_mode)==0o700 and not os.listdir(self.fd),'fresh empty private root');self.check()", """C.require(stat.S_IMODE(s.st_mode)==0o700 and not os.listdir(self.fd),'fresh empty private root')
   fs=os.fstatvfs(self.fd)
   C.require(0<fs.f_bsize<=BLOCK and 0<fs.f_frsize<=BLOCK and 0<s.st_blksize<=BLOCK,'unsupported filesystem block size')
   self.reserved=s.st_blocks*512+DIRECTORY_HEADROOM+SCRATCH_HEADROOM
   C.require(self.reserved<=LIMIT,'initial directory/scratch reservation exceeds local cap');self.check()""")
  edit("C.require(allocated<=LIMIT and logical==self.total<=LIMIT,'whole sampled allocated/logical bound')", "C.require(allocated<=self.reserved<=LIMIT and logical==self.total<=self.reserved_logical<=LIMIT,'whole sampled allocated/logical/reserved bound')")
  edit("self.names.add(n) # Reservation is not refunded after failure.", """projected,logical=project(self.reserved,self.reserved_logical,len(b),LIMIT)
   C.require(shutil.disk_usage(self.root).free>=FLOOR+projected,'pre-write disk floor plus reservation headroom')
   self.reserved=projected;self.reserved_logical=logical
   self.names.add(n) # Reservation is not refunded after failure.""")
  edit("""  self.check();result=C.verify_stream(lambda n:R.read(self.root,name(n)),terminal_pin,descriptor,provisional)
  C.require(set(result['members'])==self.names,'complete local member denominator');self.check();return result""", """  try:
   self.check();result=C.verify_stream(lambda n:R.read(self.root,name(n)),terminal_pin,descriptor,provisional)
   C.require(set(result['members'])==self.names,'complete local member denominator');self.check();return result
  except BaseException:
   self.poisoned=True;raise""")
 inverse=new
 for e in reversed(edits):assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'])
 assert inverse==old and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old))
 (H/n).write_text(new);changes[n]={'original_sha256':sha(old.encode()),'successor_sha256':sha(new.encode()),'edits':edits,'byte_inverse':True,'AST_inverse':True}
(H/'INVERSE01.json').write_text(json.dumps(changes,sort_keys=True,indent=2)+'\n')
