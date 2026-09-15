"""Standalone bootstrap adversarial inventory checks before package imports."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('release_bootstrap_test',ROOT/'scripts/options_timing_release_bootstrap.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def bundle(tmp_path):
    package=tmp_path/'package';package.mkdir();data=tmp_path/'data'
    sources={}
    for name in b.FILES:
        path=package/name;path.parent.mkdir(parents=True,exist_ok=True)
        body=(ROOT/'scripts/options_timing_release_bootstrap.py').read_bytes() if name=='release_bootstrap.py' else b'# synthetic source\n'
        path.write_bytes(body);sources[name]=hashlib.sha256(body).hexdigest()
    (package/'claim.json').write_bytes(b'{}')
    assignment={'package_files':sources,'claim_sha256':hashlib.sha256(b'{}').hexdigest(),'data_root':str(data),'host_identity':os.uname().nodename}
    raw=json.dumps(assignment).encode();(package/'assignment.json').write_bytes(raw)
    return package,data,hashlib.sha256(raw).hexdigest()


def test_external_anchor_complete_bundle(tmp_path):
    package,data,sha=bundle(tmp_path)
    assert b.verify(package,data,sha)==package


@pytest.mark.parametrize('fault',['extra_init','symlink','changed','missing','wrong_sha','wrong_root'])
def test_rejects_changed_or_unregistered_source_before_import(tmp_path,fault):
    package,data,sha=bundle(tmp_path);marker=tmp_path/'imported'
    if fault=='extra_init':(package/'tradingagents/__init__.py').write_text(f'open({str(marker)!r},"w").write("bad")')
    if fault=='symlink':(package/'unexpected').symlink_to(tmp_path)
    if fault=='changed':(package/'claim.json').write_bytes(b'{"changed":1}')
    if fault=='missing':(package/'claim.json').unlink()
    if fault=='wrong_sha':sha='0'*64
    if fault=='wrong_root':data=tmp_path/'other'
    with pytest.raises((ValueError,FileNotFoundError)):b.verify(package,data,sha)
    result=subprocess.run([sys.executable,'-I','-B',str(package/'release_bootstrap.py'),str(package),str(data),sha],capture_output=True,timeout=5)
    assert result.returncode!=0 and not marker.exists()


def test_entry_requires_isolated_mode(tmp_path):
    package,data,sha=bundle(tmp_path)
    result=subprocess.run([sys.executable,'-B',str(package/'release_bootstrap.py'),str(package),str(data),sha],capture_output=True,timeout=5)
    assert result.returncode!=0 and b'-I -B required' in result.stderr
