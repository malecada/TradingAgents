"""Forecast failure must be scored on the declared baseline's common clock."""
import numpy as np
import pandas as pd
import pytest

from tradingagents.predlab import runner, tier2, losses
from tradingagents.predlab.baselines import Forecaster


class FromColumn(Forecaster):
    def __init__(self, name, col):
        self.name, self.col = name, col

    def predict(self, y_hist, x_now=None):
        return x_now[self.col]


def test_enet_unavailable_and_missing_selected_feature_are_nan():
    enet = tier2.ElasticNetForecaster(alphas=(0.001,), n_features=1)
    assert np.isnan(enet.predict([1], [2]))
    x = np.arange(80, dtype=float).reshape(-1, 1)
    enet.fit(x[:, 0], x)
    assert np.isnan(enet.predict([1], [np.nan]))
    assert np.isnan(enet.predict([1], [np.inf]))
    assert np.isfinite(enet.predict([1], [2, np.nan]))
    assert np.isnan(tier2.ProbClip(tier2.ElasticNetForecaster()).predict([1], [2]))


@pytest.mark.parametrize('loss,target,raw,baseline,want', [
    ('se', 'T1_ret', [np.nan, np.inf, 3., 4.], [1., 2., 2., 3.], [1., 2., 3., 4.]),
    ('qlike', 'T3_rv', [0., -1., np.nan, 2.], [1., 2., 3., 4.], [1., 2., 3., 2.]),
    ('brier', 'T2_dir', [np.nan, np.inf, .3, .4], [.6, .7, .8, .9], [.6, .7, .3, .4]),
])
def test_runner_fallback_retains_raw_predictions_and_all_scoreable_origins(loss, target, raw, baseline, want):
    series = pd.DataFrame({'y': [1.] * 34, 'base': [1.] * 30 + baseline,
                           'raw': [1.] * 30 + raw},
                          index=pd.date_range('2021-01-01', periods=34, freq='h', tz='UTC'))
    cell = dict(cell='SYN|1h|' + target, target=target, horizon_bars=1,
                strong_baseline='base', loss=loss, min_train=30)
    out, preds, diagnostics = runner.run_cell(cell, series, [FromColumn('raw', 1), FromColumn('base', 0)],
                                  'unused', 'test', dry=True, return_diagnostics=True)
    assert preds['raw'] == pytest.approx(want)
    row = out.set_index('model').loc['raw']
    assert row.n_origins == 4
    assert row.n_fallback == sum(not np.isfinite(x) or (loss == 'qlike' and x <= 0) for x in raw)
    assert row.model_coverage == pytest.approx((4 - row.n_fallback) / 4)
    diag = diagnostics['raw']
    assert diag.raw_pred.to_numpy() == pytest.approx(raw, nan_ok=True)
    assert diag.pred.to_numpy() == pytest.approx(want)
    assert diag.scoreable.all()
    assert diag.fallback_used.sum() == row.n_fallback


def test_common_clock_excludes_invalid_target_and_baseline_for_every_model():
    series = pd.DataFrame({'y': [1.] * 30 + [np.nan, 1., 1., 1.],
                           'base': [1.] * 30 + [1., np.inf, 1., 1.],
                           'raw': [1.] * 30 + [1., 1., np.nan, 1.]},
                          index=pd.date_range('2021-01-01', periods=34, freq='h', tz='UTC'))
    cell = dict(cell='SYN', target='T2_dir', horizon_bars=1,
                strong_baseline='base', loss='brier', min_train=30)
    out = runner.run_cell(cell, series, [FromColumn('base', 0), FromColumn('raw', 1)],
                          'unused', 'test', dry=True)
    assert out.n_origins.tolist() == [2, 2]
    assert out.n_excluded_target.tolist() == [1, 1]
    assert out.n_excluded_baseline.tolist() == [1, 1]
    assert out.loss_mean.tolist() == [0., 0.]
    assert out.set_index('model').loc['raw', 'model_coverage'] == .5


def test_qlike_rejects_nonfinite_values_without_infinite_loss():
    assert np.isnan(losses.qlike([np.inf, 1.], [1., np.inf])).all()


def test_probability_adapter_keeps_unknown_training_labels_unknown():
    class Capture(Forecaster):
        name = 'capture'
        def fit(self, y, X=None):
            self.labels = y
        def predict(self, y, X=None):
            self.history = y
            return np.nan
    inner = Capture()
    model = tier2.ProbClip(inner)
    model.fit([1., np.nan, -1.])
    model.predict([1., np.nan, -1.])
    assert inner.labels == pytest.approx([1., np.nan, 0.], nan_ok=True)
    assert inner.history == pytest.approx([1., np.nan, 0.], nan_ok=True)


