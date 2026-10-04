"""Capture selected non-secret native settings without invoking a model."""
import ast
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from benchmark_support import digest, read, save


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else 'C:/meter-preflight-20261004/native-inventory')
    output.mkdir(parents=True, exist_ok=False)
    profiles = ROOT / 'experiments/config/next-profiles-20261003'
    profile = read(profiles / 'codex-sol.json')
    opts = []
    for i, arg in enumerate(profile['argv']):
        if arg in ('-c', '--enable', '--disable'):
            opts += [arg, profile['argv'][i+1]]
    exe = profile['version_argv'][0]
    p = subprocess.Popen([exe, *opts, 'app-server'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=(output / 'codex-server-stderr.txt').open('wb'), text=True, encoding='utf-8',
                         cwd='C:/meter-preflight-20261004/codex-sol-r1/workspace')
    messages = queue.Queue()
    def reader():
        for line in p.stdout:
            messages.put(json.loads(line))
    threading.Thread(target=reader, daemon=True).start()
    def request(identity, method, params):
        p.stdin.write(json.dumps({'id': identity, 'method': method, 'params': params})+'\n')
        p.stdin.flush()
        while True:
            value = messages.get(timeout=40)
            if value.get('id') == identity:
                if 'error' in value:
                    raise ValueError(value['error'])
                return value['result']
    try:
        request(1, 'initialize', {'clientInfo': {'name': 'comparison-preparation-inventory', 'version': '1.0'}, 'capabilities': {}})
        value = request(2, 'skills/list', {'cwds': ['C:/meter-preflight-20261004/codex-sol-r1/workspace'], 'forceReload': True})
        skills = [{k: s.get(k) for k in ('name', 'scope', 'enabled', 'path', 'pluginId')} for entry in value['data'] for s in entry['skills']]
        save(output / 'codex-skills.json', {'source': 'native skills/list, same skills/feature overrides; app-server config layer differs from exec --ignore-user-config', 'skills': skills})
    finally:
        p.terminate()
        p.wait(timeout=10)
    r = subprocess.run([exe, *opts, 'features', 'list'], capture_output=True, text=True, timeout=30)
    (output / 'codex-features.txt').write_text(r.stdout, encoding='utf-8')
    hook_path = Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex'))) / 'hooks.json'
    hooks = read(hook_path) if hook_path.exists() else {}
    save(output / 'codex-hook-inventory.json', {'source_path': str(hook_path), 'exists': hook_path.exists(),
        'source_sha256': digest(hook_path.read_bytes()) if hook_path.exists() else None,
        'configured_events': list(hooks.get('hooks', {})), 'comparison_override': 'features.hooks=false'})
    profile = read(profiles / 'opencode-muse.json')
    node = next(n for n in ast.walk(ast.parse(profile['argv'][2])) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'update')
    env = os.environ.copy()
    env.update(ast.literal_eval(node.args[0]))
    for name, command in [('config', ['debug', 'config']), ('skills', ['debug', 'skill']), ('paths', ['debug', 'paths'])]:
        r = subprocess.run([profile['version_argv'][0], *command], cwd='C:/meter-preflight-20261004/codex-sol-r1/workspace',
                           env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
        (output / ('opencode-'+name+'-stderr.txt')).write_text(r.stderr, encoding='utf-8')
        if r.returncode:
            raise ValueError(f'OpenCode {name} exited {r.returncode}: {r.stderr}')
        if name == 'paths':
            (output / 'opencode-paths.txt').write_text(r.stdout, encoding='utf-8')
            continue
        value = json.loads(r.stdout)
        if name == 'config':
            value = {k: value.get(k) for k in ('plugin', 'mcp', 'instructions', 'permission', 'agent', 'autoupdate', 'share')}
        save(output / ('opencode-'+name+'.json'), value)
    print(output)


if __name__ == '__main__':
    main()
