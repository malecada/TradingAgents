# Parent04 source review

WITHHELD. Exact source b570c7dd5e95c64ce8681ddde963b0657c4815cae85029dc4411070a069aa1d2 corrects RP1/RP2 but retains RP3 at parent_wait04.py:253–255: the finally block constructs a joined request mapping before calling finish_wait. Failure in that construction skips all remaining descriptor closes and terminal publication attempts and can replace an earlier actual fatal.

check_parent04.py executes that exact extracted finally with an ordinary plain request dictionary and injects MemoryError at its actual BUILD_MAP opcode. The prior SystemExit remains in the local primary variable but the outward exception is the later MemoryError; finish_wait is not called. This is a controlled allocation-fault test, not actual host-memory exhaustion or invocation of main. Move the mapping construction before acquiring stdio/spawning the child, leaving the final cleanup call unconditionally reachable without that allocation.

The same check independently confirms corrected file-close promotion, directory-close first-fatal preservation, both post-wait fd closes and both receipt attempts. Three actual new tiny stdlib children covered callback fatal, failed TERM followed by natural exit/reap, and actual SIGTERM cancellation. PIDs3387895/3387896/3387907 were all absent after wait; original signal handlers restored. No original capsule, source, request, research claim, native unit or numerical module was executed or modified. These checks do not establish descendants of a research workload or OS resource capacity.

Original02/03/04 remain immutable and uninvoked. Existing request/capsule acceptance remains prospective; this withheld parent is not a release.
