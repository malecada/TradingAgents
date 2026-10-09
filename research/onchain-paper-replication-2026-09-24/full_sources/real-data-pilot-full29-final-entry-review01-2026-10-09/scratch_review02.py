import pathlib,json,hashlib,ast,copy
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;E=R.parent/'real-data-pilot-full29-entry01-2026-10-09';j=lambda p:json.loads(p.read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=j(R/'BINDING_REVIEW01.json');b=j(E/'BINDING_DRAFT04.json');old=j(E/'BINDING01.json');g=j(E/'gate04.json');og=j(E/'gate03.json');NAME=b['identity'];x=g['experiments'][NAME];ox=og['experiments'][NAME];ev=dict(base['evidence'])
assert {k for k in b if b[k]!=old[k]}=={'binding_review','gate','input_refs'}
assert {k for k in b['input_refs'] if b['input_refs'][k]!=old['input_refs'][k]}=={'matching_ordered_edge_scratch'}
assert all(x['source_files'][p]==v for p,v in ox['source_files'].items());new=set(x['source_files'])-set(ox['source_files']);assert len(new)==3 and len(x['source_files'])==458
assert {pathlib.Path(p).name for p in new}=={'MATCHING_SCRATCH_RESERVATION02.json','preflight29_02.py','root_io29_02.py'}
z=copy.deepcopy(g);z['experiments'][NAME]['source_files']=ox['source_files'];z['experiments'][NAME]['inputs']=ox['inputs'];assert z==og
assert {k for k in x['inputs'] if x['inputs'][k]!=ox['inputs'][k]}=={'matching_ordered_edge_scratch'}
norm=lambda vals:{k:{q:v[q] for q in ('path','sha256')} for k,v in vals.items()};assert norm(x['inputs'])==b['input_refs'] and len(x['inputs'])==64
src=(E/'preflight29_02.py').read_text();assert src.replace('gate04.json','gate03.json').replace('BINDING02.json','BINDING01.json').replace('RELEASE_REVIEW02.json','RELEASE_REVIEW01.json')==(E/'preflight29_01.py').read_text()
assert (E/'root_io29_02.py').read_text().replace('preflight29_02','preflight29_01')==(E/'root_io29_01.py').read_text()
scratch=j(ROOT/b['input_refs']['matching_ordered_edge_scratch']['path']);previous=j(ROOT/old['input_refs']['matching_ordered_edge_scratch']['path']);changed={k for k in scratch.keys()|previous.keys() if scratch.get(k)!=previous.get(k)}
assert changed=={'installed_source','qualification','adaptive_explicit_bound_bytes','adaptive_edge_cache_source_review','current_integration_review'}
assert scratch['adaptive_explicit_bound_bytes']==9*16384+256*256+16384==229376<=scratch['incremental_explicit_numeric_scratch_bytes']==262144
# Execute only exact actual predicates, replacing the AST attribute admission.experiment
# by the actual gate dictionary. No Admission/Owner/run object is manufactured.
class ActualGate(ast.NodeTransformer):
 def visit_Attribute(self,node):
  if isinstance(node.value,ast.Name) and node.value.id=='admission' and node.attr=='experiment':return ast.copy_location(ast.Name(id='actual_experiment',ctx=ast.Load()),node)
  return self.generic_visit(node)
def need(v,msg):
 if not v:raise ValueError(msg)
tree=ast.parse(src);fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check');stmts=[n for n in fun.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need' and any(isinstance(t,ast.Name) and t.id=='scratch' for t in ast.walk(n))];assert len(stmts)==3
job=j(ROOT/b['input_refs']['execution_job']['path']);scope={'scratch':scratch,'NAME':NAME,'actual_experiment':x,'job':job,'need':need};code=compile(ast.fix_missing_locations(ActualGate().visit(ast.Module(body=copy.deepcopy(stmts),type_ignores=[]))),'<actual-preflight-scratch-predicates>','exec');exec(code,scope)
refused=False
try:exec(code,{**scope,'scratch':previous})
except ValueError as e:refused=str(e)=='scratch reservation installed source differs'
assert refused
# Exact prepared_inputs metadata predicates relevant to the deliberate scratch overlay.
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepared_inputs');prepared=j(ROOT/b['preparation']['path']);public=j(ROOT/b['public_manifest']['path']);bound=j(ROOT/b['transport_binding']['path']);prior=j(ROOT/b['public_refs']['path']);actual=b['input_refs'];review={**base,'input_refs':actual};scope={'review':review,'actual':actual,'binding':b,'public':public,'NAME':NAME,'prepared':prepared,'bound':bound,'prior':prior,'need':need};count=0
for n in f.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need':
  msg=n.value.args[-1]
  if isinstance(msg,ast.Constant) and msg.value in ('exact genuine64-role input closure differs','accepted public04 identity/roster differs','public04 original role roster differs','prepared public04 origin differs','actual binder source request differs','unbound archive role differs'):
   exec(compile(ast.Module(body=[n],type_ignores=[]),'<actual-prepared-predicate>','exec'),scope);count+=1
assert count==6
changedroles={'archive_transport','matching_ordered_edge_scratch'}|set(bound['inputs'])
assert all(actual[k]['sha256']==v['sha256'] for k,v in prior.items() if k not in changedroles)
def pin(ref):
 p=ROOT/ref['path'];assert h(p)==ref['sha256'];ev[ref['path']]=ref['sha256']
 if 'bytes'in ref:assert p.stat().st_size==ref['bytes']
for p in new:pin({'path':p,'sha256':x['source_files'][p]})
for ref in b.values():
 if isinstance(ref,dict) and {'path','sha256'}<=ref.keys():
  if ref['path'] in ev:assert ev[ref['path']]==ref['sha256']
  else:pin(ref)
for v in scratch.values():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():pin(v)
for p in (E/'BINDING_DRAFT04.json',R/'scratch_review02.py',R/'BINDING_REVIEW01.json',R/'SOURCE_REVIEW01.json'):ev[str(p.relative_to(ROOT))]=h(p)
result={'decision':'accepted','identity':NAME,'input_refs':actual,'evidence':ev,'scope':'Narrow scratch overlay and fixed caller path correction only;455 prior source proofs reused plus3 new pins. Final binding seal, actual increment14 returned verification and fresh original preflight eligibility remain required. No empirical admission/claim/whole capacity granted.'};(R/'BINDING_REVIEW02.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
report={'decision':'accepted_changed_seam_only','identity':NAME,'binding_review_sha256':h(R/'BINDING_REVIEW02.json'),'source_count':458,'input_count':64,'new_sources':{p:x['source_files'][p] for p in sorted(new)},'changed_input':'matching_ordered_edge_scratch','checks':['Gate inverse only3 added sources and1 role; all455 originalpins and63 otherroles unchanged.','Preflight inverse gate/binding/release fixed paths only; RootIO import only.','Exact three scratch predicates: actual corrected declaration passes; original inherited declaration refuses installed-source mismatch. No fake Admission/Owner.','Six exact prepared_inputs predicates and deliberate scratch-overlay exclusion pass against saved actual metadata. No rebind or public/private output changes.','Vector chunk1024, scratch262144 and native limits unchanged; adaptive bound229376 excludes state/library/process RSS.'],'qualification':'Read-only preflight refusal before claim preserved by Root. This review does not resolve current filesystem headroom or establish live eligibility. No numerical inputs/imports, runtime execution or network; unchanged source matrices not repeated.'};(R/'SOURCE_REVIEW02.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'binding':h(R/'BINDING_REVIEW02.json'),'source':h(R/'SOURCE_REVIEW02.json'),'evidence':len(ev)}))
