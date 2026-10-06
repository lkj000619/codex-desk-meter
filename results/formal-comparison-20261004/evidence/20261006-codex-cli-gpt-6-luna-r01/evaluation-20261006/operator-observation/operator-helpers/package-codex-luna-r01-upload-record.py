"""Archive upload records without changing the pre-observation package."""
from pathlib import Path
import importlib.util, json, shutil, sys
BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01');OUT=RUN/'operator-observation'
PRE=Path('C:/meter-run-restores-20261006/codex-luna-r01-pre-observation')
PACK=Path('C:/meter-run-packages-20261006/codex-luna-r01-upload-record');REST=Path('C:/meter-run-restores-20261006/codex-luna-r01-upload-record')
sys.path.insert(0,str(BASE/'scripts'))
from benchmark_support import read, save, digest, verify_evidence
from policy_review import validate_review
src=OUT/'operator-helpers/artifact-collector-evidence_package.py'
spec=importlib.util.spec_from_file_location('operator_artifact_collector',src);collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
slot=read(OUT/'hardware-slot.json');assert slot['upload_completed'] and slot['serial_closed_after_capture']
assert all(c['exit_code']==0 for c in slot['commands'])
assert not slot['receiver_accepted_sequences'] and not slot['receiver_rejected_errors']
save(OUT/'optical-observation-pending.json',{'run_id':RUN.name,'round':0,'optical_observation':'awaiting_user',
    'question_identifies_upload_at_kst':'2026-10-06 11:27','artifact_sha256':slot['artifact_sha256'],
    'implementation_and_submission_terminal':True,'independent_host_checks_complete':True,'hardware_upload_complete':True,
    'reference_status':'not_run','rm_review_applied':False,'product_pass':None,'receiver_acceptance':'unconfirmed',
    'serial_capture_bytes':0,'host_writes_completed_sequences':[0,1],'serial_closed':True,
    'remaining_followup_seconds':7200,'remaining_followup_rounds':3,'new_candidate_call_authorized':False,
    'prior_sol_observation_is_luna_evidence':False})
for p in (PRE/'post-restore-host-checks').rglob('*'):
    if p.is_file():
        dst=OUT/'independent-host-checks'/p.relative_to(PRE/'post-restore-host-checks');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
shutil.copy2(PRE/'frozen-validator-audit.json',OUT/'pre-observation-restore-audit.json')
for p in [Path('C:/meter-run-packages-20261006/verify-codex-luna-r01-pre-observation.py'),RUN.parent/'observe-codex-luna-r01.py',RUN.parent/'prepare-luna-observation.py',Path(__file__)]:shutil.copy2(p,OUT/'operator-helpers'/p.name)
host=read(OUT/'independent-host-checks/common-stimulus-check.json')
expected=read(PRE/'operator/reference/expected-frames.jsonl') if False else json.loads((PRE/'operator/reference/expected-frames.jsonl').read_bytes().splitlines()[0])
actual=read(OUT/'independent-host-checks/candidate-legacy-collector-frame.json')['payload']
differences=[]
def compare(a,b,path='payload'):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(a.keys()|b.keys()):
            if k not in a or k not in b:differences.append({'path':path+'.'+k,'expected':a.get(k),'actual':b.get(k)})
            else:compare(a[k],b[k],path+'.'+k)
    elif isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+f'[{i}]')
    elif a!=b:differences.append({'path':path,'expected':a,'actual':b})
compare(expected['payload'],actual)
save(OUT/'host-semantic-limitations.json',{'run_id':RUN.name,'legacy_payload_differences':differences,
    'provider_validity_mismatches':[v for v in host['provider_fixture_checks'] if not v['matches_expected_validity']],
    'exact_common_wire_encoder_pass':host['encoder_matches_exact_common_frames'],
    'full29_oracle_completed':False,'common_production_c_input_seam_submitted':False,
    'note':'Original behavior preserved; own Python11/C3 passing tests do not certify all collector semantics, physical receipt, optical output or full product success.'})
m=read(RUN/'run-manifest.json')
for p in OUT.rglob('*'):
    if p.is_file():m['operator']['evidence'][p.relative_to(RUN).as_posix()]=digest(p.read_bytes())
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN);validate_review(m,RUN/'run-manifest.json')
created=collector.create_package(RUN,PACK);save(PACK.parent/'codex-luna-r01-upload-record-create.json',created)
restored=collector.restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps({'package':created,'restore':restored,'legacy_difference_fields':len(differences),'provider_validity_mismatches':len(read(OUT/'host-semantic-limitations.json')['provider_validity_mismatches'])}))
