# Independent initial native dispatch review

Acceptance is withheld pending the resident-loader corrections below and closed final evidence. This is a read-only source/evidence review apart from this document. No tests, jobs, numerical artifacts, registrations or ledgers were executed or changed.

All 796 declared files in dispatch02-sources.json independently matched at review time. Manifest SHA-256: `49a5c5be1285a8c977736ef404089128ac9b0f695b008842aa269cd52152d219`. Reviewed graph_store.py SHA-256: `6cc55da9d9f61995ae8d07d386d30097ecc8775fbbf386eca15c595dafb91bc8`; native_producer.py: `5b7dff71ffe2b1e6c0570b859020d82af337d753665ae77cbea95ff07d1914ed`. This checks the declared freeze, not an independently reconstructed complete import closure.

## Material findings

**ND1 — resident allocation reparses mutable input after extent admission.** In maintained graph_store.py `_resident_array`, the first header/extent check is followed by `stream.seek(0); np.load(stream, ...)` (line38). NumPy parses the header again and allocates from that second shape. A same-file header rewrite between the first validation and np.load can therefore reach allocation with an unadmitted extent; subsequent fstat/hash rejection is too late to bound allocation. Read using the already validated offset/shape/dtype and an explicit bounded allocation, with content/signature verification of the bytes actually loaded. A deterministic regression should change the header at this boundary and assert that no allocation uses the replacement shape. No giant allocation needs to be performed to prove the boundary.

**ND2 — header cap is checked after the declared header is read.** graph_store.py lines33–34 rely on NumPy's `max_header_size=10000`. The installed NumPy implementation, numpy/lib/_format_impl.py lines635–638, reads and decodes `header_length` bytes before checking that limit. An admitted large file can consequently cause an oversized header read/allocation before refusal. Validate the version-specific length prefix against both the explicit header cap and admitted file extent before reading header bytes. Test a validly rehashed large declared header with bounded read instrumentation. The existing oversized-shape test exercises payload extent, not header-read size.

Both findings concern the new resident route's claimed preallocation boundary. They do not establish a changed numerical result or require changing the historical mapped route. Preserve the active source freeze and original failed evidence before correction.

## Corrections and composition inspected

The maintained dispatch explicitly selects the backend in both plan and job, checks native policy route names/source pins and refuses existing or redirected representation/pair namespaces before graph loading. First-owner creation checks the canonical required set and resolved same-device ancestry before mutation; failed construction or postcreation binding preserves residue and raises JournalConstructionError. The observer's missing owner/start/claim disposition does not infer ownership or permit reuse.

The prior pair-construction gap is corrected in source: every exception from ownership.open_journal becomes NativeProducerCleanupError with its exact namespace, even before a handle reaches the caller. job_payload propagates that fatal class rather than converting it to an unavailable representation. Available pair and feature handles are closed on ordinary production failure; a lost lease or failed cleanup escalates and preserves partial evidence. OwnedJournal.seal now receives only its supported status argument. No rollback, silent retry or numerical recovery is introduced.

Sampler, dictionary, MCM and graph-publication keyword arguments and proof-reference return shapes match their actual callees. Native prepare returns `(PreparedFeatures, terminal)` as expected by `_produce_eager_graphs`. One shared import chain preserves the exact issued-ticket and ownership class identities. Explicit resident loading avoids supplying NumPy memmaps to the resident GraphSnapshot route.

## Saved evidence and limits

dispatch01.log closes with one failed method in319.753s at the duplicate-producer refusal assertion. failure01.log closes with two methods and three injected pair-construction errors in119.725s. Both histories remain preserved. loading02.log closes seven passing tests in2.788s, covering existing-route selection, initial extent/shape refusal and resident value parity. At this review, dispatch02 and failure02 logs were nonterminal; no final acceptance is inferred from partial output or the author's anticipated result.

The fixture uses temporary real ResearchRun registration, fresh owner/journal creation, real sampler/dictionary/MCM/native production and synthetic optimizer fits through execute_fit_payload. Kernel guard admission is mocked. It does not demonstrate the real launcher/worker/cgroup path, full-size chronology or resource feasibility, empirical fitting, continuation, mapped parents, physical whole-workflow quota, remote artifact recovery, or completion of the original109 resource requirements/1,420 financial fits. Final review requires terminal evidence and a new complete binding manifest after any correction.
