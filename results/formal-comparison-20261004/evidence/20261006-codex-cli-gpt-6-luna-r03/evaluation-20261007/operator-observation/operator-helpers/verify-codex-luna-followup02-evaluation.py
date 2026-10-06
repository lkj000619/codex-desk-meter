"""Verify final restoration and preserved test records with its frozen validators."""
from pathlib import Path
import json, sys, zipfile
PACK=Path('C:/meter-run-packages-20261007/codex-luna-followup02-evaluation')
REST=Path('C:/meter-run-restores-20261007/codex-luna-followup02-evaluation')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit-v1';OBS=OP/'operator-observation'
trusted=json.loads((PACK.parent/'codex-luna-followup02-evaluation-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
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
assert validate_review(m,OP/'run-manifest.json')['decision']['status']=='eligible'
assert benchmark.git('rev-parse','HEAD',cwd=CO)==f['commit']
original=read(OBS/'terminal-originals/run-manifest.json')
assert digest((OBS/'terminal-originals/run-manifest.json').read_bytes())==f['original_terminal_manifest_sha256']
assert original['measurement']==m['measurement'] and m['measurement']['tokens']['total'] is None
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

slot=read(OBS/'hardware-slot.json');runtime=read(OBS/'hardware-post-upload-reset/runtime-source-binding.json')
assert slot['upload_completed'] and slot['serial_closed_after_capture'] and slot['artifact_sha256']==f['artifacts']['build/codex_desk_meter.bin']['sha256']
assert slot['board_mac']=='28:84:85:B0:85:18' and slot['flash_images_hash_verified']==3 and all(x['exit_code']==0 for x in slot['commands'])
assert (OBS/'reference-capture-r1/device-serial.bin').stat().st_size==86
raw=(OBS/'hardware-post-upload-reset/reset-and-frames-capture/device-serial.bin').read_bytes()
assert len(raw)==5732 and digest(raw)==runtime['raw_log_sha256'] and digest(elf)==runtime['elf_sha256']
assert runtime['boot_elf_sha_prefix_matches'] and runtime['psram_memory_test_ok'] and runtime['usb_receiver_ready_observed']
assert b'217445082' in raw and b'esp_psram: SPI SRAM memory test OK' in raw
assert runtime['serial_closed'] and runtime['host_writes_completed_sequences']==[0,1] and runtime['receiver_accepted_sequences']==[]
host=read(OBS/'independent-host-checks/host-checks.json');common=read(OBS/'independent-host-checks/common-stimulus-check.json')
assert len(host['checks'])==6 and all(x['exit_code']==0 for x in host['checks']) and host['python_tests_passed']==22
py=(OBS/'independent-host-checks/python-unit-tests-stderr.txt').read_text(encoding='utf-8')
assert 'Ran 22 tests' in py and 'skipped=' not in py and '... skipped ' not in py
assert common['encoder_matches_exact_common_frames'] and common['legacy_collector']['matches_common_reference_payload']
assert len(common['provider_fixture_checks'])==17 and all(x['matches_expected_validity'] for x in common['provider_fixture_checks'])
assert common['production_c_accepts_common_sequences']==[0,1] and not common['frozen_operator29_pipeline_completed']
placement=read(OBS/'pre-observation-operator-audit-artifact-placement-correction.json')
assert placement['original_audit_sha256']==digest((OBS/'pre-observation-operator-audit-procedure-v1.py').read_bytes())
assert placement['original_python_skipped_subcases']==32 and not placement['original_source_modified'] and not placement['firmware_rebuilt']
for name,sha in placement['original_host_logs'].items():
    assert digest((OBS/'operator-first-audit-host-logs'/name).read_bytes())==sha
    if not name.startswith('python-'):assert digest((OBS/'independent-host-checks'/name).read_bytes())==sha
policy=read(OBS/'operator-policy-procedure-output-correction.json')
assert policy['procedure_sha256']==digest((OBS/'operator-helpers/review-codex-luna-followup-02-policy.py').read_bytes())
assert policy['actual_decision_sha256']==digest((OP/'operator-policy-decision.json').read_bytes())
assert policy['corrected_summary']['policy_status']=='eligible' and policy['corrected_summary']['commands_reviewed']==129
native=read(OBS/'native-terminal-failure-review.json')
assert original['operator']['status']==m['operator']['status']=='environment_failed' and native['tokens']==m['measurement']['tokens']
assert native['stdout_sha256']==digest((OBS/'terminal-originals/stdout.jsonl').read_bytes())
video=read(OBS/'user-video-01/video-metadata.json');visual=read(OBS/'user-video-01/video-review.json')
assert video['source_sha256']==visual['video_sha256']==digest((OBS/'user-video-01/source.mp4').read_bytes())
assert video['duration_seconds']==38.55 and len(video['sample_frames'])==39
for item in video['sample_frames']:assert digest((OBS/'user-video-01'/item['path']).read_bytes())==item['sha256']
user=read(OBS/'user-observation-confirmation.json')
assert user['button_answer_original']=='BOOT와 RESET 모두 누름' and user['user_manual_reset'] is True
assert visual['lcd_output_present'] and not visual['normal_readable_screen_observed'] and not visual['continuous_30_seconds_verified']
review=read(OP/'reference-review.json');ledger=read(OP/'comparison-ledger.json')
assert len(ledger['runs'])==3 and all(x['reviewed'] for x in ledger['runs'])
assert ledger['runs'][0]['implementation_commit']=='c0d5d61160664923e0494302fae180089d02d247'
assert ledger['runs'][1]['implementation_commit']=='e68356829715793dc31dd188bc2a9f528f6fcbd2'
assert ledger['runs'][-1]['reference_review_sha256']==digest((OP/'reference-review.json').read_bytes())
assert m['operator']['comparison']['reference_status']=='fail' and review['policy_status']=='eligible' and not review['product_pass']
rm={k:v['status'] for k,v in review['items'].items()}
assert rm=={'RM1':'pass','RM2':'partial','RM3':'fail','RM4':'fail','RM5':'not_run'}
remaining=7200-sum(x['elapsed_seconds'] for x in ledger['runs'][1:])
assert abs(remaining-2965.735)<0.00001
final=read(OBS/'observation-finalization.json')
assert final['remaining_followup_seconds']==remaining and final['remaining_followup_rounds']==1
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,inventory_bytes_verified=True,
    immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,raw_candidate_source_files_verified=38,
    raw_candidate_artifacts_verified=20,candidate_artifact_source_binding_verified=True,host_checks_record_preserved=True,
    host_tests_repeated=False,original_run_or_checkout_path_used=False,operator_firmware_rebuild=False,hardware_upload_completed=True,
    receiver_acceptance='unconfirmed',first_serial_capture_bytes=86,serial_capture_bytes=5732,current_upload_at=slot['upload_completed_at'],
    application_boot_observed=True,psram_memory_test_ok_observed=True,usb_receiver_ready_observed=True,
    optical_status='video_rotated_duplicated_clipped_text',video_sha256=video['source_sha256'],video_duration_seconds=38.55,
    user_manual_reset=True,normal_readable_screen_observed=False,reference_review_applied=True,reference_status='fail',
    product_pass=False,rm_items=rm,policy_status='eligible',series_policy_status='invalid_for_comparison',
    additional_candidate_call_started=False,remaining_followup_seconds=remaining,remaining_followup_rounds=1)
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps(audit))
