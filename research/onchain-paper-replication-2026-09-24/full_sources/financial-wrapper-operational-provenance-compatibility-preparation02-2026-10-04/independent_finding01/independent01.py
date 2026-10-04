from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,time,fcntl
H=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('pure_bridge',H/'operational_source_compatibility.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
pin=m.sha((H/'operational_source_compatibility.py').read_bytes());target=dict(m.OLD_MAP);target.update(m.CONTROL_TARGETS);target[m.HELPER]=pin
rows=[]
def refusal(label,call):
 try:call()
 except (ValueError,TypeError,KeyError,OSError) as e:rows.append({'case':label,'refused':type(e).__name__})
 else:raise AssertionError(label)
# Exact same-set two-path substitution must fail against path-complete map.
names=[p for p in target if p!=m.HELPER];a,b=next((a,b) for a in names for b in names if target[a]!=target[b]);wrong=dict(target);wrong[a],wrong[b]=wrong[b],wrong[a];assert set(wrong.values())==set(target.values());refusal('same-hash-set-target-path-swap',lambda:m.validate_maps(m.OLD_MAP,wrong,pin))
refusal('helper-pin-substitution',lambda:m.validate_maps(m.OLD_MAP,target,'0'*64));refusal('unresolved-policy',lambda:m.validate_contract(json.loads((H/'POLICY_DRAFT01.json').read_bytes()),pin))
# Opaque pure policy structures, explicitly no claim, Run, Admission, Owner or
# expected runtime outcome is created. Both share identical reviewed195-map.
base=json.loads((H/'POLICY_DRAFT01.json').read_bytes());old={'source_commit':m.HISTORICAL_SOURCE,'source_hashes':sorted(set(m.OLD_MAP.values())),'opaque_science':'fixed','cell_id':'opaque-cell'}
for key in ('closure_input','claim_input','failed_input','checkpoint_input','plan_input','job_input'):base['historical'][key]='opaque-'+key
base['historical']['provenance']=old;base['target']['closure_input']='opaque-current-closure'
for phase,c in base['consumers'].items():c.update(experiment='opaque-'+phase,cell_id='opaque-cell')
other=copy.deepcopy(base);other['consumers']['predict']['experiment']='opaque-alternate-predict'
m.validate_contract(base,pin);m.validate_contract(other,pin);assert m.sha(m.canonical(base))!=m.sha(m.canonical(other))
# Exact production AST comparison for prediction accepts equal target source
# maps despite different source commits. It contains no policy digest at all.
t=ast.parse((H/'financial_wrapper_fixture.py').read_text());parent=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_parent')
branch=next(n for n in parent.body if isinstance(n,ast.If) and 'require_parent_compatibility' in ast.unparse(n))
assert "p['phase'] == 'continue100'" in ast.unparse(branch.test)
expr=next(n for n in ast.walk(branch.orelse[0]) if isinstance(n,ast.Compare) and isinstance(n.left,ast.DictComp))
prior={'source_commit':'1'*40,'source_hashes':sorted(set(target.values())),'opaque_science':'fixed','cell_id':'opaque-cell'};current=prior|{'source_commit':'2'*40}
assert eval(compile(ast.Expression(expr),'exact-legacy-predict-comparison','eval'),{}, {'value':{'provenance':prior},'prov':current}) is True
assert 'operational_source_compatibility' not in ast.unparse(expr)
# No alternative parent-policy join exists in the prediction branch/call route.
parent_calls=[ast.unparse(n.func) for n in ast.walk(parent) if isinstance(n,ast.Call)]
assert parent_calls.count('require_parent_compatibility')==1 and 'require_reference_policy' not in parent_calls
witness={'finding':'OPC-PREDICT-POLICY-01','two_valid_pure_metadata_policies':True,'same_target_map':base['target']['installed']==other['target']['installed'],'policy_a_sha256':m.sha(m.canonical(base)),'policy_b_sha256':m.sha(m.canonical(other)),'changed_policy_field':'consumers.predict.experiment','exact_legacy_predict_comparison':ast.unparse(expr),'legacy_comparison_accepts':True,'parent_compatibility_guard':ast.unparse(branch.test),'genuine_claim_or_parent_executed':False,'qualification':'Source control-flow plus exact pure metadata comparison; no claim/Run/Admission or numerical API executed.'}
(H/'WITNESS01.json').write_text(json.dumps(witness,indent=2)+'\n');rows.append({'case':'prediction-policy-gap','witness':True})
# Non-source science remains protected in the relation, and historical hash
# replacement/reverse direction cannot be used as lineage laundering.
new=old|{'source_commit':'3'*40,'source_hashes':sorted(set(target.values()))}
for label,value in [('science',new|{'opaque_science':'changed'}),('old-map',new|{'source_hashes':old['source_hashes']}),('reverse',new|{'source_commit':m.HISTORICAL_SOURCE})]:refusal(label,lambda value=value:m.validate_relation(m.OLD_MAP,target,old,value))
# Actual bounded reader under a real held flock, without invoking any authority
# wrapper or creating a research lock. This only tests the leaf IO behavior.
owned=H/'independent-owned';owned.mkdir();body=owned/'opaque';body.write_bytes(b'opaque\x00\xff');lock=owned/'engineering.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
try:
 fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);assert m._read(body,{'begun':time.monotonic(),'bytes':0})==b'opaque\x00\xff';rows.append({'case':'real-reader-under-owned-flock','passed':True})
finally:os.close(fd)
# Full call graph evidence: genuine leaf methods contain no nested flock;
# the private path selects only registered_unlocked, not read_input.
helper=ast.parse((H/'operational_source_compatibility.py').read_text());func={n.name:n for n in helper.body if isinstance(n,ast.FunctionDef)}
for name in ('_require_parent_under_fit_lock','_parent_predicate','_context','_registered_unlocked'):
 calls=[ast.unparse(n.func) for n in ast.walk(func[name]) if isinstance(n,ast.Call)];assert not any(c.endswith('.read_input') or c in ('_lock','authorize') for c in calls)
 rows.append({'case':'held-graph-'+name,'calls':calls})
print(json.dumps({'cases':len(rows),'rows':rows,'finding':'OPC-PREDICT-POLICY-01'},indent=2))
