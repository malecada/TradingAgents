from pathlib import Path
import ast,json,hashlib,difflib,copy
R=Path.cwd();H=Path('research/onchain-paper-replication-2026-09-24/full_sources');B=H/'pilot35-entry-source-candidate01-2026-10-11';A=H/'real-data-pilot-full34-entry-preparation01-2026-10-11';E=H/'real-data-pilot-full35-entry-preparation01-2026-10-11';T=H/'real-data-pilot-full35-binding-preparation01-2026-10-11';O=H/'pilot35-entry-source-review01-2026-10-11';refs={};checks=[]
def ref(p):
 b=p.read_bytes();v={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};refs[str(p)]=v;return v
def read(p):ref(p);return json.loads(p.read_text())
def ck(v,n):assert v,n;checks.append(n)
def dump(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
m=read(B/'MANIFEST01.json');ck(refs[str(B/'MANIFEST01.json')]['sha256']=='fbeab2b4e9a6ddf46436e8075ee31cca8428e6130ecd4af838e9ac5da5f315cf','exact frozen candidate')
for n,q in m['files'].items():a=ref(B/n);ck(all(a[k]==q[k] for k in ('bytes','sha256')),'frozen member '+n)
fw='';iv=''
for n in ('prepare_source01.py','prepare_registration01.py'):
 a=(A/n).read_text();b=(B/n).read_text();ref(A/n);ast.parse(b);fw+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='full34/'+n,tofile='candidate35/'+n));iv+=''.join(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='candidate35/'+n,tofile='full34/'+n))
ck(fw==(B/'FORWARD02.patch').read_text() and iv==(B/'INVERSE02.patch').read_text(),'exact final builder diffs')
source=(B/'prepare_source01.py').read_text();st=ast.parse(source);reg=(B/'prepare_registration01.py').read_text();rt=ast.parse(reg)
def assignment(tree,name):return next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(z,ast.Name) and z.id==name for z in n.targets))
old=(A/'preflight34_01.py').read_text();out=old;changes=ast.literal_eval(assignment(st,'changes'))
for a,b in changes:ck(a in out,'actual replaced seam '+a);out=out.replace(a,b)
oldline=next(l for l in old.splitlines() if l.startswith('FROZEN_PREPARATION='));moved=oldline.replace('20261011-34','20261011-35');replacement='FROZEN_PREPARATION='+repr(ref(T/'PREPARED01.json'));out=out.replace(moved,replacement)
execution=read(T/'public01/mcm_policy.json')['batched']['execution'];line=next(l for l in out.splitlines() if l.startswith('COMPILED_INPUTS='));insert='\nEDGE_POLICY='+repr(execution['compiled_edge_policy'])+'\nEDGE_INPUTS='+repr(execution['compiled_edge_inputs']);out=out.replace(line,line+insert);added=ast.literal_eval(assignment(st,'added'));seam=ast.literal_eval(assignment(st,'seam'));out=out.replace(seam,added+seam);ast.parse(out)
x=out.replace(added,'').replace(insert,'').replace(replacement,moved)
for a,b in reversed(changes):x=x.replace(b,a)
ck(x==old and ast.dump(ast.parse(x))==ast.dump(ast.parse(old)),'emitted preflight complete literal AST inverse')
oldres=ast.literal_eval(assignment(ast.parse(old),'EXPECTED_RESOURCES'));newres=ast.literal_eval(assignment(ast.parse(out),'EXPECTED_RESOURCES'));ck(newres==json.loads(json.dumps(oldres).replace('20261011-34','20261011-35')),'exact native controls identityonly')
ck((A/'root_io34_01.py').read_text().count('from preflight34_01 import check')==1 and "newio=oldio.replace('from preflight34_01 import check','from preflight35_01 import check')" in source,'RootIO sole import')
cap=read(E/'CAPACITY_DECLARATION_ROOT01.json');mapping=read(E/'CAPACITY_SOURCE_MAP01.json');oldmap=read(A/'CAPACITY_SOURCE_MAP01.json');oldcap=read(A/'CAPACITY_DECLARATION_ROOT01.json');ck(refs[str(E/'CAPACITY_SOURCE_MAP01.json')]['sha256']=='713bfa99920959ce0807b2e3c987ad79a11aaa2fb39d767f39da5757210d37be' and refs[str(E/'CAPACITY_DECLARATION_ROOT01.json')]['sha256']=='ab58496b354cd4b0bd97fa514d715383fb578235f53e8462ad52940f4647b179','actual Root capacity/map hashes')
pins=mapping['source_files'];ck(len(pins)==423 and cap['source_body_pins']==pins and mapping['source_anchor']==cap['source_anchor']=='53b8890630765d06f8a44e3e8fbaee1f4b00bdfb','423Root pins sourceanchor')
ck(all(ref(R/p)['sha256']==h for p,h in pins.items()),'all423actual source body joins')
addedpaths=set(pins)-set(oldmap['source_files']);changed={p for p,h in oldmap['source_files'].items() if pins[p]!=h};ck(len(oldmap['source_files'])==421 and len(addedpaths)==2 and len(changed)==13,'421with13changes2helpers')
num=read(T/'public01/pair_policy.json')['numerical_source'];ck(len(num['files'])==200 and num['commit']==mapping['source_anchor'] and all(pins[p]==h for p,h in num['files'].items()),'actual200closure subset')
for k in ('new_logical_growth_bytes','new_allocated_growth_bytes','non_directory_new_allocated_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes','allocation_semantics','directory_and_other_writers_included','runtime_residuals_included'):ck(cap[k]==oldcap[k],'unchanged capacity formula '+k)
ck(cap['owned_paths']==[p.replace('20261011-34','20261011-35') for p in oldcap['owned_paths']],'capacity ownedidentity only')
core=read(A/'CORE_MANIFEST01.json')
for role,q in core['inputs'].items():
 oldbody=read(Path(q['path']));current=read(T/'public01'/(role+'.json'))
 if role=='mcm_policy':del current['batched']['execution']['compiled_edge_policy'];del current['batched']['execution']['compiled_edge_inputs']
 ck(oldbody==current,'original core unchanged '+role)
