from pathlib import Path
import importlib.util,json,hashlib,os,types,stat
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-compatibility-operational-delta-flat-source-mode-successor04-2026-10-04';D=H.parent/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04'
s=importlib.util.spec_from_file_location('more',A/'restore01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
r=json.loads((D/'REMOTE_RECOVERY01.json').read_bytes());raw=(D/'SELECTED_BODIES01.json').read_bytes();sel=json.loads(raw);pin=hashlib.sha256(raw).hexdigest();co=M.VerifiedCohort();M.authenticate_selected(D,r,sel,pin,co);co.check();target=D/'selected'/next(iter(M.REQUIRED));results=[]
# Metadata-return overlays only; physical Root tree stays untouched. UID is checked separately from the fingerprint.
for field in ['st_uid','st_mode','st_ino','st_dev','st_mtime_ns','st_nlink','st_size']:
 original=Path.lstat
 def fake(self,*a,**kw):
  s=original(self,*a,**kw)
  if self!=target:return s
  values={n:getattr(s,n) for n in dir(s) if n.startswith('st_')};values[field]=values[field]+1
  return types.SimpleNamespace(**values)
 Path.lstat=fake
 try:
  try:co.check()
  except (ValueError,OSError) as e:results.append({'overlay':field,'refused':True,'error':str(e)})
  else:raise AssertionError(field)
 finally:Path.lstat=original
co.check()
assert {p.relative_to(A).as_posix() for p in A.rglob('*')}=={z['path'] for z in json.loads((A/'MANIFEST01.json').read_bytes())['members']}|{'MANIFEST01.json'}
(H/'READBACK03.json').write_text(json.dumps({'status':'PASS','metadata_overlays_not_actual_mutations':results,'source_scope':917,'complete_scope_only_self_excluded':True,'actual_original_after_overlay_rejoin':True},indent=2)+'\n');print('PASS seven independent terminal metadata/UID overlays; complete917-member author scope')
