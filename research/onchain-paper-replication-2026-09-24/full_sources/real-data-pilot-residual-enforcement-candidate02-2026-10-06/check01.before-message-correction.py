"""Focused offline checks of sampled residuals and their real publication seams."""
from pathlib import Path
import ast,contextlib,copy,hashlib,io,json,os,sys,tempfile,types,unittest
from unittest.mock import patch
H=Path(__file__).resolve().parent

def audit(event,args):
    if event.startswith(('subprocess.','socket.')):raise RuntimeError('offline only')
    if event=='import' and args[0].split('.')[0] in {'torch','numpy','pandas','scipy'}:raise RuntimeError('numerical import refused')
sys.addaudithook(audit)
prefix='residual_offline'
pkg=types.ModuleType(prefix);pkg.__path__=[str(H)];sys.modules[prefix]=pkg

def load(name):
    m=types.ModuleType(prefix+'.'+name);m.__package__=prefix;m.__file__=str(H/(name+'.py'))
    sys.modules[m.__name__]=m;exec(compile((H/(name+'.py')).read_text(),m.__file__,'exec'),vars(m));return m
ws=load('workflow_storage');rs=load('real_pilot_storage')

def functions(path,names,namespace):
    tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace);return namespace
native=functions(H/'resources.py',{'_native_write','_native_atomic','_native_sync'},{'json':json,'os':os})

class Opened:
    def __init__(self,short=False):self.births=0;self.raw=bytearray();self.short=short
    def _opened(self,path,mode):self.births+=1;return self
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def write(self,value):
        n=len(value)-1 if self.short else len(value);self.raw.extend(value[:n]);return n
    def flush(self):pass
    def fileno(self):return 1
    def _cleanup(self,actions):
        for a in actions:a()