def test_lgb_unfitted_model_is_explicitly_unavailable():
    assert np.isnan(tier2.LGBForecaster().predict([1.], [1.]))


def test_series_digest_binds_values_index_and_column_meaning():
    series = pd.DataFrame({'y': [1., 2.], 'feature': [3., 4.]},
                          index=pd.date_range('2021-01-01', periods=2, tz='UTC'))
    digest = runner.series_digest(series)
    assert digest == runner.series_digest(series.copy())
    changed = series.copy()
    changed.iloc[0, 1] = 30.
    assert digest != runner.series_digest(changed)
    assert digest != runner.series_digest(series.rename(columns={'feature': 'other'}))
    assert digest != runner.series_digest(series.set_axis(series.index + pd.Timedelta(days=1)))


def test_model_config_preserves_wrapper_and_resolved_inner_settings():
    config = runner.model_config(tier2.ProbClip(tier2.ElasticNetForecaster(alphas=(.1,), n_features=3), lo=.1))
    assert config['parameters']['lo'] == .1
    assert config['parameters']['inner']['parameters']['alphas'] == [.1]
    assert config['parameters']['inner']['parameters']['n_features'] == 3


@pytest.mark.parametrize('existing', ['forecast', 'card'])
def test_existing_empirical_artifact_refused_before_any_fit(tmp_path, monkeypatch, existing):
    from tradingagents.predlab import registry
    monkeypatch.setattr(registry, 'preflight', lambda *args, **kwargs: None)
    monkeypatch.setattr(registry, 'gates_path', lambda: tmp_path / 'gates.json')
    if existing == 'forecast':
        path = tmp_path / 'forecasts' / 'testgate' / 'SYN' / 'base.parquet'
        payload = b'preserved forecast'
    else:
        path = tmp_path / 'cards' / 'testgate' / 'SYN.json'
        payload = b'{"test": {"original": true}}'
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    class NoFit(FromColumn):
        def fit(self, *args):
            pytest.fail('fit occurred before existing-output refusal')
    series = pd.DataFrame({'y': [1.] * 34, 'base': [1.] * 34},
                          index=pd.date_range('2021-01-01', periods=34, freq='h', tz='UTC'))
    cell = dict(cell='SYN', target='T1_ret', horizon_bars=1, strong_baseline='base', loss='se', min_train=30)
    with pytest.raises(FileExistsError, match='existing|preserv|already'):
        runner.run_cell(cell, series, [NoFit('base', 0)], 'testgate', 'test', dry=False)
    assert path.read_bytes() == payload


def test_written_card_binds_input_and_model_settings_before_fit(tmp_path, monkeypatch):
    import json
    from tradingagents.predlab import registry
    provenance = {'git_commit': 'registered-code', 'gate_sha256': 'registered-gate'}
    monkeypatch.setattr(registry, 'preflight', lambda *args, **kwargs: provenance)
    monkeypatch.setattr(registry, 'gates_path', lambda: tmp_path / 'gates.json')
    logged = []
    monkeypatch.setattr(registry, 'log_trial', lambda *args, **kwargs: logged.append(args))
    class Constant(Forecaster):
        name = 'base'
        def __init__(self, value=1.):
            self.value = value
        def fit(self, y, X=None):
            self.value = 2.  # learned state must not replace constructor provenance
        def predict(self, y, X=None):
            return self.value
    series = pd.DataFrame({'y': [1.] * 34}, index=pd.date_range('2021-01-01', periods=34, freq='h', tz='UTC'))
    cell = dict(cell='SYN', target='T1_ret', horizon_bars=1, strong_baseline='base', loss='se', min_train=30)
    runner.run_cell(cell, series, [Constant(.5)], 'testgate', 'test', dry=False)
    card = json.loads((tmp_path / 'cards' / 'testgate' / 'SYN.json').read_text())['test']
    assert card['provenance'] == provenance
    assert card['input_series_sha256'] == runner.series_digest(series)
    assert card['model_configs']['base']['parameters']['value'] == .5
    assert logged[0][3]['model_config']['parameters']['value'] == .5
    assert logged[0][3]['input_series_sha256'] == card['input_series_sha256']
    saved = pd.read_parquet(tmp_path / 'forecasts' / 'testgate' / 'SYN' / 'base.parquet')
    assert saved['pred'].tolist() == [2.] * 4
    assert saved['raw_pred'].tolist() == [2.] * 4
    assert saved['scoreable'].all()
