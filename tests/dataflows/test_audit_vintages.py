"""A historical publication date cannot establish a later retrieved version."""
from pathlib import Path
import sys
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from backfill_alpaca_news import normalize as news_normalize
from ingest_hf_bitcoin_news import normalize as hf_normalize
from tradingagents.dataflows import coinmetrics, onchain_store, sentiment_store


def test_backfilled_revised_article_is_available_only_at_retrieval():
    item = dict(id=1, created_at='2021-01-01Z'.replace('01Z','01T00:00:00Z'),
                updated_at='2021-02-01T00:00:00Z', headline='revised')
    seen = pd.Timestamp('2021-03-01T00:00:00Z')
    row = news_normalize(item, retrieved_at=seen)
    assert row['as_of_ts'] == seen
    assert row['source_updated_at'] == pd.Timestamp('2021-02-01Z'.replace('01Z','01T00:00:00Z'))
    assert row['availability_basis'] == 'retrieved_snapshot'


def test_hf_and_coinmetrics_use_retrieval_time_not_assumed_historical_lag():
    seen = pd.Timestamp('2021-03-01T00:00:00Z')
    hf = pd.DataFrame(dict(time_unix=[1609459200], url=['url'], title=['title'], article_text=['text'], source=['source']))
    assert hf_normalize(hf, retrieved_at=seen).as_of_ts.iloc[0] == seen
    cm = coinmetrics.normalize_rows([{'time': '2021-01-01T00:00:00Z', 'TxCnt': '42'}],
                                    'btc', ['TxCnt'], retrieved_at=seen)
    assert cm.as_of_ts.iloc[0] == seen
    assert cm.availability_basis.iloc[0] == 'retrieved_snapshot'


@pytest.mark.parametrize('store', ['news', 'onchain'])
def test_conflicting_vintage_rejected_without_altering_existing_bytes(tmp_path, store):
    seen = pd.Timestamp('2021-03-01T00:00:00Z')
    if store == 'news':
        row = news_normalize(dict(id=1, created_at='2021-01-01T00:00:00Z', headline='first'), retrieved_at=seen)
        write = lambda df: sentiment_store.upsert_alpaca_rows(df, 2021, 1, tmp_path)
        field, changed = 'headline', 'revision'
    else:
        row = coinmetrics.normalize_rows([{'time': '2021-01-01T00:00:00Z', 'TxCnt': '42'}], 'btc', ['TxCnt'], retrieved_at=seen).iloc[0].to_dict()
        write = lambda df: onchain_store.upsert_rows(df, tmp_path)
        field, changed = 'value', 43.
    write(pd.DataFrame([row]))
    path = tmp_path / '2021' / '01.parquet'
    before = path.read_bytes()
    write(pd.DataFrame([row]))  # exact repeat is idempotent
    row[field] = changed
    with pytest.raises(ValueError, match='conflicting|vintage'):
        write(pd.DataFrame([row]))
    assert path.read_bytes() == before


def test_strict_query_quarantines_legacy_assumed_availability(tmp_path):
    row = dict(event_ts=pd.Timestamp('2021-01-01T00:00:00Z'), as_of_ts=pd.Timestamp('2021-01-02T00:00:00Z'),
               coin='btc', metric='TxCnt', value=42., source='coinmetrics_community', status='final')
    onchain_store.upsert_rows(pd.DataFrame([row]), tmp_path)
    args = dict(coin='btc', ts_start=row['event_ts'], ts_end=row['as_of_ts'], as_of=row['as_of_ts'], root=tmp_path)
    with pytest.raises(ValueError, match='availability|vintage'):
        onchain_store.query_metrics(**args)
    assert len(onchain_store.query_metrics(**args, strict_pit=False)) == 1


