"""Read-only exact receiver delta and eight committed input joins; no Git network."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil,subprocess,sys
H=Path(__file__).resolve().parent;F=H.parent;MAIN=F.parents[2];D=F/'financial-wrapper-continuation-refused-outcome-remote01-2026-10-05'
spec=importlib.util.spec_from_file_location('accepted_bounded_reader',F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05/verify_capture01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);Reader,R=m.Reader,m.R
rd=Reader();source=rd.read(D/'recover01.py','e66b685b2f851199b20efeec25bfbd0bc91bdf01b8de5387e5f546522a9457f9');watch=rd.read(D/'watch01.py','bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18');binding=json.loads(rd.read(D/'SOURCE_BINDING01.json'));base=rd.read(MAIN/binding['base_path'],binding['base_sha256']);inverse=source.decode()
rd.need(len(binding['changes'])==4,'only four declared substitutions')
for change in reversed(binding['changes']):
 rd.need(inverse.count(change['after'])==1,'unique actual inverse replacement');inverse=inverse.replace(change['after'],change['before'],1)
rd.need(inverse.encode()==base and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(base),include_attributes=False),'entire literal and AST inverse')
# Watch is a fixed separately reviewed dependency, not self-reviewed here.
rd.need(watch==rd.read(F/'financial-wrapper-continuation-canonical-transport-bound01-2026-10-05/watch01.py'),'unchanged accepted watch dependency')
ns={'Path':Path,'json':json};nodes=[]
for n in ast.parse(source).body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'REQUIRED','FINAL_POPULATION_COUNT','FILE'} for t in n.targets):nodes.append(n)
 if isinstance(n,ast.FunctionDef) and n.name in {'require','encode','validate_fixed_selection'}:nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual pure receiver selection predicate>','exec'),ns)
sr=rd.read(D/'SELECTED_BODIES01.json','ab73e45455a647c8de7111cd3b629e309e28e27fb42109bf9218b3c52ac83772');selection=json.loads(sr);ns['validate_fixed_selection'](selection);rd.need(ns['encode'](selection)==sr and selection['remote_commit']=='bd3ca812746142c1998e4494335bd11cba975b91','exact real canonical selection')
rows=selection['rows'];rd.need(len(rows)==8 and sum(r['bytes'] for r in rows)==267420 and [r['path'] for r in rows]==sorted(r['path'] for r in rows),'complete fixed eight selected267420-byte population')
controls=[]
for label,value in [('omitted-body',dict(selection,rows=rows[:-1])),('wrong-pin',dict(selection,rows=[dict(rows[0],sha256='0'*64)]+rows[1:]))]:
 try:ns['validate_fixed_selection'](value)
 except ValueError:controls.append({'case':label,'refused':True})
 else:raise AssertionError(label)
rd.need(ns['encode'](selection)!=(json.dumps(selection,separators=(',',':'))+'\n').encode(),'previous compact-encoding mistake would refuse')
def git(args):
 p=subprocess.run(['git','--no-optional-locks','-C',str(MAIN),*args],capture_output=True,check=True,timeout=10);rd.need(not p.stderr and len(p.stdout)<=4*1024**2,'bounded local Git read');return p.stdout
rd.need(git(['rev-parse','HEAD']).decode().strip()==selection['remote_commit'],'actual MainHEAD selectedcommit')
raw=git(['ls-tree','-r','-z',selection['remote_commit'],'--',*[r['path'] for r in rows]]);objects={}
for item in raw.split(b'\0')[:-1]:
 left,name=item.split(b'\t',1);mode,kind,oid=left.decode().split();objects[name.decode()]={'mode':mode,'kind':kind,'oid':oid}
rd.need(set(objects)=={r['path'] for r in rows},'all exact committed paths')
for row in rows:
 actual=rd.read(MAIN/row['path'],row['sha256']);o=objects[row['path']];body=git(['cat-file','blob',o['oid']]);rd.need(actual==body and len(body)==row['bytes'] and o['mode'] in ('100644','100755') and o['kind']=='blob' and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==o['oid'],'all local original/committed/body/OID joins')
rd.need(not any(os.path.lexists(D/n) for n in ('fresh-refused-continuation-outcome01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json')),'all one-use outcome namespaces fresh')
rd.need(shutil.disk_usage(D).free>=10*1024**3,'actual10GiB floor')
rd.finish();r={'schema_version':1,'decision':'ACCEPTED_EXACT_RECEIVER_SOURCE_AND_SELECTED_INPUTS_ONLY','root':str(D),'commit':selection['remote_commit'],'receiver_sha256':R.digest(source),'watch_sha256':R.digest(watch),'selection_sha256':R.digest(sr),'selection_count':8,'selection_bytes':267420,'unique_Git_objects':len({v['oid'] for v in objects.values()}),'expected_operations':10+len({v['oid'] for v in objects.values()})+2*len(rows),'source_binding_sha256':R.digest(rd.read(D/'SOURCE_BINDING01.json')),'full_literal_AST_inverse':True,'unchanged_functions_and_limits':True,'selection_objects':objects,'controls':controls,'dependency_gap_preserved':'REMOTE_ENTRY_GAP01.json','actual_entry_released':False,'checks':rd.checks,'read_bytes':rd.total};rd.finish();R.put(H/'REMOTE_SOURCE_READBACK01.json',r);print(json.dumps(r))
