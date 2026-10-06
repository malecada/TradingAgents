"""Synthetic changed-boundary checks; no actual payload or native operations."""
from pathlib import Path
import copy,hashlib,json,os,tempfile,types,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(path):
    m=types.ModuleType('fixture');m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),vars(m));return m
r=load(HERE/'retire01.py');m=load(HERE/'recovery01.py')

class Check(unittest.TestCase):
    def test_exact_recovery_inverse_and_draft_refusal(self):
        d=json.loads((HERE/'SOURCE_DELTA01.json').read_text());body=(HERE/'recovery01.py').read_text();old=(ROOT/d['recovery_parent']).read_text()
        self.assertEqual(body.replace(d['sole_replacement']['after'],d['sole_replacement']['before']),old)
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(),d['parent_sha256'])
        with patch.object(m,'recovery',side_effect=AssertionError('draft reached recovery')),self.assertRaisesRegex(ValueError,'frozen'):
            r.validate(m,json.loads((HERE/'SELECTION_TEMPLATE01.json').read_text()))

    def test_reused_backup_gate_and_absence_delta(self):
        ancestor=load(ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-july25-ledger-relocation-preparation01-2026-10-06/test_sources01.py')
        c,docs=ancestor.bundle(m)
        c,docs=json.loads(json.dumps([c,docs]).replace('real-pilot-july25-ledger-preservation-20261006-01','real-pilot-july25-ledger-preservation-20261006-02'))
        def invoke(c,docs,present=False):
            with patch.object(m,'metadata',side_effect=lambda root,p,pin:json.dumps(docs[p]).encode()),patch.object(m,'current') as current,patch.object(Path,'exists',return_value=False),patch.object(m.os.path,'lexists',return_value=present):
                m.recovery(ROOT,c);return current.call_count
        self.assertEqual(invoke(c,docs),1)
        with self.assertRaisesRegex(ValueError,'already be retired'):invoke(c,docs,True)
        bad=copy.deepcopy(c);bad['recovery_basis']['outcome_review']=None
        with self.assertRaises(ValueError):invoke(bad,docs)
        bad=copy.deepcopy(c);bad['rows'][0]['recovered']['path']=m.ORIGINAL
        with self.assertRaises(ValueError):invoke(bad,docs)
        bad=copy.deepcopy(docs);bad[m.BACKUP+'/ROOT_TERMINAL01.json']['actual_root_tool_exit_code']=1
        with self.assertRaises(ValueError):invoke(c,bad)

    def gate_fixture(self):
        c=json.loads((HERE/'SELECTION_TEMPLATE01.json').read_text());c['status']='FROZEN_FOR_REVIEW';row=c['recovery_selection']['rows'][0];row['original']['mode']=420
        target={'path':str(r.TARGET),'device':66307,'bytes':r.SIZE,'sha256':r.SHA,'stat_identity':[66307,1,1,r.SIZE,1,1,420]}
        refs={k:{'path':'invented/'+k+'.json','sha256':str(i)*64} for i,k in enumerate(c['relocation'],1)};c['relocation']=refs;c['evidence']={v['path']:v['sha256'] for v in refs.values()}
        cp=dict(identity=r.RELOCATION,original=row['original'],target=target,copy_readback_verified=True,external_byte_recovery_verified=True,typed_name_mode_verified=True,original_retired=False,source_retired=False,original_claim_sha256=m.CLAIM_SHA,original_source=m.SOURCE,recovery_review=c['recovery_selection']['recovery_basis']['outcome_review'])
        cr=dict(decision='accepted',identity=r.RELOCATION,copy_receipt_sha256=refs['copy_receipt']['sha256'],full_destination_readback_verified=True)
        rt=dict(identity=r.RELOCATION,original=row['original'],target=target,source_retired=True,original_retired=True,original_parent_status='failed',copy_receipt=refs['copy_receipt'],copy_review=refs['copy_review'])
        bridge=dict(identity=r.RELOCATION,kind='closed-ledger-cross-volume-relocation',predecessor=m.GRAPH,original={k:row['original'][k] for k in ('path','bytes','sha256')},target=target,retirement_evidence=refs['retire_receipt'],copy_readback_verified=True,external_byte_recovery_verified=True,original_retired=True,original_claim_sha256=m.CLAIM_SHA,original_source=m.SOURCE)
        outcome=dict(decision='accepted',identity=r.RELOCATION,copy_success_accepted=True,original_retirement_success_accepted=True,actual_root_exit_code=0,actual_outer_exit_code=0,actual_native_child_exit_code=0,cleanup_verified=True,evidence={v['path']:v['sha256'] for k,v in refs.items() if k!='outcome_review'})
        native=dict(phase='complete',child_exit_code=0,cleanup_verified=True,cgroup='/invented-absent-cgroup',monitor_pid=99999999)
        copy_outer=dict(identity=r.RELOCATION,phase='copy',entry_selected_exit_code=0)
        retire_outer=dict(identity=r.RELOCATION,phase='retire',entry_selected_exit_code=0,guard_phase=None,guard_child_exit_code=None,cleanup_verified=None)
        docs={refs[k]['path']:v for k,v in {'copy_receipt':cp,'copy_review':cr,'retire_receipt':rt,'relocation_receipt':bridge,'outcome_review':outcome,'copy_native':native,'copy_outer':copy_outer,'copy_root':{'actual_root_tool_exit_code':0},'retire_outer':retire_outer,'retire_root':{'actual_root_tool_exit_code':0}}.items()};return c,docs

    def test_actual_outcome_joins_refuse_ambiguity(self):
        c,docs=self.gate_fixture()
        def invoke(c,docs):
            with patch.object(m,'recovery'),patch.object(m,'current'),patch.object(m,'metadata',side_effect=lambda root,p,pin:json.dumps(docs[p]).encode()),patch.object(r,'retained'),patch.object(r.os.path,'lexists',return_value=False):return r.validate(m,c)
        invoke(c,docs)
        changes=[('copy_review','full_destination_readback_verified',False),('retire_receipt','original_retired',None),('copy_root','actual_root_tool_exit_code',1),('retire_root','actual_root_tool_exit_code',1),('retire_outer','guard_child_exit_code',0),('outcome_review','cleanup_verified',False),('relocation_receipt','target',{}),('copy_receipt','original_source','x')]
        for role,key,value in changes:
            bad=copy.deepcopy(docs);bad[c['relocation'][role]['path']][key]=value
            with self.subTest(role=role,key=key),self.assertRaises(ValueError):invoke(c,bad)

    def run_retire(self, mode):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            base=Path(directory);data=base/'data';data.mkdir();target=data/'events.sqlite';target.write_bytes(b'keep')
            get=base/'get.bin';get.write_bytes(b'copy');out=base/'out';out.mkdir()
            s=get.stat();row={'recovered':{'path':'get.bin','bytes':4,'mode':s.st_mode&0o777,'stat_identity':m.identity(s)}}
            descriptor={'path':str(target),'stat_identity':r.sig(target.stat())};events={}
            def publish(path,value):events[path.name]=value
            def check_target(value):self.assertEqual(r.sig(target.stat()),value['stat_identity'])
            def unlink(path):
                if mode=='ambiguous':raise OSError('injected unlink uncertainty')
                original_unlink(path)
            original_unlink=Path.unlink
            mm=types.SimpleNamespace(ORIGINAL='original-absent',current=lambda root,desc:get,identity=m.identity)
            cold=types.SimpleNamespace(publish=publish,sync_directory=lambda p:None)
            if mode=='sync':cold.sync_directory=lambda p:(_ for _ in ()).throw(OSError('injected sync'))
            if mode=='complete':
                def fail_complete(path,value):
                    if path.name=='complete01.json':raise OSError('injected complete')
                    publish(path,value)
                cold.publish=fail_complete
            with patch.object(r,'ROOT',base),patch.object(r,'HERE',out),patch.object(r,'TARGET',target),patch.object(r,'inactive'),patch.object(r,'retained',side_effect=check_target),patch.object(Path,'unlink',unlink):
                if mode=='ok':r.retire(mm,cold,row,descriptor,{'selection_sha256':'a'*64})
                else:
                    with self.assertRaises(OSError):r.retire(mm,cold,row,descriptor,{'selection_sha256':'a'*64})
            self.assertEqual(target.read_bytes(),b'keep')
            result=events['complete01.json' if mode=='ok' else 'failed01.json']
            self.assertEqual(result['removed'],[] if mode=='ambiguous' else ['get.bin'])
            self.assertEqual(result['ambiguous_attempts'],['get.bin'] if mode=='ambiguous' else [])
            self.assertEqual(result['get_retired'],None if mode=='ambiguous' else True)

    def test_exact_get_only_success(self):self.run_retire('ok')
    def test_unlink_uncertainty_retained(self):self.run_retire('ambiguous')
    def test_post_unlink_sync_failure_retained(self):self.run_retire('sync')
    def test_completion_failure_retained(self):self.run_retire('complete')


if __name__=='__main__':unittest.main(verbosity=2)
