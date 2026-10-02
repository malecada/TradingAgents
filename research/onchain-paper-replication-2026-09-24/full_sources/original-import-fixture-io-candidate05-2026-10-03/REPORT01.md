# Terminal uncertainty correction05

The synthetic CleanupFailure promotion now skips optional cause attachment.
The previous branch could introduce and discard the first actual MemoryError
while annotating a synthetic uncertainty. Optional cause evidence is attempted
only after an actual fatal has already been selected; that first actual fatal
retains precedence if the attachment then fails. Actual-fatal cause attachment,
ordinary precedence, missing-primary behavior and all other source AST remain.

The retained RED run against actual frozen04 fails precisely on the synthetic
uncertainty cause hook being invoked. Three extracted actual-reducer regressions
pass for new05; no numerical import or job, Binding, Owner or claim was created.
The complete28-target map changes only resource_fixture; all other04/03/02
sources remain pinned. The original numerical/preflight/authority/terminal
assembly AST is unchanged. Independent review and genuine native fixture remain
required; no empirical fit/resource capacity or paper agreement is inferred.
