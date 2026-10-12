from tradingagents.research.onchain_b import config


def test_frozen_matching_numbers():
    m = config.load('matching')
    assert (m['alpha'], m['beta0'], m['beta_final'], m['beta_rate'], m['max_iterations']) == (1.0, 1.0, 30.0, 0.075, 50)


def test_frozen_dictionary_numbers():
    d = config.load('dictionary')
    assert d['sample_count'] == 512 and d['size'] == 32 and d['hop_depth'] == 1
    assert d['n_max'] in (32, 64)


def test_artifacts_dir_is_ignored():
    text = (config.ROOT / '.gitignore').read_text()
    assert '/research_artifacts/onchain-replication-b/' in text
