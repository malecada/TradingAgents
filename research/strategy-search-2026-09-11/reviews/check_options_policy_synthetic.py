"""Exact invented normalized separate-wallet scenarios; no observed inputs."""
from fractions import Fraction as F
from pathlib import Path
import json
states=[]
for u in map(F,['.01','.1','.25','.4','.5','1','2']):
 for p in map(F,['0','.02','.1']):
  for h in map(F,['-1','0','1']):
   for jump in map(F,['.5','2']):
    for om in map(F,['0','.1']):
     for fm in map(F,['0','.01']):
      premium=u*p;liability=u*abs(jump-1);hedge_pnl=u*h*(jump-1)
      option_wallet=F(2,5)+premium-liability;hedge_wallet=F(1,2)+hedge_pnl
      option_requirement=om*u*jump;hedge_requirement=fm*u*abs(h)*jump
      total=option_wallet+hedge_wallet+F(1,10)
      assert total==1+premium-liability+hedge_pnl
      # Sale proceeds and initial marked liability cancel rather than create profit.
      assert F(2,5)+premium-premium+F(1,2)+F(1,10)==1
      oc=abs(jump-1)+om*jump-p;fc=fm*abs(h)*jump-h*(jump-1)
      ocap=None if oc<=0 else F(2,5)/oc;fcap=None if fc<=0 else F(1,2)/fc
      ob=option_wallet-option_requirement;fb=hedge_wallet-hedge_requirement
      assert (ob>=0)==(ocap is None or u<=ocap)
      assert (fb>=0)==(fcap is None or u<=fcap)
      states.append({'u_q_times_initial_spot_over_C':str(u),'premium_per_initial_notional':str(p),'hedge_units_per_q':str(h),'jump_multiplier':str(jump),'invented_option_requirement_ratio':str(om),'invented_hedge_requirement_ratio':str(fm),'option_cash_less_assigned_liability':str(option_wallet),'hedge_wallet':str(hedge_wallet),'total_equity':str(total),'option_buffer':str(ob),'hedge_buffer':str(fb),'option_u_ceiling':None if ocap is None else str(ocap),'hedge_u_ceiling':None if fcap is None else str(fcap),'option_deficit':ob<0,'hedge_deficit':fb<0})
assert len(states)==504
counter=next(s for s in states if s['u_q_times_initial_spot_over_C']=='1/2' and s['premium_per_initial_notional']=='1/50' and s['hedge_units_per_q']=='1' and s['jump_multiplier']=='2' and s['invented_option_requirement_ratio']=='0' and s['invented_hedge_requirement_ratio']=='0')
assert F(counter['total_equity'])==F(101,100) and F(counter['option_buffer'])==F(-9,100)
# Small inventory survives this finite scenario set; no universal policy rejection.
assert all(not s['option_deficit'] and not s['hedge_deficit']for s in states if s['u_q_times_initial_spot_over_C']=='1/100')
report={'passed':True,'states':states,'state_count':504,'counterexample':counter,'scope':'Invented dimensionless algebra only. Equal call/put quantities, strike equal to reference spot, assigned liability equal to expiry intrinsic payoff; not a rigorous European pre-expiry mark bound or the actual24h-before-expiry exit. Premium, hedge inventory and requirement ratios are arbitrary explicit sensitivities, not observed or claimed jointly attainable Greeks/quotes/margins. No financial input, network, empirical grant or practical capital claim.','conclusions':['Option premium cash must remain paired with its liability.','Positive total equity can coexist with a failed separate option wallet.','Finite scenario survival depends on inventory/capital ratio; it is not a loss cap, tail probability or actual margin admission.','Unbounded upward short-call payoff cannot be made bounded by a finite reserve or a delayed hedge.']}
path=Path(__file__).with_name('options-policy-normalized-synthetic-review.json');path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='states'},indent=2))
