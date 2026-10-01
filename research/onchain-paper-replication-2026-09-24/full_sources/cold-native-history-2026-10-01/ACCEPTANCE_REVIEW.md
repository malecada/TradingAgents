# Independent completed-run certificate acceptance

Accepted for the bounded historical lifecycle/registration/output/guard/observer
certificate. This supersedes the withholding in `REVIEW.md` and
`FINAL_REVIEW.md` only for the corrected source identified below; both earlier
reviews remain preserved.

CH1–CH3 remain addressed as recorded in `FINAL_REVIEW.md`. CH4 is now closed:
`_read_metadata` opens with `O_NONBLOCK | O_NOFOLLOW`, then checks the opened
descriptor against the admitted regular-file signature before reading. The new
test substitutes a real FIFO in the stat/open interval, asserts the nonblocking
flag before opening, forbids the reader, and requires descriptor refusal. The
flag assertion prevents this regression from hanging against the old source.

The saved `check04.log` reports 13 tests passing in 0.072 seconds. This is the
history test result from the first command in a sequential shell invocation;
the later publication-test failure is separate and is not represented as a
successful combined invocation. Tests were inspected, not rerun.

Independently calculated SHA-256 values:

- `terminal.py`: `bae47e38f64b9fc2f5a2f76c681f7617f28238b581649e4235232a5366807cce`
- `test_terminal.py`: `f2522af575c236edb35722e98b2072709ec04acd99874fbb8f91bd4b146f04a3`
- `check04.log`: `95f6ca0ba56ffd6b817b03dc0ec5176177200c8e071d28a46d5370f8ddc6cf30`
- Preserved `terminal.py.check03`: `089cb473103e7e7eef9e517e4e5860fd096486d8de6a79bf62bd9576edfb57a6`
- Preserved `test_terminal.py.check03`: `c8c156347d2bfbb35fbe311d1ea84347b44422aea8a4c09e1714454490548af5`

The certificate intentionally leaves current-run admission, native-feature
verification, source compatibility and array reads false. No scientific
denominator, resource-policy compatibility, seal/member admission, numerical
array correctness, current guard, atomic continuously changing snapshot,
financial result or empirical release is established here. Some semantic tests
mock decoded records and therefore establish join refusal rather than a complete
rehashed malformed filesystem history. No test, job, producer or financial
experiment was executed by the reviewer.
