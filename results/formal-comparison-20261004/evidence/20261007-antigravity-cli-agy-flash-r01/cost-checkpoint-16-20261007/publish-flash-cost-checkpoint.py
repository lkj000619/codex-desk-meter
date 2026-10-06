"""Snapshot terminal attempts only; keep missing usage null and old checkpoints immutable."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,subprocess,sys
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004';BASE=Path('C:/meter-operator-20261004')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import read,save,digest
count=int(sys.argv[1]);RUN=Path(sys.argv[2]);checkpoint=FORMAL/('comparison-checkpoint-%02d.md'%count)
assert not checkpoint.exists()
ledgers=[Path(s) for s in (
 'C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json',
 'C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-flash-r01.json',
 'C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-pro-r01.json',
 'C:/meter-runs-20261005/ledgers/20261005-codex-cli-gpt-6-sol-r01.json',
 'C:/meter-runs-20261006/ledgers/20261006-codex-cli-gpt-6-luna-r01.json')]
inputs=[]
for ledger in ledgers:
 for entry in read(ledger)['runs']:
  if entry['status'] not in {'completed','timeout','aborted','environment_failed'}:continue
  source=Path(entry['directory'])/'run-manifest.json'
  if entry['run_id']=='20261005-codex-cli-gpt-6-sol-r01':source=Path('C:/meter-policy-corrections-20261006/codex-sol-initial/run-manifest.json')
  assert read(source)['operator']['status']==entry['status'];inputs.append(source)
assert len(inputs)==len({read(p)['run_id'] for p in inputs})==count
known=[read(p)['measurement']['tokens']['total'] for p in inputs if read(p)['measurement']['tokens']['total'] is not None]
assert len(known)==count-1
subprocess.run([sys.executable,'-B','-X','utf8',BASE/'scripts/summarize-benchmark.py',*inputs,'--output',checkpoint],check=True,capture_output=True)
header=('2026-10-07 checkpoint%d: 종료된%d회만 집계한다. 알려진 정규화 합계%s token·coverage%d/%d, 전체 합계 미상(null). '
 'Luna 후속2 token 미계측과 과거 정책·실패 비용을 보존한다. 실행 중 호출은 최종 비용에 포함하지 않는다. '
 'Flash 추가 후속의 권한 거부는 environment_failed이며, 새 펌웨어 부재를 이전 보드 동작으로 대체하지 않는다.\n\n')%(count,count,format(sum(known),','),len(known),count)
body=checkpoint.read_text(encoding='utf-8');assert body.startswith('# Benchmark results\n\n')
checkpoint.write_text(body.replace('# Benchmark results\n\n','# Benchmark results\n\n'+header,1),encoding='utf-8')
PUBLIC=FORMAL/'evidence'/RUN.name/('cost-checkpoint-%02d-20261007'%count);PUBLIC.mkdir(parents=True,exist_ok=False)
copies=[]
for n,source in enumerate(inputs,1):
 name='cost-inputs/%02d-%s.json'%(n,read(source)['run_id']);dest=PUBLIC/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
 copies.append({'original_path':str(source),'snapshot_path':name,'run_id':read(source)['run_id'],'sha256':digest(source.read_bytes())})
save(PUBLIC/'cost-checkpoint-inputs.json',{'unique_attempts':count,'token_measurement_coverage':'%d/%d'%(len(known),count),
 'total_normalized_tokens':None,'known_normalized_tokens':sum(known),'input_manifests':copies,
 'checkpoint':checkpoint.relative_to(ROOT).as_posix(),'checkpoint_sha256':digest(checkpoint.read_bytes()),'original_cost_definitions_unchanged':True})
shutil.copy2(checkpoint,PUBLIC/'checkpoint-original.md');shutil.copy2(Path(__file__),PUBLIC/Path(__file__).name)
save(PUBLIC/'snapshot-inventory.json',{'run_id':RUN.name,'captured_at':datetime.now(timezone.utc).isoformat(),
 'files':{p.relative_to(PUBLIC).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in PUBLIC.rglob('*') if p.is_file()},
 'scope':'Dated cost supplement; original terminal/evaluation/package records remain unchanged.'})
p=read(FORMAL/'progress.json');p.update(cost_checkpoint=checkpoint.relative_to(ROOT).as_posix(),cost_checkpoint_covers_completed_invocations=count,
 cost_checkpoint_covers_completed_executions=count,known_normalized_tokens_all_attempts=sum(known),total_normalized_tokens_all_attempts=None,
 token_measurement_coverage='%d/%d'%(len(known),count))
save(FORMAL/'progress.json',p)
print(json.dumps({'terminal_attempts':count,'known_tokens':sum(known),'coverage':'%d/%d'%(len(known),count),'current_state':p['state']}))
