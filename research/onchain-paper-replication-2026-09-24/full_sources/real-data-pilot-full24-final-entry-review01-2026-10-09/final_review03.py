import pathlib,json,hashlib,subprocess,ast,copy,stat,os,resource,signal
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();E=F/'real-data-pilot-full24-entry01-2026-10-09';G=F/'real-data-pilot-grouped-registration01-2026-10-09';T=F/'real-data-pilot-full24-transport-binding01-2026-10-09';P=F/'real-data-pilot-full24-input-binding01-2026-10-09'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
b=j(E/'BINDING_DRAFT04.json');gate=j(E/'gate01.json');name=b['identity'];entry=gate['experiments'][name];norm=lambda d:{k:{q:v[q] for q in ('path','sha256')} for k,v in d.items()};inputs=norm(entry['inputs']);evidence={}
def pin(ref):
 path=ref['path'];p=ROOT/path;assert p.is_file() and p.resolve()==p and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2,path
 assert h(p)==ref['sha256'],path
 if path in evidence:assert evidence[path]==ref['sha256']
 evidence[path]=ref['sha256']
assert len(inputs)==64 and len(entry['source_files'])==378
assert inputs==b['input_refs']==norm(j(G/'ALL_INPUT_REFS01.json'))
for path,digest in entry['source_files'].items():pin({'path':path,'sha256':digest})
for ref in inputs.values():pin(ref)
for role,ref in b.items():
 if isinstance(ref,dict) and {'path','sha256'}<=ref.keys():pin(ref)
assert b['binding_review'] is None
public=j(P/'PUBLIC_MANIFEST04.json');core=j(P/'CORE_MANIFEST03.json');prepared=j(T/'PREPARED01.json');bound=j(T/'BOUND01.json');prior=j(P/'PUBLIC_INPUT_REFS04.json')
assert prepared['preparation_origin']['public_manifest']==b['public_manifest']
assert bound['source_request']['prepared']==b['preparation'] and bound['source_request']['archive_policy']==b['unbound_archive']
assert prepared['builder03_spec']['references']['archive_policy']==b['unbound_archive']
for role,document in bound['inputs'].items():assert j(ROOT/inputs[role]['path'])==document
for role,ref in core['inputs'].items():assert j(ROOT/inputs[role]['path'])==j(ROOT/ref['path'])
for role in set(prior)-set(bound['inputs'])-{'archive_transport','matching_ordered_edge_scratch'}:assert inputs[role]['sha256']==prior[role]['sha256']
assert bound['private_input']=={'archive_transport':b['transport']}
private=ROOT/b['transport']['path'];assert stat.S_IMODE(private.stat().st_mode)==0o600 and stat.S_IMODE(private.parent.stat().st_mode)==0o700 and private.stat().st_size==b['transport']['bytes']
assert entry['cumulative_budget_extension']['review']==b['budget_review']
oldgate=j(F/'real-data-pilot-final23-2026-10-09/gate03.json');oldentry=oldgate['experiments']['eth-paper-real-data-end-to-end-resource-20261009-23']
for k in ('families','datasets','program_id'):assert gate[k]==oldgate[k]
for k in ('family','stage','windows','reuse','selection','runtime_hashes'):assert entry[k]==oldentry[k],k
assert entry['parent']=='eth-paper-real-data-end-to-end-resource-20261009-23' and entry['cells']==['real-eth-seven-graph-joint-update-resource24']
assert entry['outputs']==[x for x in oldentry['outputs'] if x!='real-pilot-scoring-diagnostic.json']
pin(entry['charter']);ext=j(ROOT/entry['cumulative_budget_extension']['extension']['path']);pin(entry['cumulative_budget_extension']['extension']);pin(ext['allocation']);assert ext['cumulative_ceiling']==95 and ext['consumed_before']==63
assert j(ROOT/b['budget_review']['path'])['extension_sha256']==h(ROOT/entry['cumulative_budget_extension']['extension']['path'])
cap=j(ROOT/b['capacity_observation']['path']);assert cap['source_body_pins']==public['source_pins'] and len(cap['source_body_pins'])==365
assert 'source' not in cap and 'max_age_seconds' not in cap
assert all(entry['source_files'].get(p)==v for p,v in cap['source_body_pins'].items())
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert subprocess.run(['git','merge-base','--is-ancestor',cap['source_anchor'],head]).returncode==0
assert 'Remaining joins checked' in (R/'REMAINING_CHECK04.log').read_text()
assert cap['directory_allocated_bound_bytes']==2*1024**3 and cap['other_writer_reserved_bytes']==1024**3
assert cap['new_allocated_growth_bytes']==cap['non_directory_new_allocated_growth_bytes']+3*1024**3==13551374941
assert cap['new_logical_growth_bytes']==10988852301 and cap['new_entries']==650000
forecast=j(F/'mcm-batched-grouped-capacity03-2026-10-09/CAPACITY01.json');assert cap['non_directory_new_allocated_growth_bytes']==forecast['joined']['non_directory_increment_allocated_upper']
scratch=j(ROOT/inputs['matching_ordered_edge_scratch']['path']);assert scratch['experiment']==name and scratch['incremental_explicit_numeric_scratch_bytes']==262144 and scratch['chunk_edge_products']==1024
for k in ('installed_source','current_validation_source_review','independent_source_review'):pin(scratch[k])
assert entry['source_files'][scratch['installed_source']['path']]==scratch['installed_source']['sha256']
manifest=j(E/'MANIFEST03.json')
for n,v in manifest['files'].items():pin({'path':str((E/n).relative_to(ROOT)),'sha256':v})
assert (E/'root_io24_03.py').read_text().replace('from preflight24_03 import check','from preflight24_02 import check')==(E/'root_io24_02.py').read_text()
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef)}
f1=funcs(E/'preflight24_02.py');f2=funcs(E/'preflight24_03.py');assert all(f1[k]==f2[k] for k in f1 if k!='prepared_inputs')
for p in [E/'preflight24_03.py',E/'root_io24_03.py',R/'TRANSPORT_REVIEW01.json',F/'mcm-batched-full24-core-review01-2026-10-09/SOURCE_REVIEW03.json',F/'mcm-batched-full24-core-review01-2026-10-09/SOURCE_REVIEW02.json',T/'bind_actual01.py',P/'bind_public04.py',P/'bind_core03.py',E/'BINDING_DRAFT04.json']:
 pin({'path':str(p.relative_to(ROOT)),'sha256':h(p)})
