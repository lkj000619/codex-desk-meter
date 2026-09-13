# OpenCode E2E preparation check

## Scope and confirmed configuration

The selected cohort is `version-2-end-to-end-v1`. The common task includes F1–F9,
I1–I4, and G1–G6. The transport is USB serial `cdm/1`; physical flashing is performed
later by the operator against the frozen artifact. A fixture embedded in firmware
or a host reference receiver does not replace production device integration.

The installed OpenCode version reports `1.18.30`. `opencode models` lists
`opencode/muse-spark-1.3-contributor-free`. The local npm launcher resolves to a
native executable, so runner argv must use that executable rather than a shell
command string. The profile deliberately retains an executable placeholder until
an isolated execution environment is selected. No model variant was selected.

## Telemetry probe

A separate one-response probe used `run --pure --format json` with every tool
permission denied in a new temporary directory. It returned `METER_PROBE_OK`
and exited 0. This is a model-access/usage probe, not a product implementation run.

The observed `step_finish.part.tokens` values were:

| Field | Provider-reported value |
|---|---:|
| input | 2005 |
| output | 15 |
| reasoning | 45 |
| total | 2065 |
| cache.read | 0 |
| cache.write | 0 |

The full command took approximately 3.27 seconds in the host execution tool.
This duration includes startup and is not a benchmark measurement. The runner
now preserves provider totals and reasoning separately and sums per-step usage;
it does not add reasoning or cache to the reported total again. Cache write and
original events remain in raw stdout. Tool/failed-command normalization for
OpenCode remains unsupported and must be null rather than inferred from tokens.

## Isolation outcome

`--pure` disables external plugins. A tool-deny probe is useful for checking
configuration but is not OS isolation for a coding agent that needs a shell.
OpenCode's permission system controls tool actions and external-directory access;
it is not evidence that a subprocess cannot read other host files.

The local Docker client is present, but its Linux engine is unavailable:
`dockerDesktopLinuxEngine` named pipe was not found. WSL distributions are listed,
but no profile-bound isolated build/read/network/settings receipt was established.
Therefore `read_isolation`, `idf_build`, `network_policy`, and `settings_inventory`
remain unverified. No passing sandbox receipt was fabricated.

The next preparation step is to provide a container/VM build environment with
only the clean candidate checkout mounted, fixed compiler/ESP-IDF tools, and an
explicit model-network policy. Logs and prior results remain outside the mounted
checkout. The agent's runtime configuration must also be inventoried there.

## Remaining runner boundary

The operator run manifest now accepts E2E cohort IDs and prepare selects the E2E
result path. This is an execution/measurement manifest, not the separate E2E
evaluation manifest. The current archive command still targets the historical
hardware-feature schema; E2E evaluation-manifest generation and E2E archive
normalization require a separate implementation before claiming a complete
formal E2E workflow. Raw implementation snapshots remain the authoritative output.

The changed prompt/config are uncommitted preparation changes. They must be
frozen as a new baseline before candidate execution. The prior `d2f2e22` commit
still contains the historical task. No candidate product run has started.

## Regression verification

The changed tree passed 51 unit/integration tests, the E2E default validator,
provider fixture matrix validator, historical validator, and `git diff --check`.
Each command returned exit code 0. The additional usage test verifies repeated
OpenCode steps and prevents adding reasoning/cache to a provider total twice.
Stdin delivery for the full candidate task remains unverified: the access probe
used a positional message. It must be checked separately before runner execution.

Reference: https://opencode.ai/docs/permissions/
