from pathlib import Path
import ast,copy,hashlib,json,subprocess,sys,types
H=Path(__file__).resolve().parent;R=H.parents[4];F=H.parent.parent;D=F/'real-data-pilot-final03-2026-10-06';P=H.parent/'final-binding01';N='eth-paper-real-data-end-to-end-resource-20261006-03'
def sha(b):return hashlib.sha256(b).hexdigest()
prior=json.loads((P/'RELEASE_REVIEW01.json').read_bytes());e=prior['evidence'].copy()
def body(p):
 assert 'real_pilot_runtime' not in p.parts and p.name!='connection.json';b=p.read_bytes();assert len(b)<4*1024**2;e[str(p.relative_to(R))]=sha(b);return b
def read(p):return json.loads(body(p))
def auth(ref):
 b=body(R/ref['path']);assert sha(b)==ref['sha256'];return json.loads(b)
old=body(D/'preflight01.py.before-inventory-isolation01');new=body(D/'preflight01.py');assert sha(old)==prior['preflight_sha256']
a=ast.parse(new);check=next(x for x in a.body if isinstance(x,ast.FunctionDef) and x.name=='check');i=next(i for i,x in enumerate(check.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='runtime_inventory' for t in x.targets));block=check.body[i:i+2]
start=block[0].lineno-1;end=block[1].end_lineno;lines=new.decode().splitlines(True);replacement="    if inventory(ROOT,include_torch=True)!=json.loads((ROOT/admission.inputs['environment']['path']).read_bytes()):raise ValueError('installed runtime inventory differs')\n"
assert ''.join(lines[:start])+replacement+''.join(lines[end:])==old.decode()
g=read(D/'gate01.json');og=read(D/'gate01.json.before-inventory-isolation01');exp=g['experiments'][N];rel=str((D/'preflight01.py').relative_to(R));expected=copy.deepcopy(og);expected['experiments'][N]['source_files'][rel]=sha(new);assert g==expected
assert sha(body(D/'BINDING01.json.before-inventory-isolation01'))==prior['binding_sha256']
assert sha(body(D/'RELEASE_REVIEW01.json.before-inventory-isolation01'))==sha(body(P/'RELEASE_REVIEW01.json'))
b=read(D/'BINDING_DRAFT02.json');ob=read(D/'BINDING01.json.before-inventory-isolation01');assert b['binding_review'] is None
for k in b:
 if k not in ('binding_review','status','gate'):assert b[k]==ob[k]
assert b['gate']['path']==rel.replace('preflight01.py','gate01.json') and b['gate']['sha256']==sha(body(D/'gate01.json'))
proof=read(D/'RUNTIME_INVENTORY_ISOLATION01.json');assert proof['preflight_sha256']==sha(new) and proof['gate_sha256']==sha(body(D/'gate01.json')) and proof['actual_child_exit']==0 and proof['child_reaped'] and not proof['torch_present_in_parent_sys_modules']
assert proof['expected_reference']==exp['inputs']['environment'];inventory=auth(proof['expected_reference']);assert proof['actual_inventory']==inventory
# Execute only the actual two new statements, with synthetic subprocess outputs/errors.
# No inventory or numerical package is imported by this reviewer.
code=compile(ast.Module(body=block,type_ignores=[]),'actual child inventory admission statements','exec');calls=[]
def fake(command,**kw):
 assert command==proof['command'] and kw=={'cwd':R,'timeout':30};calls.append(True);return (json.dumps(inventory,sort_keys=True)+'\n').encode()
ns={'subprocess':types.SimpleNamespace(check_output=fake),'sys':types.SimpleNamespace(executable=str(R/'.venv/bin/python')),'ROOT':R,'json':json,'admission':types.SimpleNamespace(inputs=exp['inputs'])}
exec(code,ns);assert len(calls)==1
refusals=[]
for label,value in [('nonzero',subprocess.CalledProcessError(1,proof['command'])),('timeout',subprocess.TimeoutExpired(proof['command'],30)),('invalid-json',b'{invalid'),('different-inventory',b'{}')]:
 def fail(*a,**kw):
  if isinstance(value,Exception):raise value
  return value
 ns['subprocess']=types.SimpleNamespace(check_output=fail)
 try:exec(code,ns)
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired,json.JSONDecodeError,ValueError):refusals.append(label)
 else:raise AssertionError(label+' failed open')
refusal=read(D/'PREFLIGHT_RAM_REFUSAL01.json');assert refusal['actual_root_exit_code']==1 and not any(refusal['namespaces_present'].values()) and refusal['startup_available_requirement_bytes']==9663676416
assert all(e[p]==v for p,v in exp['source_files'].items()) and all(e[r['path']]==r['sha256'] for r in exp['inputs'].values())
assert [p for p in e if 'real_pilot_runtime' in Path(p).parts]==[b['transport']['path']]
assert not (R/'research_runs'/N).exists() and not any(k in sys.modules for k in ('torch','numpy','scipy','tradingagents'))
result={'schema_version':1,'status':'PASS','scope':'Exact inventory child isolation delta only','identity':N,'exact_source_inverse':True,'gate_single_preflight_pin_delta':True,'binding_only_gate_repin':True,'source_inputs_budget_caps_unchanged':True,'actual_inventory_proof':proof,'synthetic_actual_statement_refusals':refusals,'qualification':'Parent proof used exact existing inventory in pinned child; reviewer executed only two actual statements with synthetic outputs. No runtime/scientific work repeated. No RAM fit or successful launch claim.','evidence':e}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
r={'schema_version':1,'decision':'accepted','identity':N,'reviewer':'independent pilot_correction_review','scope':'Exact six-reference final03 composition after bounded child inventory isolation. Only preflight source pin and gate reference change; package179/input59/budget74/caps unchanged. Final binding/release and fresh committed entry mandatory.','evidence':{b[k]['path']:b[k]['sha256'] for k in ('gate','draft','preparation','baseline','transport','transport_binding')},'findings':[],'checks':{'source_inverse':True,'single_gate_pin':True,'actual_inventory_equal':True,'child_reaped':True,'parent_torch_absent':True,'error_refusals':refusals,'previous_release_sha256':sha(body(P/'RELEASE_REVIEW01.json'))}}
(H/'BINDING_REVIEW02.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print('BINDING_REVIEW02',sha((H/'BINDING_REVIEW02.json').read_bytes()))
