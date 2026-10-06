"""Fresh frozen-validator audit and host tests using the independent restoration."""
from datetime import datetime,timezone
from pathlib import Path
import copy,importlib.util,json,os,re,subprocess,sys,time,zipfile

PACK=Path('C:/meter-run-packages-20261006/codex-luna-r01-evaluation')
REST=Path('C:/meter-run-restores-20261006/codex-luna-r01-evaluation')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit-v1';OUT=REST/'post-restore-host-checks'
trusted=json.loads((PACK.parent/'codex-luna-r01-evaluation-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(OP/'operator-baseline.zip') as z:z.extractall(FROZEN)
sys.path.insert(0,str(FROZEN/'scripts'))
import benchmark
from benchmark_support import digest,read,save,verify_evidence
from operator_baseline import verify
from policy_review import validate_review
from evidence_package import verify_report_dependencies
assert digest((PACK/'package-manifest.json').read_bytes())==trusted
package=read(PACK/'package-manifest.json');m=read(OP/'run-manifest.json');f=read(OP/'operator-source-freeze.json')
for name,item in package['files'].items():
    p=PACK/name;b=Path('\\\\?\\'+str(p.resolve())).read_bytes()
    assert len(b)==item['bytes'] and digest(b)==item['sha256'],name
verify(m,OP);verify_evidence(m,OP);benchmark.verify_agent_inputs(OP,m);verify_report_dependencies(m,OP)
assert validate_review(m,OP/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit']
original=read(OP/'operator-observation/terminal-originals/run-manifest.json')
assert digest((OP/'operator-observation/terminal-originals/run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert original['measurement']==m['measurement']
for key,value in original['execution'].items():
    if key!='worktree':assert value==m['execution'][key],key
for name,item in f['sources'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert digest(raw)==item['sha256'] and len(raw)==item['bytes']
    if name!=m['outputs']['structured_result']:assert (CO/name).read_bytes().replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),name
for name,item in f['artifacts'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
    if name.endswith(('.bin','.elf')):assert (CO/name).read_bytes()==raw,name
assert not f['firmware_source_mutations_after_last_build'] and (CO/'build-idf/codex_desk_meter.elf').read_bytes()[:4]==b'\x7fELF'

slot=read(OP/'operator-observation/hardware-attempt-02/hardware-slot.json')
capture=read(OP/'operator-observation/hardware-attempt-02/reference-capture-r1/capture.json')
assert slot['upload_completed'] and slot['serial_closed_after_capture'] and slot['artifact_sha256']==f['artifacts']['build-idf/codex_desk_meter.bin']['sha256']
assert all(v['exit_code']==0 for v in slot['commands'])
assert [v['sequence'] for v in capture['frames']]==[0,1] and all(v['bytes_written']==v['bytes_requested']==1543 for v in capture['frames'])
assert (OP/'operator-observation/hardware-attempt-02/reference-capture-r1/device-serial.bin').stat().st_size==0
host=read(OP/'operator-observation/independent-host-checks/host-checks.json')
assert len(host['checks'])==4 and all(v['exit_code']==0 for v in host['checks'])
assert read(OP/'operator-observation/hardware-attempt-02/optical-observation-pending.json')['rm_review_applied'] is False
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,inventory_bytes_verified=True,
    immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,
    raw_candidate_source_files_verified=len(f['sources']),raw_candidate_artifacts_verified=len(f['artifacts']),
    candidate_artifact_source_binding_verified=True,host_checks_record_preserved=True,host_tests_repeated=False,
    original_run_or_checkout_path_used=False,operator_firmware_rebuild=False,hardware_upload_completed=True,
    receiver_acceptance='unconfirmed',serial_capture_bytes=0,current_upload_at=slot['upload_completed_at'],
    first_upload_logs_preserved=True,first_upload_target_association='unconfirmed_by_user_report',
    optical_status='user_report_black_screen',reference_review_applied=True,reference_status='fail',product_pass=False)
review=read(OP/'reference-review.json');ledger=read(OP/'comparison-ledger.json')
assert ledger['runs'][0]['reviewed'] and ledger['runs'][0]['reference_review_sha256']==digest((OP/'reference-review.json').read_bytes())
assert m['operator']['comparison']['reference_status']=='fail'
assert {k:v['status'] for k,v in review['items'].items()}=={'RM1':'partial','RM2':'partial','RM3':'fail','RM4':'not_run','RM5':'not_run'}
assert read(OP/'operator-observation/hardware-attempt-02/user-black-screen-report.json')['lcd_report']=='black screen only'
audit.update(rm_items={k:v['status'] for k,v in review['items'].items()},policy_status='invalid_for_comparison',
    additional_candidate_call_started=False,remaining_followup_seconds=7200,remaining_followup_rounds=3)
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps(audit))
