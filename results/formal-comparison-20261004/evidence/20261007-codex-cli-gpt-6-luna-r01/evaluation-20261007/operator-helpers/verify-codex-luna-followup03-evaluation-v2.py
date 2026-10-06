"""Verify final restoration and preserved test records with its frozen validators."""
from pathlib import Path
import json, re, sys, zipfile
PACK=Path('C:/meter-run-packages-20261007/codex-luna-followup03-evaluation')
REST=Path('C:/meter-run-restores-20261007/codex-luna-followup03-evaluation')
OP=REST/'operator';CO=REST/'checkout';FROZEN=REST/'frozen-operator-audit-v1';OBS=OP/'operator-observation'
trusted=json.loads((PACK.parent/'codex-luna-followup03-evaluation-create.json').read_text(encoding='utf-8'))['package_manifest_sha256']
FROZEN.mkdir(exist_ok=True)
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
assert original['measurement']==m['measurement'] and m['measurement']['tokens']['total']==4090978
for key,value in original['execution'].items():
    if key!='worktree':assert value==m['execution'][key],key
for name,item in f['sources'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256']
    if name!=m['outputs']['structured_result']:assert (CO/name).read_bytes().replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),name
for name,item in f['artifacts'].items():
    raw=(OP/item['operator_raw_copy']).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256']
    if name.endswith(('.bin','.elf')):assert (CO/name).read_bytes()==raw,name
assert len(f['sources'])==37 and len(f['artifacts'])==20 and not f['firmware_source_mutations_after_last_build']
elf=(CO/'build/codex_desk_meter.elf').read_bytes();assert elf[:4]==b'\x7fELF'

