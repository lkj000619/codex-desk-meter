"""Preserve public preparation logs/artifacts and derive inspectable summaries."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from benchmark import profile_digest
from benchmark_support import digest, read, save
from agy_pilot_environment import paths_for

TARGETS = {'codex-sol': 'codex-sol-r2', 'codex-luna': 'codex-luna-r1',
           'opencode-muse': 'opencode-muse-r2', 'agy-flash': 'agy-flash-r1', 'agy-pro': 'agy-pro-r1'}
REPORT = Path(__file__).resolve().parent
EXTERNAL = Path('C:/meter-preflight-20261004')


def event_tools(events, adapter):
    tools = []
    for event in events:
        if adapter == 'codex' and event.get('type') == 'item.completed':
            item = event['item']
            if item['type'] == 'command_execution':
                tools.append({'tool': 'command', 'input': item['command'], 'status': item['status'], 'exit_code': item['exit_code'], 'output': item.get('aggregated_output', '')})
            elif item['type'] == 'file_change':
                tools.append({'tool': 'file_change', 'input': item['changes'], 'status': item['status'], 'output': ''})
        elif adapter == 'opencode' and event.get('type') == 'tool_use':
            part = event['part']
            state = part['state']
            tools.append({'tool': part['tool'], 'input': state.get('input'), 'status': state.get('status'), 'output': state.get('output', '')})
        elif adapter == 'antigravity' and event.get('event') == 'step_update':
            item = event['step_update']
            if item.get('step_type') == 'tool' and item.get('state') == 'DONE':
                info = item['tool_info']
                tools.append({'tool': item['tool_name'], 'input': info['parameters'], 'status': 'DONE', 'output': info.get('output', '')})
    return tools


def main():
    previous_summary = read(REPORT/'capability-summary.json') if (REPORT/'capability-summary.json').exists() else {}
    evidence = REPORT / 'evidence'
    evidence.mkdir(exist_ok=True)
    native = evidence / 'native'
    shutil.copytree(EXTERNAL / 'native-inventory-r3', native, dirs_exist_ok=True)
    summary, attempts = {}, []
    for directory in sorted(EXTERNAL.iterdir()):
        if not (directory / 'process.json').exists():
            continue
        target = evidence / 'probes' / directory.name
        target.mkdir(parents=True, exist_ok=True)
        for path in directory.iterdir():
            if path.is_file():
                shutil.copyfile(path, target / path.name)
        profile = read(directory / 'profile.json')
        process = read(directory / 'process.json')
        events = [json.loads(line) for line in (directory / 'stdout.jsonl').read_text(encoding='utf-8').splitlines() if line.startswith('{')]
        tools = event_tools(events, profile['adapter'])
        for item in tools:
            output = item.pop('output')
            item['output_excerpt'] = output[:160] + ('\n...\n' if len(output) > 360 else '') + (output[-200:] if len(output) > 360 else output[160:])
        save(target / 'tool-summary.json', tools)
        attempts.append({'probe': directory.name, 'model': profile['model'], **process,
                         'selected': directory.name in TARGETS.values(),
                         'terminal_usage': next((event.get('usage', event.get('result', {}).get('usage')) for event in reversed(events)
                                                 if event.get('type') == 'turn.completed' or event.get('event') == 'result'), None)})
        if profile['adapter'] == 'antigravity':
            restoration = {}
            for key, path in paths_for(Path.home()/'.gemini').items():
                original = directory / 'private-backup' / (key+'.original')
                restoration[key] = {'original_sha256': digest(original.read_bytes()) if original.exists() else None,
                                    'current_sha256': digest(path.read_bytes()) if path.exists() else None}
                assert restoration[key]['original_sha256'] == restoration[key]['current_sha256'], 'global settings changed after preparation'
            save(target / 'scope-restoration.json', {'restored': True, 'files': restoration})
        selected_name = next((name for name, probe in TARGETS.items() if probe == directory.name), None)
        if selected_name is None:
            continue
        workspace = directory / 'workspace'
        assert process['status'] == 'completed' and process['code'] == 0
        assert (workspace/'probe-output.txt').read_text().strip() == (workspace/'probe-input.txt').read_text().strip()
        assert 'Test Passed.' in (workspace/'build-host/Testing/Temporary/LastTest.log').read_text(errors='replace')
        assert list((workspace/'tests/__pycache__').glob('probe.*.pyc'))
        artifacts = {}
        for pattern in ('probe-input.txt', 'probe-output.txt', 'tests/probe.py', 'build-host/preparation_host.exe',
                        'build-host/Testing/Temporary/LastTest.log', 'build-idf/*.bin', 'build-idf/*.elf', 'build-idf/*.map',
                        'build-idf/bootloader/bootloader.bin', 'build-idf/partition_table/partition-table.bin'):
            for path in workspace.glob(pattern):
                name = path.relative_to(workspace).as_posix()
                copy = target / 'artifacts' / name
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, copy)
                artifacts[name] = digest(path.read_bytes())
        assert all(any(name.endswith(suffix) for name in artifacts) for suffix in ('.elf', '.map', 'bootloader.bin', 'partition-table.bin', 'preparation_fixture.bin'))
        capability = {'model': profile['model'], 'executed_profile_sha256': profile_digest(profile),
                      'probe': directory.name, 'process_seconds': process['elapsed'], 'artifact_sha256': artifacts,
                      'status': 'artifacts_and_raw_tool_events_available', 'operator_review_required': True}
        prior = previous_summary.get(selected_name, {})
        if all(prior.get(key) == capability[key] for key in ('probe','executed_profile_sha256','artifact_sha256')):
            capability.update(prior)  # Preserve a prior review only for identical execution/artifact evidence.
        save(target / 'capabilities.json', capability)
        summary[selected_name] = capability
    save(REPORT / 'capability-summary.json', summary)
    save(REPORT / 'preparation-attempts.json', {'attempts': attempts, 'total_process_seconds': sum(a['elapsed'] for a in attempts),
        'scope': 'Infrastructure only; includes rejected Opus, superseded hook-enabled Sol and superseded pre-tab-fix OpenCode; independent of product budgets.'})
    print(json.dumps({k: {'probe': v['probe'], 'artifacts': len(v['artifact_sha256'])} for k,v in summary.items()}))


if __name__ == '__main__':
    main()