def test_new_vintage_preserves_prior_shard_and_strict_consumers_reject_legacy(tmp_path, monkeypatch):
    from tradingagents.dataflows import onchain_features, crypto_sentiment_pit
    row = dict(event_ts=pd.Timestamp('2021-01-01T00:00:00Z'), as_of_ts=pd.Timestamp('2021-01-02T00:00:00Z'),
               coin='btc', metric='TxCnt', value=42., source='coinmetrics_community', status='final')
    chain = tmp_path / 'chain'
    onchain_store.upsert_rows(pd.DataFrame([row]), chain)
    old = (chain / '2021' / '01.parquet').read_bytes()
    revision = {**row, 'as_of_ts': pd.Timestamp('2021-02-01T00:00:00Z'), 'value': 43., 'availability_basis': 'observed'}
    onchain_store.upsert_rows(pd.DataFrame([revision]), chain)
    assert any(p.read_bytes() == old for p in chain.rglob('_vintages/*/*.parquet'))
    with pytest.raises(ValueError, match='availability|vintage'):
        onchain_features._load_metric_series('btc', 'TxCnt', chain)
    news = news_normalize(dict(id=1, created_at='2021-01-01T00:00:00Z', headline='old', symbols=['BTCUSD']),
                          retrieved_at=pd.Timestamp('2021-01-02T00:00:00Z'))
    news.pop('availability_basis')
    newsroot = tmp_path / 'news'
    sentiment_store.upsert_alpaca_rows(pd.DataFrame([news]), 2021, 1, newsroot)
    monkeypatch.setattr(sentiment_store, 'DEFAULT_ROOT', newsroot)
    with pytest.raises(ValueError, match='availability|vintage'):
        crypto_sentiment_pit.get_crypto_news_pit('bitcoin', '2021-01-01', '2021-01-03')


def test_queries_choose_latest_eligible_vintage_before_limits(tmp_path):
    event = pd.Timestamp('2021-01-01T00:00:00Z')
    first, later = pd.Timestamp('2021-01-02T00:00:00Z'), pd.Timestamp('2021-01-03T00:00:00Z')
    newsroot, chainroot = tmp_path / 'news', tmp_path / 'chain'
    for seen, headline, value in [(first, 'first', '42'), (later, 'revised', '43')]:
        row = news_normalize(dict(id=1, created_at=event.isoformat(), headline=headline, symbols=['BTCUSD']), retrieved_at=seen)
        sentiment_store.upsert_alpaca_rows(pd.DataFrame([row]), 2021, 1, newsroot)
        chain = coinmetrics.normalize_rows([{'time': event.isoformat(), 'TxCnt': value}], 'btc', ['TxCnt'], retrieved_at=seen)
        onchain_store.upsert_rows(chain, chainroot)
    for asof, headline, value in [(first, 'first', 42.), (later, 'revised', 43.)]:
        news = sentiment_store.query_news('bitcoin', event, later, asof, root=newsroot)
        chain = onchain_store.query_metrics('btc', event, later, asof, root=chainroot)
        assert news.headline.tolist() == [headline]
        assert chain.value.tolist() == [value]


def test_late_revision_of_old_event_does_not_replace_more_recent_event_in_features():
    from tradingagents.dataflows.onchain_features import _pit_align
    series = pd.DataFrame({'event_ts': pd.to_datetime(['2021-01-01', '2021-01-02', '2021-01-01'], utc=True),
                           'as_of_ts': pd.to_datetime(['2021-01-02', '2021-01-03', '2021-01-04'], utc=True),
                           'value': [1., 2., 1.5]})
    out = _pit_align(pd.date_range('2021-01-02', periods=3, tz='UTC'), series, 'value')
    assert out.tolist() == [1., 2., 2.]


def test_version_cannot_claim_availability_before_source_update(tmp_path):
    row = news_normalize(dict(id=1, created_at='2021-01-01T00:00:00Z', headline='first'),
                         retrieved_at=pd.Timestamp('2021-01-03T00:00:00Z'))
    row.update(availability_basis='published_version', source_updated_at=pd.Timestamp('2021-01-04T00:00:00Z'))
    with pytest.raises(ValueError, match='update|availability|vintage'):
        sentiment_store.upsert_alpaca_rows(pd.DataFrame([row]), 2021, 1, tmp_path)
