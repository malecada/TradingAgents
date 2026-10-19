# tests/research/onchain_b6/test_labels6.py
import numpy as np

from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import config, labels6

A, B, C, D, E, F, G = ('0x' + c * 40 for c in 'abcdef1')
CFG = config.load()


def _rows():
    return [{'address': A, 'chainId': '1', 'label': 'binance', 'nameTag': 'Binance 14'},
            {'address': B, 'chainId': '1', 'label': 'dex', 'nameTag': 'Uniswap V3: Router 2'},
            {'address': C, 'chainId': '1', 'label': 'mev-bot', 'nameTag': 'MEV Bot: 0x…'},
            {'address': D, 'chainId': '1', 'label': 'take-action', 'nameTag': 'Wintermute Trading 3'},
            {'address': E, 'chainId': '1', 'label': 'bridge', 'nameTag': 'Arbitrum: L1 Gateway'},
            {'address': B, 'chainId': '1', 'label': 'coinbase', 'nameTag': 'Coinbase 9'},      # exchange wins
            {'address': F, 'chainId': '56', 'label': 'dex', 'nameTag': 'PancakeSwap Router'}]  # other chain


def test_classify_precedence_and_sources():
    b2 = {G: {'name': 'Kraken 4', 'added': None, 'sources': ['spellbook']}}
    doc = labels6.classify(b2, _rows(), [(E, 'Arbitrum: Bridge'), (F, 'Other: Bridge')], [(D, 'Wintermute Trading')], CFG)
    assert doc['exchange'] == {G: 'Kraken 4', A: 'binance', B: 'coinbase'}
    assert doc['dex'] == [] and doc['mev'] == [C] and doc['funds'] == [D]
    assert doc['bridge'] == [E, F]                                 # spellbook bridge on another chain still an address
    assert doc['issuer']['usdt_treasury'] == CFG['issuer']['usdt_treasury']


def test_parse_sql_addresses():
    t = "values\n  (0xAbC0000000000000000000000000000000000001, 'Across Protocol: Bridge', 'bridge')\n"
    assert labels6.parse_sql_addresses(t) == [('0xabc0000000000000000000000000000000000001', 'Across Protocol: Bridge')]


def test_activation_is_day_after_first_observation(tmp_path):
    doc = labels6.classify({}, _rows(), [], [], CFG)
    st = labels6.LabelState(doc, CFG['issuer']['usdt_treasury'])
    ka, kb, kc = addr_keys(np.array([A, B, C], object))
    st.begin_day(10)
    assert st.is_exchange(np.array([ka, kb, kc], np.uint64)).tolist() == [False, False, False]
    st.observe(np.array([ka, kc], np.uint64), 10)
    st.begin_day(10)
    assert st.is_exchange(np.array([ka], np.uint64)).tolist() == [False]          # same day: not yet
    st.begin_day(11)
    assert st.is_exchange(np.array([ka, kb], np.uint64)).tolist() == [True, False]
    assert st.in_class('mev', np.array([kc, ka], np.uint64)).tolist() == [True, False]
    assert st.entity_of(np.array([ka, kc], np.uint64)).tolist() == [st.entity_names.index('binance'), -1]
    st.save(tmp_path / 'labels_state.npz')
    st2 = labels6.LabelState.load(tmp_path / 'labels_state.npz', doc, CFG['issuer']['usdt_treasury'])
    st2.begin_day(11)
    assert st2.is_exchange(np.array([ka], np.uint64)).tolist() == [True]
