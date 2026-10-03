"""Root-invoked preparation only. Never register, commit, admit or launch.

Export -> root establishes genuine Git/anchor -> inputs -> root commits source
and templates -> materialization drafts -> root final A/release -> actual proof
-> comparison drafts at A -> root sole-child B/release. No automatic retries.
"""
import argparse,ast,hashlib,importlib.util,json,os,re,stat,subprocess,sys
from pathlib import Path
BASE='research/onchain-paper-replication-2026-09-24/full_sources/'
CSC=BASE+'neural-cold-feature-handoff-proof-source-composition03-2026-10-03'
GEN=BASE+'neural-cold-feature-handoff-engineering-registration-preparation03-2026-10-03'
PINS={CSC+'/MANIFEST03.json':'4c770e65ca9b4c93335cf1cf87610fd9f24097da939252ce897afc43e8e1b7a8',GEN+'/MANIFEST03.json':'44a3f97a480084c233bba66c13a90dbc7b72ea204c1150ac499f073ea57ec4d2'}
INV='8576e2baba60576818ee4def16fcfad32cc69bd197c4ff1b727808d9695786d2'
GIB=1073741824;MAX=4194304

def require(v,m):
 if not v:raise ValueError(m)
def digest(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def relative(name):
 require(type(name) is str and bool(name),'relative path required');p=Path(name)
 require(not p.is_absolute() and '..' not in p.parts and str(p)==name and not any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') for x in p.parts),'unsafe path')
 return name
def reference_shape(r):
 require(type(r) is dict and set(r)=={'path','sha256'} and type(r['sha256']) is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'exact body reference required');relative(r['path'])
def bounded(root,name):
 p=root/relative(name);require(p.resolve()==p,'redirected body');s=p.lstat()
 require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=MAX,'bounded single-link body required')
 b=p.read_bytes();t=p.lstat();require((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns) and len(b)==s.st_size,'body changed');return b
def ref(root,r):
 reference_shape(r);b=bounded(root,r['path']);require(digest(b)==r['sha256'],'reference mismatch');return b
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},stderr=subprocess.PIPE,timeout=15)
def ordered_rows(rows):
 require(type(rows) is list and len(rows)==195,'195 source rows required')
 names=[relative(r['target']) for r in rows];require(names==sorted(set(names)),'unique sorted source rows required')
 for r in rows:require(type(r['bytes']) is int and 0<r['bytes']<=MAX and type(r['sha256']) is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'source extent/hash differs')
 return rows
def runtime_shape(v):
 rows=v['distribution_records'];require(type(rows) is list and len(rows)==251 and len({r['name'] for r in rows})==251,'251 unique runtime RECORD bindings required')
 for r in rows:require(type(r['record']) is str and Path(r['record']).is_absolute() and type(r['record_sha256']) is str and re.fullmatch('[0-9a-f]{64}',r['record_sha256']),'runtime RECORD pin absent')
