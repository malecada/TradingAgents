# Seventh dated attempt: independent failure-preservation decision

September 11, 2026. **Approve failed-receipt closure only; reject completion or
rerun.** The 120-second guard stopped the single registered execution. A later
forensic review of retained outputs may be informative, but cannot convert this
into a successful bounded run or justify another attempt merely to finish a
receipt. The original grant remains consumed.

The reviewed resource report is reviews/dated-spread-actual-guard.json, SHA256
`884b9703eed6660f7dd805cb6d06f9b161db716e3826ef5e30714ef840f7c3e3`.
It records 120.051 seconds, wall-clock limit exceeded, child exit -15 and
418,467,840 bytes peak sampled aggregate RSS. The guard's waited exit and the
coordinator's checks of PIDs404095/404099 establish termination of the known
processes. Independent /proc command-argument inspection found no live
dated_spread_run.py process. No resource override is permitted.

HEAD remains `6d6d65f9712dd41e135672a2f0fb8a7d8389507b`. The claim SHA256 is
`d0116773878c723689d6c21a1b6c00bbda4839acccd0a0cd5b744a97e9fb3c2d`.
Before closure, no complete.json or failed.json exists. Independent byte-only
inspection confirms these retained files without parsing financial values:

| Output | Bytes | SHA256 |
|---|---:|---|
| books.json | 1,003,789 | c2fae39d2d4ad4deca423cc49a1f7cbc720202cb1438b34da48fad7870cfaa06 |
| summary.json | 37,815 | d68d734977d0d0842573681aedd2a84e39d38f64843e47ba0f0e85b9fcd1b21c |
| source-audit.json | 22,305 | 2da802b1d74a39ccfd62b5f910fb486d97feb62dbaa7437de6284637beb9b635 |

The source/charter pins are unchanged according to the coordinator's check;
the recovery must re-admit the exact original committed target with its own
claim excluded only from duplicate-consumption accounting. Use the existing
ResearchRun(admit(..., _own_claim=ID)) construction, explicitly restore only the
preserved raw claim digest into its ownership field, then call fail(reason).
The existing lock and active-claim check must protect the immutable failed
receipt. Do not call start, finish, evaluate, rewrite an output or alter a
registration. Record the wall-limit reason and guard hash. Require the claim,
all three output hashes, HEAD and lack of a prior terminal to agree immediately
before closure; require those bytes to remain identical after closure. Keep the
recovery script/check record and independently verify the failed receipt.

This procedure is exceptional operational finalization of the existing stopped
claim, not a resumed financial run or a new budget unit. The private ownership
field is restored from the immutable saved claim only after process death and
re-admission; it is not an authorization shortcut around source/history checks.

All three declared output files suggest evaluation and publication advanced
before termination, but file presence does not prove which exact finalization
operation was interrupted. No claim that the financial calculation or its
scientific gates passed is made by this metadata review. A failed receipt has
no completed lifecycle cell verdict. The eight intended identities remain in
the claim; any eight-case accounting subsequently reconstructed from retained
files must be labeled failed-run output forensics. The full 8/16/72 evidence
denominators can be checked without rerunning the experiment. If those retained
outputs are internally valid, another trial solely to obtain complete.json has
no scientific information value.
