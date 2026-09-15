"""Externally SHA-checked entry point, executed with isolated Python -I -B.

Usage: python3.13 -I -B release_bootstrap.py PACKAGE DATA ASSIGNMENT_SHA256
No package imports occur until the externally anchored complete inventory passes.
The runtime distribution must be separately verified before this script runs.
"""
import hashlib
import json
import os
from pathlib import Path
import runpy
import stat
import sys

FILES={f'tradingagents/research_options_timing/{n}.py' for n in ('journal','transport','schedule','worker','adapter')}
FILES.add('release_bootstrap.py')
FILES.update('research/strategy-search-2026-09-11/options_policy_'+n+'.py' for n in ('selection','batch'))


def safe(path):
    path=Path(path)
    if not path.is_absolute() or str(path)!=str(path.resolve()):raise ValueError('canonical absolute path required')
    for p in (path,*path.parents):
        if p.is_symlink():raise ValueError('symlink forbidden')
    return path


def read(path,cap):
    fd=os.open(safe(path),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size>cap:raise ValueError('bounded regular file required')
        with os.fdopen(fd,'rb',closefd=False) as stream:return stream.read(cap+1)
    finally:os.close(fd)


def verify(package,data,expected):
    package=safe(package);data=safe(data)
    raw=read(package/'assignment.json',1024**2)
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('external assignment SHA mismatch')
    assignment=json.loads(raw)
    if set(assignment['package_files'])!=FILES:raise ValueError('exact source inventory required')
    allowed=FILES|{'assignment.json','claim.json'};seen=set()
    for current,dirs,names in os.walk(package,followlinks=False):
        for name in dirs:
            if (Path(current)/name).is_symlink():raise ValueError('symlink directory forbidden')
        for name in names:
            p=Path(current)/name;rel=p.relative_to(package).as_posix()
            if rel not in allowed:raise ValueError('unexpected source member')
            cap=512*1024 if rel=='claim.json' else 2*1024**2
            body=read(p,cap);seen.add(rel)
            expected_hash=assignment['package_files'].get(rel)
            if rel=='claim.json':expected_hash=assignment['claim_sha256']
            if expected_hash is not None and hashlib.sha256(body).hexdigest()!=expected_hash:raise ValueError('anchored member mismatch')
    if seen!=allowed:raise ValueError('missing anchored source member')
    if str(data)!=assignment['data_root'] or assignment['host_identity']!=os.uname().nodename:raise ValueError('assigned host/data mismatch')
    return package


def main():
    if sys.version_info[:3]!=(3,13,13) or not sys.flags.isolated or not sys.dont_write_bytecode:raise ValueError('verified Python3.13.13 -I -B required')
    if len(sys.argv) not in (4,6) or len(sys.argv)==6 and (sys.argv[4]!='--child-fd' or not sys.argv[5].isdigit()):raise ValueError('package data expectedSHA and optional inherited child descriptor required')
    package=verify(*sys.argv[1:4])
    if Path(__file__).resolve()!=package/'release_bootstrap.py':raise ValueError('execute anchored bootstrap')
    sys.path.insert(0,str(package))
    # Exact inventory forbids __init__.py, sitecustomize and unpinned shadows.
    runpy.run_module('tradingagents.research_options_timing.worker',run_name='__main__')


if __name__=='__main__':main()
