from tradingagents.research.onchain_b3 import config


def test_frozen_numbers():
    c = config.load()
    assert c['k'] == 20000 and c['dictionary']['seed'] == 11 and c['structure']['cores'] == [2, 3, 5, 10]
    assert c['structure']['wedges'] == 200000 and c['history']['bloom_bits_log2'] == 33
    assert set(c['targets']) == {'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'}
    assert c['targets']['T6']['horizon'] == 28 and c['targets']['T7']['block'] == 8
    assert c['comparisons'] == [['S5', 'S1'], ['S6', 'S5'], ['S7', 'S0']] and c['gate']['seed'] == 20261014
    assert c['models']['fallback_alpha'] == 100.0 and c['models']['trees']['min_samples_leaf'] == 30


def test_paths_and_ignore():
    assert config.B2_ARTIFACTS.name == 'onchain-b2' and config.ARTIFACTS.name == 'onchain-b3'
    assert '/research_artifacts/onchain-b3/' in (config.ROOT / '.gitignore').read_text()