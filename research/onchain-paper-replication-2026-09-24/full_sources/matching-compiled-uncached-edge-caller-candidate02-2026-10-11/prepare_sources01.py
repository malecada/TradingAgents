"""Finite candidate derivation; writes only this new candidate directory."""
from pathlib import Path
import ast,difflib,hashlib,json
P=Path(__file__).resolve().parent;BASE=Path('tradingagents/research/onchain_replication');OLD=P.parent/'matching-compiled-uncached-edge-caller-candidate01-2026-10-11'
texts={};original={}
for name in ('compiled_edge_owner.py','edge_chunk_adapter.py','matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py'):texts[name]=(OLD/name).read_text()
for name in ('batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py','compact_mcm_batched.py','real_pilot_import_caller.py'):texts[name]=(BASE/name).read_text()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
s=texts['compiled_edge_owner.py'];point='\ndef abi_metadata(body):'
extra='''
def attach(owner,value):
    owner._compiled_edge_policy=freeze(value)
    owner._compiled_edge_policy_pin=owner._compiled_edge_policy

def current_policy(owner):
    require(owner._compiled_edge_policy is owner._compiled_edge_policy_pin,'edge policy replaced')

def options(owner):
    current_policy(owner)
    return {'compiled_edge_policy_value':dict(owner._compiled_edge_policy)} if owner._compiled_edge_policy is not None else {}

def join(owner,child):
    current_policy(owner);current_policy(child)
    require(owner._compiled_edge_policy==child._compiled_edge_policy,'edge policy chain differs')
'''
texts['compiled_edge_owner.py']=one(s,point,'\n'+extra+point)
s=texts['matching_immutable_session.py'];s=one(s,'        compiled_normalization_policy.attach(self,compiled_normalization_policy_value)','        compiled_normalization_policy.attach(self,compiled_normalization_policy_value)\n        require(edge_chunk_owner is None or type(edge_chunk_owner) is compiled_edge_owner.EdgeOwner, "typed edge owner required")\n        compiled_edge_owner.attach(self,None if edge_chunk_owner is None else dict(edge_chunk_owner.policy))')
s=one(s,'    def _edge_current(self):','    def _edge_current(self):\n        compiled_edge_owner.current_policy(self)');texts['matching_immutable_session.py']=s
for name in ('batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py','compact_mcm_batched.py'):
 s=texts[name];s=one(s,'from . import compiled_normalization_policy','from . import compiled_normalization_policy\nfrom . import compiled_edge_owner')
 if name!='compact_mcm_batched.py':
  s=one(s,'compiled_normalization_policy_value=None):','compiled_normalization_policy_value=None,compiled_edge_policy_value=None):')
  lines=s.splitlines(True);out=[]
  for line in lines:
   out.append(line)
   if 'compiled_normalization_policy.attach(self,compiled_normalization_policy_value)' in line:out.append(line.replace('compiled_normalization_policy.attach(self,compiled_normalization_policy_value)','compiled_edge_owner.attach(self,compiled_edge_policy_value)'))
   if 'compiled_normalization_policy.join(self,' in line:out.append(line.replace('compiled_normalization_policy.join','compiled_edge_owner.join'))
  s=''.join(out)
  s=s.replace('**compiled_normalization_policy.options(self))','**compiled_normalization_policy.options(self),**compiled_edge_owner.options(self))')
 texts[name]=s
