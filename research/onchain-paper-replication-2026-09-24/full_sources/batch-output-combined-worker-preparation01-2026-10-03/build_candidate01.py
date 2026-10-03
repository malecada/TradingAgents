from pathlib import Path
import ast
P=Path(__file__).parent;s=(P/'held_score_consumer.py.baseline').read_text()
def function(name):
 n=next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name==name);return ast.get_source_segment(s,n)
closure=function('_transfer_closure').replace('def _transfer_closure(','def _combined_closure(').replace("value['schema_version']==1","value['schema_version']==2").replace("value['kind']=='selected-held-transfer-source-closure-v1'","value['kind']==COMBINED_KIND").replace('201','202').replace('150','151').replace('206','207')
closure=closure.replace('    return code',"    require('tradingagents/research/onchain_replication/completed_f32.py' in package,'complete raw module absent from actual anchor')\n    return code")
aux=function('_transfer_auxiliary').replace('def _transfer_auxiliary(','def _combined_auxiliary(').replace("'selected-held-auxiliary-source-metadata-v1'","'held-auxiliary-source-metadata-v1'").replace("'implementation_source_count':201,'package_count':150","'implementation_source_count':202,'package_count':151").replace("'entries':[{'role':role,'reference':refs[role]} for role in sorted(refs)]","'entry_count':4,'entries':[{'role':role,'reference':dict(refs[role],bytes=len(_body(run.admission.root/refs[role]['path'])))} for role in sorted(refs)]")
pre=function('transfer_preflight').replace('def transfer_preflight(','def _combined_preflight(')
pre=pre.replace("require(p['schema_version']==2,'network route requires schema2; default never activates it')","require(p['schema_version'] in (2,3),'explicit combined f64 or raw route required')")
pre=pre.replace("require(pop['schema_version']==2 and pop['part_bytes']==p['part_bytes'],'same explicit selected population required')","require(pop['schema_version']==p['schema_version'] and pop['part_bytes']==p['part_bytes'],'same explicit selected population required')")
pre=pre.replace("code=_transfer_closure(closure,run.admission.experiment['source_files'],job_api.required_sources())","code=_combined_closure(closure,run.admission.experiment['source_files'],job_api.required_sources())")
pre=pre.replace("_transfer_auxiliary(run,closure)","_combined_auxiliary(run,closure)")
pre=pre.replace('2a146e27460341dcd8aec3219306a5246da0fe6f538c5df69d5e6596c2462bb3','c62e1521f783accd59989625b7b0baf511386b064759521ae90e8ecc056b87b3')
# Use actual frozen dependency full SHA rather than an abbreviated saved label.
import hashlib
D=P.parent/'batch-output-produced-f32-adapter-preparation02-2026-10-03'
pre=pre.replace('c62e1521f783accd59989625b7b0baf511386b064759521ae90e8ecc056b87b3',hashlib.sha256((D/'archive_non_tail.py').read_bytes()).hexdigest()).replace('abad085e10f3c3a68af89d5b8e849ca30d430ca8464bdbd89bbee1e4e15adb8e',hashlib.sha256((D/'selected_non_tail_transport.py').read_bytes()).hexdigest())
pre=pre.replace("'kind':'registered-held-f64-network-release-v1'","'kind':('registered-combined-held-f64-network-release-v2' if p['schema_version']==2 else 'registered-combined-produced-f32-network-release-v2')")
pre=pre.replace("'execution_scope':'two-original-import-f64-targets'","'execution_scope':('two-original-import-f64-targets' if p['schema_version']==2 else 'two-original-import-f32-targets-with-local-held-readback')")
pre=pre.replace("    _transfer_budget(p,pop,tx,fixture['target_nodes'],compact['stage_policy']['score_chunk_cells'],execution['resources'])","""    if p['schema_version']==2:_transfer_budget(p,pop,tx,fixture['target_nodes'],compact['stage_policy']['score_chunk_cells'],execution['resources'])
    else:
        from . import completed_f32
        expected_raw='tradingagents/research/onchain_replication/completed_f32.py'
        require(Path(completed_f32.__file__)==run.admission.root/expected_raw and hashlib.sha256(_body(Path(completed_f32.__file__))).hexdigest()==code[expected_raw],'actual completed raw adapter source differs')
        _combined_budget(p,fixture['target_nodes'],compact['stage_policy']['score_chunk_cells'])
        actual=completed_f32._selected(run,job_input)
        require(actual is not None and actual==(p['population_input'],pop),'actual complete raw budget/policy differs')""")
s=s.replace("TRANSFER_KIND='original-import-held-score-selected-transfer-v2'","TRANSFER_KIND='original-import-held-score-selected-transfer-v2'\nCOMBINED_KIND='selected-combined-f64-f32-source-closure-v2'\nRAW_KIND='original-import-held-score-completed-f32-v3'")
s=s.replace('def _policy(p,graphs,outputs):','''def _policy(p,graphs,outputs):
    if type(p) is dict and type(p.get('schema_version')) is int and p['schema_version']==3:
        require(p.get('kind')==RAW_KIND,'explicit completed raw held policy kind')
        legacy=dict(p,schema_version=2,kind=TRANSFER_KIND)
        _policy(legacy,graphs,outputs)
        return p''')
