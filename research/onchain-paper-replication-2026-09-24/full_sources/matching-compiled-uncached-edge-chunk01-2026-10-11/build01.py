"""Compile only; never load extension. Run under documented finite shell limits."""
import json,hashlib,subprocess,sysconfig
from pathlib import Path
p=Path(__file__).resolve().parent
cmd=['cc','-shared','-fPIC','-O2','-fno-fast-math','-ffp-contract=off','-Wall','-Wextra','-I'+sysconfig.get_path('include'),str(p/'edge_chunk.c'),'-o',str(p/('_edge_chunk'+sysconfig.get_config_var('EXT_SUFFIX')))]
r=subprocess.run(cmd,capture_output=True,timeout=8)
(p/'BUILD.stdout').write_bytes(r.stdout);(p/'BUILD.stderr').write_bytes(r.stderr)
value={'command':cmd,'returncode':r.returncode,'native_loaded':False}
if r.returncode==0:
 q=Path(cmd[-1]);value.update(library=q.name,bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest())
(p/'BUILD01.json').write_text(json.dumps(value,indent=2)+'\n')
raise SystemExit(r.returncode)
