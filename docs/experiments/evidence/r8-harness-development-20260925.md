# R8 evaluator harness development check — 2026-09-25 KST

This records a development-checkout rehearsal of the proposed pre-pilot R8
commands. It is **not an R8 pass**: the working tree contains uncommitted
runner and documentation changes, and these commands have not been repeated
from the final clean baseline checkout. No model/provider, serial device, or
firmware was accessed.

- Reviewed HEAD: `b7bc2f1d0cbc5ba22b25e58f810640e32cb8c4b0`
- Previously selected baseline tag: `benchmark-v2-baseline-20260923` →
  `9ef945efd9d6c2c4b4eedca75eccc9f280b3aced`
- Observation time: 2026-09-24 17:37 UTC (2026-09-25 02:37 KST)

| Command | Exit | Observed result |
|---|---:|---|
| `python -m unittest discover -s scripts/tests -p test_*.py` | 0 | 85 tests, `OK` |
| `python scripts/validate-end-to-end-result.py` | 0 | Valid synthetic E2E example |
| `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json` | 0 | Valid E2E example and fixture matrix |
| `python scripts/validate-end-to-end-result.py --result experiments/examples/invalid/invalid-product-pass.example.json` | 1 | `INVALID [PRODUCT_PASS_REQUIRES_CORE_RESULTS]` as expected |
| `python scripts/validate-experiment-result.py` | 0 | Valid historical manifest/result example |
| `python scripts/run-host-device-pipeline.py --dry-run --output <frame> --report-output <report>` | 0 | `rendered`, 3961 frame bytes, `device_accessed=false`, no collection failures |

The frame and report were written outside the repository to the task's
`$env:TEMP` directory. Their SHA-256 values are:

```text
frame  02724A9EFF07E5667CDD3B0056FFE301E6BE85D66ED130CF34D2E6A7CA24FEEC
report 026D60E276482475A1DF894E440713564507849C22914C280F34BAB8EB51C581
```

Current local runner files at the time of this check:

```text
scripts/benchmark.py                 2A7E9D373EBA340CF5B3E65636B746FB1CC525BEF46AB83946BE617EDD0DA68F
scripts/run-host-device-pipeline.py  FBB23F1F62A4F9858D8555572A4A6E8CA2B8AB7629CAABBDC226142C7C1F262C
```

At 2026-09-24 17:45 UTC, the AGY parser gained an additional `init.model`
comparison against the selected profile. `scripts/benchmark.py` then had SHA-256
`EC779D1191BC8E147DBCFECD6D657D1003997783120A0C63B97049C15492F2EE`.
The 85-test suite and the E2E matrix and historical validators were repeated
after that change, each with exit 0. This remains a dirty-checkout development
check rather than a frozen R8 review.

Representative fixed input file hashes were also checked:

```text
experiments/prompts/version-2-agent-task.md             F99D708CA9F3BDFC2134942C44E30B6C14BB7A098FE36F75AD5472C8210F4A77
experiments/config/version-2-baseline.yaml              F80D88B527C36F4CA591926BE3842983FD61AFA6ACE517E6C31CF0AB197B337F
experiments/fixtures/provider-fixture-matrix.json       646957AB364B64942D6E5BACB4868A7574E44E110D238146759CA717D0B773AD
experiments/schema/end-to-end-result.schema.json        0CBCA288D59F1830DD15540995405108D26DBB2254885A91CAFE7E6DF101AFE5
```

The original AGY receipt remains blocked. The next R8 decision must use a
clean, approved baseline checkout; preserve command stdout/stderr, input and
output hashes, and a dated maintainer review. Candidate production code,
serial receipt, firmware receiver and LCD outcomes belong to post-run
evaluation and are absent here.

At the later continuation on 2026-09-25 KST, two regression tests were added for
a `SUCCESS` result containing a structured `PermissionDenied` tool error. The
runner rejects that stream for execution status while retaining the terminal
usage and failed-command count in the raw measurement record. The full dirty-tree
suite then ran 87 tests with exit 0. `scripts/benchmark.py` SHA-256 at this
point was `35A887AB026EBD2D623ACCF1BFA762D73BB3493ABE8F596C3360AC32FEFA47C6`.

The subsequent AGY 1.2.11 drift fix passes an explicit child environment to both
the CLI version check and the execution process, setting
`AGY_CLI_DISABLE_AUTO_UPDATE=true` for AGY. A child-environment regression test
was added. The 2026-09-25 dirty-tree offline suite then ran 88 tests with exit 0;
the current `scripts/benchmark.py` SHA-256 was
`3F7942A29BB5DF0F1D148B68ED6CEA014EB4745B3630D7DE4BF4640344C887AC`.
This remains development evidence, not a final-baseline R8 pass.
The official headless documentation describes tool failures in
`tool_info.error` and also says a soft-denied tool can leave the process at
exit 0. It does not guarantee that every soft denial has a particular error
type, so stderr review remains part of post-pilot evaluation. This later
development check also does not promote R8 to pass.