s=texts['batched_pair_executor.py'];s=one(s,'import copy','import copy,sys')
marker='    def close(self):'
extra='''        self._edge_owner=None;self._edge_owner_pin=None
        if self._compiled_edge_policy is not None:
            normal_cleanup=self._normalization_cleanup
            edge_cleanup=None
            def combined_cleanup():
                primary=None
                try:normal_cleanup()
                except BaseException as error:primary=error
                try:
                    if edge_cleanup is not None:edge_cleanup()
                except BaseException as error:
                    if primary is None:primary=error
                    else:
                        try:BaseException.add_note(primary,'edge owner cleanup failed: '+repr(error))
                        except BaseException:pass
                if primary is not None:raise primary
            self._normalization_cleanup=combined_cleanup
            owner=None
            try:
                owner=compiled_edge_owner.EdgeOwner(dict(self._compiled_edge_policy),numpy=annealing.np,scipy=sys.modules['scipy'],agreement=annealing.agreement)
                edge_cleanup=owner.close
                self._edge_owner=self._edge_owner_pin=owner
                self._edge_methods=tuple((name,getattr(owner,name)) for name in ('current','borrow','close'))
            except BaseException as primary:
                try:
                    if owner is not None and edge_cleanup is None:edge_cleanup=owner.close
                    combined_cleanup()
                except BaseException as error:
                    try:BaseException.add_note(primary,'edge parent construction failed: '+repr(error))
                    except BaseException:pass
                raise
'''
s=one(s,marker,extra+marker)
s=one(s,'            compiled_normalization_policy.current(self)','''            compiled_normalization_policy.current(self)
            compiled_edge_owner.current_policy(self)
            if self._edge_owner is not self._edge_owner_pin:raise ValueError('edge parent replaced')
            if self._edge_owner is not None:
                for name,function in self._edge_methods:
                    if getattr(self._edge_owner,name) is not function:raise ValueError('edge parent method replaced')
                self._edge_methods[0][1]()''')
s=one(s,'**({"_normalization_owner":self._normalization_owner} if self._normalization_owner is not None else {}))','**({"_normalization_owner":self._normalization_owner} if self._normalization_owner is not None else {}),**({"edge_chunk_owner":self._edge_owner} if self._edge_owner is not None else {}))')
texts['batched_pair_executor.py']=s
# Numerical summaries retain explicit policy and check it on readback.
s=texts['batched_numeric_execution.py'];out=[]
for line in s.splitlines(True):
 out.append(line)
 if "if self._compiled_normalization_policy is not None:" in line:out.append(line.replace('_compiled_normalization_policy','_compiled_edge_policy').replace("['compiled_normalization_policy']","['compiled_edge_policy']"))
 if "normalization=compiled_normalization_policy.freeze(binding.get('compiled_normalization_policy'))" in line:out.append(line.replace('normalization=compiled_normalization_policy','edge_selection=compiled_edge_owner').replace("'compiled_normalization_policy'","'compiled_edge_policy'"))
 if "numeric summary normalization policy differs" in line:out.append(line.replace('compiled_normalization_policy.freeze','compiled_edge_owner.freeze').replace("'compiled_normalization_policy'","'compiled_edge_policy'").replace('==normalization','==edge_selection').replace('normalization policy','edge policy'))
