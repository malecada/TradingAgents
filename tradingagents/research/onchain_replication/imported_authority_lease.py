"""Opt-in genuine imported authority with explicit sampled detection timing."""
import contextlib,hashlib,json,sys,types
import builtins
from . import phase_timing
from pathlib import Path
from .imported_authority_interval import Interval,fingerprint,policy,require

AUTHORITY_CLASSES={'ImportedOriginal','PreparedImport','MaterializedOriginal','ImportStage','ImportedExecution','Binding','Owner','Stage','Target','Lease','Interval','BindingLeaseTiming','PhaseTotals','NumericAgreementAdapter'}

def _loaded(root,sources):
    result={}
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if not path:continue
        p=Path(path)
        if not p.is_absolute() or not p.is_relative_to(root):continue
        rel=str(p.relative_to(root))
        if rel not in sources:continue
        functions=[]
        def add(label,value):
            if isinstance(value,(staticmethod,classmethod)):value=value.__func__
            if type(value) is types.FunctionType and value.__module__==name:
                if value.__globals__ is not vars(module):
                    wrapped=getattr(value,'__wrapped__',None)
                    require(type(wrapped) is types.FunctionType and wrapped.__globals__ is vars(module),'loaded globals differ')
                    exemplar=contextlib.contextmanager(wrapped)
                    require(value.__globals__ is vars(contextlib) and value.__code__ is exemplar.__code__ and value.__closure__ is not None and len(value.__closure__)==1 and value.__closure__[0].cell_contents is wrapped,'contextmanager wrapper differs')
                    functions.append((label+'.contextmanager',value,value.__code__))
                    functions.append((label+'.wrapped',wrapped,wrapped.__code__))
                else:functions.append((label,value,value.__code__))
            elif type(value) is property:
                for role in ('fget','fset','fdel'):
                    if getattr(value,role) is not None:add(label+'.'+role,getattr(value,role))
        for key,value in tuple(vars(module).items()):
            add(key,value)
            if isinstance(value,type) and value.__module__==name and value.__name__ in AUTHORITY_CLASSES:
                for attr,item in tuple(vars(value).items()):
                    # This six-field metadata dataclass is not matching_owner.Binding
                    # or an authority capability. Its standard generated methods are
                    # outside that roster, like other metadata dataclasses. Authored
                    # methods/properties (including overrides) remain authenticated.
                    if (name=='tradingagents.research.onchain_replication.typed_tail_binding'
                            and key==value.__name__=='Binding'
                            and attr in {'__init__','__repr__','__eq__','__setattr__','__delattr__','__hash__','__replace__'}
                            and type(item) is types.FunctionType
                            and item.__code__.co_filename!=str(p)):
                        functions.append((key+'.'+attr+'.metadata_generated',item,item.__code__))
                        continue
                    add(key+'.'+attr,item)
        result[name]=(module,p,tuple(functions))
    return result

def _authenticate_loaded(loaded,sources,root):
    with phase_timing.measure('module_auth'):
        for module,p,functions in loaded.values():
            with phase_timing.measure('source_read'):
                raw=p.read_bytes();phase_timing.add_bytes('source_read',len(raw))
                require(hashlib.sha256(raw).hexdigest()==sources[str(p.relative_to(root))],'loaded source body differs')
            with phase_timing.measure('source_compile'):
                compiled=compile(raw,str(p),'exec',dont_inherit=True,optimize=sys.flags.optimize)
            codes={}
            def walk(code):
                codes.setdefault(code.co_name,[]).append(code)
                for value in code.co_consts:
                    if type(value) is types.CodeType:walk(value)
            walk(compiled)
            for label,fn,code in functions:
                if label.endswith('.metadata_generated'):
                    require(module.__name__=='tradingagents.research.onchain_replication.typed_tail_binding'
                            and label in {'Binding.'+attr+'.metadata_generated' for attr in
                                ('__init__','__repr__','__eq__','__setattr__','__delattr__','__hash__','__replace__')}
                            and fn is vars(module.Binding).get(label.split('.')[1])
                            and code.co_filename!=str(p), 'generated metadata boundary differs')
                    # Generated metadata methods retain identity/code snapshot checks;
                    # their bodies are runtime-generated, not source-authored authority.
                    continue
                if label.endswith('.contextmanager'):
                    wrapped=getattr(fn,'__wrapped__',None)
                    require(type(wrapped) is types.FunctionType and fn.__code__ is contextlib.contextmanager(wrapped).__code__ and fn.__globals__ is vars(contextlib) and len(fn.__closure__ or ())==1 and fn.__closure__[0].cell_contents is wrapped,'contextmanager changed')
                else:require(code.co_filename==str(p) and any(code==candidate for candidate in codes.get(code.co_name,())),'loaded code not bound to authenticated source: '+label)


