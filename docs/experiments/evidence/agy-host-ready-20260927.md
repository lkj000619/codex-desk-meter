# Host toolchain preflight correction

The prior pilot exposed a real environment gap: IDF's Xtensa compiler does not establish
that CMake can compile and execute host C/C++ programs. Added `check-host-compiler.py`
to the mandatory preflight. It configures, compiles, links and executes separate C and
C++ standard-library fixtures with CMake/Ninja/CTest, failing on any nonzero command.
The test failed before provisioning and passed after activation.

Pinned portable [LLVM-MinGW release 20260616](https://github.com/mstorsjo/llvm-mingw/releases/tag/20260616)
under `C:/Espressif/benchmark-host-tools`. Archive SHA-256 was verified against the upstream
GitHub asset digest before extraction. Configuration records that digest and compiler hashes.
Activation verifies executable hashes and supplies process-local PATH only. Agent installation,
global PATH edits and broader permission rules are not required.

A separate actual AGY diagnostic passed CMake host configure/build, two CTest runtime cases,
IDF 5.3.2 version/target and an ESP32-S3 binary build under the unchanged finite command policy.
See [diagnostic hashes and usage](agy-host-idf-smoke-20260927.json).
All 101 repository regression tests passed. Native source fixtures contain no product solution.

The shared prompt now states that missing tools end the run; users' folders are not toolchain
search space; temporary diagnostic files may remain; Python replicas cannot substitute for
linked product C modules; only the operator can attest operator review. These clarify existing
scope and evaluation rules. Freeze a new baseline and receipt; do not pool with earlier inputs.
Product pilot pass remains false pending a reviewed new run.
