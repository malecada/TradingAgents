# Independent composed IO candidate04 review

Disposition: **WITHHELD for one remaining synthetic-uncertainty cause-attachment branch.** The IO03 optional-annotation corrections and protection of cause attachment after a true fatal are accepted narrowly. No further material delta issue was found in this bounded source review. Actual numerical execution, genuine fixture authority, native controls and resource capacity remain unproved.

## Frozen identities and independent checks

| Object | SHA-256 |
|---|---|
| manifest01.json | 5c69625c999a231c767edd376e4ed128e6019439a2b882bd1023f5e3dd514851 |
| REPORT01.md | 23178d0697498a8e61c180530cbf07e7ab3247f2a192c35ebf99e81df674d362 |
| owned_io.py | 09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb |
| resource_fixture.py | 317e8c782075bbff98d3b78404dade1981c9d2485125c070ff7965ab7c6ccf45 |

All 13 local manifest members were independently read, length/hash checked and found regular with one link, totaling 70,064 bytes. All four explicit dependency pins match. All 21 IO03 members (119,043 bytes) and all 93 IO02 members (872,046 bytes) remain byte-exact. All 28 installation mappings were independently rehashed with unique targets; only owned_io and resource_fixture differ from IO03. The corrected IO03 matcher remains selected. The external workload pin matches. Both immediate baselines equal their predecessor bodies; both published patches exactly reproduce the source changes.

Independent AST reconstruction verified that the complete resource module differs only by removal of the optional note try-block, and the complete owned helper differs only inside its selected-fatal diagnostic block. Numerical bodies, preflight, original identities, actual authority route, 32-motif/two-target checks, cell recording and publication action ordering are unchanged. This verifies source preservation, not execution equivalence.

## Remaining material finding

**IO4-1 — a first actual fatal during synthetic-uncertainty cause attachment is suppressed.** At resource_fixture.py:186–191, `_preserve_terminal` can select a non-Exception `CleanupFailure` over an ordinary primary through the second condition, even though owned_io._fatal explicitly excludes CleanupFailure from actual fatals. Cause access/group construction/assignment then uses `except BaseException: pass` regardless of whether a true fatal has already been selected.

A deterministic source-level counterexample uses the actual selected CleanupFailure class:

```python
first_actual_fatal = MemoryError('cause attachment failed')
class Uncertain(CleanupFailure):
    def __setattr__(self, name, value):
        if name == '__cause__':
            raise first_actual_fatal
        super().__setattr__(name, value)

ordinary = ValueError('body failure')
uncertain = Uncertain('close uncertain')
# Actual helper returns uncertain, suppressing first_actual_fatal:
_preserve_terminal(ordinary, uncertain)
```

The first condition `_fatal(ordinary)` is false and `_fatal(uncertain)` is also false. The non-Exception branch nevertheless selects uncertain. Its initially empty cause triggers assignment, the first actual MemoryError is raised by the owned diagnostic action, and line191 discards it. The same precedence issue can occur through a real allocation failure while constructing a grouped cause for a synthetic uncertainty. This is not an allocation-at-every-instruction claim; it is the explicitly protected optional diagnostic branch currently advertised as safe only after a true fatal.

Required narrow correction: perform best-effort attachment suppression only after an actual fatal already has precedence. For synthetic uncertainty, either avoid optional fallible cause attachment or promote a first actual fatal raised during it, preserving the original selected object when the later error is ordinary. A deterministic extracted-helper sentinel should cover the counterexample, plus the existing true-fatal control and ordinary/synthetic control; no real memory pressure or numerical run is required. Preserve all04 bytes in a new candidate. The proposed code above is a source trace, not an executed test in this review.

## Accepted corrections and evidence qualifications

The owned_io selected-fatal branch no longer invokes an overridable add_note method. If the selected actual fatal is already the active primary, cleanup returns so the surrounding propagation retains that exact object. Otherwise optional cause reading, grouping and assignment are protected before raising that same selected fatal. Independent closes still run once before selection. This closes the specific IO3-1 annotation/cause masking path within its stated scope.

The resource reducer no longer performs optional annotation for ordinary-primary/ordinary-secondary errors. There is therefore no annotation allocation to swallow on that route, closing the specific IO3-2 note finding. Its already-selected actual-fatal precedence is coherent. IO4-1 concerns the distinct synthetic CleanupFailure branch, not repetition of the removed note defect.

The six new methods execute AST-extracted actual helpers with stdlib stand-ins. Retained REDs include overridden-note and cause-assignment failures; GREEN reports six passing methods. The annotation-allocation probe substitutes the extracted function's BaseException symbol and proves that the removed call is not attempted; it is not actual interpreter memory exhaustion. The rejected-cause sentinel exercises a true-fatal SystemExit subclass, so suppression there is correct. It does not exercise the synthetic CleanupFailure counterexample.

The compatibility harness loads the exact frozen03 test modules, redirects the helper/resource source to04, and retains the actual03 matcher method. Its log reports all seven previous methods passing. The actual numerical try-body is replaced by an injected error in assembly tests, and authority/numerical operators are inert stand-ins where documented. Six plus seven methods are evidence of those finite seams, not a complete imported-dictionary execution. No tests, candidate modules or numerical packages were imported or run by this reviewer.

Both genuinely completed target rows remain complete if later Owner/journal closure fails; the overall error still propagates. Each independently possible retention/publication action remains attempted once, missing terminal/summary assembly refuses publication, and no success acknowledgement or retry is introduced by04. Impossible diagnostic publication can still leave missing evidence; final outer inventory and failed disposition must represent it honestly. Removing optional notes loses supplementary exception text and protected cause attachment may be unavailable after an attachment failure; no stronger recovery guarantee is made.

## Remaining release boundary

After the single narrow correction and independent review, a complete isolated committed source/runtime/input closure, separately registered synthetic targets, reviewed one-use native controller, all-writable-root coverage, complete final inventory and process/cgroup cleanup are still required before genuine two-target/all32-original-motif success/failure/mutation proof. This review grants no installation, empirical claim, registration change, full23-cell coverage, archive/offload, full-size capacity or financial fitting authority. Historical failed attempts and identities remain unchanged and closed. Timing, PnL, fees/funding, exposure and paper numerical agreement were not tested.
