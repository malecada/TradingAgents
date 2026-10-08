"""Opt-in genuine imported authority with explicit sampled detection timing."""
import contextlib,hashlib,json,sys,types
from pathlib import Path
from .imported_authority_interval import Interval,fingerprint,policy,require

AUTHORITY_CLASSES={'ImportedOriginal','PreparedImport','MaterializedOriginal','ImportStage','ImportedExecution','Binding','Owner','Stage','Target','Lease','Interval'}

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
    for module,p,functions in loaded.values():
        raw=p.read_bytes();require(hashlib.sha256(raw).hexdigest()==sources[str(p.relative_to(root))],'loaded source body differs')
        compiled=compile(raw,str(p),'exec',dont_inherit=True,optimize=sys.flags.optimize);codes=[]
        def walk(code):
            codes.append(code)
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
            else:require(code.co_filename==str(p) and any(code==candidate for candidate in codes),'loaded code not bound to authenticated source: '+label)

_TOKEN=object()
class Lease:
    def __init__(self,token,execution,selected):
        require(token is _TOKEN,'use genuine registered activation')
        from .provenance import canonical_bytes,thaw
        self.execution=execution;self.owner=execution._owner;self.stage=execution._stage;self.prepared=self.stage.prepared;self.bound=execution._bound;self.run=self.bound._run
        self.objects=(execution,self.owner,self.stage,self.prepared,self.bound,self.run,execution._materialized,self.prepared._cap)
        self.scheduler=Interval(selected);self._scheduler_pin=self.scheduler;self._policy_pin=self.scheduler.policy;self._clock_pin=self.scheduler.clock;self.closed=False;self.target=None;self.targets={}
        self.configuration=canonical_bytes({'prepared':self.prepared._configuration().hex(),'execution':execution._execution_pin.hex(),'claim':self.run._claim_sha256,'source':self.run.admission.source,'registration':self.run.admission.registration_sha256,'inputs':thaw(self.run.admission.inputs),'sources':thaw(self.run.admission.experiment['source_files']),'runtime':thaw(self.bound.context)})
        self.sources=dict(self.run.admission.experiment['source_files']);root=self.run.admission.root
        paths={root/name for name in self.sources} # registered source paths; inputs appended below
        paths.update(root/v['path'] for v in self.run.admission.inputs.values())
        paths.add(root/'uv.lock');require(len(paths)<=2048,'bounded evidence roster exceeded')
        self.paths=tuple(sorted(paths));self.fingerprints=tuple(fingerprint(p) for p in self.paths)
        self.loaded=_loaded(root,self.sources);_authenticate_loaded(self.loaded,self.sources,root)
        self.value=canonical_bytes(execution.check())
        self.scheduler.validate(self._full,self._finger,self._live,boundary=True)
    def _identity(self):
        from .provenance import canonical_bytes,thaw
        e=self.execution
        require(self.scheduler is self._scheduler_pin and self.scheduler.policy is self._policy_pin and self.scheduler.clock is self._clock_pin,'registered scheduler/policy/clock changed')
        require(not self.closed and all(a is b for a,b in zip((e,e._owner,e._stage,e._stage.prepared,e._bound,e._bound._run,e._materialized,e._stage.prepared._cap),self.objects,strict=True)),'import authority objects changed')
        require(not self.prepared._closed and not self.prepared._cap._closed and self.stage.closed and not self.owner.closed and not self.owner.poisoned,'import owner/prepared is closed/poisoned/incomplete')
    def _finger(self):
        from .provenance import canonical_bytes,thaw
        e=self.execution
        current=canonical_bytes({'prepared':self.prepared._configuration().hex(),'execution':e._execution_pin.hex(),'claim':self.run._claim_sha256,'source':self.run.admission.source,'registration':self.run.admission.registration_sha256,'inputs':thaw(self.run.admission.inputs),'sources':thaw(self.run.admission.experiment['source_files']),'runtime':thaw(self.bound.context)})
        require(current==self.configuration,'import interval baseline changed')
        self._identity();require(tuple(fingerprint(p) for p in self.paths)==self.fingerprints,'source/input identity changed')
        current=_loaded(self.run.admission.root,self.sources)
        require(current==self.loaded,'loaded module/function identity changed')
    def _full(self):
        from .provenance import canonical_bytes
        self._identity();require(canonical_bytes(self.execution.check())==self.value,'full imported baseline differs')
        _authenticate_loaded(self.loaded,self.sources,self.run.admission.root)
        if self.target is not None:self.target.final(full_graph=False)
    def _live(self):
        from . import compact_owner
        self._identity();active=self.owner.active
        if active is None:self.owner.lease()
        else:
            require(type(active) is compact_owner.Stage,'actual active MCM stage required');active.lease()
        compact_owner.verify_current(self.owner, sampled_archive_evidence=True)
    def check(self,*,boundary=False):
        from . import compact_owner
        try:
            self._identity()
            if self.target is not None:self.target._pins()
            self.scheduler.validate(self._full,self._finger,self._live,boundary=boundary)
            self._identity()
        except BaseException:self.closed=True;self.scheduler.closed=True;raise

def activate(execution,input_name):
    from .original_import_stage import ImportedExecution
    require(type(execution) is ImportedExecution and not hasattr(execution,'_sampled_authority_lease'),'genuine unused imported execution required')
    execution.check();run=execution._bound._run
    from .real_pilot_import_caller import admitted
    job=json.loads(run.read_input('execution_job'));_,_,plan=admitted(run.admission,job)
    require(plan['schema_version']==2 and plan.get('imported_authority_lease_input')==input_name and input_name in run.admission.inputs,'explicit registered schema2 interval input required')
    selected=policy(json.loads(run.read_input(input_name)))
    contract=Lease(_TOKEN,execution,selected);execution._sampled_authority_lease=contract
    return contract

def check(execution,*,boundary=False):
    contract=getattr(execution,'_sampled_authority_lease',None)
    if contract is None:return execution.check()
    require(type(contract) is Lease and contract.execution is execution,'typed original interval required')
    return contract.check(boundary=boundary)


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
