# Independent initial review — acceptance withheld

Read-only source review found two material admission/accounting gaps. No tests, jobs or empirical numerical reads were performed by the reviewer. The saved pure-helper suite records six passing methods in 1.094 seconds, including maintained batch-factory/model gradient smoke coverage; it does not establish the pending actual registered preparation integration.

## NM1 — budget feasibility is checked after sealing

`native_map.py:136` validates policy schema, then `native_map.py:140` performs the irreversible once-only publication/seal/output transition. Numeric feasibility is first checked by `verified_hashes()` at line 156. An allowance smaller than one required graph's read/verification peak therefore fails only after sealing and publishing. Separately, `verified_hashes()` does not test capacity to return one tensor graph: a sufficiently large read allowance but smaller-than-required `max_live_tensor_bytes` can produce a map unable to serve required graph keys.

Derive every required graph's exact native payload size from the already admitted resident node/edge dimensions and motif count before calling `seal.finish`. Require at least the largest graph's tensor bytes within the live-output cap and its native-plus-tensor copy peak plus declared scratch within the numeric cap. If preparation intends to guarantee a complete registered batch, preflight that exact batch denominator separately; minimum single-graph feasibility does not prove arbitrary batch feasibility. Exercise both insufficient-read and insufficient-live/copy allowances with `seal.finish` forbidden, proving refusal before mutation. This finding is an independently reconstructed source counterexample, not a reviewer-executed test.

## NM2 — public accounting can discard concurrent registrations

`native_map.py:57–64` exposes `live_tensor_bytes()` without the operation lock even though it prunes and replaces `self._live`. Allocation methods hold the lock, but a concurrent public accounting call can collect the old live list, pause, and then assign its stale `alive` list after a newly completed batch registered and returned additional tensors. Subsequent budget checks can omit those still-live returned wrappers.

Use an internal accounting helper only while the operation lock is held, and make the public query acquire the same lock or otherwise synchronize pruning and registration. Avoid recursively acquiring the non-reentrant lock from existing allocation methods. A controlled concurrent query/registration regression should reject the query or preserve the new registrations. The current reentrancy test exercises nested allocation/verification calls, not this unguarded accounting method.

## Other inspected scope and limits

The helper deduplicates requested graph keys, preflights its per-call aggregate before numeric loading, validates exact native component schema and hashes, uses the strict reader and accepted tensor boundary, and brackets batch exposure with leases. `verified_hashes()` recomputes wire hashes sequentially, including empty edges. Weakrefs intentionally account only for original returned tensor wrappers; aliases, detached/autograd-held storage, model memory and total RSS are excluded. Those exclusions must remain explicit and cannot be described as a bound on all resident feature storage.

The registered `prepare` path calls the actual seal implementation rather than accepting an arbitrary caller-supplied Receipt or callback. The private helper's direct constructor tests establish numeric behavior only. Acceptance remains withheld pending NM1/NM2 corrections, closed registered integration evidence and final declared bindings. No cold/historical reuse, full-fold resource feasibility, financial fit or empirical release is established.

Reviewed SHA256 values:

- `native_map.py`: `317593330e195feb30902c69a8a8a13e1c1aa76499a018b2fd8427ff665868b2`.
- `test_map.py`: `a25c7fa4af430699a96f3a2880c939e862b584de02106fbd69f22b08aa55ad42`.
- `check01.log`: `e56ad31719bdbdec021bb7064ca5a71fbf85b108e9212597339850d05ceb3d97`.
