"""Renew only unstarted block-one reservations; never invoke a model."""
import contextlib
from datetime import datetime
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

BASE = Path('C:/meter-operator-20261004')
ORIGINAL_REPORT = Path('C:/Users/\uC774\uAD11\uC9C4/orca/codex-desk-meter/results/experiment-launch-preparation-20261004')
EVIDENCE = Path('C:/meter-preflight-20261005/renewal')
RUN_ROOT = Path('C:/meter-runs-20261005')
sys.path.insert(0, str(BASE / 'scripts'))
import benchmark
from benchmark_support import KST, digest, read, save, verify_evidence
from comparison_manager import init_comparison
from operator_baseline import verify
from agy_pilot_environment import scoped_environment, verify_scoped_environment, paths_for

assert datetime.now(KST).strftime('%Y%m%d') == '20261005', 'Do not reuse this dated preparation helper.'
assert benchmark.git('status', '--porcelain', cwd=BASE) == ''
assert benchmark.git('rev-parse', 'HEAD', cwd=BASE) == '272875140d1998d458e26fdb2f6deab5e5d8f7b5'
EVIDENCE.mkdir(parents=True, exist_ok=False)
shutil.copytree(ORIGINAL_REPORT / 'evidence', EVIDENCE / 'evidence')
for name in ('capability-summary.json', 'tests-final.txt'):
    shutil.copyfile(ORIGINAL_REPORT / name, EVIDENCE / name)
order = ['agy-flash.json', 'agy-pro.json', 'codex-sol.json', 'codex-luna.json']
series = []
for filename in order:
    profile_path = BASE / 'experiments/config/next-profiles-20261003' / filename
    profile = read(profile_path)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        benchmark.prepare(SimpleNamespace(baseline='comparison-baseline-20261004', profile=str(profile_path),
                                          root=str(RUN_ROOT), phase='benchmark', seed=1, timeout=7200, port=None))
    directory = Path(output.getvalue().strip().splitlines()[-1])
    ledger = RUN_ROOT / 'ledgers' / (directory.name + '.json')
    init_comparison(ledger, directory, BASE / 'experiments/reference/codex-7923f96/reference-inputs.json')
    manifest = read(directory / 'run-manifest.json')
    benchmark.verify_agent_inputs(directory, manifest)
    verify(manifest, directory)
    assert manifest['execution']['started_at'] is None
    assert benchmark.git('rev-list', '--count', 'HEAD', cwd=directory / 'checkout') == '1'
    series.append({'profile': filename, 'run_id': directory.name, 'directory': str(directory), 'ledger': str(ledger),
                   'old_unstarted_run_id': '20261004' + directory.name[8:],
                   'candidate_commit': manifest['operator']['local_base_commit'],
                   'candidate_tree': benchmark.git('rev-parse', 'HEAD^{tree}', cwd=directory / 'checkout'),
                   'profile_sha256': manifest['execution']['profile_sha256'],
                   'input_bundle_sha256': manifest['execution']['input_bundle_sha256']})
    print(json.dumps({'prepared': directory.name}), flush=True)
save(EVIDENCE / 'prepared-reservations.json', {'series': series, 'product_invocations_during_preparation': 0})

current = EVIDENCE / 'current'
current.mkdir()
versions = {}
for filename in order:
    profile = read(BASE / 'experiments/config/next-profiles-20261003' / filename)
    version = subprocess.check_output(profile['version_argv'], text=True, encoding='utf-8', timeout=30).strip()
    assert version == profile['agent_version'], (filename, version)
    versions[filename] = version
idf_version = subprocess.check_output([sys.executable, 'C:/Espressif/v5.3.2/esp-idf/tools/idf.py', '--version'],
                                      text=True, encoding='utf-8', timeout=30).strip()
assert idf_version == 'ESP-IDF v5.3.2'

