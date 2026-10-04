"""Explicit domain proof for newly selected PAX dependency; byte utilities only."""
import hashlib,importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'utilities'));sha=lambda b:hashlib.sha256(b).hexdigest()
def load(n,f):
 sp=importlib.util.spec_from_file_location(n,H/'utilities'/f);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
old=load('Rold','recovery04.py');new=load('Rnew','recovery_pax01.py');t=H/'pax-tiny';t.mkdir(mode=0o700);root=t/'original';root.mkdir(mode=0o700);directory=root/('a'*99);directory.mkdir(mode=0o700);(directory/'opaque.bin').write_bytes(b'opaque exact PAX bytes\0');m=new.scan(root);archive=t/'canonical.tar.gz';info=new.pack(root,m,archive)
try:list(old.framed_members(archive.read_bytes()))
except ValueError as e:assert str(e)=='noncanonical raw member slash/type';red={'type':type(e).__name__,'reason':str(e)}
else:raise AssertionError('old cut-slash should fail')
out=t/'flat';out.mkdir(mode=0o700);result=new.restore(archive,info,m,out);metadata=json.loads(new.read(out,result['metadata_file']));assert new.read(out,metadata['flat_members'][('a'*99)+'/opaque.bin'])==b'opaque exact PAX bytes\0'
# Truncated compressed body with a matching tiny utility byte descriptor still refuses framing/canonical restoration.
bad=t/'truncated.tar.gz';bad.write_bytes(archive.read_bytes()[:-8]);badinfo=dict(info,bytes=bad.stat().st_size,sha256=sha(bad.read_bytes()));dest=t/'bad-flat';dest.mkdir(mode=0o700)
try:new.restore(bad,badinfo,m,dest)
except BaseException as e:truncated={'type':type(e).__name__,'reason':str(e)}
else:raise AssertionError('truncated accepted')
C=H.parent/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';capture=json.loads((H/'ACTUAL_CAPTURE01.json').read_bytes());canonical=[]
for label,row in capture['scopes'].items():
 manifest=json.loads((C/(label.upper()+'_MANIFEST01.json')).read_bytes());raw=(C/('complete-'+label+'01.tar.gz')).read_bytes();sink=new.ExactSink(raw);new.tar_stream(Path(row['snapshot']),manifest,sink);assert sink.count==len(raw) and sink.hash.hexdigest()==sha(raw);canonical.append({'scope':label,'full_recompression_matches':True,'archive_sha256':sha(raw),'bytes':len(raw)})
(H/'PAX_DOMAIN06.json').write_text(json.dumps({'tiny_original_RED':red,'tiny_new_private_flat_GREEN':result,'tiny_truncated_refusal':truncated,'actual_two_scope_full_canonical_recompression':canonical,'no_actual_Root_restore':True,'ordinary_tiny_bytes_only':True},indent=2,sort_keys=True)+'\n');print(json.dumps({'tiny_old_RED_new_GREEN':True,'actual_canonical_scopes':len(canonical),'truncated_refused':True}))