budget=read(H/'pilot35-cumulative-machine-review01-2026-10-11/EXTENSION106_REVIEW01.json');ck(refs[str(H/'pilot35-cumulative-machine-review01-2026-10-11/EXTENSION106_REVIEW01.json')]['sha256']=='606114a28d18d01843c0b27db95dcaaeb18357a78229fe50dce39c8ac3f70b9d' and budget['decision']=='accepted' and set(budget)=={'schema_version','decision','extension_sha256','reviewer','scope'},'strict actual106accepted')
commands=read(B/'COMMANDS01.json');ck(commands['source']['argv'][-2:]==[mapping['source_anchor'],refs[str(E/'CAPACITY_DECLARATION_ROOT01.json')]['sha256']] and commands['registration']['argv'][-1]==refs[str(H/'pilot35-cumulative-machine-review01-2026-10-11/EXTENSION106_REVIEW01.json')]['sha256'],'exact commandargvactualpins')
ck("for k in ('path','sha256')" in reg and "'e0a1e3f89926094373e6c58022627e5861cda03064657e88a245129756810b9a'" in reg and "'0320608cc703f7c8c2e4f1867bfc478a51efcd62ac70d318b409bd49c55815db'" in reg,'strict extension/allocation sourcepins andtwofieldrefs')
ck(ref(Path('tradingagents/research/onchain_replication/matching_annealing.py'))['sha256']=='86ccc3a471827bdce7784145914240d04416d2cc0023e8acb77fb26ae473df57' and "scratch['installed_source']['sha256']=ref(ROOT/kernel)['sha256']" in reg,'actual current scratchkernel86ccc')
if (T/'ALL_INPUT_REFS01.json').exists():
 boundrefs=read(T/'ALL_INPUT_REFS01.json');draft=read(T/'PUBLIC_INPUT_REFS_DRAFT01.json');ck(len(boundrefs)==72 and len(draft)==71 and set(boundrefs)==set(draft)|{'archive_transport'},'actual72bound71draft')
 for kind,role in execution['compiled_edge_inputs'].items():q=boundrefs[role];ck(q['sha256']==execution['compiled_edge_policy'][kind+'_sha256'] and str(R/q['path'])==execution['compiled_edge_policy'][kind+'_path'],'actualnative role join '+kind)
ck("experiment=copy.deepcopy(gate['experiments'][PRIOR])" in reg and "gate['experiments'][NAME]=experiment" in reg and "'binding_review':None" in reg,'preserved historicalgate and freshchild draftonly')
ck("save(HERE/'CAPACITY_DECLARATION_ROOT01.json'" not in source and "save(HERE/'CAPACITY_SOURCE_MAP01.json'" not in source,'doesnot overwrite Rootcapacity')
result={'decision':'accepted','scope':'Exact two prospective E35 builder sources and commands only; no actual generated gate/preflight/binding/release acceptance.','checks':checks,'references':refs,'commands':commands,'root_verdict':'Copy exact reviewed builders to E35 then execute source argv once, followed by registration argv once after actual bound72 and all declared prerequisites. Existing exclusive outputs must be absent.','limits':['No builders/Git/binder/native/science/authority executed by this review.','Current423body hashes and200subset verified, but builder must independently check actualHEAD+committedblob joins before output.','Root capacity declaration/formula reuse is conditional source evidence, not measured whole workload capacity or external reservation.','Actual generated entry/gate/binding/final release and preparation recovery must be reviewed before empirical launch.','Historical34failed/spent and105adopted remain;106review is prospective only.']}
dump(O/'REVIEW01.json',result);(O/'REPORT.md').write_text('Accepted exact prospective E35 source and registration builders. Final builderdiffs and emitted preflight literal/AST inverse verified; original native/scientific controls remain except declared identity106/423/72andfive-role selection joins. Actual Root713bmap/ab58declaration match423current bodies (13updated+2helpers);200numerical closure subset and kernel86ccc match. Strict106review606and sourcepinned extension/allocation refs retained. Root capacity/map not rewritten. Root may copy and execute exact COMMANDS01 source then registration once, subject to fresh existing guards. No actualgate/release/admission/launch approval or empirical capacity claim.\n');dump(O/'MANIFEST01.json',{'status':'FROZEN_ENTRY_BUILDER_SOURCE_REVIEW','files':{p.name:ref(p) for p in O.iterdir()}});print(json.dumps({'review':ref(O/'REVIEW01.json'),'manifest':ref(O/'MANIFEST01.json'),'checks':len(checks)}))