slot=read(OBS/'hardware-slot.json');runtime=read(OBS/'hardware-post-upload-reset/runtime-source-binding.json')
assert slot['upload_completed'] and slot['serial_closed_after_capture'] and slot['artifact_sha256']==f['artifacts']['build/codex_desk_meter.bin']['sha256']
assert slot['board_mac']=='28:84:85:B0:85:18' and slot['flash_images_hash_verified']==3 and all(x['exit_code']==0 for x in slot['commands'])
assert (OBS/'reference-capture-r1/device-serial.bin').stat().st_size==150
raw=(OBS/'hardware-post-upload-reset/reset-and-frames-capture/device-serial.bin').read_bytes()
assert len(raw)==5733 and digest(raw)==runtime['raw_log_sha256'] and digest(elf)==runtime['elf_sha256']
assert runtime['boot_elf_sha_prefix_matches'] and runtime['psram_memory_test_ok'] and runtime['usb_receiver_ready_observed']
boot_prefix=re.search(rb'ELF file SHA256:\s*([a-f0-9]+)',raw)
assert boot_prefix and len(boot_prefix.group(1))>=9 and digest(elf).startswith(boot_prefix.group(1).decode())
assert b'esp_psram: SPI SRAM memory test OK' in raw
assert runtime['serial_closed'] and runtime['host_writes_completed_sequences']==[0,1] and runtime['receiver_accepted_sequences']==[]
host=read(OBS/'independent-host-checks/host-checks.json');common=read(OBS/'independent-host-checks/common-stimulus-check.json')
assert len(host['checks'])==6 and all(x['exit_code']==0 for x in host['checks']) and host['python_tests_passed']==22
py=(OBS/'independent-host-checks/python-unit-tests-stderr.txt').read_text(encoding='utf-8')
assert 'Ran 22 tests' in py and 'skipped=' not in py and '... skipped ' not in py
assert common['encoder_matches_exact_common_frames'] and common['legacy_collector']['matches_common_reference_payload']
assert len(common['provider_fixture_checks'])==17 and all(x['matches_expected_validity'] for x in common['provider_fixture_checks'])
assert common['production_c_accepts_common_sequences']==[0,1] and not common['frozen_operator29_pipeline_completed']
terminal=read(OBS/'terminal-verification.json')
assert original['operator']['status']==m['operator']['status']=='completed'
assert terminal['measurement']==m['measurement'] and terminal['raw_native_events']==229
events=[json.loads(line) for line in (OBS/'terminal-originals/stdout.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
completed=[event for event in events if event.get('type')=='turn.completed']
assert len(completed)==1 and completed[0]['usage']['input_tokens']==4032791 and completed[0]['usage']['output_tokens']==58187
correction=read(OBS/'operator-publication-correction.json')
inventory_raw=(OBS/'operator-publication-previous-checkpoint/snapshot-inventory.json').read_bytes()
assert correction['original_inventory_sha256']==digest(inventory_raw)
assert correction['original_publisher_sha256']==digest((OBS/'operator-helpers/publish-luna-followup03-optical-awaiting.py').read_bytes())
assert correction['original_inventory_round']==2 and correction['corrected_ledger_round']==3
supplement=read(OBS/'operator-publication-inventory-supplement.json')
assert supplement['original_inventory_sha256']==digest(inventory_raw) and supplement['round']==3
for name,item in supplement['additional_inventory_entries'].items():
    raw=Path('\\\\?\\'+str((OP/name).resolve())).read_bytes()
    assert len(raw)==item['bytes'] and digest(raw)==item['sha256']
video=read(OBS/'user-video-01/video-metadata.json');visual=read(OBS/'user-video-01/video-review.json')
assert video['source_sha256']==visual['video_sha256']==digest((OBS/'user-video-01/source.mp4').read_bytes())
assert video['duration_seconds']==48.17 and len(video['sample_frames'])==48
for item in video['sample_frames']:assert digest((OBS/'user-video-01'/item['path']).read_bytes())==item['sha256']
user=read(OBS/'user-observation-confirmation.json')
assert user['button_answer_original']=='BOOT와 RESET 모두' and user['user_manual_reset'] is True
assert visual['lcd_output_present'] and not visual['normal_readable_screen_observed'] and not visual['continuous_30_seconds_verified']
review=read(OP/'reference-review.json');ledger=read(OP/'comparison-ledger.json')
assert len(ledger['runs'])==4 and all(x['reviewed'] for x in ledger['runs'])
assert ledger['runs'][0]['implementation_commit']=='c0d5d61160664923e0494302fae180089d02d247'
assert ledger['runs'][1]['implementation_commit']=='e68356829715793dc31dd188bc2a9f528f6fcbd2'
assert ledger['runs'][-1]['reference_review_sha256']==digest((OP/'reference-review.json').read_bytes())
assert m['operator']['comparison']['reference_status']=='fail' and review['policy_status']=='eligible' and not review['product_pass']
rm={k:v['status'] for k,v in review['items'].items()}
assert rm=={'RM1':'pass','RM2':'partial','RM3':'fail','RM4':'fail','RM5':'not_run'}
remaining=7200-sum(x['elapsed_seconds'] for x in ledger['runs'][1:])
assert abs(remaining-1773.142)<0.00001
final=read(OBS/'observation-finalization.json')
assert final['remaining_followup_seconds']==remaining and final['remaining_followup_rounds']==0
closure=read(OBS/'operator-series-completion.json')
assert closure['derived_state']=='remediation_round_limit_reached' and closure['followup_rounds']==3 and closure['candidate_invocations']==4
assert closure['remaining_followup_rounds']==0 and not closure['additional_followup_allowed']
assert closure['ledger_sha256']==digest((OP/'comparison-ledger.json').read_bytes())
assert closure['series_normalized_tokens'] is None and closure['known_series_normalized_tokens']==34918496 and closure['token_measurement_coverage']=='3/4'
assert ledger['runs'][2]['status']=='environment_failed' and ledger['runs'][2]['tokens']['total'] is None
audit=dict(read(REST/'restore-report.json'),frozen_operator_validators_used=True,inventory_bytes_verified=True,
    immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,raw_candidate_source_files_verified=37,
    raw_candidate_artifacts_verified=20,candidate_artifact_source_binding_verified=True,host_checks_record_preserved=True,
    host_tests_repeated=False,original_run_or_checkout_path_used=False,operator_firmware_rebuild=False,hardware_upload_completed=True,
    receiver_acceptance='unconfirmed',first_serial_capture_bytes=150,serial_capture_bytes=5733,current_upload_at=slot['upload_completed_at'],
    application_boot_observed=True,psram_memory_test_ok_observed=True,usb_receiver_ready_observed=True,
    optical_status='video_rotated_duplicated_clipped_text',video_sha256=video['source_sha256'],video_duration_seconds=48.17,
    user_manual_reset=True,normal_readable_screen_observed=False,reference_review_applied=True,reference_status='fail',
    product_pass=False,rm_items=rm,policy_status='eligible',series_policy_status='invalid_for_comparison',
    additional_candidate_call_started=False,remaining_followup_seconds=remaining,remaining_followup_rounds=0)
audit.update(series_closed=True,derived_series_state=closure['derived_state'],known_series_normalized_tokens=34918496,series_token_measurement_coverage='3/4',publication_metadata_corrections_preserved=True)
procedure=read(REST/'operator-audit-procedure-correction.json')
assert procedure['original_auditor_sha256']==digest((OBS/'operator-helpers/verify-codex-luna-followup03-evaluation.py').read_bytes())
assert procedure['corrected_auditor_sha256']==digest(Path(__file__).read_bytes())
audit['operator_audit_procedure_correction']=procedure
save(REST/'frozen-validator-audit.json',audit)
print(json.dumps(audit))