s=''.join(out)
# Selected ownership adds independent cleanup; protect annotation at original enclosing cleanup loops.
s=s.replace("primary.add_note('numeric constructor cleanup: '+repr(cleanup))","\n                try:BaseException.add_note(primary,'numeric constructor cleanup: '+repr(cleanup))\n                except BaseException:pass")
s=s.replace("else:primary.add_note('additional numeric cleanup: '+repr(error))","else:\n                    try:BaseException.add_note(primary,'additional numeric cleanup: '+repr(error))\n                    except BaseException:pass")
texts['batched_numeric_execution.py']=s
# Real role schema, five original input bodies and environment join.
s=texts['compact_mcm_batched.py']
s=one(s," | ({'compiled_normalization_policy','compiled_normalization_inputs'} if 'compiled_normalization_policy' in execution else set()),"," | ({'compiled_normalization_policy','compiled_normalization_inputs'} if 'compiled_normalization_policy' in execution else set()) | ({'compiled_edge_policy','compiled_edge_inputs'} if 'compiled_edge_policy' in execution else set()),")
s=one(s,'    _compiled_policy(execution)\n','    _compiled_policy(execution)\n    _edge_policy(execution)\n')
new='''
def _edge_policy(execution):
    if 'compiled_edge_policy' not in execution:
        require('compiled_edge_inputs' not in execution,'edge roles without selection')
        return None
    value=compiled_edge_owner.freeze(execution['compiled_edge_policy'])
    require(value is not None,'explicit edge selection required')
    roles=execution.get('compiled_edge_inputs')
    require(type(roles) is dict and set(roles)=={'source','adapter','library','runtime','abi'},'exact five edge roles required')
    require(all(type(role) is str and 0<len(role)<=128 and role.isascii() and all(c.isalnum() or c in '_-' for c in role) for role in roles.values()) and len(set(roles.values()))==5 and 'environment' not in roles.values(),'distinct finite edge roles required')
    return value

def _edge_inputs(execution,run):
    value=_edge_policy(execution)
    if value is None:return None
    policy=dict(value);ad=run.admission;runtime=None
    for kind in ('source','adapter','library','runtime','abi'):
        role=execution['compiled_edge_inputs'][kind]
        require(role in ad.inputs,'edge role not admitted')
        info=ad.inputs[role];path=ad.root/info['path']
        require(str(path)==policy[kind+'_path'] and path.resolve()==path and info['sha256']==policy[kind+'_sha256'],'edge registered path/hash differs')
        limit=4096 if kind in ('runtime','abi') else 65536
        size=policy[kind+'_bytes'] if kind in ('runtime','abi') else (17072 if kind=='library' else None)
        body=compiled_edge_owner.read_reference(path,info['sha256'],limit,size,owned=kind=='library')
        require(run.read_input(role)==body,'edge genuine input body differs')
        if kind=='runtime':runtime=compiled_normalization_policy.runtime_metadata(body)
        if kind=='abi':compiled_edge_owner.abi_metadata(body)
        if kind=='adapter':
            require(path==ad.root/'tradingagents/research/onchain_replication/edge_chunk_adapter.py' and ad.experiment['source_files'].get('tradingagents/research/onchain_replication/edge_chunk_adapter.py')==info['sha256'],'edge adapter input/source join differs')
    require('environment' in ad.inputs and runtime['runtime_inventory_sha256']==ad.inputs['environment']['sha256'],'edge runtime inventory/environment differs')
    info=ad.inputs['environment'];body=compiled_edge_owner.read_reference(ad.root/info['path'],info['sha256'],1024**2)
    require(run.read_input('environment')==body,'edge environment genuine input differs')
    return value

'''
s=one(s,'def _modules(root, admission=None, *, grouped=False, geometry=False, binding_timing=False, compiled=False):',new+'def _modules(root, admission=None, *, grouped=False, geometry=False, binding_timing=False, compiled=False, edge=False):')
s=one(s,"        if compiled:names+=('compiled_normalization_policy','compiled_small_lse','matching_annealing','matching_checkpoint')","        if compiled:names+=('compiled_normalization_policy','compiled_small_lse','matching_annealing','matching_checkpoint')\n        if edge:names+=('compiled_edge_owner','edge_chunk_adapter','compiled_normalization_policy','matching_annealing','matching_checkpoint')")
s=one(s,"compiled='compiled_normalization_policy' in b['execution'])","compiled='compiled_normalization_policy' in b['execution'],edge='compiled_edge_policy' in b['execution'])")
s=one(s,"        normalization=_compiled_inputs(b['execution'],owner.bound._run)","        normalization=_compiled_inputs(b['execution'],owner.bound._run)\n        edge_selection=_edge_inputs(b['execution'],owner.bound._run)")
s=one(s,"**({'compiled_normalization_policy_value':dict(_compiled_policy(execution))} if 'compiled_normalization_policy' in execution else {}))","**({'compiled_normalization_policy_value':dict(_compiled_policy(execution))} if 'compiled_normalization_policy' in execution else {}),**({'compiled_edge_policy_value':dict(_edge_policy(execution))} if 'compiled_edge_policy' in execution else {}))")
lines=s.splitlines(True);out=[]
for line in lines:
 out.append(line)
 if 'batched/numeric normalization selection differs' in line:out.append(line.replace('compiled_normalization_policy.freeze','compiled_edge_owner.freeze').replace("'compiled_normalization_policy'","'compiled_edge_policy'").replace('normalization selection','edge selection'))
 if "require(_compiled_policy(b['execution'])==normalization" in line:out.append(line.replace('_compiled_policy','_edge_policy').replace('==normalization','==edge_selection').replace('normalization selection','edge selection'))
 if 'completed numeric normalization selection differs' in line:out.append(line.replace('compiled_normalization_policy.freeze','compiled_edge_owner.freeze').replace("'compiled_normalization_policy'","'compiled_edge_policy'").replace('==normalization','==edge_selection').replace('normalization selection','edge selection'))
 if "if normalization is not None:binding['compiled_normalization_policy']=dict(normalization)" in line:out.append(line.replace('normalization','edge_selection').replace("'compiled_edge_selection_policy'","'compiled_edge_policy'"))