s=s.replace('def _transfer_closure(value,registered,required):','''def _transfer_closure(value,registered,required):
    if type(value) is dict and value.get('kind')==COMBINED_KIND:return _combined_closure(value,registered,required)''')
s=s.replace('def transfer_preflight(run,execution,*,job_input=\'execution_job\'):',"def _transfer_preflight_legacy(run,execution,*,job_input='execution_job'):")
s=s.replace("if p['schema_version']==2:_worker_current(run,p)","if p['schema_version'] in (2,3):_worker_current(run,p)")
s=s.replace("def transfer_worker(run,execution,*,job_input='execution_job'):\n    return _TransferWorker(run,execution,job_input)","""def transfer_worker(run,execution,*,job_input='execution_job'):
    p,_=transfer_preflight(run,execution,job_input=job_input)
    return _RawWorker(run,execution,job_input) if p['schema_version']==3 else _TransferWorker(run,execution,job_input)""")
s=s.replace('def _worker_current(run,p):','''def _worker_current(run,p):
    if p['schema_version']==3:return _raw_current(run,p)''')
s+='\n\n'+closure+'\n\n'+aux+'\n\n'+pre+'\n'
s+='''
def _combined_budget(p,nodes,chunk):
    require(type(chunk) is int and chunk>0,'positive original chunk required')
    require(type(nodes) is dict and len(nodes)==2 and set(nodes)==set(p['targets']),'exact raw target held-readback population')
    for n in nodes.values():
        require(type(n) is int and n in (2,3) and 32*n*8<=p['max_read_bytes'] and (32*n+chunk-1)//chunk<=p['max_members'],'raw held readback bound before Context birth')

def transfer_preflight(run,execution,*,job_input='execution_job'):
    from ..lifecycle import ResearchRun
    from . import resource_fixture
    require(type(run) is ResearchRun,'actual admitted ResearchRun required before selection')
    run._active();run._check_source();run._check_inputs()
    _,selected,_=resource_fixture.selection(execution)
    _,p=_transfer_json(run,selected[FIELD]);_policy(p,selected['descriptor']['required_graphs'],run.admission.experiment['outputs'])
    _,closure=_transfer_json(run,p['source_closure_input'],4*1024**2)
    if type(closure) is dict and closure.get('kind')==COMBINED_KIND:return _combined_preflight(run,execution,job_input=job_input)
    require(p['schema_version']==2,'raw route requires explicit combined202 closure')
    return _transfer_preflight_legacy(run,execution,job_input=job_input)

class _RawWorker:
    def __init__(self,run,execution,job_input):
        self.run=run;self.execution=execution;self.job_input=job_input;self.thread=threading.get_ident();self.context=None;self.cm=None
    def __enter__(self):
        global _WORKER
        from . import completed_f32,archive_non_tail
        with _LOCK:
            require(_WORKER is None,'another selected worker scope active')
            p,outputs=transfer_preflight(self.run,self.execution,job_input=self.job_input)
            require(p['schema_version']==3 and all(name not in self.run._published_outputs and not os.path.lexists(self.run.directory/'outputs'/name) for name in outputs),'raw output reserved before Context birth')
            self.cm=completed_f32.completed_worker(self.run,job_input=self.job_input)
            self.context=self.cm.__enter__()
            try:
                require(type(self.context) is archive_non_tail.Context and self.context.run is self.run and self.context.policy['schema_version']==3,'genuine completed raw Context required')
                self.context.check();_WORKER=self
            except BaseException as primary:
                archive_non_tail.close_all([lambda:self.cm.__exit__(type(primary),primary,primary.__traceback__)],primary)
        return self
    def __exit__(self,typ,primary,tb):
        global _WORKER
        from . import archive_non_tail
        failure=primary
        try:require(_WORKER is self and self.thread==threading.get_ident(),'raw worker ownership changed')
        except BaseException as error:failure=archive_non_tail.select(failure,error)
        try:self.cm.__exit__(None if failure is None else type(failure),failure,None if failure is None else failure.__traceback__)
        except BaseException as error:failure=archive_non_tail.select(failure,error)
        finally:
            with _LOCK:
                if _WORKER is self:_WORKER=None
        if failure is not None:raise failure
        return False

def _raw_current(run,p):
    from . import archive_non_tail
    with _LOCK:
        worker=_WORKER
        require(type(worker) is _RawWorker and worker.run is run and worker.thread==threading.get_ident(),'raw route lacks original worker scope')
        require(type(worker.context) is archive_non_tail.Context and worker.context.run is run and worker.context.input==p['population_input'],'genuine raw Context/policy differs')
        again,_=transfer_preflight(run,worker.execution,job_input=worker.job_input);require(again==p,'raw policy changed');worker.context.check();return worker
'''
(P/'held_score_consumer.py').write_text(s)
r=(P/'resource_fixture.py.baseline').read_text();assert r.count("if policy['schema_version']==2:")==1;r=r.replace("if policy['schema_version']==2:","if policy['schema_version'] in (2,3):");(P/'resource_fixture.py').write_text(r)
(P/'completed_f32.py').write_bytes((P/'completed_f32.py.baseline').read_bytes())
