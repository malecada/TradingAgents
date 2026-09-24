"""Exercise price CLI ownership paths without launching a process or network."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

HERE=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/full_sources/prices-01'


@pytest.mark.parametrize('asset',['BTC','ETH'])
def test_price_supervisor_asset_paths_and_exclusive_identity(tmp_path,monkeypatch,asset):
    spec=importlib.util.spec_from_file_location('price_launch',HERE/'launch.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=tmp_path
    captured=[]
    monkeypatch.setattr(module.subprocess,'check_output',lambda *a,**k:'a'*40+'\n')
    monkeypatch.setattr(module.signal,'signal',lambda *a:None)
    def popen(command,**kwargs):
        assert command[command.index('--asset')+1]==asset
        ownership=tmp_path/'research_artifacts/onchain-paper-replication-2026-09-24'/('source-prices-01-'+asset.lower()+'-supervisor')
        owner=json.loads((ownership/'owner.json').read_text())
        (ownership/'monitor.json').write_text(json.dumps({'nonce':owner['nonce'],'asset':asset}))
        captured.append(command)
        return SimpleNamespace(wait=lambda:0,poll=lambda:0)
    monkeypatch.setattr(module.subprocess,'Popen',popen)
    def reconcile(receipt,artifacts,source,identity,observed_asset):
        assert receipt.name=='source-prices-01-'+asset.lower()+'-guard'
        assert artifacts.name=='paper-prices-'+asset.lower()+'-20260924'
        assert source=='a'*40 and identity['asset']==observed_asset==asset
        return {'status':'complete'}
    monkeypatch.setattr(module.importlib.util,'module_from_spec',lambda _:SimpleNamespace(reconcile=reconcile))
    monkeypatch.setattr(module.importlib.util,'spec_from_file_location',lambda *a:SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _:None)))
    assert module.launch(asset)==0 and len(captured)==1
    with pytest.raises(FileExistsError):module.launch(asset)
    assert len(captured)==1