s=''.join(out)
marker="    return verify_content(stage.root,contract,stage.reference)"
extra="""    if 'compiled_edge_policy' in binding:
        policy=json.loads(stage.owner.bound._run.read_input(binding['mcm_policy_input']))
        execution=validate(policy,binding['cells'])['execution']
        require(_edge_inputs(execution,stage.owner.bound._run)==compiled_edge_owner.freeze(binding['compiled_edge_policy']),'closed edge policy differs from admitted input')
"""
s=one(s,marker,extra+marker);texts['compact_mcm_batched.py']=s
s=texts['real_pilot_import_caller.py'];s=one(s,'def _prepare_lease_modules(*, batched=False, grouped=False, compiled=False):','def _prepare_lease_modules(*, batched=False, grouped=False, compiled=False, edge=False):')
s=one(s,'            from . import compiled_normalization_policy, compiled_small_lse','            from . import compiled_normalization_policy, compiled_small_lse\n        if edge:\n            from . import compiled_edge_owner, edge_chunk_adapter')
s=one(s,"compiled=selected_mcm.get('schema_version') in (5,6) and 'compiled_normalization_policy' in selected_mcm['batched']['execution'])","compiled=selected_mcm.get('schema_version') in (5,6) and 'compiled_normalization_policy' in selected_mcm['batched']['execution'],edge=selected_mcm.get('schema_version') in (5,6) and 'compiled_edge_policy' in selected_mcm['batched']['execution'])")
texts['real_pilot_import_caller.py']=s
# Selected numerical source attestation adds actual package helper bodies; imported names are exact.
s=texts['batched_numeric_reuse.py']
s=one(s,'def attest(counters):','def attest(counters,edge_policy=None):')
s=one(s,'    for module,pin in SOURCE_PINS:',"    selected_pins=()\n    if edge_policy is not None:\n        from . import edge_chunk_adapter\n        selected_pins=((compiled_edge_owner,'OWNER_PIN'),(edge_chunk_adapter,compiled_edge_owner.ADAPTER))\n    for module,pin in SOURCE_PINS+selected_pins:")
s=s.replace('attest(self.counters)','attest(self.counters,self._compiled_edge_policy)')
# Constructor tail is only metadata allocation; nevertheless close captured parent on failure.
a=s.index('        self._executor_pin=self.executor');b=s.index('    @property',a);tail=s[a:b]
s=s[:a]+'''        cleanup=self.executor.close
        try:
'''+''.join('    '+line+'\n' for line in tail.splitlines())+'''        except BaseException as primary:
            try:cleanup()
            except BaseException as error:
                try:BaseException.add_note(primary,'numeric parent construction cleanup failed: '+repr(error))
                except BaseException:pass
            raise
'''+s[b:]
s=one(s,'from . import compiled_edge_owner','from . import compiled_edge_owner, edge_chunk_adapter')
s=one(s,'immutable_session,adaptive_edge_policy,compiled_normalization_policy)','immutable_session,adaptive_edge_policy,compiled_normalization_policy,compiled_edge_owner,edge_chunk_adapter)')
s=s.replace("primary.add_note('authority timing failed: '+repr(timing_error))","compiled_edge_owner._note(primary,timing_error)")
# Pin only dependency bodies, never this module itself.
for expr,name in [('accepted','batched_pair_executor.py'),('engine','matching_checkpoint.py'),('engine.ann','matching_annealing.py'),('immutable_session','matching_immutable_session.py')]:
 tree=ast.parse(s);assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_PINS' for t in n.targets))
 oldpin=next(el.elts[1].value for el in assignment.value.elts if ast.unparse(el.elts[0])==expr)
 s=s.replace(oldpin,hashlib.sha256(texts[name].encode()).hexdigest())
s=s.replace('OWNER_PIN',hashlib.sha256(texts['compiled_edge_owner.py'].encode()).hexdigest());texts['batched_numeric_reuse.py']=s
for name,text in texts.items():
 ast.parse(text,filename=name);(P/name).write_text(text)
 if (BASE/name).exists():
  old=(BASE/name).read_text();original[name]=hashlib.sha256(old.encode()).hexdigest()
  for suffix,a,b in [('patch',old,text),('inverse.patch',text,old)]:
   (P/(name+'.'+suffix)).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=name,tofile=name)))
(P/'BASELINES01.json').write_text(json.dumps(original,indent=2,sort_keys=True)+'\n')
print('prepared',len(texts),'module bodies')