_EXPECTED_COMPILE = builtins.compile
EXPECTED_POLICY = {'schema_version': 1, 'kind': 'activation-owned-expected-code-v1', 'max_loaded_modules': 2048, 'max_code_objects': 262144, 'assumption': 'Expected source code is compiled once per loaded module per activation. Repeated compile/audit/profiling and compiler-warning side effects are intentionally not equivalent; no absence of hooks is asserted. Every authentication still freshly reads and hashes source and checks current loaded capabilities. No validation success, stat or resolved-path cache.'}

def expected_code_policy(value):
    if value is None:return None
    require(type(value) is dict and set(value)==set(EXPECTED_POLICY), 'exact expected-code policy required')
    require(all(type(value[k]) is type(v) and value[k]==v for k,v in EXPECTED_POLICY.items()), 'unsupported expected-code contract')
    return tuple(sorted(value.items()))

def _expected_context(lease,selected):
    compiler=builtins.compile
    require(compiler is _EXPECTED_COMPILE and type(compiler) is types.BuiltinFunctionType
            and compiler.__module__=='builtins' and compiler.__name__=='compile'
            and globals().get('compile',compiler) is compiler, 'captured builtin compiler required')
    require(len(lease.loaded)<=dict(selected)['max_loaded_modules'], 'expected module allowance exceeded')
    scope=tuple((name,module,path,functions) for name,(module,path,functions) in lease.loaded.items())
    return (compiler,sys.flags.optimize,lease.loaded,tuple(lease.sources.items()),lease.run.admission.root,scope)

def _expected_current(lease,*,check_scope=False):
    require(lease._expected_policy is lease._expected_policy_pin, 'expected-code policy replaced')
    if lease._expected_policy is None:return
    require(expected_code_policy(dict(lease._expected_policy))==lease._expected_policy, 'expected-code policy changed')
    context=lease._expected_context
    require(context is lease._expected_context_pin and lease._expected_tables is lease._expected_tables_pin, 'expected-code table/context replaced')
    compiler,optimize,loaded,sources,root,scope=context
    require(builtins.compile is compiler and _EXPECTED_COMPILE is compiler
            and globals().get('compile',compiler) is compiler and sys.flags.optimize==optimize, 'expected-code compiler/optimization changed')
    if not check_scope:return
    require(lease.loaded is loaded and tuple(lease.sources.items())==sources
            and lease.run.admission.root==root, 'expected-code source scope changed')
    require(len(loaded)==len(scope), 'expected-code loaded roster changed')
    for name,module,path,functions in scope:
        require(name in loaded and loaded[name][0] is module and loaded[name][1]==path
                and loaded[name][2] is functions and sys.modules.get(name) is module, 'expected-code module scope changed')
        for label,fn,code in functions:
            require(fn.__code__ is code, 'expected-code loaded function code changed: '+label)

def _authenticate_expected(lease):
    with phase_timing.measure('module_auth'):
        _expected_current(lease,check_scope=True)
        compiler,optimize,loaded,source_items,root,scope=lease._expected_context
        sources=lease.sources;expected=lease._expected_tables;tables=[];total_codes=0
        require(_loaded(root,sources)==loaded, 'expected-code current loaded scope differs')
        for index,(module,p,functions) in enumerate(loaded.values()):
            with phase_timing.measure('source_read'):
                raw=p.read_bytes();phase_timing.add_bytes('source_read',len(raw))
                require(hashlib.sha256(raw).hexdigest()==sources[str(p.relative_to(root))],'loaded source body differs')
            if expected is None:
                with phase_timing.measure('source_compile'):
                    compiled=compiler(raw,str(p),'exec',dont_inherit=True,optimize=optimize)
                codes={}
                def walk(code):
                    codes.setdefault(code.co_name,[]).append(code)
                    for value in code.co_consts:
                        if type(value) is types.CodeType:walk(value)
                walk(compiled)
                total_codes+=sum(len(v) for v in codes.values())
                require(total_codes<=dict(lease._expected_policy)['max_code_objects'], 'expected code allowance exceeded')
                frozen=types.MappingProxyType({name:tuple(values) for name,values in codes.items()})
                tables.append((p,sources[str(p.relative_to(root))],frozen))
            else:
                require(len(expected)==len(loaded), 'expected table extent changed')
                path,digest,codes=expected[index]
                require(path==p and digest==sources[str(p.relative_to(root))], 'expected table path/hash differs')
            for label,fn,code in functions:
                if label.endswith('.metadata_generated'):
                    require(module.__name__=='tradingagents.research.onchain_replication.typed_tail_binding'
                            and label in {'Binding.'+attr+'.metadata_generated' for attr in
                                ('__init__','__repr__','__eq__','__setattr__','__delattr__','__hash__','__replace__')}
                            and fn is vars(module.Binding).get(label.split('.')[1])
                            and code.co_filename!=str(p), 'generated metadata boundary differs')
                    # Generated metadata methods retain identity/code snapshot checks;
                    # their bodies are runtime-generated, not source-authored authority.
                    continue
                if label.endswith('.contextmanager'):
                    wrapped=getattr(fn,'__wrapped__',None)
                    require(type(wrapped) is types.FunctionType and fn.__code__ is contextlib.contextmanager(wrapped).__code__ and fn.__globals__ is vars(contextlib) and len(fn.__closure__ or ())==1 and fn.__closure__[0].cell_contents is wrapped,'contextmanager changed')
                else:require(code.co_filename==str(p) and any(code==candidate for candidate in codes.get(code.co_name,())),'loaded code not bound to authenticated source: '+label)
        _expected_current(lease,check_scope=True)
        return tuple(tables) if expected is None else expected

