# Independent producer-library identity review

Accepted for exact historical/current producer-library byte comparison only.
The component does not establish full execution compatibility or current-run
admission; its explicit false flags correctly retain those exclusions.

The source inventory combines the maintained job/native producer requirements
with every historically registered Python file under the maintained library and
dated component prefixes. This retains the three registered owner journal,
ownership and workload dependencies omitted by the earlier dynamic helper
inventory. Every required path must be present in the original claim. Both the
historical and prospective file must equal that original registered SHA-256;
there is no exception for a changed dispatch or control module.

The accepted strict reader opens nonblocking with no symlink following, validates
regular-file/single-link/same-device containment, and checks descriptor and path
signatures. The source wrapper bounds file count, each opened extent and their
aggregate before hashing. Hash reads use bounded chunks and the expected extent
plus one trailing-byte check. A final pass reopens every file against its saved
signature and hash. These checks provide a bounded observation, not an atomic
filesystem snapshot or proof of arbitrary process/import security.

Independent read-only reconstruction from the retained claim found 120 declared
sources: 119 library files and the separately reported `engine.py`. Hashing the
119 files in both roots produced 238 exact matches, 1,859,534 bytes in one pass
across both roots, and a largest file of 25,467 bytes. No mismatch was found.
This reconstruction read only source files and compact claim metadata and did
not execute the component or any test. `source_bytes_read_once` intentionally
excludes the final hash pass and the separate historical metadata inspection;
it must not be presented as total I/O or a process-memory measure.

Saved `source-check02.log` reports three tests passing in 0.187 seconds: exact
119-file identity, count/byte cap refusal, and a real changed dictionary source
in an isolated temporary checkout. `source-check01.log` remains a failed
three-method run in 0.219 seconds, reporting 116 instead of 119 files. The tests
do not independently exercise every concurrent replacement/special-file branch;
those defenses are inherited from the inspected strict-reader implementation.
No test or historical job was rerun by the reviewer.

Independently calculated SHA-256 values:

- `source_identity.py`: `1d634e6e31b7405f054b6c9d10fe81a7865886ce127f0658fa915a4beca7f7ed`
- `test_source_identity.py`: `06cc5bdfd6552762ae49c96edd0f396019a979046ed5664d8779131da4cf9a6d`
- `source-check01.log`: `cd00dbae937e4202a79100313ae5c317112f4c6b1ab4c740834fee7ea78d7dba`
- `source-check02.log`: `580074fd999c30a07305a96b857db716e2a30c57841e38652176e8e22471250f`

The historical entrypoint and new consumer dependencies are not admitted by this
comparison. A future current worker must bind its complete reader/source/runtime
closure, explicit source transition and registration, current guard, scientific
inputs and saved members. This review grants no relocation, numerical producer
replay, empirical release, full-scale resource feasibility or financial claim.
The prior scientific `REVIEW.md` remains unchanged.