# Read native settings with the frozen profile's existing overrides. No model turn.
spec = importlib.util.spec_from_file_location('dated_native_inventory', ORIGINAL_REPORT / 'native_inventory.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
native.ROOT = BASE
sys.argv = [str(ORIGINAL_REPORT / 'native_inventory.py'), str(current / 'native')]
native.main()
for name in ('codex-skills.json', 'codex-features.txt', 'opencode-config.json', 'opencode-skills.json'):
    actual = (current / 'native' / name).read_bytes()
    prior = (ORIGINAL_REPORT / 'evidence/native' / name).read_bytes()
    assert actual == prior, 'Native settings changed: ' + name

gemini = Path.home() / '.gemini'
paths = paths_for(gemini)
before = {key: digest(path.read_bytes()) if path.is_file() else None for key, path in paths.items()}
exe = read(BASE / 'experiments/config/next-profiles-20261003/agy-flash.json')['version_argv'][0]
env = os.environ.copy()
env['AGY_CLI_DISABLE_AUTO_UPDATE'] = 'true'
workspace = Path(series[0]['directory']) / 'checkout'
policy = BASE / 'experiments/config/agy-pilot-permissions.json'
backup = Path('C:/meter-private-preflight-20261005/native-inventory-scope')
with scoped_environment(gemini, policy, backup, workspace=workspace) as identity:
    scoped_sha = verify_scoped_environment(gemini, policy, workspace)
    save(current / 'agy-active-scope.json', {'settings_sha256': scoped_sha, 'policy_sha256': identity['policy_sha256'],
                                            'workspace': str(workspace), 'instructions_absent':True, 'hooks_absent':True})
    for name, argv in [('mcp', ['mcp','list']), ('plugins', ['plugins','list']), ('agents',['agents']), ('models',['models'])]:
        run = subprocess.run([exe, *argv], cwd=workspace, env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
        (current / ('agy-' + name + '.txt')).write_bytes(run.stdout.encode('utf-8'))
        (current / ('agy-' + name + '-stderr.txt')).write_bytes(run.stderr.encode('utf-8'))
        assert run.returncode == 0, ('AGY inventory failed', name, run.returncode)
        if name != 'models':
            assert run.stdout.encode('utf-8') == (ORIGINAL_REPORT / 'evidence/native' / ('agy-' + name + '.txt')).read_bytes(), name
    catalog = (current / 'agy-models.txt').read_text(encoding='utf-8')
    assert 'gemini-3.8-flash-medium' in catalog and 'gemini-3.1-pro-high' in catalog
after = {key: digest(path.read_bytes()) if path.is_file() else None for key, path in paths.items()}
assert after == before, 'Global AGY files did not restore'
save(current / 'agy-restoration.json', {'before':before, 'after':after, 'restored_byte_identical':True})
save(current / 'current-checks.json', {'checked_at':datetime.now(KST).isoformat(), 'versions':versions,
                                     'idf_version':idf_version, 'native_settings_match_frozen_preparation':True,
                                     'model_catalog_confirms_selected_AGY_ids':True,
                                     'model_entitlement_retested':False,
                                     'prior_capability_probe_date':'2026-10-04',
                                     'model_probe_repeated':False, 'product_invocations':0,
                                     'candidate_hardware_access':False,
                                     'original_reservations_preserved':True})

evidence = {p.relative_to(EVIDENCE).as_posix():digest(p.read_bytes()) for p in EVIDENCE.rglob('*') if p.is_file()}
checks = {key:'pass' for key in ('idf_build','compiler','ninja','git','temp_write','network_policy',
                               'settings_inventory','prompt_scope','activity_logging')}
checks['read_isolation']='not_enforced'
capabilities = read(EVIDENCE / 'capability-summary.json')
for item in series:
    directory = Path(item['directory'])
    manifest = read(directory / 'run-manifest.json')
    profile = read(directory / 'profile.json')
    cap = capabilities[Path(item['profile']).stem]
    assert cap['current_profile_sha256'] == manifest['execution']['profile_sha256']
    cap_path = 'evidence/probes/' + cap['probe'] + '/capabilities.json'
    receipt = {'access_policy':'prompt-and-log', 'base_commit':manifest['execution']['base_commit'],
               'profile_sha256':manifest['execution']['profile_sha256'], 'infrastructure_ready':True,
               'comparison_id':manifest['operator']['comparison']['comparison_id'],
               'input_bundle_sha256':manifest['execution']['input_bundle_sha256'],
               'reference_inputs_sha256':manifest['operator']['comparison']['reference_inputs_sha256'],
               'checks':checks, 'evidence':evidence,
               'capabilities':{key:{'status':'pass','evidence':cap_path} for key in cap['capabilities']},
               'note':'Fresh 2026-10-05 run-bound receipt. Historical 2026-10-04 capability proofs retained; current CLI/SDK/native settings rechecked. No model or product turn invoked during renewal.'}
    receipt_path = EVIDENCE / (Path(item['profile']).stem + '-receipt.json')
    save(receipt_path, receipt)
    benchmark.validate_preflight_receipt(receipt, manifest, profile, EVIDENCE)
    verify_evidence(manifest, directory)
    item.update(receipt=str(receipt_path),receipt_sha256=digest(receipt_path.read_bytes()))
save(EVIDENCE / 'renewal.json', {'checked_at':datetime.now(KST).isoformat(), 'baseline_commit':benchmark.git('rev-parse','HEAD',cwd=BASE),
                               'block':1,'seed':1,'series':series,'product_invocations':0,
                               'existing_active_series_unchanged':'20261004-opencode-cli-opencode-muse-r01',
                               'next_model':'agy-flash.json'})
print(json.dumps({'renewal_complete':True,'unstarted_series':len(series),'product_invocations':0}), flush=True)
