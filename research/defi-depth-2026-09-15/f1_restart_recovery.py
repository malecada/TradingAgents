"""Reviewed manual attachment to one interrupted, zero-output F1 claim.

This is additional execution provenance, not a new empirical claim or a general
resume API. Original source, registration, claim and runtime files stay intact.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from tradingagents.research import ResearchRun,admit
from tradingagents.research.lifecycle import _immutable,_lock
from tradingagents.research.verify import verify_claim

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
CONFIG='research/defi-depth-2026-09-15/f1-restart-recovery.json'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()


def empty_live_claim(root,config):
    directory=Path(root)/'research_runs'/config['experiment']
    if not directory.is_dir() or directory.is_symlink():raise ValueError('original claim directory required')
    if {p.name for p in directory.iterdir()}!={'claim.json','outputs'}:
        raise ValueError('only original claim and empty outputs may exist')
    if not (directory/'outputs').is_dir() or (directory/'outputs').is_symlink() or list((directory/'outputs').iterdir()):
        raise ValueError('zero-output recovery forbids any published or pending output')
    raw=(directory/'claim.json').read_bytes()
    if sha(raw)!=config['original_claim_sha256']:raise ValueError('original claim hash changed')
    return directory,raw


def restore(root,config,source_guard=lambda:None):
    """Restore ownership bookkeeping only after complete original admission checks."""
    root=Path(root).resolve()
    with _lock(root):
        directory,raw=empty_live_claim(root,config)
        claim=verify_claim(directory)
        if (claim['source']!=config['original_source'] or claim['registration']!=config['registration']
            or claim['started_at']!=config['original_started_at']):raise ValueError('original claim identity differs')
        admitted=admit(root=root,registration=claim['registration'],experiment=claim['experiment_id'],
            source=claim['source'],design_source=claim['design_source'],bindings=claim['bindings'],_own_claim=claim['experiment_id'])
        if not admitted.ready or admitted.inputs!=claim['inputs'] or admitted.experiment!=claim['experiment'] or admitted.family!=claim['family']:
            raise ValueError('restored admission differs from the already spent original claim')
        class RecoveredRun(ResearchRun):
            def _check_source(self):
                source_guard()
                return super()._check_source()
        run=RecoveredRun(admitted)
        run._claim_sha256=sha(raw);run._published_outputs={}
        run._check_source();run._check_inputs()
        empty_live_claim(root,config)
        return run


def factory(run):
    class ExistingClaim:
        used=False
        @classmethod
        def start(cls,**arguments):
            expected={'root':run.admission.root,'registration':run.admission.registration,
                      'experiment':run.admission.experiment_id,'source':run.admission.source}
            if cls.used or arguments!=expected:raise ValueError('recovery attaches once to the exact original main')
            cls.used=True
            return run
    return ExistingClaim


@contextmanager
def exclusive_owner(root,experiment):
    # The lock is shared by all recovery checkout locations for this original
    # root. Hidden runtime metadata does not enter the scientific output grid.
    with (Path(root)/'research_runs'/('.'+experiment+'-recovery.lock')).open('a') as handle:
        fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def reserve_attachment(root,config,event):
    """One durable attachment across all adapter checkout locations, even crashes."""
    path=Path(root)/'research_runs'/('.'+config['experiment']+'-recovery-attachment.json')
    _immutable(path,event)
    return path


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--recovery-source',required=True);args=parser.parse_args()
    config_raw=(ROOT/CONFIG).read_bytes();config=json.loads(config_raw)
    def source_guard():
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
        if head!=args.recovery_source:raise ValueError('recovery execution HEAD changed')
        for path,expected in config['source_files'].items():
            raw=(ROOT/path).read_bytes()
            committed=subprocess.check_output(['git','show',args.recovery_source+':'+path],cwd=ROOT)
            if sha(raw)!=expected or raw!=committed:raise ValueError('committed recovery source changed')
        if (ROOT/CONFIG).read_bytes()!=config_raw or subprocess.check_output(['git','show',args.recovery_source+':'+CONFIG],cwd=ROOT)!=config_raw:
            raise ValueError('committed recovery decision changed')
    source_guard();root=Path(config['execution_root']).resolve()
    # Hold a recovery-specific process lock throughout. The original runtime's
    # lock remains authoritative for every claim/input/output operation.
    records=ROOT/'research_recoveries';records.mkdir(exist_ok=True)
    with exclusive_owner(root,config['experiment']):
        live=subprocess.run(['pgrep','-f','[f]1_source.py'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if live.returncode!=1:raise ValueError('original F1 process absence not established; no recovery attachment')
        directory,raw=empty_live_claim(root,config)
        receipt_dir=records/config['recovery_id']
        if receipt_dir.exists():raise FileExistsError('recovery event already exists')
        event={'recovery_id':config['recovery_id'],'started_at':now(),
            'recovery_source':args.recovery_source,'recovery_config_sha256':sha(config_raw),
            'original_claim_sha256':sha(raw),'original_source':config['original_source'],
            'original_started_at':config['original_started_at'],'original_root':str(root),
            'recovery_receipt_directory':str(receipt_dir),
            'initial_output_members':[],'new_empirical_claim':False,'new_source_request_before_attachment':False,
            'scope':'One manual same-claim zero-output crash continuation; additional execution provenance'}
        reserve_attachment(root,config,event)
        receipt_dir.mkdir(exist_ok=False)
        _immutable(receipt_dir/'started.json',event)
        try:
            run=restore(root,config,source_guard)
            path=root/config['original_runner']
            spec=importlib.util.spec_from_file_location('f1_original_main_recovered',path)
            original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
            original.ResearchRun=factory(run)
            old_argv=sys.argv
            try:
                sys.argv=[str(path),'--source',config['original_source']]
                original.main()
            finally:sys.argv=old_argv
            terminal=directory/'complete.json'
            if not terminal.exists():raise ValueError('original main did not publish completion')
            _immutable(receipt_dir/'complete.json',{'ended_at':now(),'original_claim_sha256':sha((directory/'claim.json').read_bytes()),
                'original_terminal_sha256':sha(terminal.read_bytes()),'original_terminal':'complete.json',
                'scope':'Original frozen claim completed with separately recorded crash-recovery execution'})
        except BaseException as exc:
            _immutable(receipt_dir/'failed.json',{'ended_at':now(),'reason':type(exc).__name__+': '+str(exc),
                'original_claim_sha256':sha((directory/'claim.json').read_bytes()),
                'original_terminal_files':[n for n in ('complete.json','failed.json') if (directory/n).exists()]})
            raise


if __name__=='__main__':main()
