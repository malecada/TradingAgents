import json

from tradingagents.research.onchain_b2 import labels as L

SPELL = """
SELECT address, cex_name, distinct_name, added_by, added_date
FROM (VALUES
    -- Binance
    (0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be, 'Binance', 'Binance 1', 'hildobby', date '2022-08-28')
    , (0xD551234AE421E3BCBA99A0DA6D736074F22192FF, 'Binance', 'Binance 2', 'hildobby', date '2022-08-28')
    , (0x71660c4005ba85c37ccec55d0c4493e66fe775d3, 'Coinbase', 'Coinbase 1', 'hildobby', date '2022-11-14')
    , (0x1234, 'Broken', 'x', 'y', date '2022-01-01')
    ) AS x (address, cex_name, distinct_name, added_by, added_date)
"""
ETH = json.dumps([{'address': '0x71660c4005ba85c37ccec55d0c4493e66fe775d3', 'nameTag': 'Coinbase 1'},
                  {'address': '0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD', 'nameTag': ''}])


def test_parse_spellbook_lowercases_and_counts_unparsed():
    rows, unparsed = L.parse_spellbook(SPELL)
    assert set(rows) == {'0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be', '0xd551234ae421e3bcba99a0da6d736074f22192ff',
                         '0x71660c4005ba85c37ccec55d0c4493e66fe775d3'}
    assert rows['0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be'] == {'name': 'Binance', 'added': '2022-08-28'}
    assert unparsed == 1


def test_union_keeps_sources():
    u = L.union(L.parse_spellbook(SPELL)[0], L.parse_ethlabels(ETH))
    assert len(u) == 4
    assert u['0x71660c4005ba85c37ccec55d0c4493e66fe775d3']['sources'] == ['ethlabels', 'spellbook']
    assert u['0xabcdefabcdefabcdefabcdefabcdefabcdefabcd']['sources'] == ['ethlabels']


def test_fetch_and_store_pins_commits_and_hashes(tmp_path):
    def get(url):
        if url.endswith('/commits/main'):
            return json.dumps({'sha': 's' * 40}).encode()
        if url.endswith('/commits/master'):
            return json.dumps({'sha': 'e' * 40}).encode()
        if 'spellbook/' + 's' * 40 in url:
            return SPELL.encode()
        if 'eth-labels/' + 'e' * 40 in url:
            return ETH.encode()
        raise AssertionError(url)

    meta = L.fetch_and_store(get, tmp_path)
    assert meta['count'] == 4 and meta['sources']['spellbook']['commit'] == 's' * 40 and meta['sources']['spellbook']['unparsed'] == 1
    assert len(meta['sources']['ethlabels']['sha256']) == 64
    arr = L.exchange_array(tmp_path / 'labels.json')
    assert arr.to_pylist() == sorted(arr.to_pylist()) and len(arr) == 4