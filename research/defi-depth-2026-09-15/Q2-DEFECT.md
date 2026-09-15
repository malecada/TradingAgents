# Q2 — source collector compatibility failure

Q2 started once from `1dce226c4a37791a96dc0fabe04c20ebe8d558c0`.
The selected Base API accepted one-member chain and two-member header batches.
Eight retained state-batch responses returned HTTP200 with JSON-RPC error-32014:
`maximum 10 calls in 1 batch`. The harness incorrectly assumed15/29-member
batches would be accepted. No state data or financial outcome was obtained.

After recognizing the repeated deterministic incompatibility, the owning Q2
process received SIGINT. The ordinary lifecycle preserved `failed.json` and all46
published outputs. This was an explicit defect stop, not an elapsed-time kill,
a provider-access workaround or economic rejection. The frozen Q2 code/gate/spec
are preserved and must not be resumed or rewritten.

Nineteen HTTP intents representing168 logical RPC subcalls are charged. Eighteen
receipts retain37,336 raw bytes. The September10 state intent has no published
receipt because interruption occurred while publishing that receipt. Its fifteen
subcalls stay charged and its bytes/outcome unresolved; no raw response is
reconstructed from the repeated earlier error. Eight complete daily result
vectors and the chain result are retained. The other registered dates/cells were
not evaluated. Structural verification passes the46-output failed manifest and
reports zero terminal complete cells; that is not a claim that no partial work
occurred.

The independently reviewed shared R1 repair is justified by this concrete
transport-compatibility defect. It preserves every Q2 input, field, date, clock,
cohort, source endpoint, source-only scope and cell recipe. Only the repair harness
splits each exact ordered state vector into chunks of at most10. The original
spec's transport bounds remain a baseline record; explicit new repair bounds
must be frozen separately. Each chunk requires its own actual intent/receipt.

A full replay adds18,689 logical subcalls and at most3,293HTTP requests. With Q1
and failedQ2, conservative acquisition usage would be18,986/25,000 logical
subcalls, leaving6,014. R1 raw reservation is863,240,192bytes. Include the known
Q1/Q2 rawbytes and reserve262,144bytes for Q2's unreceipted final intent when
reporting the envelope. No experiment duration cutoff is introduced.

Use the existing narrow `research_amended` certificate route, preserving the
source-family object prior1/cap3 with exactly one explicit effective increment.
Q1 and failedQ2 remain in the complete prior-claim inventory. The latest failed
Q2 is the parent; inputs/windows/cells remain identical. Bind the exact repair
contract, unchanged accounting/ABI dependencies, independent review and passing
synthetic preflight. This consumes the one shared repair allowance and grants no
financial trial, revised metric or further repair chain.
