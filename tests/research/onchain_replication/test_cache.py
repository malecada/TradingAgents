import json
import pytest
from tradingagents.research.onchain_replication.cache import cache_key, publish, read_artifact


def test_cache_changes_with_training_or_weights():
    base=dict(source_hashes=['a'*64],config_hash='b'*64,fold_id='2018',train_member_hash='c'*64,dictionary_hash='d'*64,seed=11,weight_hash='e'*64)
    assert cache_key(base)==cache_key(dict(reversed(list(base.items()))))
    for field in ['train_member_hash','weight_hash','config_hash','dictionary_hash']:
        assert cache_key(base)!=cache_key(base|{field:'f'*64})
    with pytest.raises(ValueError):cache_key({'bad':float('nan')})


def test_immutable_publish_and_corrupt_member(tmp_path):
    key=cache_key({'fold':'2024','weights':'v1'})
    manifest=publish(tmp_path,key,{'payload.bin':b'abc'},{'fold':'2024'})
    assert read_artifact(manifest,{'fold':'2024'})=={'payload.bin':b'abc'}
    with pytest.raises(FileExistsError):publish(tmp_path,key,{'payload.bin':b'bad'},{'fold':'2024'})
    with pytest.raises(ValueError,match='provenance'):read_artifact(manifest,{'fold':'2023'})
    (manifest.parent/'payload.bin').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash'):read_artifact(manifest,{'fold':'2024'})


def test_missing_and_traversal_rejected(tmp_path):
    key=cache_key({'source':1})
    with pytest.raises(ValueError):publish(tmp_path,key,{'../escape':b'x'}, {})
    manifest=publish(tmp_path,key,{'payload.bin':b'abc'}, {})
    (manifest.parent/'payload.bin').unlink()
    with pytest.raises(ValueError,match='missing'):read_artifact(manifest,{})


def test_typed_key_rejects_missing_scientific_dependency():
    from tradingagents.research.onchain_replication.cache import artifact_key
    from tradingagents.research.onchain_replication.contracts import ArtifactKey
    key=ArtifactKey(('a'*64,),1,'b'*40,'c'*64,'2024','d'*64,'e'*64,11,'f'*64)
    assert len(artifact_key(key))==64
    from dataclasses import replace
    with pytest.raises(ValueError):artifact_key(replace(key,train_member_hash=''))
    with pytest.raises(ValueError):artifact_key(replace(key,weight_hash=''))