# Exact helper refs required by caller, and nested declaration evidence.
tree=ast.parse((E/'preflight24_03.py').read_bytes());constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('INDEX_CAPACITY','BINDER','EXPECTED_RESOURCES')}
for k in ('INDEX_CAPACITY','BINDER'):pin(constants[k])
job=j(ROOT/inputs['execution_job']['path']);assert job['resources']==constants['EXPECTED_RESOURCES']
for ref in cap['basis'].values():pin(ref)
assert not (ROOT/'research_runs'/name).exists()

previous=j(E/'gate-PREDECESSOR01.json');ps=previous['experiments'][name]['source_files'];assert len(ps)==375
assert all(entry['source_files'][p]==v for p,v in ps.items())
assert set(entry['source_files'])-set(ps)=={str((E/n).relative_to(ROOT)) for n in ('preflight24_03.py','root_io24_03.py','MANIFEST03.json')}
gcopy=copy.deepcopy(gate);gcopy['experiments'][name]['source_files']=ps;assert gcopy==previous
bd2=j(E/'BINDING_DRAFT02.json');bd3=j(E/'BINDING_DRAFT03.json');bc=copy.deepcopy(b);bc['budget_review']=bd3['budget_review'];bc['status']=bd3['status'];assert bc==bd3;bc=copy.deepcopy(bd3);bc['gate']=bd2['gate'];bc['status']=bd2['status'];assert bc==bd2
s3=(E/'preflight24_03.py').read_text();s2=(E/'preflight24_02.py').read_text()
s3=s3.replace("    bound=read(binding['transport_binding'])\n    changed={'archive_transport','matching_ordered_edge_scratch'}|set(bound['inputs'])", "    changed={'archive_transport','archive_policy','producer_plan','execution_job','matching_ordered_edge_scratch'}")
s3=s3.replace("    prepared=read(binding['preparation']);unbound=read(binding['unbound_archive'])\n", "    prepared=read(binding['preparation']);unbound=read(binding['unbound_archive']);bound=read(binding['transport_binding'])\n")
assert s3==s2

review={'decision':'accepted','identity':name,'input_refs':inputs,'evidence':evidence,'scope':'Exact full24 source/input/binding-draft review for guarded resource measurement only. Prospective2GiB directory+1GiB competing-writer headroom is not observed future usage/quota. Current preflight eligibility, committed final binding/release and actual recovery remain separate.'}
(R/'BINDING_REVIEW01.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n')
out={'decision':'accepted_source_input_binding_only','binding_review_sha256':h(R/'BINDING_REVIEW01.json'),'source_count':378,'input_count':64,'evidence_count':len(evidence),'capacity_anchor':cap['source_anchor'],'review_head':head,'checks':['All378 admitted source bodies,64 normalized input hashes and every concrete draft binding ref joined. Sole opaque dispatch hash/stat only.','365 exact capacity-source bodies authenticated against actual ancestor Git blobs and current admitted pins; no self-referential current HEAD or static300s expiry.','Caller02 source inverse leaves unrelated original functions and RootIO logic unchanged; live union/free/RAM/namespace/runtime checks remain.','Core/public/binder inverses and original scientific/native/storage/spent chronology reused and joined; additive scratch24 has actual matching source and accepted validation review.','Budget95 samefamily/base51/history17; prior23 terminal remains failed. Full7graph/415968128cells/32motifs/512spent samples with no diagnostic prefix.','Declared growth10330149469+2147483648+1073741824=13551374941; logical10988852301 includes other-writer headroom. Source forecast remains conditional, observed current totals checked only at real entry.'],'predecessor_withheld_sha256':h(R/'WITHHELD01.json'),'successor_checks':['Literal03 inverse is only authenticated bound role roster/read relocation; subsequent actual public hash+decoded checks and core equality retained.','All375 predecessor sources unchanged plus3 exact active03 pins; draft03 only corrected gate/status versus02; draft04 only exact budget review/status versus03.','Three exact public_manifest/prepared/archive refs now preserve original byte-count fields.'],'limitations':['No genuine preflight/admission/native/Owner/transport execution performed.','Final BINDING01/release and actual public incremental external recovery pending.','Source-only approval does not promise successful complete capacity, numerical completion, writer exclusion or hard quota.']}
(R/'SOURCE_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'binding_review_sha256':h(R/'BINDING_REVIEW01.json'),'source_review_sha256':h(R/'SOURCE_REVIEW01.json'),'evidence_count':len(evidence)}))
