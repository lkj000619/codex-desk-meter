"""Verify final restoration and preserved test records with its frozen validators."""
from pathlib import Path
import json, sys, zipfile
PACK=Path('C:/meter-run-packages-20261006/codex-luna-followup01-evaluation')
REST=Path('C:/meter-run-restores-20261006/codex-luna-followup01-evaluation')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit-v1';OBS=OP/'operator-observation'
trusted=json.loads((PACK.parent/'codex-luna-followup01-evaluation-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
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
    raw=Path('\\\\?\\'+str((PACK/name).resolve())).read_bytes()
    assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
verify(m,OP);verify_evidence(m,OP);benchmark.verify_agent_inputs(OP,m);verify_report_dependencies(m,OP)
assert validate_review(m,OP/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit']
original=read(OBS/'terminal-originals/run-manifest.json')
assert digest((OBS/'terminal-originals/run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert original['measurement']==m['measurement'] and m['measurement']['tokens']['total']==13414031
for key,value in original['execution'].items():
    if key!='worktree':assert value==m['execution'][key],key
for name,item in f['sources'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256']
    if name!=m['outputs']['structured_result']:assert (CO/name).read_bytes().replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),name
for name,item in f['artifacts'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256']
    if name.endswith(('.bin','.elf')):assert (CO/name).read_bytes()==raw,name
assert len(f['sources'])==38 and len(f['artifacts'])==20 and not f['firmware_source_mutations_after_last_build']
elf=(CO/'build/codex_desk_meter.elf').read_bytes();assert elf[:4]==b'\x7fELF'
slot=read(OBS/'hardware-slot.json');capture=read(OBS/'reference-capture-r1/capture.json')
assert slot['upload_completed'] and slot['serial_closed_after_capture'] and slot['artifact_sha256']==f['artifacts']['build/codex_desk_meter.bin']['sha256']
assert slot['board_mac']=='28:84:85:B0:85:18' and slot['flash_images_hash_verified']==3 and all(v['exit_code']==0 for v in slot['commands'])
assert [v['sequence'] for v in capture['frames']]==[0,1] and all(v['bytes_written']==v['bytes_requested']==1543 for v in capture['frames'])
assert (OBS/'reference-capture-r1/device-serial.bin').stat().st_size==0
runtime=read(OBS/'hardware-post-upload-reset/runtime-source-binding.json')
raw=(OBS/'hardware-post-upload-reset/reset-and-frames-capture/device-serial.bin').read_bytes()
assert len(raw)==5938 and digest(raw)==runtime['raw_log_sha256'] and digest(elf)==runtime['elf_sha256']
assert runtime['boot_elf_sha_prefix_matches'] and runtime['usb_receiver_ready_observed'] and b'81c1bd1d2' in raw and b'SPI SRAM memory test OK' in raw
assert runtime['host_writes_completed_sequences']==[0,1] and runtime['serial_closed'] and not runtime['receiver_accepted_sequences'] and not runtime['receiver_rejected_errors']
correction=read(OBS/'hardware-post-upload-reset/runtime-observation-correction.json')
assert correction['corrected_value'] is True and correction['original_record_sha256']==digest((OBS/'hardware-post-upload-reset/runtime-source-binding.json').read_bytes())
host=read(OBS/'independent-host-checks/host-checks.json');common=read(OBS/'independent-host-checks/common-stimulus-check.json')
assert len(host['checks'])==6 and all(v['exit_code']==0 for v in host['checks'])
assert 'Ran 22 tests' in (OBS/'independent-host-checks/python-unit-tests-stderr.txt').read_text(encoding='utf-8')
assert common['encoder_matches_exact_common_frames'] and common['legacy_collector']['matches_common_reference_payload']
assert len(common['provider_fixture_checks'])==17 and all(v['matches_expected_validity'] for v in common['provider_fixture_checks'])
assert common['production_c_accepts_common_sequences']==[0,1] and not common['frozen_operator29_pipeline_completed']
guard=read(OBS/'pre-observation-operator-audit-guard-correction.json')
assert guard['original_audit_sha256']==digest((OBS/'pre-observation-operator-audit-procedure-v1.py').read_bytes())
for name,sha in guard['original_host_logs'].items():
    assert digest((OBS/'operator-first-audit-host-logs'/name).read_bytes())==sha==digest((OBS/'independent-host-checks'/name).read_bytes())
review=read(OP/'reference-review.json');ledger=read(OP/'comparison-ledger.json')
assert len(ledger['runs'])==2 and ledger['runs'][0]['reviewed'] and ledger['runs'][0]['implementation_commit']=='c0d5d61160664923e0494302fae180089d02d247'
assert ledger['runs'][-1]['reviewed'] and ledger['runs'][-1]['reference_review_sha256']==digest((OP/'reference-review.json').read_bytes())
assert m['operator']['comparison']['reference_status']=='fail'
rm={k:v['status'] for k,v in review['items'].items()};assert rm=={'RM1':'pass','RM2':'partial','RM3':'fail','RM4':'not_run','RM5':'not_run'}
user=read(OBS/'user-black-screen-report.json');assert user['user_answer_original']=='검은 화면이 계속됨' and user['boot_press_count'] is None and user['continuous_30_seconds_observed'] is None
final=read(OBS/'observation-finalization.json');assert final['remaining_followup_seconds']==4213 and final['remaining_followup_rounds']==2
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,inventory_bytes_verified=True,
    immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,raw_candidate_source_files_verified=38,
    raw_candidate_artifacts_verified=20,candidate_artifact_source_binding_verified=True,host_checks_record_preserved=True,
    host_tests_repeated=False,original_run_or_checkout_path_used=False,operator_firmware_rebuild=False,hardware_upload_completed=True,
    receiver_acceptance='unconfirmed',first_serial_capture_bytes=0,serial_capture_bytes=5938,current_upload_at=slot['upload_completed_at'],
    application_boot_observed=True,psram_memory_test_ok_observed=True,usb_receiver_ready_observed=True,
    optical_status='user_report_black_screen',reference_review_applied=True,reference_status='fail',product_pass=False,
    rm_items=rm,policy_status='invalid_for_comparison',additional_candidate_call_started=False,
    remaining_followup_seconds=4213,remaining_followup_rounds=2)
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps(audit))
