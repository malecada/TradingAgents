from pathlib import Path
import ast
H=Path(__file__).resolve().parent;p=H/'operational_source_compatibility.py';s=p.read_text();(H/'DRAFT02_operational_source_compatibility.py').write_text(s)
a=s.index('def _read(');b=s.index('\ndef validate_maps',a)
s=s[:a]+'''def _read(path,budget):
 path=Path(path);require(path.is_absolute() and path.resolve(strict=True)==path and len(path.parts)<=64,'canonical bounded evidence origin')
 require(time.monotonic()-budget['begun']<120,'finite operational evidence deadline')
 fds=[];primary=None
 try:
  fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC);fds.append(fd)
  for part in path.parts[1:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);fds.append(fd)
  parent=fd;fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);fds.append(fd)
  a=os.fstat(fd);require(stat.S_ISREG(a.st_mode) and 0<=a.st_size<=FILE,'bounded regular evidence')
  budget['bytes']+=a.st_size;require(budget['bytes']<=TOTAL,'aggregate evidence read limit')
  raw=bytearray()
  while True:
   require(time.monotonic()-budget['begun']<120,'finite operational evidence deadline')
   block=os.read(fd,min(1024**2,FILE+1-len(raw)))
   if not block:break
   raw.extend(block);require(len(raw)<=FILE,'evidence grew beyond bound')
  sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  require(sig(a)==sig(os.fstat(fd))==sig(os.stat(path.name,dir_fd=parent,follow_symlinks=False))==sig(path.lstat()) and path.resolve(strict=True)==path and len(raw)==a.st_size,'evidence changed while read')
  return bytes(raw)
 except BaseException as error:primary=error;raise
 finally:
  selected=primary
  for fd in reversed(fds):
   try:_close(fd,selected)
   except BaseException as error:selected=error
  if selected is not primary:raise selected

''' +s[b:]
s=s.replace(" require(plan['closure_input']==target['closure_input']", " require(ad.experiment['parent']==({'complete100':None,'continue100':HISTORICAL_ID,'predict':consumers['continue100']['experiment']}[plan['phase']]),'exact phase parent topology differs')\n require(plan['closure_input']==target['closure_input']")
# Strict JSON version admits integers only, not True.
s=s.replace("policy['schema_version']==1", "type(policy['schema_version'])is int and policy['schema_version']==1")
p.write_text(s);ast.parse(s);print('anchored bounded reader and explicit consumer parent topology parsed')