def _checked_value(raw,baseline,current,current_pin,original):
    """Callback-free metadata rejoin; grants no authority by itself."""
    from .provenance import canonical_bytes
    require(type(raw) is bytes and raw==baseline,'same-boundary value changed')
    value=json.loads(raw)
    require(type(value) is dict and {'current','original'}<=set(value),'same-boundary result schema differs')
    require(canonical_bytes(current)==current_pin==canonical_bytes(value['current']),
            'same-boundary execution metadata changed')
    require(canonical_bytes(original)==canonical_bytes(value['original']),
            'same-boundary original metadata changed')
    return value

_TOKEN=object()
class Lease:
    def __init__(self,token,execution,selected,expected_policy=None):
        require(token is _TOKEN,'use genuine registered activation')
        from .provenance import canonical_bytes,thaw
        self.execution=execution;self.owner=execution._owner;self.stage=execution._stage;self.prepared=self.stage.prepared;self.bound=execution._bound;self.run=self.bound._run
        self.objects=(execution,self.owner,self.stage,self.prepared,self.bound,self.run,execution._materialized,self.prepared._cap)
        self.scheduler=Interval(selected);self._scheduler_pin=self.scheduler;self._policy_pin=self.scheduler.policy;self._clock_pin=self.scheduler.clock;self.closed=False;self.target=None;self.targets={}
        self.configuration=canonical_bytes({'prepared':self.prepared._configuration().hex(),'execution':execution._execution_pin.hex(),'claim':self.run._claim_sha256,'source':self.run.admission.source,'registration':self.run.admission.registration_sha256,'inputs':self.run.admission.inputs,'sources':self.run.admission.experiment['source_files'],'runtime':self.bound.context})
        self.sources=dict(self.run.admission.experiment['source_files']);root=self.run.admission.root
        paths={root/name for name in self.sources} # registered source paths; inputs appended below
        paths.update(root/v['path'] for v in self.run.admission.inputs.values())
        paths.add(root/'uv.lock');require(len(paths)<=2048,'bounded evidence roster exceeded')
        self.paths=tuple(sorted(paths));self.fingerprints=tuple(fingerprint(p) for p in self.paths)
        self.loaded=_loaded(root,self.sources)
        self._expected_policy=expected_code_policy(expected_policy);self._expected_policy_pin=self._expected_policy
        self._expected_context=self._expected_context_pin=None
        self._expected_tables=self._expected_tables_pin=None
        if self._expected_policy is None:
            _authenticate_loaded(self.loaded,self.sources,root)
        else:
            self._expected_context=self._expected_context_pin=_expected_context(self,self._expected_policy)
            self._expected_tables=self._expected_tables_pin=_authenticate_expected(self)
            _expected_current(self,check_scope=True)
        self.value=canonical_bytes(execution.check())
        self.scheduler.validate(self._full,self._finger,self._live,boundary=True)
    def _identity(self):
        from .provenance import canonical_bytes,thaw
        e=self.execution
        _expected_current(self)
        require(self.scheduler is self._scheduler_pin and self.scheduler.policy is self._policy_pin and self.scheduler.clock is self._clock_pin,'registered scheduler/policy/clock changed')
        require(not self.closed and all(a is b for a,b in zip((e,e._owner,e._stage,e._stage.prepared,e._bound,e._bound._run,e._materialized,e._stage.prepared._cap),self.objects,strict=True)),'import authority objects changed')
        require(not self.prepared._closed and not self.prepared._cap._closed and self.stage.closed and not self.owner.closed and not self.owner.poisoned,'import owner/prepared is closed/poisoned/incomplete')
    def _finger(self):
        with phase_timing.measure('lease_fingerprint'):
            from .provenance import current_canonical_bytes,thaw
            e=self.execution
            current=current_canonical_bytes({'prepared':self.prepared._configuration().hex(),'execution':e._execution_pin.hex(),'claim':self.run._claim_sha256,'source':self.run.admission.source,'registration':self.run.admission.registration_sha256,'inputs':self.run.admission.inputs,'sources':self.run.admission.experiment['source_files'],'runtime':self.bound.context})
            require(current==self.configuration,'import interval baseline changed')
            self._identity();require(tuple(fingerprint(p) for p in self.paths)==self.fingerprints,'source/input identity changed')
            current=_loaded(self.run.admission.root,self.sources)
            require(current==self.loaded,'loaded module/function identity changed')
            _expected_current(self,check_scope=True)
    def _full(self):
        with phase_timing.measure('lease_full'):
            from .provenance import canonical_bytes
            self._identity();value=canonical_bytes(self.execution.check())
            require(value==self.value,'full imported baseline differs')
            if self._expected_policy is None:
                _authenticate_loaded(self.loaded,self.sources,self.run.admission.root)
            else:
                require(_authenticate_expected(self) is self._expected_tables,'expected table replaced by authentication')
            if self.target is not None:self.target.final(full_graph=False)
            return value
    def _live(self):
        with phase_timing.measure('lease_live'):
            from . import compact_owner
            self._identity();active=self.owner.active
            if active is None:self.owner.lease()
            else:
                require(type(active) is compact_owner.Stage,'actual active MCM stage required');active.lease()
            compact_owner.verify_current(self.owner, sampled_archive_evidence=True)
    def check(self,*,boundary=False,_return_value=False):
        from . import compact_owner
        try:
            require(type(_return_value) is bool and (not _return_value or boundary is True),
                    'checked value requires explicit full boundary')
            self._identity()
            if self.target is not None:self.target._pins()
            # Capture only this invocation's actual full-check result. Never
            # expose a previous interval's value on a sampled inner callback.
            baseline=self.value;checked=[]
            def full():checked.append(self._full())
            self.scheduler.validate(full if _return_value else self._full,self._finger,self._live,boundary=boundary)
            self._identity()
            if _return_value:
                require(len(checked)==1 and self.value==baseline,'same-boundary result missing or baseline changed')
                # Scheduler callbacks may follow _full. Rejoin genuine authority,
                # original metadata and source fingerprints after those callbacks.
                now=self.scheduler.now()
                require(self.scheduler.full is not None and
                        (now-self.scheduler.full)*1000<=self.scheduler.policy['max_stale_ms'],
                        'same-boundary value became stale')
                # No clock/live callback after the final evidence rejoin.
                compact_owner.verify_current(self.owner)
                self.stage.integrity()
                original=self.execution._materialized._integrity()
                self._finger();self._identity()
                require(self.value==baseline,'same-boundary baseline changed after callbacks')
                return _checked_value(checked[0],baseline,self.execution._execution,
                                      self.execution._execution_pin,original)
        except BaseException:self.closed=True;self.scheduler.closed=True;raise

