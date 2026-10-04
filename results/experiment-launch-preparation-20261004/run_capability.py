"""Run one separate, non-product capability probe and retain every outcome.

Invoke from a shell activated with scripts/activate-idf.ps1. This never runs
benchmark.py run or touches serial hardware. Profiles may still be pending:
this command produces the evidence needed to review them, not a passed receipt.
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from benchmark import capture, profile_digest
from benchmark_support import digest, read, save
from agy_pilot_environment import scoped_environment, verify_scoped_environment


def run(profile_path, destination):
    profile = read(profile_path)
    destination = destination.resolve()
    if not str(destination).isascii() or destination.is_relative_to(ROOT):
        raise ValueError('probe requires a new ASCII directory outside the repository')
    destination.mkdir(parents=True, exist_ok=False)
    workspace = destination / 'workspace'
    workspace.mkdir()
    original = Path('C:/meter-preflight-20261002/codex-sol-capabilities-r4')
    inventory = read(original / 'fixture-inventory.json')
    for name, expected in inventory.items():
        data = (original / 'workspace' / name).read_bytes()
        if digest(data) != expected:
            raise ValueError('original infrastructure fixture changed: ' + name)
        path = workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (workspace / 'tests/probe.py').write_text('assert 2 + 2 == 4\n', encoding='utf-8')
    for args in (['init'], ['add', '.'], ['-c', 'user.name=Preparation', '-c', 'user.email=preparation@localhost', 'commit', '-m', 'Empty infrastructure fixture']):
        subprocess.run(['git', *args], cwd=workspace, check=True, capture_output=True)
    prompt = (original / 'prompt.txt').read_text(encoding='utf-8').replace(str(original).replace('\\', '/'), destination.as_posix())
    prompt += '\n10. Run python -m py_compile tests/probe.py. Do not invoke or modify product code.\n'
    save(destination / 'profile.json', profile)
    save(destination / 'fixture-inventory.json', {p.relative_to(workspace).as_posix(): digest(p.read_bytes()) for p in workspace.rglob('*') if p.is_file() and '.git' not in p.parts})
    (destination / 'prompt.txt').write_text(prompt, encoding='utf-8')
    env = os.environ.copy()
    env.update(IDF_TARGET='esp32s3', AGY_CLI_DISABLE_AUTO_UPDATE='true')
    argv = [arg.replace('{model}', profile['model']) for arg in profile['argv']]
    save(destination / 'invocation.json', {'argv': argv, 'profile_sha256': profile_digest(profile), 'scope': 'infrastructure only', 'timeout_seconds': 900})
    executable = Path(profile['version_argv'][0])
    version = subprocess.run(profile['version_argv'], capture_output=True, text=True, env=env, timeout=30)
    save(destination / 'runtime.json', {'version': version.stdout.strip(), 'version_stderr': version.stderr, 'version_exit': version.returncode,
        'executable_sha256': digest(executable.read_bytes()), 'IDF_PATH': env.get('IDF_PATH'), 'IDF_TOOLS_PATH': env.get('IDF_TOOLS_PATH'),
        'TEMP': env.get('TEMP'), 'TMP': env.get('TMP'), 'ccache': env.get('IDF_CCACHE_ENABLE')})
    if version.returncode or version.stdout.strip() != profile['agent_version']:
        raise ValueError('version guard failed; original attempt retained')
    scope = contextlib.nullcontext({})
    if profile['adapter'] == 'antigravity':
        probe = subprocess.run(['powershell', '-NoProfile', '-Command', '@(Get-Process agy -ErrorAction SilentlyContinue).Count'], capture_output=True, text=True)
        if probe.returncode or probe.stdout.strip() != '0':
            raise ValueError('close existing AGY before temporary scoped environment')
        scope = scoped_environment(Path.home() / '.gemini', ROOT / 'experiments/config/agy-pilot-permissions.json',
                                   destination / 'private-backup', workspace=workspace)
    try:
        with scope as identity:
            if identity:
                env['AGY_PILOT_LOCK_TOKEN'] = identity['lock_token']
                value = verify_scoped_environment(Path.home() / '.gemini', ROOT / 'experiments/config/agy-pilot-permissions.json', workspace)
                save(destination / 'scope.json', {'settings_sha256': value, 'policy_sha256': identity['policy_sha256']})
            result = capture(argv, workspace, prompt.encode('utf-8'), destination, 900, env=env)
            save(destination / 'process.json', result)
    except Exception as exc:
        save(destination / 'setup-error.json', {'error': str(exc), 'type': type(exc).__name__})
        raise
    artifacts = {}
    for pattern in ('probe-output.txt', 'build-host/Testing/Temporary/LastTest.log', 'build-idf/*.bin', 'build-idf/*.elf', 'tests/__pycache__/probe.*.pyc'):
        for path in workspace.glob(pattern):
            if path.is_file():
                artifacts[path.relative_to(workspace).as_posix()] = digest(path.read_bytes())
    save(destination / 'artifacts.json', artifacts)
    print(json.dumps({'directory': str(destination), 'process': result, 'artifacts': artifacts}, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(args.profile, args.output)
