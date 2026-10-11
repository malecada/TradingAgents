"""Root-only one-use offline binding/publication. Not admission or launch."""
import hashlib, json, os, types
from pathlib import Path
ROOT=Path.cwd().resolve()
HERE=Path(__file__).resolve().parent
BINDER=HERE.parent/'real-data-pilot-full29-transport-binding01-2026-10-09/binder02/bind01.py'
EXPECTED='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
NAME='eth-paper-real-data-end-to-end-resource-20261011-35'
def require(ok,message):
 if not ok: raise ValueError(message)
def raw(x): return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def load(p): return json.loads(p.read_bytes())
def ref(p):
 b=p.read_bytes(); return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,x):
 with p.open('xb') as f: f.write(raw(x))
def main():
 # Review must authenticate this manifest externally. It is no authority object.
 manifest=load(HERE/'MANIFEST01.json')
 for name,pin in manifest['files'].items():
  p=HERE/name
  require(p.resolve().is_relative_to(HERE) and not p.is_symlink(),'noncanonical preparation member')
  require(ref(p)['sha256']==pin['sha256'] and p.stat().st_size==pin['bytes'],'preparation changed')
 require(ref(BINDER)['sha256']==EXPECTED,'accepted binder changed')
 request=load(HERE/'REQUEST01.json')
 parent=ROOT/request['private_parent']
 require(request['private_parent']=='research_artifacts/real_pilot_runtime/pilot-transport-20261011-35-01','private route changed')
 for p in (ROOT/'research_runs'/NAME,ROOT/'research_artifacts'/'archive-dispatch-ethpilot-20261011-35',parent,HERE/'BOUND01.json',HERE/'inputs01',HERE/'ALL_INPUT_REFS01.json',HERE/'BINDING_CHECK01.json'):
  require(not os.path.lexists(p),'fresh route already used: '+str(p))
 require(parent.parent.resolve()==parent.parent and parent.parent.is_dir(),'canonical private scaffold required')
 module=types.ModuleType('accepted_opaque_binder'); module.__file__=str(BINDER)
 exec(compile(BINDER.read_bytes(),str(BINDER),'exec'),vars(module))
 # No connection/key read in this wrapper. Only the reviewed binder consumes
 # the pinned connection internally, and returns metadata without its body.
 parent.mkdir(mode=0o700,exist_ok=False)
 bound=module.bind(ROOT,request)
 save(HERE/'BOUND01.json',bound)
 destination=HERE/'inputs01'; destination.mkdir()
 refs=load(HERE/'PUBLIC_INPUT_REFS_DRAFT01.json')
 for role,value in bound['inputs'].items():
  require(role in refs,'unexpected public role')
  p=destination/(role+'.json'); save(p,value); pin=ref(p)
  refs[role]={'path':pin['path'],'sha256':pin['sha256'],'dataset':'eth'}
 require(set(bound['private_input'])=={'archive_transport'},'unexpected private role')
 for role,pin in bound['private_input'].items():
  refs[role]={'path':pin['path'],'sha256':pin['sha256'],'dataset':'eth'}
 require(len(refs)==72,'full31 role count changed')
 save(HERE/'ALL_INPUT_REFS01.json',refs)
 save(HERE/'BINDING_CHECK01.json',{'status':bound['status'],'experiment':NAME,'actual_opaque_input':bound['private_input'],'all_input_roles':len(refs),'binder':ref(BINDER),'prepared':ref(HERE/'PREPARED01.json'),'request':ref(HERE/'REQUEST01.json'),'bound':ref(HERE/'BOUND01.json'),'claim':False,'network':False,'launch':False})
 print(json.dumps({'status':bound['status'],'all_roles':len(refs),'claim':False,'network':False}))
if __name__=='__main__': main()