def request_shape(v):
 common={'schema_version','stage','repository','provenance_commit','capsule'}
 fields={'export':set(),'inputs':{'anchor','resources','environment','runtime','cpus'},'materialize':{'request','output'},'compare':{'request','output'}}
 require(type(v) is dict and v.get('stage') in fields and set(v)==common|fields[v['stage']] and type(v['schema_version']) is int and v['schema_version']==1,'preparation stage fields differ')
 require(type(v['provenance_commit']) is str and re.fullmatch('[0-9a-f]{40}',v['provenance_commit']),'genuine provenance commit required')
 for k in ('repository','capsule'):require(type(v[k]) is str and Path(v[k]).is_absolute() and Path(v[k]).resolve()==Path(v[k]),'absolute direct root required')
 require(not Path(v['capsule']).is_relative_to(Path(v['repository'])),'fresh independent capsule outside source repository required')
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verify_preparation(repo,commit):
 require(not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules),'no numerical/research imports')
 require(git(repo,'rev-parse',commit+'^{commit}').decode().strip()==commit,'provenance commit missing')
 for name,h in PINS.items():
  raw=bounded(repo,name);require(digest(raw)==h and git(repo,'show',commit+':'+name)==raw,'accepted manifest/Git differs')
  manifest=json.loads(raw);parent=str(Path(name).parent)
  require(len(manifest['files'])==manifest['file_count'],'manifest count differs')
  require(len({r['path'] for r in manifest['files']})==len(manifest['files']),'duplicate manifest members')
  for r in manifest['files']:
   path=parent+'/'+relative(r['path']);b=bounded(repo,path)
   require(len(b)==r['bytes'] and digest(b)==r['sha256'] and git(repo,'show',commit+':'+path)==b,'preparation source/Git differs: '+path)
 invraw=bounded(repo,CSC+'/source_inventory03.json');require(digest(invraw)==INV,'selected195 inventory differs')
 inv=json.loads(invraw);rows=ordered_rows(inv['source_inventory']);require(inv['package_count']==147,'package147 required')
 for r in rows:
  raw=bounded(repo,CSC+'/source-bodies/'+r['target']);require(len(raw)==r['bytes'] and digest(raw)==r['sha256'],'copied body differs')
  if r.get('git_commit') is not None:require(git(repo,'show',r['git_commit']+':'+r['git_path'])==raw,'historical Git origin differs')
  else:require(git(repo,'show',commit+':'+CSC+'/source-bodies/'+r['target'])==raw,'candidate committed snapshot differs')
 return inv,load(repo/GEN/'generate03.py','accepted_cold_generator03'),load(repo/CSC/'prepare_metadata_composed03.py','accepted_composed_metadata03')
def put(gen,root,name,data):
 relative(name);p=root/name;require(p.resolve()==p and not p.exists() and not p.is_symlink(),'exclusive destination required')
 p.parent.mkdir(parents=True,exist_ok=True);gen.write_exclusive(p,data)
 return {'path':name,'sha256':digest(data)}
def git_installed(root,rows):
 require((root/'.git').is_dir() and not (root/'.git').is_symlink() and not (root/'.git/objects/info/alternates').exists(),'root must establish independent real Git first')
 commit=git(root,'rev-parse','HEAD').decode().strip()
 for r in rows:
  b=bounded(root,r['target']);require(digest(b)==r['sha256'] and git(root,'show',commit+':'+r['target'])==b,'installed committed source differs')
 return commit
def native_map(root):
 tree=ast.parse(bounded(root,'tradingagents/research/onchain_replication/resources.py'))
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_native_owned_env'];require(len(nodes)==1,'selected native environment helper missing')
 ns={'Path':Path};exec(compile(ast.Module(body=nodes,type_ignores=[]),'selected-native-map','exec'),ns)
 return ns['_native_owned_env'](root)
