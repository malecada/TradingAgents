"""Synthetic compact evidence; OS death/boot boundaries mocked, no jobs or arrays."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent

def api():
    assert (HERE/'death.py').is_file(),'failed-owner death verifier missing'
    s=importlib.util.spec_from_file_location('candidate_death',HERE/'death.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class DeathTests(unittest.TestCase):
    def setUp(self):
        self.m=api();self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.name='synthetic-failed-parent';self.source='a'*40
        self.run=self.root/'research_runs'/self.name
        self.base=self.root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/self.name
        self.run.mkdir(parents=True);(self.base/'guard').mkdir(parents=True)
        self.files={};self.values={}
        self.owner={'experiment':self.name,'source_commit':self.source,'supervisor_pid':101,'nonce':'synthetic','monitor_pid':102,'monitor_start_ticks':'123'}
        self.write('claim',self.run/'claim.json',{'experiment_id':self.name,'source':self.source,'registration':'synthetic-gate.json'})
        self.write('failed',self.run/'failed.json',{'status':'failed','experiment_id':self.name,'claim_sha256':self.files['claim']['sha256'],'output_sha256':{}})
        self.write('owner',self.base/'owner.json',self.owner)
        self.write('launch',self.base/'launch.json',{k:v for k,v in self.owner.items() if k not in ('monitor_pid','monitor_start_ticks')})
        self.live={'owner_identity':self.owner,'monitor_pid':102,'boot_id':'synthetic-boot',
            'command':[str(self.root/'.venv/bin/python'),'-B','-m','tradingagents.research.onchain_replication.job','--mode','worker','--root',str(self.root),'--registration','synthetic-gate.json','--experiment',self.name,'--source',self.source],
            'cgroup':'/sys/fs/cgroup/user.slice/onchain-replication-synthetic.service','unit':'onchain-replication-synthetic.service','phase':'running'}
        self.write('live',self.base/'guard/live.json',self.live)
        self.write('death',self.base/'guard/observer-death.json',{**self.live,'phase':'failed','cleanup_verified':True,'live_sha256':self.files['live']['sha256']})
        self.write('cells',self.base/'postmortem-cells.json',[])
        self.write('journals',self.base/'unsealed-journals.json',[])
        self.write('observer',self.base/'observer.json',{'status':'failed','owner_sha256':self.files['owner']['sha256'],
            'terminal_sha256':self.files['failed']['sha256'],'cgroup_empty':True,
            'cell_ledger_sha256':self.files['cells']['sha256'],'unsealed_journals':0,
            'evidence_sha256':{str((self.root/v['path']).relative_to(self.base)):v['sha256'] for k,v in self.files.items() if k in ('launch','live','death','cells','journals')}})
        self.patches=[patch.object(self.m,'boot_id',return_value='synthetic-boot'),
            patch.object(self.m,'same_process_alive',return_value=False),
            patch.object(self.m,'pid_exists',return_value=False),
            patch.object(self.m,'group_populated',return_value=False)]
        self.mocks=[p.start() for p in self.patches]
        self.addCleanup(patch.stopall)

    def write(self,key,path,value):
        raw=json.dumps(value,sort_keys=True).encode();path.write_bytes(raw)
        self.files[key]={'path':str(path.relative_to(self.root)),'sha256':hashlib.sha256(raw).hexdigest()};self.values[key]=value

    def change(self,key,**changes):
        self.write(key,self.root/self.files[key]['path'],{**self.values[key],**changes})

    def verify(self):return self.m.verify(self.root,{'experiment':self.name,'source_commit':self.source},self.files)

    def test_joined_failed_owner_is_read_only(self):
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result=self.verify()
        self.assertEqual(result['experiment'],self.name);self.assertFalse(result['continuation_admitted'])
        self.assertFalse(result['outputs_verified']);self.assertFalse(result['arrays_read'])
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_active_monitor_refused(self):
        self.mocks[1].return_value=True
        with self.assertRaises(ValueError):self.verify()

    def test_existing_supervisor_refused(self):
        self.mocks[2].return_value=True
        with self.assertRaises(ValueError):self.verify()

    def test_populated_group_refused(self):
        self.mocks[3].return_value=True
        with self.assertRaises(ValueError):self.verify()

    def test_different_boot_refused(self):
        self.mocks[0].return_value='new-boot'
        with self.assertRaises(ValueError):self.verify()

    def test_foreign_source_refused(self):
        with self.assertRaises(ValueError):self.m.verify(self.root,{'experiment':self.name,'source_commit':'b'*40},self.files)

    def test_changed_hash_refused(self):
        (self.run/'claim.json').write_text('{}')
        with self.assertRaises(ValueError):self.verify()

    def test_complete_parent_refused(self):
        (self.run/'complete.json').write_text('{}')
        with self.assertRaises(ValueError):self.verify()

    def test_missing_observer_refused(self):
        self.files.pop('observer')
        with self.assertRaises(ValueError):self.verify()

    def test_foreign_monitor_receipt_refused(self):
        self.change('death',monitor_pid=103)
        with self.assertRaises(ValueError):self.verify()

    def test_observer_terminal_join_refused(self):
        self.change('observer',terminal_sha256='b'*64)
        with self.assertRaises(ValueError):self.verify()

    def test_copied_claim_outside_fixed_layout_refused(self):
        p=self.root/'foreign.json';p.write_bytes((self.run/'claim.json').read_bytes());self.files['claim']['path']=p.name
        with self.assertRaises(ValueError):self.verify()

    def test_linked_evidence_refused(self):
        p=self.run/'claim.json';q=self.root/'copy';p.rename(q);p.symlink_to(q)
        with self.assertRaises(ValueError):self.verify()

    def test_oversized_metadata_refused(self):
        p=self.run/'claim.json';raw=b' '*(self.m.MAX_BYTES+1);p.write_bytes(raw);self.files['claim']['sha256']=hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError):self.verify()

    def test_existing_final_cannot_be_omitted(self):
        (self.base/'guard/final.json').write_text('{}')
        with self.assertRaises(ValueError):self.verify()

    def test_optional_final_must_join_observer(self):
        self.write('final',self.base/'guard/final.json',{**self.live,'phase':'failed'})
        evidence={**self.values['observer']['evidence_sha256'],'guard/final.json':self.files['final']['sha256']}
        self.change('observer',evidence_sha256=evidence)
        self.assertEqual(self.verify()['checked_evidence_files'],10)

    def test_observer_evidence_inventory_cannot_omit_journals(self):
        evidence=dict(self.values['observer']['evidence_sha256']);evidence.pop('unsealed-journals.json')
        self.change('observer',evidence_sha256=evidence)
        with self.assertRaises(ValueError):self.verify()

    def test_monitor_recheck_refuses_changed_liveness(self):
        self.mocks[1].side_effect=[False,True]
        with self.assertRaises(ValueError):self.verify()

    def test_final_appearing_during_liveness_check_refused(self):
        def dead_monitor(*args):
            (self.base/'guard/final.json').write_text('{}')
            return False
        self.mocks[1].side_effect=dead_monitor
        with self.assertRaises(ValueError):self.verify()

    def test_broken_final_symlink_refused(self):
        (self.base/'guard/final.json').symlink_to(self.root/'missing')
        with self.assertRaises(ValueError):self.verify()

if __name__=='__main__':unittest.main()
