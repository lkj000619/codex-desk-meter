"""Fresh non-model checks followed by one unchanged-runner Codex followup call."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import queue
import shutil
import subprocess
import sys
import threading

BASE = Path('C:/meter-operator-20261004')
ROOT = Path('C:/Users/\uC774\uAD11\uC9C4/orca/codex-desk-meter')
RUN = Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03')
CO = RUN / 'checkout'
RENEWAL = Path('C:/meter-preflight-20261006/luna-initial')
SOURCE_RECEIPT = RENEWAL / 'luna-launch-receipt.json'
RECEIPT = RENEWAL / 'luna-followup02-launch-receipt.json'
OUT = RUN / 'operator-launch-preflight'
sys.path.insert(0, str(BASE / 'scripts'))
import benchmark
from benchmark_support import KST, digest, read, save, verify_evidence
from operator_baseline import verify

assert datetime.now(KST).strftime('%Y%m%d') == '20261006'
assert benchmark.git('rev-parse', 'HEAD', cwd=BASE) == '272875140d1998d458e26fdb2f6deab5e5d8f7b5'
assert not benchmark.git('status', '--porcelain', cwd=BASE)
previous_path = ROOT / 'results/formal-comparison-20261004/progress.json'
previous_bytes = previous_path.read_bytes()
previous = json.loads(previous_bytes)
assert previous['state'] == 'codex_luna_followup_01_reviewed_black_screen'
assert previous['product_executions_started'] == previous['product_executions_completed'] == 13
assert previous['remaining_current_series_followup_rounds'] == 2
assert read(Path('C:/meter-run-restores-20261006/codex-luna-followup01-evaluation/frozen-validator-audit.json'))['reference_review_applied']
m = read(RUN / 'run-manifest.json'); profile = read(RUN / 'profile.json')
ledger = read(Path(m['operator']['comparison']['ledger']))
assert m['operator']['status'] == 'prepared' and m['execution']['started_at'] is None
assert m['execution']['timeout_seconds'] == 4213 and profile['model'] == 'gpt-6-luna' and profile['reasoning'] == 'max'
assert len(ledger['runs']) == 3 and all(r['reviewed'] for r in ledger['runs'][:2]) and ledger['runs'][2]['status'] == 'prepared' and ledger['runs'][2]['round'] == 2
assert not benchmark.git('status', '--porcelain', cwd=CO)
assert benchmark.git('rev-parse', 'HEAD', cwd=CO) == m['operator']['local_base_commit']
cleanup=read(RUN/'operator-source-preparation.json')
assert cleanup['inherited_generated_files']==0 and len(cleanup['product_source_verified'])==33 and cleanup['model_calls_during_preparation']==0
assert all(not (CO/n).exists() for n in ('build','build-host','build-idf','sdkconfig'))
benchmark.verify_agent_inputs(RUN, m); verify_evidence(m, RUN); verify(m, RUN)
source = read(SOURCE_RECEIPT)
benchmark.validate_preflight_receipt(source, m, profile, RENEWAL)
version = subprocess.check_output(profile['version_argv'], text=True, encoding='utf-8', timeout=30).strip()
assert version == profile['agent_version']
idf = subprocess.check_output([sys.executable, 'C:/Espressif/v5.3.2/esp-idf/tools/idf.py', '--version'], text=True, timeout=30).strip()
assert idf == 'ESP-IDF v5.3.2'
available = {n: shutil.which(n) for n in ('cmake','ninja','git','xtensa-esp32s3-elf-gcc')}
assert all(available.values())
assert not (Path.home()/'.gemini/.agy-pilot-owner.json').exists()
OUT.mkdir(exist_ok=False)
opts = []
for i, arg in enumerate(profile['argv']):
    if arg in ('-c','--enable','--disable'): opts += [arg, profile['argv'][i+1]]
exe = profile['version_argv'][0]
# Same limited native inventory method as the frozen preparation. No model turn.
with (OUT/'codex-server-stderr.txt').open('xb') as err:
    server = subprocess.Popen([exe,*opts,'app-server'], cwd=CO, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=err, text=True, encoding='utf-8')
    messages = queue.Queue()
    def reader():
        for line in server.stdout:
            try: messages.put(json.loads(line))
            except ValueError: messages.put({'inventory_parse_error':True})
    threading.Thread(target=reader, daemon=True).start()
    def request(identity, method, params):
        server.stdin.write(json.dumps({'id':identity,'method':method,'params':params})+'\n');server.stdin.flush()
        while True:
            value=messages.get(timeout=40)
            assert not value.get('inventory_parse_error')
            if value.get('id')==identity:
                assert 'error' not in value,value.get('error')
                return value['result']
    try:
        request(1,'initialize',{'clientInfo':{'name':'comparison-preparation-inventory','version':'1.0'},'capabilities':{}})
        value=request(2,'skills/list',{'cwds':[str(CO)],'forceReload':True})
        skills=[{k:s.get(k) for k in ('name','scope','enabled','path','pluginId')} for entry in value['data'] for s in entry['skills']]
        save(OUT/'codex-skills.json',{'source':'native skills/list, same skills/feature overrides; app-server config layer differs from exec --ignore-user-config','skills':skills})
    finally:
        server.terminate();server.wait(timeout=10)
features=subprocess.run([exe,*opts,'features','list'],capture_output=True,text=True,timeout=30)
assert features.returncode==0
(OUT/'codex-features.txt').write_text(features.stdout,encoding='utf-8')
(OUT/'codex-features-stderr.txt').write_text(features.stderr,encoding='utf-8')
for name in ('codex-skills.json','codex-features.txt'):
    assert (OUT/name).read_bytes()==(RENEWAL/'current/native'/name).read_bytes(),'Native settings changed: '+name
hook_path=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'hooks.json'
hooks=read(hook_path) if hook_path.exists() else {}
save(OUT/'codex-hook-inventory.json',{'source_path':str(hook_path),'exists':hook_path.exists(),
    'source_sha256':digest(hook_path.read_bytes()) if hook_path.exists() else None,
    'configured_events':list(hooks.get('hooks',{})),'comparison_override':'features.hooks=false'})
assert '--ignore-user-config' in profile['argv'] and '--ignore-rules' in profile['argv'] and '--ephemeral' in profile['argv']
assert all(['--disable',n] == profile['argv'][i:i+2] for n in ('plugins','remote_plugin','apps','memories','hooks') for i in [profile['argv'].index(n)-1])
now=datetime.now(timezone.utc).isoformat()
save(OUT/'current-checks.json',{'checked_at':now,'run_id':RUN.name,'round':2,'cli_version':version,'idf_version':idf,
    'baseline_commit':m['execution']['base_commit'],'candidate_commit':m['operator']['local_base_commit'],
    'immutable_input_files_verified':57,'profile_sha256':m['execution']['profile_sha256'],
    'input_bundle_sha256':m['execution']['input_bundle_sha256'],'original_capability_receipt_sha256':digest(SOURCE_RECEIPT.read_bytes()),
    'native_settings_match_frozen_preparation':True,'model':'gpt-6-luna','reasoning':'max',
    'hooks_disabled':True,'plugins_apps_memories_disabled':True,'fresh_ephemeral_exec':True,
    'app_server_inventory_scope_note':'Same feature/skill overrides; app-server user config layer differs from exec. Inventory does not prove the exec effective model or settings.',
    'model_entitlement_retested':False,'capability_proof_date':'2026-10-04','model_invocations_during_preflight':0,
    'tools':available,'read_isolation':'not_enforced','network_mode':'offline-fixture','candidate_hardware_access':False,
    'previous_evaluation_and_preservation_complete':True,'global_files_changed':False})
save(RUN/'operator-next-model-decision.json',{'recorded_at':now,'user_instruction':'추가 실험 진행 요청. lcd 화면이 나올 때까지. 하지만 남은 후속 70분13초·최대2회 안에서',
    'authorized_model':'gpt-6-luna','authorized_run_id':RUN.name,'round':2,'previous_run_id':previous['current_run'],
    'previous_frozen_commit':previous['implementation_commit'],'previous_progress_sha256':digest(previous_bytes),
    'source_cleanup_sha256':digest((RUN/'operator-source-preparation.json').read_bytes()),
    'remaining_rounds_including_this':2,'remaining_seconds_including_this':4213,
    'scope':'User authorizes remaining Luna followups until visible LCD output within4213seconds and at most2additional rounds; this is round2, under unchanged frozen comparison contract. Observations only; no operator diagnostic repair method, new reference or other candidate implementation. Muse/Pro/Sol closed, Flash deferred; initial original policy invalid and all prior results preserved.'})
(RUN/'previous-progress-at-transition.json').write_bytes(previous_bytes)
relative='current/codex-luna-followup02-20261006';fresh=RENEWAL/relative;fresh.mkdir(exist_ok=False)
receipt=dict(source,checked_at=now,launch_run_id=RUN.name);receipt['evidence']=dict(source['evidence'])
for path in OUT.iterdir():
    if path.is_file():shutil.copy2(path,fresh/path.name);receipt['evidence'][relative+'/'+path.name]=digest(path.read_bytes())
shutil.copy2(RUN/'operator-next-model-decision.json',fresh/'operator-next-model-decision.json')
receipt['evidence'][relative+'/operator-next-model-decision.json']=digest((fresh/'operator-next-model-decision.json').read_bytes())
assert not RECEIPT.exists();save(RECEIPT,receipt)
benchmark.validate_preflight_receipt(receipt,m,profile,RENEWAL)
assert datetime.now(KST).strftime('%Y%m%d')=='20261006','Date changed before followup call; preserve preparation, do not invoke this reservation.'
print(json.dumps({'launch_preflight':'passed','run_id':RUN.name,'model':profile['model'],'timeout_seconds':4213,'receipt_sha256':digest(RECEIPT.read_bytes())}),flush=True)
result=subprocess.run([sys.executable,'-B','-X','utf8',str(BASE/'scripts/benchmark.py'),'run',str(RUN),'--receipt',str(RECEIPT)])
save(OUT/'runner-exit.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'runner_exit_code':result.returncode,'global_files_changed':False})
raise SystemExit(result.returncode)
