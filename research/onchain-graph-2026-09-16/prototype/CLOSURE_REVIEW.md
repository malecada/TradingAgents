# Independent prototype closure and source diagnosis

Reviewer: onchain_review research-reviewer, read-only. The original lifecycle result is COMPLETE with119cells:117complete extraction cells and2unavailable cells (integrity/graph), with250outputs. It is not failed.json and must not be relabelled or rerun. The prototype allowance is consumed2/2 including its imported predecessor.

Independent raw reconstruction verified117responses,118,730,958bytes, ETags/ranges/hashes/timestamps, all1,101,465unique transactions, complete block-position coverage and every retained block binding. Three source-order inversions were confirmed. All258imported files, including252run members, match detached evidence. No additional integrity or preservation defect was found.

All777rejected recipients are exclusively the literal string `"None"`, not empty strings or actual nulls. They occur in all13groups and711blocks. The original footer reports zero recipient nulls and maximum string value `"None"` in every group. Breakdown: successful zero686/positive76; failed zero9/positive6. These support a consistent encoded missing-recipient sentinel, not proof of contract creation.

A narrow exact-sentinel-to-missing normalization would retain every row and exclude all777from graph edges. Under unchanged exclusion precedence, categories reconcile to invalid0, reverted20524, missing recipient762, zero value530351, self-transfer2496 and graph events547332. This is forensic reconciliation, not a corrected passing lifecycle claim. Other malformed strings must remain invalid.

Existing amendment helpers require a failed.json parent and cannot be silently applied to this complete-but-unavailable parent. Preserve originalcap2/2 and evidence. Either use a separately reviewed additive policy or a clearly identified, separately frozen forensic reconstruction that does not claim new lifecycle/source admission or reset a budget.

The independent reconstruction took9.04seconds with sampled peakRSS395,558,912bytes under two-core/memory-only guard. No new network, financial outcomes or graph summary metrics were evaluated. Import-manifest SHA256: bd2cd0bd343448e8cfca7ee4fe7b6021a9b7f5a9ed442ffcb7fbc11e6a48e483.

## Documentary corroboration

The AWS producer code at commit[a72285ae82da1c38fd39c5b8c7c60e209372342b](https://github.com/aws-samples/digital-assets-examples/blob/a72285ae82da1c38fd39c5b8c7c60e209372342b/analytics/producer/copilot/ethereum-worker/worker.py#L190-L192) converts string columns using `astype('str')`. This is consistent with turning a Python missing value into the observed literal. It is not proof of the deployed producer revision for the captured file. [Ethereum JSON-RPC documentation](https://ethereum.org/en/developers/docs/apis/json-rpc/#eth_gettransactionbyhash) defines an absent recipient for contract-creation transactions. No receipt_contract_address or independent RPC witness was captured, so individual contract-creation attribution remains unproved.
