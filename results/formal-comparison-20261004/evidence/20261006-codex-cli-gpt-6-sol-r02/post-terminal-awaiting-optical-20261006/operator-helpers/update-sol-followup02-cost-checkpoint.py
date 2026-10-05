"""Generate a new checkpoint from unique actual invocations, using dated correction."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004'
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read,save,digest
ledgers=[Path('C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-flash-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-pro-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-codex-cli-gpt-6-sol-r01.json')]
inputs=[]
for ledger in ledgers:
    for run in read(ledger)['runs']:
        assert run['status'] in {'completed','timeout','aborted','environment_failed'}
        path=Path(run['directory'])/'run-manifest.json'
        if run['run_id']=='20261005-codex-cli-gpt-6-sol-r01':path=Path('C:/meter-policy-corrections-20261006/codex-sol-initial/run-manifest.json')
        inputs.append(path)
assert len(inputs)==11 and len({read(p)['run_id'] for p in inputs})==11
assert (Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02')/'policy-review.json').exists()
output=FORMAL/'comparison-checkpoint-10.md';assert not output.exists()
subprocess.run([sys.executable,'-B','-X','utf8','C:/meter-operator-20261004/scripts/summarize-benchmark.py',
    *map(str,inputs),'--output',str(output)],check=True)
body=output.read_text(encoding='utf-8')
header='2026-10-06 checkpoint10: Sol 후속 2회차 종료 후 후보11회 비용 집계다. 최초 정책의 [날짜 있는 정정](evidence/20261005-codex-cli-gpt-6-sol-r01/policy-correction-20261006/correction-note.json)을 반영하며 최초 eligible review·원본 비용·package와 checkpoint08/09를 보존한다. 현재 후속2의 광학/RM 평가는 대기이며 전체 실험이나 제품 합격을 뜻하지 않는다. 품질 부적격 호출도 실제 비용은 포함한다.\n\n'
assert body.startswith('# Benchmark results\n')
output.write_text(body.replace('# Benchmark results\n\n','# Benchmark results\n\n'+header,1),encoding='utf-8')
total=sum(read(p)['measurement']['tokens']['total'] for p in inputs)
save(Path('C:/meter-followups-20261006/sol-followup02-cost-checkpoint-inputs.json'),{'unique_attempts':11,
    'total_normalized_tokens':total,'input_manifests':[{'path':str(p),'run_id':read(p)['run_id'],'sha256':digest(p.read_bytes())} for p in inputs],
    'checkpoint':output.relative_to(ROOT).as_posix(),'checkpoint_sha256':digest(output.read_bytes()),
    'original_snapshots_and_cost_definitions_unchanged':True,'current_rm_waiting_for_optical_observation':True})
print(json.dumps({'unique_attempts':11,'normalized_tokens_all_attempts':total,'checkpoint':str(output)}))