def activate(execution,input_name):
    from .original_import_stage import ImportedExecution
    require(type(execution) is ImportedExecution and not hasattr(execution,'_sampled_authority_lease'),'genuine unused imported execution required')
    execution.check();run=execution._bound._run
    from .real_pilot_import_caller import admitted
    job=json.loads(run.read_input('execution_job'));_,_,plan=admitted(run.admission,job)
    require(plan['schema_version']==2 and plan.get('imported_authority_lease_input')==input_name and input_name in run.admission.inputs,'explicit registered schema2 interval input required')
    selected=policy(json.loads(run.read_input(input_name)))
    expected=None
    if 'expected_code_cache_input' in plan:
        role=plan['expected_code_cache_input']
        require(role in run.admission.inputs and role!=input_name,'distinct admitted expected-code input required')
        expected=expected_code_policy(json.loads(run.read_input(role)))
        require(expected is not None,'explicit expected-code selection required')
    contract=Lease(_TOKEN,execution,selected,**({'expected_policy':dict(expected)} if expected is not None else {}));execution._sampled_authority_lease=contract
    return contract

def check(execution,*,boundary=False,_return_value=False):
    contract=getattr(execution,'_sampled_authority_lease',None)
    if contract is None:return execution.check()
    require(type(contract) is Lease and contract.execution is execution,'typed original interval required')
    return contract.check(boundary=boundary,_return_value=_return_value)


def target_lease(target,*,boundary=False):
    from .imported_mcm_identity import Target
    require(type(target) is Target,'genuine target required')
    execution=target.execution;contract=getattr(execution,'_sampled_authority_lease',None)
    require(type(contract) is Lease and contract.execution is execution,'original sampled contract required')
    try:
        if id(target) not in contract.targets:
            require(boundary,'target requires full entry boundary')
            target.final(full_graph=False);contract.targets[id(target)]=target
        require(contract.targets[id(target)] is target,'target identity reused')
        contract.target=target;contract.check(boundary=boundary)
    except BaseException:contract.closed=True;contract.scheduler.closed=True;raise
