# Optional call aggregation: preparation only

Documentary operations58–60 exhaust the phase's60-operation documentary envelope.
The official [Multicall3 source](https://raw.githubusercontent.com/mds1/multicall3/main/src/Multicall3.sol)
was inspected for aggregate3: an array of target, allowFailure and calldata
produces per-call success and return bytes. This is a possible read-only eth_call
transport optimization, not authorization to submit a transaction. Its inner
execution uses calls, so an adapter would require an explicit getter whitelist.

The [deployment page](https://www.multicall3.com/deployments) returned no extracted
content. The official [deployment registry](https://raw.githubusercontent.com/mds1/multicall3/main/deployments.json)
was opened with a limited excerpt; the displayed portion did not contain Base.
Thus a Base deployment has not been verified by these observations. No contract
address or historical runtime is admitted from memory. No new empirical request
was made. These sources do not establish historical deployed code semantics.

Aggregation remains optional and unadmitted. Individual existing read-only RPC
calls avoid adding this dependency. Their exact count, worst-case bytes and
source semantics must still be registered before any F1/F3 acquisition. There is
no additional documentary lookup allowance; existing source evidence can be reused.
