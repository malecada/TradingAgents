# Runtime inventory input correction

The genuine compact_mcm_batched._compiled_inputs guard requires runtime_inventory_sha256 to equal the admitted environment input body SHA256. Input01 instead used the aggregate INVENTORY01 manifest SHA7f0cbd…, whose references already include the exact environment body SHA3a97a20ba8058cac81c8c62a7ba3596aac2fe4deb17627d0aa57bf53a93b86dc. Input02 corrects that one semantic field. Platform, interpreter, executable, NumPy and SciPy fields are unchanged. JSON is serialized canonically; POLICY01 has the corresponding new runtime path/body hash/extent.

LINEAGE01 authenticates the unchanged historical six-body inventory, old runtime reference, current genuine caller/parser and actual public environment body. No inventory was rerun and no numerical package/native code imported. Original inventory exclusions and observation age remain: this correction provides no current package/library/loaded-runtime proof.

Actual stdlib parser functions and the exact caller predicate operands were checked: old reference fails the environment join; corrected reference passes. Three malformed metadata controls refuse. The shared focused result is in sibling binding-preparation02/CHECK_RESULT01.json; source fixture there is executable without scientific imports. Literal patch reverses the runtime body to input01; original files remain immutable.

This is a public input correction pending independent review and fresh binding/admission, not numerical or empirical acceptance.
