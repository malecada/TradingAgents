# Pre-execution admission corrections

The initial preparation commit 8faae280247707597e01d64f45b81fac81ab9188
was pushed before any acquisition. An admission-only invocation first supplied
a short source hash and was rejected; the required full HEAD was then supplied.
The full-HEAD check found that the spot dataset's registered window had no
input metadata mapped to it. No ResearchRun claim or network acquisition occurred.

The correction adds a committed spot acquisition plan containing the exact
38 months and 76 URLs, maps it to the existing spot window and verifies it in
the runner. Source windows, cohort, byte/request/resource bounds, allowance and
scientific rules are unchanged. The initial commit remains preserved. All
final source/charter/input hashes must match the successor execution HEAD;
only that reviewed successor may be claimed.
