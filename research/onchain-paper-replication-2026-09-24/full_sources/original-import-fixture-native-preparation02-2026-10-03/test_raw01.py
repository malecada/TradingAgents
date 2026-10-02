"""Retained tiny fake raw receipts exercise real parser, never live authority."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
import raw_receipts01 as parser

def enc(v):return json.dumps(v,sort_keys=True).encode()
def sha(b):return hashlib.sha256(b).hexdigest()

def fixture(root,case):
    source='a'*40;identity='synthetic-parser-case';registration='gate.json';base='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity;run='research_runs/'+identity
    def write(name,value):
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value if isinstance(value,bytes) else enc(value))
    limits={'memory_max_bytes':3*parser.GIB,'memory_high_bytes':3*parser.GIB,'memory_swap_max_bytes':0};environment={'TMPDIR':str(root/'tmp')};family={'mechanism_id':'original-dictionary-import-engineering-v1','attempt_budget':2,'prior_attempts':0};outputs=['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json'];experiment={'outputs':outputs,'inputs':{}};targets=[{'graph_hash':'1'*64,'nodes':2},{'graph_hash':'2'*64,'nodes':3}]
    release={'cases':{case:{'identity':identity,'job_resources':limits,'experiment':experiment,'targets':targets}},'capsule_commit':source,'runtime':{'executable':'/pinned/python'},'registration':registration,'registration_sha256':'b'*64,'program_id':'original-dictionary-import-engineering-2026-10-02','family':family,'native_environment':environment}
    launch={'experiment':identity,'source_commit':source,'supervisor_pid':2000000101,'nonce':'n'};owner=launch|{'monitor_pid':2000000102,'monitor_start_ticks':'1'};unit='onchain-replication-'+'a'*32+'.service';cg='/sys/fs/cgroup/'+unit
    command=['/pinned/python','-B','-m','tradingagents.research.onchain_replication.job','--mode','worker','--root',str(root),'--registration',registration,'--experiment',identity,'--source',source]
    guard=limits|{'owner_identity':owner,'monitor_pid':owner['monitor_pid'],'command':command,'cwd':str(root),'kernel_controls':{'memory.max':str(3*parser.GIB),'memory.high':str(3*parser.GIB),'memory.swap.max':'0'},'cpus':[0,1],'native_unit_properties':{'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'30min'},'native_environment':environment,'unit':unit,'cgroup':cg,'cleanup_verified':True,'cleanup_unit_properties':{'ActiveState':'inactive','SubState':'dead'},'memory_events':{'oom':0,'oom_kill':0},'phase':'complete' if case=='success' else 'failed','child_exit_code':0 if case=='success' else 1,'limit_reason':None if case=='success' else "RuntimeError: child or unit failed: {'Result':'exit-code'}",'unit_properties':{'Result':'success' if case=='success' else 'exit-code'}}
    write(base+'/launch.json',launch);write(base+'/owner.json',owner);write(base+'/guard/final.json',guard);write(base+'/guard/release.json',{'kernel_controls_verified':True});write(base+'/guard/child.log',b'tiny fake child log\n')
    write(base+'/guard/cpu_ready.json',{'pid':2000000103,'cpus':[0,1],'native_unit_limits':{'file_size_bytes':parser.MAX},'file_size_limit':[parser.MAX]*2,'native_environment':environment});write(base+'/guard/child_exit.json',{'workload_pid':2000000104,'exit_code':guard['child_exit_code']})
    for role,pid in [('monitor',2000000102),('worker',2000000104)]:write(base+'/'+role+'-file-limit.json',{'role':role,'experiment':identity,'source_commit':source,'pid':pid,'file_size_limit':[parser.MAX]*2,'before_claim':True,'native_environment':environment,'native_unit':unit if role=='worker' else None,'native_cgroup':cg if role=='worker' else None})
    cells=[]
    for i,target in enumerate(targets):
        if case!='success' and i==1:cells.append({'id':'import-target-02','status':'failed','reason':'FixturePublicationFailure'});continue
        path='research_artifacts/test-output/'+str(i);matrix=b'\0'*(4*32*target['nodes']);manifest={'rows':target['nodes'],'motifs':32,'dtype':'<f4','order':'row-major','array_sha256':sha(matrix)};manifest_raw=enc(manifest);receipt=enc({'artifact_sha256':sha(manifest_raw)})
        write(path+'/artifact/matrix.f32',matrix);write(path+'/artifact/manifest.json',manifest_raw);write(path+'/receipt.json',receipt)
        record={'graph_hash':target['graph_hash'],'rows':target['nodes'],'motifs':32,'cells':32*target['nodes'],'matrix_sha256':sha(matrix),'output':{'directory':str(root/path),'receipt_sha256':sha(receipt),'artifact_sha256':sha(manifest_raw)}}
        cells.append({'id':'import-target-0'+str(i+1),'status':'complete','target':record,'reference_atol':1e-5,'reference_rtol':1e-4})
    summary={'resource_only':True,'financial_representation_admitted':False,'original_motifs':32,'cells':cells,'original_dictionary':'48832eeb9774ef6ca13915364c17d1ac89f5c67165636de5811ebf82ad6ad726'}
    journal={'schema_version':2,'kind':'original-import-resource-terminal','status':'complete' if case=='success' else 'failed','resource_only':True,'financial_representation_admitted':False}
    if case=='success':
        journal_owner={'experiment':identity,'source_commit':source,'workflow_identity':'d'*64,'producer':'fixture'};compact=enc({'stages':3,'pairs':160,'representation_admitted':False})
        journal.update(original_dictionary=summary['original_dictionary'],cells=['import-target-01','import-target-02'],targets=[r['target'] for r in cells],owner=journal_owner,compact_owner_sha256=sha(compact))
        d='research_artifacts/onchain_representations/'+'d'*64+'/'+identity
        write(d+'/complete.json',journal);write(d+'/owner.json',journal_owner);write(d+'/compact/complete.json',compact)
    else:journal['reason']='FixturePublicationFailure: second-target publication boundary'
    for name,value in [('cell-ledger.json',cells),('resource-summary.json',summary),('resource-binding.json',journal),('resource-journal.json',journal)]:write(run+'/outputs/'+name,value)
    claim={'experiment_id':identity,'source':source,'program_id':release['program_id'],'registration':registration,'registration_sha256':'b'*64,'family':family,'experiment':experiment,'inputs':{}};write(run+'/claim.json',claim)
    status='complete' if case=='success' else 'failed';terminal={'status':status,'experiment_id':identity,'claim_sha256':sha(enc(claim)),'output_sha256':{name:sha((root/run/'outputs'/name).read_bytes()) for name in outputs}}
    if status=='complete':terminal.update(source=source,registration_sha256='b'*64,cells=cells,cell_count=2,unavailable_count=0)
    else:terminal['reason']='FixturePublicationFailure: registered second-target publication boundary; retain first output; no retry'
    write(run+'/'+status+'.json',terminal)
    return release,base,run,write

class Raw(unittest.TestCase):
    def test_success_and_expected_failed_lifecycle_controls(self):
        for case in ('success','second_target_publication_failure'):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);release,*_=fixture(root,case);result=parser.authenticate(root,case,release);self.assertEqual(result['expected_failure'],case!='success')
    def test_source_native_and_failure_counterexamples(self):
        mutations=[('guard/final.json','storage_breach',{'allocated_bytes':999}),('guard/final.json','cleanup_verified',False),('guard/final.json','command',['different']),('guard/cpu_ready.json','file_size_limit',None),('guard/cpu_ready.json','native_environment',{}),('worker-file-limit.json','pid',2000000111),('guard/final.json','memory_events',{'oom':1,'oom_kill':0}),('guard/final.json','native_unit_properties',{'LimitFSIZE':'4194304','LimitFSIZESoft':'infinity','RuntimeMaxUSec':'30min'})]
        for name,key,value in mutations:
            with self.subTest(name=name,key=key),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);release,base,_,write=fixture(root,'second_target_publication_failure');record=parser.metadata(root,base+'/'+name);record[key]=value;write(base+'/'+name,record)
                with self.assertRaises((ValueError,KeyError)):parser.authenticate(root,'second_target_publication_failure',release)
    def test_resource_terminal_mutation_even_with_rehashed_outputs(self):
        for key,value in [('status','failed'),('financial_representation_admitted',True),('cells',['import-target-01']),('compact_owner_sha256','e'*64)]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);release,base,run,write=fixture(root,'success')
                terminal=parser.metadata(root,run+'/complete.json')
                for name in ('resource-binding.json','resource-journal.json'):
                    current=parser.metadata(root,run+'/outputs/'+name);current[key]=value;write(run+'/outputs/'+name,current);terminal['output_sha256'][name]=sha((root/run/'outputs'/name).read_bytes())
                write(run+'/complete.json',terminal)
                with self.assertRaises(ValueError):parser.authenticate(root,'success',release)
    def test_changed_matrix_and_claim_rejected(self):
        for which in ('matrix','claim'):
            with self.subTest(which=which),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);release,base,run,write=fixture(root,'success')
                if which=='matrix':write('research_artifacts/test-output/0/artifact/matrix.f32',b'x'*256)
                else:
                    claim=parser.metadata(root,run+'/claim.json');claim['source']='c'*40;write(run+'/claim.json',claim)
                with self.assertRaises(ValueError):parser.authenticate(root,'success',release)
if __name__=='__main__':unittest.main()
