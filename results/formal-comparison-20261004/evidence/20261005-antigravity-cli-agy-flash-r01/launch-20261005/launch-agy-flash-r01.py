"""Recheck the prepared first AGY series and execute the unchanged frozen runner once."""
from datetime import datetime,timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

BASE=Path('C:/meter-operator-20261004')
RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
CO=RUN/'checkout'
RENEWAL=Path('C:/meter-preflight-20261005/renewal')
RECEIPT=RENEWAL/'agy-flash-receipt.json'
PRIVATE=Path('C:/meter-private-preflight-20261005/agy-flash-initial-scope')
OUT=RUN/'operator-launch-preflight'
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import KST,digest,read,save,verify_evidence
from operator_baseline import verify
from agy_pilot_environment import scoped_environment,verify_scoped_environment,paths_for,run_child,_OWNER_ENV

assert datetime.now(KST).strftime('%Y%m%d')=='20261005'
prior=Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
completion=read(prior/'operator-series-completion.json')
assert completion['derived_state']=='budget_exhausted' and not completion['additional_followup_allowed']
assert read(prior/'operator-observation/observation-finalization.json')['board_slot_released_for_next_candidate']
audit=read(Path('C:/meter-run-restores-20261005/opencode-muse-r02-final/frozen-validator-audit.json'))
assert audit['rm_review_completed'] and audit['inventory_bytes_verified'] and audit['frozen_operator_validators_used']
assert benchmark.git('rev-parse','HEAD',cwd=BASE)=='272875140d1998d458e26fdb2f6deab5e5d8f7b5'
assert benchmark.git('status','--porcelain',cwd=BASE)==''
m=read(RUN/'run-manifest.json');profile=read(RUN/'profile.json')
assert m['operator']['status']=='prepared' and m['execution']['started_at'] is None
assert m['execution']['timeout_seconds']==7200 and profile['model']=='gemini-3.8-flash-medium'
assert benchmark.git('status','--porcelain',cwd=CO)==''
assert benchmark.git('rev-parse','HEAD',cwd=CO)==m['operator']['local_base_commit']
benchmark.verify_agent_inputs(RUN,m);verify_evidence(m,RUN);verify(m,RUN)
benchmark.validate_preflight_receipt(read(RECEIPT),m,profile,RENEWAL)
assert digest(RECEIPT.read_bytes())=='68aa243049ba3750a47b70830e3deef3874c50f03bcc8e526ce66f24f11063cc'
env=os.environ.copy();env['AGY_CLI_DISABLE_AUTO_UPDATE']='true'
version=subprocess.check_output(profile['version_argv'],env=env,text=True,encoding='utf-8',timeout=30).strip()
assert version==profile['agent_version']
idf=subprocess.check_output([sys.executable,'C:/Espressif/v5.3.2/esp-idf/tools/idf.py','--version'],text=True,timeout=30).strip()
assert idf=='ESP-IDF v5.3.2'
tools={name:shutil.which(name) for name in ['cmake','ninja','git','xtensa-esp32s3-elf-gcc']}
assert all(tools.values()),tools
other=subprocess.check_output(['powershell','-NoProfile','-Command',
    "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^agy(\\.exe)?$|^opencode' }).Count"],text=True).strip()
assert other=='0','Another benchmark-capable AGY/OpenCode process is active.'
gemini=Path.home()/'.gemini';paths=paths_for(gemini)
before={key:digest(path.read_bytes()) if path.is_file() else None for key,path in paths.items()}
assert before==read(RENEWAL/'current/agy-restoration.json')['before'],'Global native files changed since receipt renewal.'
OUT.mkdir(exist_ok=False)
policy=BASE/'experiments/config/agy-pilot-permissions.json'
result=None
try:
    with scoped_environment(gemini,policy,PRIVATE,workspace=CO) as identity:
        scoped=verify_scoped_environment(gemini,policy,workspace=CO)
        for name,args in [('mcp',['mcp','list']),('plugins',['plugins','list']),('agents',['agents']),('models',['models'])]:
            p=subprocess.run([profile['version_argv'][0],*args],cwd=CO,env=env,capture_output=True,timeout=60)
            (OUT/(name+'-stdout.txt')).write_bytes(p.stdout);(OUT/(name+'-stderr.txt')).write_bytes(p.stderr)
            assert p.returncode==0,('Native inventory failed',name,p.returncode)
            if name!='models':assert p.stdout==(RENEWAL/('current/agy-'+name+'.txt')).read_bytes(),name
        assert profile['model'] in (OUT/'models-stdout.txt').read_text(encoding='utf-8')
        checked={'checked_at':datetime.now(timezone.utc).isoformat(),'run_id':RUN.name,'cli_version':version,'idf_version':idf,
                 'baseline_commit':m['execution']['base_commit'],'candidate_commit':m['operator']['local_base_commit'],
                 'immutable_input_files_verified':57,'receipt_sha256':digest(RECEIPT.read_bytes()),
                 'profile_sha256':m['execution']['profile_sha256'],'input_bundle_sha256':m['execution']['input_bundle_sha256'],
                 'scoped_settings_sha256':scoped,'policy_sha256':identity['policy_sha256'],
                 'instructions_absent':True,'hooks_absent':True,'global_files_before_sha256':before,
                 'mcp_plugins_custom_agents_clear':True,'model_catalog_selected_id_present':True,
                 'model_entitlement_retested':False,'capability_proof_date':'2026-10-04',
                 'read_isolation':'not_enforced','network_mode':'offline-fixture','tools':tools,
                 'candidate_hardware_access':False,'previous_series_budget_exhausted_and_fully_reviewed':True,
                 'model_invocations_during_preflight':0,'backup_private_outside_repository':str(PRIVATE)}
        save(OUT/'current-checks.json',checked)
        print(json.dumps({'launch_preflight':'passed','run_id':RUN.name,'model':profile['model'],'timeout_seconds':7200}),flush=True)
        child_env=env.copy();child_env[_OWNER_ENV]=identity['lock_token']
        result=run_child([sys.executable,'-B','-X','utf8',str(BASE/'scripts/benchmark.py'),'execute',
                          '--directory',str(RUN),'--receipt',str(RECEIPT)],child_env)
finally:
    after={key:digest(path.read_bytes()) if path.is_file() else None for key,path in paths.items()}
    save(OUT/'scope-exit.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'runner_exit_code':result,
                               'before_sha256':before,'after_sha256':after,'global_files_restored':before==after,
                               'owner_journal_present':(gemini/'.agy-pilot-owner.json').exists()})
    print(json.dumps({'scope_exit':'recorded','global_files_restored':before==after}),flush=True)
if result is None:raise RuntimeError('Runner did not start; inspect preflight failure.')
raise SystemExit(result)
