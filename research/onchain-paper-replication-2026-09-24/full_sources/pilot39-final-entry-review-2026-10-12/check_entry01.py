"""Metadata and source-only exact entry review; no admissions/imports/scans."""
import ast,hashlib,json,stat,difflib
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];F=D.parent;E=F/'real-data-pilot-full39-entry-preparation01-2026-10-12';O=F/'real-data-pilot-full38-entry-preparation01-2026-10-12';P=F/'real-data-pilot-full39-binding-preparation01-2026-10-12';N='eth-paper-real-data-end-to-end-resource-20261012-39';OLD='eth-paper-real-data-end-to-end-resource-20261012-38';ev={};checks=[]
def pin(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink() and p.resolve()==p
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.lstat();assert all(getattr(s,k)==getattr(t,k) for k in ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns'))
 v={'path':str(p.relative_to(R)),'sha256':h.hexdigest(),'bytes':s.st_size};ev[v['path']]=v['sha256'];return v
def load(p):pin(p);return json.loads(p.read_bytes())
def ck(name,x):assert x,name;checks.append(name)
def reference(x):
 p=R/x['path'];v=pin(p);ck('exact ref '+x['path'],v['sha256']==x['sha256'] and ('bytes' not in x or v['bytes']==x['bytes']));return p
g=load(E/'gate01.json');old=load(O/'gate01.json');b=load(E/'BINDING_DRAFT01.json');ex=g['experiments'][N];prev=old['experiments'][OLD]
ck('exact frozen gate',pin(E/'gate01.json')['sha256']=='0d9691570304849f518ec983fdb62e7b8bd9c8092828c7846a0dae1869382dea')
ck('16definitions all15old preserved',len(g['experiments'])==16 and len(old['experiments'])==15 and all(g['experiments'][k]==v for k,v in old['experiments'].items()))
ck('program family datasets preserved',all(g[k]==old[k] for k in old if k!='experiments'))
ck('fresh parentNone exactwholecell',ex['parent'] is None and ex['cells']==['real-eth-whole-seven-graph-joint-pilot-resource39'])
ck('original fields retained',all(ex[k]==prev[k] for k in ['charter','cumulative_budget_extension','family','reuse','runtime_hashes','selection','stage','windows']))
ck('exact1142pins preserves1036',len(ex['source_files'])==1142 and len(prev['source_files'])==1036 and all(ex['source_files'].get(k)==v for k,v in prev['source_files'].items()))
for p,h in ex['source_files'].items():ck('current registered '+p,pin(R/p)['sha256']==h)
inputs={k:{z:v[z] for z in ('path','sha256')} for k,v in ex['inputs'].items()};ck('actual73 binding roster',len(inputs)==73 and b['input_refs']==inputs and b['identity']==N)
for role,v in inputs.items():reference(v)
for role,ref in b.items():
 if role!='binding_review' and type(ref) is dict and {'path','sha256'}<=set(ref):reference(ref)
nulls=sorted(k for k,v in b.items() if v is None);ck('genuine unavailable refs retained',nulls==['binding_readback','binding_review','complete_increment_recovery','endpoint_review','new_increment_recovery_review'])
opaque=R/b['transport']['path'];ck('soleopaque930modeparent',pin(opaque)['bytes']==930 and stat.S_IMODE(opaque.stat().st_mode)==0o600 and stat.S_IMODE(opaque.parent.stat().st_mode)==0o700 and [k for k,v in inputs.items() if v['path']==b['transport']['path']]==['archive_transport'])
# No decoding of opaque body.
core=load(E/'CORE_MANIFEST01.json');priorcore=load(O/'CORE_MANIFEST01.json')
for role,ref in core['inputs'].items():
 reference(ref);ck('current core role '+role,all(ref[k]==inputs[role][k] for k in ('path','sha256')))
 current=load(R/ref['path']);prior=load(R/priorcore['inputs'][role]['path'])
 if role=='mcm_policy':prior.pop('entry_qualification');ck('removeonlyentryqualification',current==prior and 'entry_qualification' not in current)
 else:ck('unchangedscientificcore '+role,current==prior)
scratch=load(R/inputs['matching_ordered_edge_scratch']['path']);ps=load(O/'MATCHING_SCRATCH_RESERVATION01.json');ps['experiment']=N;ck('scratchselectoronly',scratch==ps)
job=load(R/inputs['execution_job']['path']);obs=load(E/'BASELINE_STORAGE_OBSERVATION01.json');ck('actualjob unchangednative limits',job['resources']==obs['resources'])
selected=next(iter(job['payload']['representation_jobs'].values()));pilot=load(R/inputs[selected['real_pilot_input']]['path']);ck('pilot exact cell and full denominator',pilot['cell_id']==ex['cells'][0] and 'partial_progress' not in pilot and 'scoring_diagnostic' not in pilot)
capacity=load(E/'CAPACITY_DECLARATION_ROOT01.json');public=load(E/'PUBLIC_MANIFEST01.json');cm=load(E/'CAPACITY_SOURCE_MAP01.json')
ck('unchanged428capacitysource',cm==load(O/'CAPACITY_SOURCE_MAP01.json') and len(cm)==428 and cm==capacity['source_body_pins']==public['source_pins'] and all(ex['source_files'][k]==v for k,v in cm.items()))
ck('acceptedgrowth exactresult',capacity['basis']['growth_review']==pin(D/'GROWTH_REVIEW01.json') and capacity['whole_projection']==load(E/'ROOT_GROWTH_PROJECTION01.json')==load(E/'WHOLE_CAPACITY_RESULT01.json'))
ck('capacity limitedwholestorage',capacity['decision']=='accepted' and capacity['identity']==N and capacity['memory_fit_proven'] is False and capacity['full_pilot_capacity_admitted'] is False and capacity['physical_reservation'] is False and capacity['whole_cells']==415968128 and capacity['whole_graphs']==7)
review=load(F/'pilot39-entry-source-review-2026-10-12/SOURCE_PUBLIC_REVIEW01.json');ck('acceptedhelpercurrent',pin(E/'prepare_entry01.py')['sha256']==review['helper_sha256'] and review['decision']=='accepted')
ck('genuine110two-keyreview',ex['cumulative_budget_extension']['review']==b['budget_review'] and set(b['budget_review'])=={'path','sha256'})
for v in ex['cumulative_budget_extension'].values():reference(v)
for n in ['preflight39_01.py','root_io39_01.py']:
 before=(O/n.replace('39','38')).read_text();after=(E/n).read_text();ast.parse(after)
 actual=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=n.replace('39','38'),tofile=n))
 ck('exact recorded literal patch '+n,(E/(n+'.diff')).read_text()==actual);pin(E/n);pin(E/(n+'.diff'))