def execute(request):
 request_shape(request);repo=Path(request['repository']);root=Path(request['capsule']);stage=request['stage']
 inv,gen,metadata=verify_preparation(repo,request['provenance_commit']);rows=inv['source_inventory']
 if stage=='export':
  require(not root.exists() and root.parent.is_dir(),'capsule must be fresh with existing parent')
  total=sum(r['bytes'] for r in rows);require(total<=8*1024**2,'source export bound exceeded')
  root.mkdir(mode=0o700)
  for r in rows:
   data=bounded(repo,CSC+'/source-bodies/'+r['target']);require(len(data)==r['bytes'] and digest(data)==r['sha256'],'source changed before copy')
   put(gen,root,r['target'],data)
  put(gen,root,'cold_prep/source_inventory.json',bounded(repo,CSC+'/source_inventory03.json'))
  for name in ('CHARTER_MATERIALIZE02.md','CHARTER_COMPARE02.md','HISTORY02.md'):put(gen,root,'cold_prep/'+name,bounded(repo,GEN+'/'+name))
  result={'status':'unregistered-source-export','source_count':195,'package_count':147,'logical_source_bytes':total,'origin_commit':request['provenance_commit'],'actual_capsule_commit':None,'execution_authorized':False}
  put(gen,root,'cold_prep/export.json',encoded(result));return result
 require(root.is_dir() and root.resolve()==root and Path.cwd()==root,'existing genuine capsule and cwd required');source=git_installed(root,rows)
 require(digest(bounded(root,'cold_prep/source_inventory.json'))==INV,'capsule inventory changed')
 if stage=='inputs':
  # Source/anchor ancestry exists before any draft input is generated.
  documents={k:json.loads(ref(repo,request[k])) for k in ('anchor','resources','environment','runtime')}
  anchor=documents['anchor'];require(set(anchor)=={'commit','files'} and anchor['files'],'genuine numerical anchor required')
  git(root,'merge-base','--is-ancestor',anchor['commit'],source)
  for name,h in anchor['files'].items():require(digest(git(root,'show',anchor['commit']+':'+relative(name)))==h,'numerical anchor object differs')
  gen.resources(root,documents['resources']);runtime_shape(documents['runtime'])
  cpus=request['cpus'];require(type(cpus) is list and len(cpus)==2 and all(type(n) is int and n>=0 for n in cpus) and cpus==sorted(set(cpus)),'two exact CPUs required')
  checker=load(root/'proof_tools/runtime_gate01.py','capsule_runtime_check01');checker.check(root,documents['runtime'])
  refs={k:put(gen,root,'cold_prep/'+k+'.json',encoded(v)) for k,v in documents.items()}
  envref=put(gen,root,'cold_prep/native_environment.json',encoded(native_map(root)))
  draft=metadata.build(root,root/'cold_inputs',root/refs['anchor']['path'],root/refs['resources']['path'],root/refs['environment']['path'],root/'cold_prep/source_inventory.json')
  inputs=draft['first_experiment']['inputs'];require(len(inputs)==9,'initial nine input denominator differs')
  req={'schema_version':1,'phase':'materialize','root':str(root),'source':source,'inventory':{'path':'cold_prep/source_inventory.json','sha256':INV},'runtime':refs['runtime'],'native_environment':envref,'environment':{k:inputs['environment'][k] for k in ('path','sha256')},'resources':{k:inputs['future_resources'][k] for k in ('path','sha256')},'anchor':{k:inputs['anchor'][k] for k in ('path','sha256')},'inputs':inputs,'cpus':cpus}
  put(gen,root,'cold_prep/materialize-request.json',encoded(req))
  return {'status':'unregistered-nine-input-draft','request':'cold_prep/materialize-request.json','source_at_preparation':source,'root_must_rebind_request_to_actual_source_before_render':True,'execution_authorized':False}
 req=json.loads(ref(root,request['request']));require(req['source']==source,'request must bind current actual source')
 out=gen.new_path(root,request['output'])
 if stage=='materialize':
  require(req.get('phase')=='materialize','materialization request required')
  charter={'path':'cold_prep/CHARTER_MATERIALIZE02.md','sha256':digest(bounded(root,'cold_prep/CHARTER_MATERIALIZE02.md'))};history={'path':'cold_prep/HISTORY02.md','sha256':digest(bounded(root,'cold_prep/HISTORY02.md'))}
  value=gen.render(root,req,charter,history);gen.write_exclusive(out,encoded(value))
 else:
  require(req.get('phase')=='compare','comparison request required')
  value=gen.prepare_compare(root,req);require(request['output'] not in value['files'],'external gate must not overlap B additions')
  require(all((root/p).parent.is_dir() for p in value['files']) and out.parent.is_dir(),'existing genuine draft parents required')
  for name,b in value['files'].items():gen.write_exclusive(root/name,b)
  gen.write_exclusive(out,encoded(value['gate_template']))
 return {'status':'unregistered-draft','stage':stage,'output':request['output'],'execution_authorized':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--request',required=True);a=p.parse_args();path=Path(a.request).resolve();s=path.lstat();require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=MAX,'bounded root request required')
 result=execute(json.loads(path.read_bytes()));print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
