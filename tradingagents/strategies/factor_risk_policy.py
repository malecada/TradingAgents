"""Registered factor sizing/re-entry controls, separate from financial accounting.

Raw targets retain the original signal/hold/entry-gate decisions. A controller
is single-use and advances over return indices1..N-1 of that unchanged target
clock. Stop notifications occur only after the engine executed a price exit.
"""
from __future__ import annotations

from numbers import Integral, Real

import numpy as np

from tradingagents.strategies.v2_sizing import compute_realized_vol


def causal_sigma(close):
    """Exact original twenty-return, sqrt252 estimator, lagged once at sizing."""
    raw=np.asarray(close)
    if raw.dtype.kind=='b':
        raise ValueError('close observations cannot be booleans')
    values=np.asarray(close,dtype=float)
    if values.ndim!=1 or not len(values) or not np.isfinite(values).all() or (values<=0).any():
        raise ValueError('causal volatility requires a complete positive close vector')
    return compute_realized_vol(np.r_[values[0],values[:-1]],lookback=20)


class FactorRiskPolicy:
    """Fixed2×2 target controller; instantiate anew for every sleeve/cost arm.

    ``blocked_before`` is the latch entering the decision. ``blocked_after_decision``
    includes a raw zero/opposite release, before intrabar execution. ``blocked_after``
    is initially the same but an executed price-stop notification updates it to the
    end-of-bar latch. ``decision_blocked`` counts only an otherwise nonzero raw
    request suppressed by that latch, not flat or permanently halted dates.

    None/invalid sigma is retained as null trace metadata. It makes only an
    admitted nonzero daily-sizing request unavailable; it never produces cash
    or a NaN target. The estimator itself is not an entry/exit volatility gate.
    """

    def __init__(self, *, sizing, reentry, sigma):
        if sizing not in ('saved','daily'):
            raise ValueError('unsupported factor sizing policy')
        if reentry not in ('immediate','new_target_episode'):
            raise ValueError('unsupported factor re-entry policy')
        raw=np.asarray(sigma)
        if raw.dtype.kind=='b':
            raise ValueError('sigma observations cannot be booleans')
        values=np.array(sigma,dtype=float,copy=True)
        if values.ndim!=1 or not len(values):
            raise ValueError('sigma must be a nonempty vector on the target clock')
        values.setflags(write=False)
        self.sizing, self.reentry, self.sigma = sizing,reentry,values
        self._blocked_direction=0
        self._last_index=0
        self._last_target=0.
        self._last_halted=False
        self._stop_notified=False

    def decide(self,i,raw_target,halted,*,date=None):
        """Resolve one causal decision, before observing this bar's price move."""
        location=f'{date} index {i}' if date is not None else f'index {i}'
        if not isinstance(i,Integral) or isinstance(i,(bool,np.bool_)) or i!=self._last_index+1:
            raise ValueError(f'{location}: decision order must advance once from index1')
        if i<1 or i>=len(self.sigma):
            raise ValueError(f'{location}: decision outside sigma/target clock')
        if not isinstance(raw_target,Real) or isinstance(raw_target,(bool,np.bool_)) or not np.isfinite(raw_target):
            raise ValueError(f'{location}: raw target must be finite and numeric')
        if abs(raw_target)>3.:
            raise ValueError(f'{location}: raw target exceeds the registered leverage cap')
        if not isinstance(halted,(bool,np.bool_)):
            raise ValueError(f'{location}: permanent halt flag must be boolean')
        raw_target=float(raw_target)
        direction=int(np.sign(raw_target))
        sigma=float(self.sigma[i])
        before=self._blocked_direction
        release=None
        blocked=False
        if halted:
            target,reason=0.,'permanent_halt'
        else:
            if before and direction!=before:
                self._blocked_direction=0
                release='raw_flat' if direction==0 else 'raw_opposite'
            if direction==0:
                target,reason=0.,'raw_flat'
            elif self._blocked_direction:
                target,reason,blocked=0.,'waiting_same_direction',True
            elif self.sizing=='saved':
                target,reason=raw_target,'saved_target'
            else:
                if not np.isfinite(sigma) or sigma<=0:
                    raise ValueError(f'{location}: admitted daily target requires finite positive sigma; got {sigma!r}')
                target,reason=float(direction*min(3.,.15/sigma)),'daily_resize'
                if not np.isfinite(target) or target==0.:
                    raise ValueError(f'{location}: daily sizing produced an invalid nonzero target')
        self._last_index,self._last_target,self._last_halted=i,target,bool(halted)
        self._stop_notified=False
        return target,dict(raw_target=raw_target,requested_target=target,
            sizing_sigma=sigma if np.isfinite(sigma) else None,
            blocked_before=before,blocked_after_decision=self._blocked_direction,
            blocked_after=self._blocked_direction,decision_blocked=blocked,
            block_release=release,decision_reason=reason,stopped_direction=0,
            policy_sizing=self.sizing,policy_reentry=self.reentry)

    def on_price_stop(self,i,exposure):
        """Notify an actual executed price-stop exit; never apply a hypothetical stop."""
        if i!=self._last_index or i==0:
            raise ValueError('price-stop notification has no matching decision')
        if self._stop_notified:
            raise ValueError('price-stop decision already notified')
        if (not isinstance(exposure,Real) or isinstance(exposure,(bool,np.bool_)) or
                not np.isfinite(exposure) or exposure==0 or self._last_target==0 or
                self._last_halted or np.sign(exposure)!=np.sign(self._last_target)):
            raise ValueError('price-stop notification requires the actual nonzero admitted direction')
        stopped=int(np.sign(exposure))
        if self.reentry=='new_target_episode':
            self._blocked_direction=stopped
        self._stop_notified=True
        return dict(stopped_direction=stopped,blocked_after=self._blocked_direction)