src=(E/'preflight39_01.py').read_text();tree=ast.parse(src);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='check');body=ast.get_source_segment(src,fn)
ck('missingrecoveryrefusesbeforegitadmission',body.index("'complete_increment_recovery','new_increment_recovery_review'")<body.index('subprocess.check_output')<body.index('_admitted(args)'))
ck('whole stop absence enforced',"need('entry_qualification' not in mcm" in src)
# Bind unchanged accepted binder and current controls as required by final preflight.
assign={x.targets[0].id:ast.literal_eval(x.value) for x in tree.body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id in ['BINDER','FROZEN_PREPARATION']}
reference(assign['BINDER']);ck('exact current preparedbody',assign['FROZEN_PREPARATION']==b['preparation'])
op=load(E/'ROOT_PREPARATION_OPERATION01.json');ck('actualonce metadataonlypreparation',op['actual_exit']==0 and op['claim'] is False and op['numerical_execution'] is False)
out={'schema_version':1,'decision':'accepted','identity':N,'input_refs':inputs,'evidence':ev,'reviewer':'independent integration reviewer /root/pilot_efficiency_integration_review','scope':'Actual concrete39 gate and currently known draft binding references only; pending actual entry recovery/final binding/release remain unavailable.','source_count':1142,'input_count':73,'preserved_definitions':15,'preserved_source_pins':1036,'checks':checks,'unavailable_binding_roles':nulls,'limitations':['No admission/helper/binder/scans/numerical/Owner/claim/Git/network execution.','This review must be supplemented with actual new recovery and any new bound references before final binding/release acceptance.','Prospective guarded storage only; full training memory fit and physical reservation remain unproved.']}
with (D/'BINDING_REVIEW01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'checks':len(checks),'evidence':len(ev),'review':pin(D/'BINDING_REVIEW01.json')}))
