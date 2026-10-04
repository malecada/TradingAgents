import gzip,hashlib,importlib.util,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'financial-genuine-wrapper-recordfix-failed-scope-recovery-preparation01-2026-10-04';sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('footer_source',P/'restore01.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);R=M.R;src=O/'owned/tiny-source';manifest=R.scan(src);arc=O/'owned/source.tar.gz';raw=arc.read_bytes();inflated=gzip.decompress(raw);bad=inflated[:-1]+b'X';new=gzip.compress(bad,mtime=0);badpath=O/'owned/footer-nonzero.tar.gz';badpath.write_bytes(new);dest=O/'owned/footer-refusal';M.reserve(dest);info={'bytes':len(new),'sha256':R.digest(new),'manifest_sha256':R.digest(R.encode(manifest))}
try:R.restore(badpath,info,manifest,dest)
except ValueError as e:result={'schema_version':1,'test':'real tiny nonzero TAR footer despite matching supplied archive hash','refusal_type':type(e).__name__,'message':str(e),'actual_fullscope_restore':False}
else:raise AssertionError('nonzero footer accepted')
(O/'FOOTER_REFUSAL03.json').write_bytes(R.encode(result));print(json.dumps(result))
