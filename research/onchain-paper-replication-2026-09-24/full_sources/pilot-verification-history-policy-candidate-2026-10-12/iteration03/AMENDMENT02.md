# FIFO refusal amendment02

Candidate01 and manifest669bb0d07ca9c9f2e15d8327a534c1a60896e51fc36a5e910a4b3c0e331cc85d are preserved verbatim in iteration01; original SOURCE_MANIFEST01 remains unchanged. Independent reviewer retained actual FIFO-hang RED in its FRONTIER_CHECK01 evidence. O_RDONLY can block while opening a FIFO before the regular-file fstat. The only admission semantic delta adds O_NONBLOCK and O_CLOEXEC to this same bounded open; fstat and all body/hash checks remain.

FIFO_CHECK02 passes the single actual temporary FIFO control through the exact extracted _history_frontier under a250ms alarm in0.020s. No unchanged matrix was repeated. Benchmark output now explicitly labels the measured history-frontier/audit component and excludes current admission checks, warm own-claim verification and production warm latency. Benchmark algorithm and scope are unchanged and were not executed. No live source, registration, claims, Git or state mutation.
