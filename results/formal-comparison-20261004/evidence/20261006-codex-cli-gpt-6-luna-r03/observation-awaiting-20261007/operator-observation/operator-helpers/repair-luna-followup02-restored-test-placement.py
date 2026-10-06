"""Restore an archived executable, preserving the first skipped-test audit."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
REST=Path('C:/meter-run-restores-20261007/codex-luna-followup02-pre-observation')
audit=Path('C:/meter-run-packages-20261007/verify-codex-luna-followup02-pre-observation.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copy2(audit,REST/'operator-audit-procedure-v1.py')
logs={p.name:sha(p) for p in (REST/'post-restore-host-checks').glob('*-*.txt')}
assert len(logs)==8
correction={'run_id':'20261006-codex-cli-gpt-6-luna-r03','recorded_at':datetime.now(timezone.utc).isoformat(),
    'original_audit_sha256':sha(audit),'original_host_logs':logs,'original_python_tests_run':22,'original_python_skipped_subcases':32,
    'cause':'Candidate result does not list build-host/meter_receiver_cli.exe as result evidence. Package preserves the exact binary under operator artifact-snapshot but checkout does not have the path required by own production tests.',
    'correction':'Materialize that same archived binary in the independent checkout, verify its frozen hash, repeat previously incomplete Python suite. Reuse the three already-passing C executable logs.',
    'original_source_modified':False,'firmware_rebuilt':False,'operator_receiver_implementation':False}
(REST/'operator-audit-artifact-placement-correction.json').write_text(json.dumps(correction,indent=2)+'\n',encoding='utf-8')
s=audit.read_text(encoding='utf-8').replace("FROZEN=REST/'frozen-operator-audit-v1';OUT=REST/'post-restore-host-checks'","FROZEN=REST/'frozen-operator-audit-v2';OUT=REST/'post-restore-host-checks-v2'")
old="""check('python-unit-tests',[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-v'])
for name in ['test_meter_parser','test_meter_state','test_idle_dim']:
    check(name,[OP/'operator-observation/artifact-snapshot/build-host'/(name+'.exe')])"""
new="""correction=read(REST/'operator-audit-artifact-placement-correction.json')
assert digest((REST/'operator-audit-procedure-v1.py').read_bytes())==correction['original_audit_sha256']
source=OP/'operator-observation/artifact-snapshot/build-host/meter_receiver_cli.exe'
target=CO/'build-host/meter_receiver_cli.exe'
assert digest(source.read_bytes())==f['artifacts']['build-host/meter_receiver_cli.exe']['sha256']
assert target.resolve().is_relative_to(CO.resolve()) and not target.exists()
target.parent.mkdir(parents=True,exist_ok=True);__import__('shutil').copy2(source,target)
assert target.read_bytes()==source.read_bytes()
save(OUT/'artifact-materialization.json',{'path':'build-host/meter_receiver_cli.exe','sha256':digest(target.read_bytes()),'source':'operator/operator-observation/artifact-snapshot/build-host/meter_receiver_cli.exe','candidate_source_modified':False,'rebuild':False})
check('python-unit-tests',[sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-v'])
for name in ['test_meter_parser','test_meter_state','test_idle_dim']:
    for suffix in ('stdout','stderr'):
        prior=REST/'post-restore-host-checks'/(name+'-'+suffix+'.txt')
        assert digest(prior.read_bytes())==correction['original_host_logs'][prior.name]
        __import__('shutil').copy2(prior,OUT/prior.name)
    checks.append({'name':name,'exit_code':0,'elapsed_seconds':None,'reused_original_passing_logs':True,'exit_status_basis':'First audit passed all four exit0 assertion before rejecting the skipped Python production cases.'})"""
assert old in s;s=s.replace(old,new)
s=s.replace('host_checks_completed=True,generated_bytecode_cache_not_loaded=True,','host_checks_completed=True,restored_host_executable_materialized=True,original_skipped_suite_preserved=True,generated_bytecode_cache_not_loaded=True,')
ast.parse(s)
Path('C:/meter-run-packages-20261007/verify-codex-luna-followup02-pre-observation-v2.py').write_text(s,encoding='utf-8')
