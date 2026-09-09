import pandas as pd
import pytest
from tradingagents.models import lgb_model


def test_dir_accuracy_uses_same_transformed_row_reference_without_second_shift():
    # The transform already lagged prices: at Jan02 the reference is200.
    # A prediction150 is DOWN, while actual250 is UP; expected accuracy0.
    pooled = pd.DataFrame({'coin_id': ['btc', 'btc'], 'prices': [100., 200.]},
                          index=pd.DatetimeIndex(['2021-01-01', '2021-01-02']))
    pred = pd.DataFrame({'date': ['2021-01-02'], 'coin_id': ['btc'], 'prediction': [150.], 'actual': [250.]})
    assert lgb_model._dir_acc(pred, pooled, 7) == 0.
    # Changing an older reference cannot alter the scored origin.
    pooled.iloc[0, 1] = 300.
    assert lgb_model._dir_acc(pred, pooled, 7) == 0.


def test_forecast_quality_note_withdraws_unvalidated_historical_accuracy():
    for coin in ['bitcoin', 'ethereum']:
        note = lgb_model._format_dir_acc_note(coin, 14)
        assert 'unvalidated' in note.lower()
        assert '%' not in note


def test_agent_report_does_not_present_withdrawn_accuracy_as_evidence(monkeypatch):
    import numpy as np
    from scripts import evaluate_models_multi
    pooled = pd.DataFrame({'coin_id': ['bitcoin', 'bitcoin'], 'prices': [100., 101.],
                           'prices_h14': [102., np.nan]},
                          index=pd.date_range('2021-01-01', periods=2))
    monkeypatch.setattr(evaluate_models_multi, 'build_pooled_transformed', lambda **kwargs: pooled.copy())
    class FixedPrediction:
        def fit(self, X, y):
            return self
        def predict(self, X):
            return [102.]
    monkeypatch.setattr(lgb_model, '_build_lgb', FixedPrediction)
    report = lgb_model.forecast_next('bitcoin', horizons=[14], trade_date='2021-01-02')
    assert 'unvalidated' in report.lower()
    assert '85%' not in report and '76%' not in report
