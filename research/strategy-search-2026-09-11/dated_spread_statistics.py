"""Descriptive fixed56-day marked-wallet exposure, no profit uncertainty test."""
import numpy as np
import statsmodels.api as sm
from dated_statistics import spot_returns


def exposure(nav,capital,btc_rows,eth_rows):
    try:
        values=np.asarray(nav,dtype=float);btc=spot_returns(btc_rows);eth=spot_returns(eth_rows)
        previous=np.r_[float(capital),values[:-1]]
        if values.shape!=(56,) or not np.isfinite(np.r_[values,previous,btc,eth]).all() or np.any(values<=0) or np.any(previous<=0):raise ValueError('56finite positive NAV observations required')
        X=np.column_stack((np.ones(56),btc,eth))
        if np.linalg.matrix_rank(X)!=3:raise ValueError('singular BTC/ETH design')
        fit=sm.OLS(values/previous-1,X).fit(cov_type='HAC',cov_kwds={'maxlags':7},use_t=True)
        interval=np.asarray(fit.conf_int(alpha=.025));cov=np.asarray(fit.cov_params())
        if not np.isfinite(np.r_[fit.params,fit.bse,interval.ravel(),cov.ravel()]).all():raise ValueError('undefined HAC statistics')
        return {'status':'complete','observations':56,'intercept':float(fit.params[0]),
            'btc_beta':float(fit.params[1]),'eth_beta':float(fit.params[2]),
            'btc_standard_error':float(fit.bse[1]),'eth_standard_error':float(fit.bse[2]),
            'btc_interval':interval[1].tolist(),'eth_interval':interval[2].tolist(),
            'covariance_order':['intercept','btc','eth'],'covariance':cov.tolist(),'hac_lags':7,
            'individual_confidence':.975,'scope':'Daily marked NAV, final cash substituted on exit; exploratory within-book nominal95%Bonferroni intervals, not finite-sample guarantee or all-search confirmation.'}
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,np.linalg.LinAlgError) as exc:
        return {'status':'unavailable','reason':type(exc).__name__+': '+str(exc)}
