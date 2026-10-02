# Independent initial fit/checkpoint review

No material blocker identified in the bounded synthetic test design. Execution acceptance remains pending the active check01 terminal result. Source and fixture inspection only; no tests or numerical jobs were rerun by the reviewer.

The fixture registers both synthetic classification/regression cell names and the explicit model/training JSON inputs before claim. It constructs the actual fresh compact producer and native map. Maintained fit_scaler receives a price table derived solely from training rows' input dates/prices, then applies its unique-date and fold-window rule. The current assertion checks training hash and scaler-date membership, not an independent expected mean/std calculation. Repeated-date price consistency is inherited from this known synthetic fixture rather than independently tested here.

Both tasks use maintained batch_factory, fit_cell and predict_cell. Two motifs, two time steps, two epochs and batch size one are explicit synthetic overrides; production configuration files are unchanged. Direction uses the two-logit classifier and regression uses standardized-price MSE. Epoch logs must count all supplied training examples. Prediction shape and checkpoint manifest hash are checked. The actual checkpoint reader verifies artifact member bytes/provenance and loads model, optimizer and RNG state. A restored model must reproduce exactly the prediction tensors and every original model-state tensor, with epoch two, batch zero and identical logs. Duplicate fit calls must refuse the already-claimed cell.

This is model-state/prediction restoration evidence, not independent equality of every optimizer or RNG value or resumed-optimizer trajectory. The test does not explicitly read and join fit complete.json to the returned checkpoint; that file is written by the maintained fit implementation. Synthetic checkpoint provenance is supplied directly to fit_cell: the full evaluate_cell scientific configuration/cell/scaler/output validation, execute_batch, independent metrics, prediction ledgers and actual OS guard are not invoked. Those omissions must remain explicit in any final claim.

After each task, model/checkpoint references are released, garbage collection is requested, tracked native returned-tensor bytes must be zero, saved feature hashes must be unchanged, and full compact producer finalization must pass. This does not prove release of all aliases/autograd/model memory or RSS, nor numerical parity against an independent training oracle. Synthetic source fixtures are temporary and no retained checkpoint blob, financial outcome or empirical release is claimed.

Direct inspected SHA-256 bindings:

- test_compact_native_fit.py: `b5643819da569bca454b49829599a8f1ec393dafad8421dc6864ba8e999ffafc`
- training.py: `5c0380de62c670d356ea3546c7b81eed4ccab55a886bc27b6a1bbfd75c2c3369`
- checkpoints.py: `74e7bd16d4331cbac45143884e1f35a52687b19280c214457834b0cf19a457bc`
- dataset.py: `c8d701b5646395bb94e5037aefcc2d0d29a55de95cca05e019ce35d3f53561df`
- evaluation.py: `b3af7cf6b71f8adcdd762eb471abb66d8fdd00f20087aeff377447d51a854b29`
