"""Numerical-free finite coordinator. One enclosing native guard owns all children.

Not a native launcher/admission service. Never use a closed owned namespace.
The first failed arm ends this finite proof; later arms are recorded unattempted.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('checkpoint_proof_io',HERE/'oracle02.py')
io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)  # stdlib only


def main():
    p=argparse.ArgumentParser();p.add_argument('--owned',type=Path,required=True);p.add_argument('--source-commit',required=True)
    p.add_argument('--run-id',required=True);p.add_argument('--manifest-sha256',required=True);args=p.parse_args()
    io.require(re.fullmatch('[0-9a-f]{40}',args.source_commit) is not None,'source commit required')
    io.require(re.fullmatch('[a-z0-9][a-z0-9-]{1,95}',args.run_id) is not None,'new engineering identity required')
    raw=(HERE/'source-manifest02.json').read_bytes();io.require(io.sha(raw)==args.manifest_sha256,'manifest differs')
    for item in json.loads(raw)['sources']:
        source=io.ROOT/item['path'];io.require(source.resolve()==source and stat.S_ISREG(source.lstat().st_mode) and source.stat().st_size==item['bytes'] and io.sha(source.read_bytes())==item['sha256'],'source differs')
    cg,native=io.native();root=args.owned.absolute();io.require(root.resolve()==root and root.parent.is_dir(),'owned root redirected');root.mkdir(mode=0o700)
    io.write_new(root,'intent.json',io.encoded(dict(run_id=args.run_id,source_commit=args.source_commit,manifest_sha256=args.manifest_sha256,native=native)))
    records=[];primary=None;active=None
    try:
        for mode in io.P['modes']:
            record=dict(mode=mode,status='unattempted',pid=None,returncode=None)
            records.append(record)
            logfd=os.open(root/(mode+'.log'),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
            try:
                command=[sys.executable,'-B',str(HERE/'oracle02.py'),'--mode',mode,'--owned',str(root/mode),
                    '--source-commit',args.source_commit,'--run-id',args.run_id,'--manifest-sha256',args.manifest_sha256]
                started=time.monotonic_ns()
                active=subprocess.Popen(command,cwd=io.ROOT,stdout=logfd,stderr=subprocess.STDOUT,close_fds=True)
                record.update(status='running',pid=active.pid,started_monotonic_ns=started)
                io.write_new(root,mode+'.started.json',io.encoded(record))
                code=active.wait();active=None;record.update(returncode=code,status='exited',ended_monotonic_ns=time.monotonic_ns())
            finally:io.close_once((lambda:os.close(logfd),),sys.exception())
            io.write_new(root,mode+'.exited.json',io.encoded(record))
            io.require(code==0,'arm failed '+mode+' with actual returncode '+str(code))
            terminal_path=root/mode/'terminal.json';io.require(terminal_path.is_file() and not terminal_path.is_symlink(),'arm terminal missing')
            body=terminal_path.read_bytes();io.require(len(body)<=io.P['max_metadata_bytes'],'arm terminal exceeded bound')
            terminal=json.loads(body);io.require(terminal['status']=='passed' and terminal['mode']==mode and terminal['run_id']==args.run_id and terminal['manifest_sha256']==args.manifest_sha256,'arm terminal identity/status differs')
    except BaseException as error:primary=error
    def assemble(selected):
        # Padding and error formatting belong to the protected assembly too.
        for mode in io.P['modes'][len(records):]:records.append(dict(mode=mode,status='unattempted',pid=None,returncode=None))
        return dict(schema_version=1,status='passed' if selected is None else 'failed',run_id=args.run_id,
            source_commit=args.source_commit,manifest_sha256=args.manifest_sha256,arms=records,
            active_child_pid=None if active is None else active.pid,cleanup_owner='outer-native-guard',
            error=None if selected is None else dict(type=type(selected).__name__,message=str(selected)))
    return io.terminal_boundary(primary,None,assemble,
        lambda value:io.write_new(root,'terminal.json',io.encoded(value)))
if __name__=='__main__':raise SystemExit(main())
