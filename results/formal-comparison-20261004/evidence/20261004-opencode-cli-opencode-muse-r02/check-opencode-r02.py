"""Independent post-timeout checks; does not edit candidate source or submission."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

RUN = Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
CO = RUN / 'checkout'
OUT = RUN / 'operator-observation'
OUT.mkdir(exist_ok=True)
sys.path.insert(0, 'C:/meter-operator-20261004/scripts')
from benchmark_support import digest, read, save
import benchmark

manifest = read(RUN / 'run-manifest.json')
freeze = read(RUN / 'operator-source-freeze.json')
benchmark.verify_agent_inputs(RUN, manifest)
checks = []

def run_check(name, argv, cwd=CO):
    started = time.monotonic()
    result = subprocess.run(argv, cwd=cwd, capture_output=True)
    (OUT / (name + '-stdout.txt')).write_bytes(result.stdout)
    (OUT / (name + '-stderr.txt')).write_bytes(result.stderr)
    checks.append({'name':name, 'argv':[str(a) for a in argv], 'exit_code':result.returncode,
                   'elapsed_seconds':time.monotonic()-started})
    return result

python_result = run_check('python-tests', [sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-v'])
for executable in sorted((CO / 'build-host-r02').glob('test_*.exe')):
    run_check(executable.stem, [str(executable)])
collector_result = run_check('legacy-collector', [sys.executable,'-B','-X','utf8','pc_tools/collector.py',
    '--fixture','gemini-cli-unsupported.json','--legacy-usage','personal-usage.json',
    '--reference-time','2026-09-30T18:40:49Z', '--out-payload',str(OUT/'candidate-collector-payload.json'),
    '--out-report',str(OUT/'candidate-collector-report.json')])
payload = read(OUT / 'candidate-collector-payload.json')
reference = Path('C:/meter-operator-20261004/experiments/reference/codex-7923f96')
frames = [json.loads(x) for x in (reference / 'expected-frames.jsonl').read_text(encoding='utf-8').splitlines()]
sys.path.insert(0, str(CO))
from pc_tools import sender
frames_check = []
for frame in frames:
    generated = sender.encode_frame(sender.build_frame(frame['payload'], frame['sequence'], frame['sent_at']))
    raw = (reference / 'expected-frames.jsonl').read_bytes().splitlines(keepends=True)[frame['sequence']]
    frames_check.append({'sequence':frame['sequence'],'candidate_encoder_matches_frozen_wire':generated==raw,
                         'sha256':digest(generated)})
normalization = {'usage':payload['usage'], 'global_resets':payload['global_resets']}
diag = {'run_id':manifest['run_id'],'checked_at':datetime.now(timezone.utc).isoformat(),
        'implementation_commit':freeze['commit'], 'collector_exit_code':collector_result.returncode,
        'collector_report':read(OUT/'candidate-collector-report.json'),
        'legacy_values':[{'provider_id':s['provider_id'],'agent_id':s['agent_id'],'stale':s['stale'],
                          'windows':[{'window_id':w['window_id'],'percent_remaining':w['percent_remaining']} for w in s['windows']]}
                         for s in payload['usage']],
        'normalization_matches_frozen_payload':normalization==frames[0]['payload'],
        'candidate_sender_emission_check':frames_check,
        'scope':'Actual collector CLI and sender encoder checked without serial. This is host evidence; real receiver and optical results are separate.'}
save(OUT/'common-stimulus-check.json', diag)
save(OUT/'host-checks.json', checks)
raw_events=[json.loads(x) for x in (RUN/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
firmware_mutations=[{'line':i+1,'timestamp':e['timestamp'],'tool':e['part']['tool'],'path':e['part']['state']['input'].get('filePath')}
                    for i,e in enumerate(raw_events) if e.get('type')=='tool_use' and e['part'].get('tool') in {'edit','write'}
                    and '/firmware/' in e['part']['state'].get('input',{}).get('filePath','').replace('\\','/')]
builds=[{'line':i+1,'timestamp':e['timestamp'],'output_contains_build_complete':'Project build complete' in e['part']['state'].get('output','')}
        for i,e in enumerate(raw_events) if e.get('type')=='tool_use' and e['part'].get('tool')=='bash'
        and e['part']['state'].get('input',{}).get('command')=='idf.py build']
assert builds and builds[-1]['output_contains_build_complete']
assert all(e['timestamp'] < builds[-1]['timestamp'] for e in firmware_mutations)
save(OUT/'build-source-review.json', {'run_id':manifest['run_id'],'implementation_commit':freeze['commit'],
     'firmware_mutations':firmware_mutations,'firmware_build_events':builds,
     'no_candidate_firmware_mutation_after_successful_build':True,
     'source_sha256':{p.relative_to(CO).as_posix():digest(p.read_bytes()) for p in (CO/'firmware').rglob('*') if p.is_file()
                      and 'build' not in p.relative_to(CO/'firmware').parts and p.suffix in {'.c','.h'}},
     'scope':'Raw candidate build log and source mutations bind the preserved artifact to the final firmware source; no operator rebuild.'})
assert subprocess.check_output(['git','status','--porcelain'],cwd=CO,text=True).strip()==''
benchmark.verify_agent_inputs(RUN,manifest)
print(json.dumps({'checks':checks,'normalization_matches_frozen_payload':diag['normalization_matches_frozen_payload'],
                   'candidate_emission_matches':all(x['candidate_encoder_matches_frozen_wire'] for x in frames_check),
                   'legacy_values':diag['legacy_values'],'source_and_input_unchanged':True},ensure_ascii=False,indent=2))
