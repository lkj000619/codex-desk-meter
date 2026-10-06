"""Keep both hardware attempts and archive the currently observed firmware."""
from pathlib import Path
import importlib.util, json, shutil, sys
RUN=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01');OUT=RUN/'operator-observation';CURRENT=OUT/'hardware-attempt-02'
PACK=Path('C:/meter-run-packages-20261006/codex-luna-r01-upload02-awaiting-optical');REST=Path('C:/meter-run-restores-20261006/codex-luna-r01-upload02-awaiting-optical')
sys.path.insert(0,'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest, verify_evidence
from policy_review import validate_review
slot=read(CURRENT/'hardware-slot.json');capture=read(CURRENT/'reference-capture-r1/capture.json')
assert slot['upload_completed'] and slot['serial_closed_after_capture'] and all(v['exit_code']==0 for v in slot['commands'])
assert [v['sequence'] for v in capture['frames']]==[0,1] and all(v['bytes_written']==v['bytes_requested']==1543 for v in capture['frames'])
assert not slot['receiver_accepted_sequences'] and not slot['receiver_rejected_errors']
save(CURRENT/'optical-observation-pending.json',{'run_id':RUN.name,'round':0,'optical_observation':'awaiting_user',
    'question_identifies_upload_at_kst':'2026-10-06 21:03','artifact_sha256':slot['artifact_sha256'],
    'implementation_and_submission_terminal':True,'independent_host_checks_complete':True,'hardware_upload_complete':True,
    'reference_status':'not_run','rm_review_applied':False,'product_pass':None,'receiver_acceptance':'unconfirmed',
    'serial_capture_bytes':0,'host_writes_completed_sequences':[0,1],'serial_closed':True,
    'earlier_upload_target_association':'unconfirmed_by_user_report','same_original_artifact':True,
    'remaining_followup_seconds':7200,'remaining_followup_rounds':3,'new_candidate_call_authorized':False})
save(CURRENT/'console-source-review.json',{'run_id':RUN.name,'configuration':'sdkconfig',
    'primary_console':'UART0','secondary_console':'USB Serial/JTAG','direct_input':'main/app_main.c usb_serial_jtag_read_bytes',
    'captured_serial_bytes':0,'receiver_acceptance':'unconfirmed','failure_cause':'unconfirmed',
    'scope':'Both console configurations are preserved. Zero captured bytes does not prove accepted receipt, rejected receipt, boot failure or a specific console-routing cause. LCD/BOOT observation pending; no firmware setting changes.'})
helpers=OUT/'operator-helpers'
for p in [RUN.parent/'reupload-codex-luna-r01.py',RUN.parent/'observe-codex-luna-r01-upload02.py',Path(__file__),Path('C:/meter-run-packages-20261006/verify-codex-luna-r01-upload02.py')]:shutil.copy2(p,helpers/p.name)
m=read(RUN/'run-manifest.json')
for p in OUT.rglob('*'):
    if p.is_file():m['operator']['evidence'][p.relative_to(RUN).as_posix()]=digest(p.read_bytes())
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
spec=importlib.util.spec_from_file_location('operator_artifact_collector',helpers/'artifact-collector-evidence_package.py');collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
created=collector.create_package(RUN,PACK);save(PACK.parent/'codex-luna-r01-upload02-awaiting-optical-create.json',created)
restored=collector.restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps({'package':created,'restore':restored,'current_upload_at':slot['upload_completed_at']}))
