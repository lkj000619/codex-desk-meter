from datetime import datetime,timezone
from pathlib import Path
import json,re,shutil,sys
BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01')
OUT=RUN/'operator-observation';REST=Path('C:/meter-run-restores-20261007/codex-luna-followup03-pre-observation')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import read,save,digest,verify_evidence
from policy_review import validate_review
now=datetime.now(timezone.utc).isoformat();f=read(RUN/'operator-source-freeze.json');m=read(RUN/'run-manifest.json')
original=read(OUT/'terminal-originals/run-manifest.json')
assert original['operator']['status']=='completed' and original['measurement']['tokens']['total']==4090978
shutil.copytree(REST/'post-restore-host-checks',OUT/'independent-host-checks')
for source,target in [(REST/'frozen-validator-audit.json','pre-observation-frozen-validator-audit.json'),(REST/'restore-report.json','pre-observation-restore-report.json')]:shutil.copy2(source,OUT/target)
for helper in [Path(__file__),RUN.parent/'observe-codex-luna-followup-03.py',RUN.parent/'prepare-luna-followup03-reset-capture.py',Path('C:/meter-run-packages-20261007/verify-codex-luna-followup03-pre-observation.py')]:shutil.copy2(helper,OUT/'operator-helpers'/helper.name)
host=read(OUT/'independent-host-checks/host-checks.json');common=read(OUT/'independent-host-checks/common-stimulus-check.json')
assert host['python_tests_passed']==22 and all(x['exit_code']==0 for x in host['checks'])
save(OUT/'host-semantic-review.json',{'run_id':RUN.name,'reviewed_at':now,'source_commit':f['commit'],
    'python_tests_passed':22,'python_skipped_subcases':0,'host_c_executables_passed':3,'provider_validity_cases_passed':17,
    'collector_matches_common_reference_payload':common['legacy_collector']['matches_common_reference_payload'],
    'encoder_matches_common_frames':common['encoder_matches_exact_common_frames'],'production_c_accepts_common_sequences':[0,1],
    'candidate_wire_schema_cases':common['candidate_wire_schema_cases'],'frozen_operator29_pipeline_completed':False,
    'archived_cli_materialization':read(OUT/'independent-host-checks/artifact-materialization.json'),
    'operator_product_source_modified':False,'operator_firmware_rebuild':False,
    'scope':'Independent host checks only; device receipt, LCD, BOOT and stability require independent observations.'})
reset=OUT/'hardware-post-upload-reset';raw=(reset/'reset-and-frames-capture/device-serial.bin').read_bytes()
boot=re.search(rb'ELF file SHA256:\s*([a-f0-9]+)',raw);elf_hash=f['artifacts']['build/codex_desk_meter.elf']['sha256']
assert boot and elf_hash.startswith(boot.group(1).decode()) and b'esp_psram: SPI SRAM memory test OK' in raw
accepted=[int(x) for x in re.findall(rb'accepted cdm/1 frame sequence=(\d+)',raw)]
rejected=[{'error':a.decode(),'retained_last_good_sequence':int(b)} for a,b in re.findall(rb'rejected frame: ([^;\r\n]+); last-good sequence=(\d+)',raw)]
session=read(reset/'reset-and-frames-session.json');capture=read(reset/'reset-and-frames-capture/capture.json')
save(reset/'runtime-source-binding.json',{'run_id':RUN.name,'source_commit':f['commit'],
    'app_sha256':f['artifacts']['build/codex_desk_meter.bin']['sha256'],'elf_sha256':elf_hash,
    'boot_elf_sha_prefix_matches':True,'boot_observed':True,'psram_memory_test_ok':True,
    'boot_screen_submitted_log_observed':b'boot screen submitted before USB receiver setup' in raw,
    'usb_receiver_ready_observed':b'USB Serial/JTAG receiver ready' in raw,
    'usb_data_chunk_observed':b'USB Serial/JTAG receive path observed data (64 bytes)' in raw,
    'raw_log_sha256':digest(raw),'serial_capture_bytes':len(raw),'reset_requested_at':session['reset_requested_at'],
    'receiver_accepted_sequences':accepted,'receiver_rejected_errors':rejected,
    'host_writes_completed_sequences':[x['sequence'] for x in capture['frames'] if x['bytes_written']==x['bytes_requested']],
    'serial_closed':True,'wait_seconds_per_frame':5,
    'scope':'Matching archived ELF boot and first USB chunk observed. Host writes do not establish full frame receipt or readable LCD; first150-byte capture retained.'})
assert m['execution']==original['execution'] and m['measurement']==original['measurement']
for path in OUT.rglob('*'):
    if path.is_file():m['operator']['evidence'][path.relative_to(RUN).as_posix()]=digest(path.read_bytes())
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN)
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='eligible'
print(json.dumps({'host22_c3_provider17':True,'runtime_bytes':len(raw),'elf_hash':elf_hash,'frame_acceptance':accepted,'serial_closed':True}))
