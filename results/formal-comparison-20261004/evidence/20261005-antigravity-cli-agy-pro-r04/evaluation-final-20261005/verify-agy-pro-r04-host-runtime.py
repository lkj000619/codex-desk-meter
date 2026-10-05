"""Evaluate the archived host prototype with its recorded compiler runtime."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import sys

REST = Path('C:/meter-run-restores-20261005/agy-pro-r04-final')
CO = REST / 'checkout'
FROZEN = REST.parent / 'agy-pro-r04-final-frozen-operator'
OP = REST / 'operator'
PACK = Path('C:/meter-run-packages-20261005/agy-pro-r04-final')
expected = 'aaf375f63861eb47e9e65ce71429e52badb13936cf2e22dba0556e3218048da3'
assert hashlib.sha256((PACK / 'package-manifest.json').read_bytes()).hexdigest() == expected
exe = CO / 'build-host/test_meter_parser.exe'
raw_exe = OP / 'operator-observation/host-artifact-snapshot/build-host/test_meter_parser.exe'
assert exe.read_bytes() == raw_exe.read_bytes()
compiler_line = next(line for line in (CO / 'build-host/CMakeCache.txt').read_text(encoding='utf-8').splitlines() if line.startswith('CMAKE_CXX_COMPILER:FILEPATH='))
compiler = Path(compiler_line.split('=', 1)[1])
assert compiler.is_file() and compiler.parent == Path('C:/Espressif/benchmark-host-tools/llvm-mingw-20260616-ucrt-x86_64/bin')
# Process-local runtime path; no global settings or candidate files changed.
os.environ['PATH'] = str(compiler.parent) + os.pathsep + os.environ['PATH']
sys.path.insert(0, str(FROZEN / 'scripts'))
spec = importlib.util.spec_from_file_location('packaged_partial_state_evaluator', FROZEN / 'scripts/evaluate-product.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cases = module.evaluate([str(exe)], CO)
assert not any('3221225781' in item.get('reason', '') for item in cases)
original = json.loads((OP / 'operator-host-checks.json').read_bytes())
assert all('3221225781' in item.get('reason', '') for item in original['cases'])
report = {
    'run_id': '20261005-antigravity-cli-agy-pro-r04', 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'source_package_manifest_sha256': expected, 'original_run_or_checkout_used': False,
    'packaged_frozen_evaluator_used': True, 'source_executable_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
    'source_executable_bytes': exe.stat().st_size, 'recorded_compiler': str(compiler),
    'initial_operator_check': '29 loader errors with exit 0xC0000135 (3221225781); default operator PATH lacked recorded compiler DLL directory. Those are environment errors, not conformance failures.',
    'original_operator_check_preserved_in_package': True, 'environment_correction': 'Recorded compiler runtime directory added only to this evaluation process PATH.',
    'cases': cases, 'passed': sum(c['status'] == 'pass' for c in cases), 'failed': sum(c['status'] == 'fail' for c in cases),
    'scope': 'Submitted partial C state module plus mocked normalizer. No real firmware or collector/device conformance claim.',
    'candidate_source_or_cost_changed': False, 'operator_firmware_rebuild': False,
    'candidate_result_submission': 'missing', 'candidate_selection_document_submission': 'missing',
    'hardware_status': 'not_run_no_firmware', 'product_pass': False
}
assert exe.read_bytes() == raw_exe.read_bytes()
out = REST.parent / 'agy-pro-r04-post-package-host-runtime-check.json'
assert not out.exists()
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'host_cases': len(cases), 'passed': report['passed'], 'failed': report['failed'],
                  'loader_environment_errors': 0, 'from_independent_archive': True, 'product_pass': False}))
