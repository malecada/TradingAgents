# Maintained archive transport extraction

Bounded engineering assignment from the coordinator, based on accepted commit
`b449a2a59549ea500790e95df1615df21b753401`. This written scope records the
assignment; it is not an empirical preregistration or an external-run release.

Owned implementation: `tradingagents/research/onchain_replication/archive_transport.py`.
Owned tests: `tests/research/onchain_replication/test_archive_transport_production.py`.
Owned evidence: this directory, except independent `REVIEW*.md` assigned to the reviewer.
Existing source, tests, historical jobs, gates, STATE and evidence remain unchanged.

The module implements the existing archive_chunks interface: transport identity,
exclusive remote mkdir, finite put and get with an explicitly bound expected
extent. Configuration injects host, user, port, identity-file path and known-hosts
path. No authentication file is read during construction and no endpoint or
credential is embedded. Caller-supplied SSH authentication is used only if a
separately admitted caller invokes an operation.

Upload bytes are read through the existing bounded descriptor reader, copied
into a sealed Linux memfd and reserved before the child starts. Source-path
growth cannot increase the transmitted snapshot. Downloads reserve the original
conservative `32768 * (expected_bytes // 32768 + 1)` payload upper bound and retain
failed partial staging files. Exact size is required before exclusive local
destination publication. Every operation uses a mandatory caller lease; the
receiver also checks it while polling. Each process has a finite deadline,
bounded diagnostic tail and bounded cleanup wait. No automatic retries exist.

The focused verification admits only temporary synthetic files and local Python
child processes. The historical smoke script is never executed as a job; its
existing five tests import it and replace transport commands with local children.
No network, credentials, external mutations, actual-owner source-scanning tests,
empirical source reads or research claims are admitted by this assignment.

The adapter does not provide current remote availability proof, remote capacity
admission, wire-byte metering, filesystem physical accounting, resource admission,
producer integration or whole-owner/terminal publication. Caller authority and
guard requirements remain unchanged. The explicit versioned transport identity
does not upgrade historical smoke-job receipts. No scientific denominator,
research gate or spent evidence is changed.