class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=H,prefix='synthetic-');self.root=Path(self.tmp.name).resolve()
        (self.root/'research_artifacts').mkdir();(self.root/'research_runs').mkdir();(self.root/'research_runs/.lock').touch()
        self.limits={'max_allocated_bytes':20*1024**3,'max_logical_bytes':16*1024**3,'max_entries':1000000,'max_depth':64,'max_scan_seconds':5}
        self.budget={'schema_version':2,'kind':rs.KIND,'authority_root':str(self.root),'experiment':rs.EXPERIMENT,'roots':[str(self.root/'research_artifacts'),str(self.root/'research_runs'/rs.EXPERIMENT)],'shared_files':[str(self.root/'research_runs/.lock')],'limits':self.limits}
        self.policy=copy.deepcopy(rs.RESIDUAL_POLICY)
    def tearDown(self):rs.RESIDUAL_POLICY.clear();rs.RESIDUAL_POLICY.update(self.policy);self.tmp.cleanup()
    def root_for(self,domain,index=0):
        p=rs.residual_paths(self.root)[domain][index];p.mkdir(parents=True,exist_ok=True);return p
    def small(self,domain):rs.RESIDUAL_POLICY[domain]={'logical_bytes':128,'regular_files':8,'directories':8,'max_file_bytes':64}
    def test_complete_union_contains_domains_without_double_counting(self):
        p=self.root_for('runtime_temp_cache');(p/'body').write_bytes(b'abc')
        watch=rs.WritableUnion(self.budget,self.root);obs=watch.check()
        self.assertEqual(obs['logical_file_bytes'],3);self.assertEqual(obs['residual_domains']['runtime_temp_cache']['logical_file_bytes'],3)
        self.assertEqual(watch.native_metadata_bytes,4*1024**2)
    def test_runtime_logical_and_per_file_refusals(self):
        self.small('runtime_temp_cache');p=self.root_for('runtime_temp_cache');(p/'body').write_bytes(b'x'*65)
        with self.assertRaisesRegex(ws.StorageLimit,'domain file bytes'):rs.residual_check(self.root)
        (p/'body').unlink()
        for n in range(3):(p/str(n)).write_bytes(b'x'*50)
        with self.assertRaisesRegex(ws.StorageLimit,'logical'):rs.residual_check(self.root)
    def test_lifecycle_counts_aggregate_both_roots(self):
        self.small('training_and_lifecycle')
        for index in (0,1):
            p=self.root_for('training_and_lifecycle',index)
            for n in range(5):(p/str(n)).write_bytes(b'x')
        with self.assertRaisesRegex(ws.StorageLimit,'domain regular_files'):rs.residual_check(self.root)
    def test_pending_and_atomic_scratch_are_included(self):
        a=self.root_for('training_and_lifecycle');b=self.root_for('training_and_lifecycle',1)
        (a/'.pending-synthetic').write_bytes(b'x'*7);(b/'live.tmp').write_bytes(b'y'*11)
        v=rs.residual_check(self.root)['training_and_lifecycle'];self.assertEqual(v['logical_file_bytes'],18);self.assertEqual(v['regular_files'],2)
    def test_redirected_root_and_rebirth_refused(self):
        p=self.root_for('runtime_temp_cache');identities={};rs.residual_check(self.root,identities=identities)
        p.rename(p.with_name('old-runtime'));p.mkdir()
        with self.assertRaisesRegex(ValueError,'replaced'):rs.residual_check(self.root,identities=identities)
        p.rmdir();p.symlink_to(p.with_name('old-runtime'),target_is_directory=True)
        with self.assertRaises(ValueError):rs.residual_check(self.root)
    def test_absence_has_no_invented_identity_and_later_birth_pinned(self):
        ids={};a=rs.residual_check(self.root,identities=ids);self.assertEqual(ids,{})
        p=self.root_for('runtime_temp_cache');rs.residual_check(self.root,identities=ids);self.assertIn(str(p),ids)
        p.rmdir()
        with self.assertRaisesRegex(ValueError,'disappeared'):rs.residual_check(self.root,identities=ids)
    def test_shared_time_limit_is_not_reset(self):
        with patch.object(rs.time,'monotonic',return_value=6):
            with self.assertRaisesRegex(ws.StorageLimit,'residual time'):rs.residual_check(self.root,begin=0)
    def test_entry_policy_invalid_and_legacy_none(self):
        p=self.root_for('runtime_temp_cache');(p/'body').write_bytes(b'x'*65)
        self.assertEqual(ws.StorageWatch(p,self.limits).check()['logical_file_bytes'],65)
        for bad in ({'regular_files':True,'directories':1,'max_file_bytes':1},{'regular_files':1,'directories':1}):
            with self.assertRaises(ValueError):ws.StorageWatch(p,self.limits,entry_limits=bad)
    def test_exact_lifecycle_file_boundary_and_one_above(self):
        a=self.root_for('training_and_lifecycle');b=self.root_for('training_and_lifecycle',1)
        for n in range(68):(a/str(n)).write_bytes(b'x')
        self.assertEqual(rs.residual_check(self.root)['training_and_lifecycle']['regular_files'],68)
        (b/'extra').write_bytes(b'x')
        with self.assertRaisesRegex(ws.StorageLimit,'residual aggregate regular_files'):rs.residual_check(self.root)
    def test_exact_lifecycle_directory_boundary_and_one_above(self):
        a=self.root_for('training_and_lifecycle');self.root_for('training_and_lifecycle',1)
        for n in range(14):(a/str(n)).mkdir()
        self.assertEqual(rs.residual_check(self.root)['training_and_lifecycle']['directories'],16)
        (a/'extra').mkdir()
        with self.assertRaisesRegex(ws.StorageLimit,'residual aggregate directories'):rs.residual_check(self.root)
    def test_native_encoder_parity_oversize_and_partial_failure(self):
        value={'status':'failed','error':'retained\ntext','v':[1,True,None]};expected=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
        for cap in (None,len(expected)):
            sink=Opened()
            with patch.object(os,'fsync'):native['_native_write'](Path('synthetic'),value,sink,max_bytes=cap)
            self.assertEqual(bytes(sink.raw),expected)
        sink=Opened()
        with self.assertRaises(ValueError):native['_native_write'](Path('synthetic'),value,sink,max_bytes=len(expected)-1)
        self.assertEqual(sink.births,0)
        sink=Opened(short=True)
        with self.assertRaisesRegex(OSError,'partial retained'):native['_native_write'](Path('synthetic'),value,sink,max_bytes=len(expected))
        self.assertTrue(sink.raw)
    def test_actual_launch_checks_before_publication_and_after_print(self):
        events=[];ns={'Path':Path,'os':os,'uuid':types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='synthetic')), 'json':json,
            '_admitted':lambda a:(None,{'resources':{}}),'_base':lambda a:self.root/'synthetic-job',
            'durable_mkdir':lambda p:p.mkdir(parents=True,exist_ok=True),'sync_directory':lambda p:None,
            '_physical_scope':lambda *a,**k:None,'metadata_scope':lambda s:contextlib.nullcontext(),
            '_immutable':lambda *a:events.append('publication'),'_command':lambda *a:[],
            'subprocess':types.SimpleNamespace(Popen=lambda *a,**k:types.SimpleNamespace(wait=lambda:events.append('monitor-ended') or 0,poll=lambda:0)),
            'signal':types.SimpleNamespace(SIGTERM=15,SIGINT=2,signal=lambda *a:None),
            'reconcile':lambda a:{'status':'complete'}}
        functions(H/'job.py',{'launch'},ns)
        def observed(*a):events.append('residual-check')
        ns['_pilot_residual_tail']=observed
        output=io.StringIO()
        with contextlib.redirect_stdout(output):self.assertEqual(ns['launch'](types.SimpleNamespace(root=str(self.root),experiment=rs.EXPERIMENT,source='synthetic')),0)
        self.assertEqual(events,['residual-check','publication','monitor-ended','residual-check','residual-check'])
        self.assertIn('complete',output.getvalue())
    def test_late_source_launch_failure_keeps_output_and_propagates(self):
        source=ast.parse((H/'job.py').read_text());fn=next(x for x in source.body if isinstance(x,ast.FunctionDef) and x.name=='launch')
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_pilot_residual_tail' for n in ast.walk(fn)),3)
        # Same actual source function from previous test, with final checker failure.
        ns={};calls=[]
        ns.update(Path=Path,os=os,uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='synthetic')),json=json,
            _admitted=lambda a:(None,{'resources':{}}),_base=lambda a:self.root/'late-job',durable_mkdir=lambda p:p.mkdir(parents=True,exist_ok=True),sync_directory=lambda p:None,
            _physical_scope=lambda *a,**k:None,metadata_scope=lambda s:contextlib.nullcontext(),_immutable=lambda *a:None,_command=lambda *a:[],
            subprocess=types.SimpleNamespace(Popen=lambda *a,**k:types.SimpleNamespace(wait=lambda:0,poll=lambda:0)),signal=types.SimpleNamespace(SIGTERM=15,SIGINT=2,signal=lambda *a:None),reconcile=lambda a:{'status':'complete'})
        functions(H/'job.py',{'launch'},ns)
        def fail_final(*a):
            calls.append(1)
            if len(calls)==3:raise ws.StorageLimit('synthetic final',{})
        ns['_pilot_residual_tail']=fail_final;out=io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaisesRegex(ws.StorageLimit,'synthetic final'):ns['launch'](types.SimpleNamespace(root=str(self.root),experiment=rs.EXPERIMENT,source='synthetic'))
        self.assertIn('complete',out.getvalue());self.assertEqual(len(calls),3)

if __name__=='__main__':unittest.main(verbosity=2)
