"""Independent restore audit using the package's own frozen validators, never the original checkout."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import zipfile

PACK=Path('C:/meter-run-packages-20261005/agy-flash-r02-final');REST=Path('C:/meter-run-restores-20261005/agy-flash-r02-final')
FROZEN=Path('C:/meter-run-restores-20261005/agy-flash-r02-final-frozen-operator');FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(REST/'operator/operator-baseline.zip') as z:
    for info in z.infolist():
        p=FROZEN/info.filename;assert p.resolve().is_relative_to(FROZEN.resolve()) and not info.is_dir()
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
sys.path.insert(0,str(FROZEN/'scripts'))
from benchmark_support import digest,read,save,validate_schema,validate_operator,verify_evidence
from benchmark import verify_agent_inputs,validate_preflight_receipt,_load_e2e_validator
from evidence_package import verify_report_dependencies
from policy_review import review_eligibility
from reference_inputs import validate_reference

expected='b0e2880fc7c786ae338b9d1870ccd4c3510bf9afb3f5881089ff4d23515f244c'
assert digest((PACK/'package-manifest.json').read_bytes())==expected
pack=read(PACK/'package-manifest.json')
assert {p.relative_to(PACK).as_posix() for p in PACK.rglob('*') if p.is_file()}==set(pack['files'])|{'package-manifest.json'}
for name,meta in pack['files'].items():
    data=(PACK/name).read_bytes();assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
    if name.startswith(('operator/','checkout/')):
        target='operator/raw-run-manifest.json' if name=='operator/run-manifest.json' else name
        assert (REST/target).read_bytes()==data
OP=REST/'operator';CO=REST/'checkout';m=read(OP/'run-manifest.json');raw=read(OP/'raw-run-manifest.json')
validate_schema(m,'run-manifest.schema.json');validate_operator(m);verify_evidence(m,OP)
verify_report_dependencies(m,OP);verify_agent_inputs(OP,m)
validate_preflight_receipt(read(OP/'execution-preflight.json'),m,read(OP/'profile.json'),OP/'preflight-evidence')
validate_reference(OP/'reference/reference-inputs.json')
orig_path=OP/'operator-observation/terminal-originals/run-manifest.json';orig=read(orig_path)
ledger=read(OP/'comparison-ledger.json');freeze=read(OP/'operator-source-freeze.json')
entry=next(x for x in ledger['runs'] if x['run_id']==m['run_id'])
assert digest(orig_path.read_bytes())==freeze['original_terminal_manifest_sha256']==entry['terminal_manifest_sha256']
assert orig['operator']['status']==m['operator']['status']=='completed'
assert orig['outputs']['implementation_commit'] is None and m['measurement']==orig['measurement']
assert {k:v for k,v in orig['execution'].items() if k!='worktree'}=={k:v for k,v in m['execution'].items() if k!='worktree'}
assert entry['reviewed'] and entry['reference_status']=='fail' and entry['implementation_commit']==freeze['commit']
before=read(OP/'run-manifest-after-reference-review.json');post=read(OP/'operator-post-review-evidence.json')
assert digest((OP/'run-manifest-after-reference-review.json').read_bytes())==post['reference_review_manifest_sha256']
assert post['post_review_changes']==['operator.evidence'];normalized=copy.deepcopy(before)
for name in post['added_files']+['operator-post-review-evidence.json']:normalized['operator']['evidence'][name]=digest((OP/name).read_bytes())
assert normalized==raw
eligible,status,reason=review_eligibility(m,OP/'run-manifest.json');assert not eligible and status=='invalid_for_comparison'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CO,text=True).strip()==freeze['commit']==m['outputs']['implementation_commit']
assert subprocess.check_output(['git','remote'],cwd=CO,text=True).strip()==''
differences=[]
for category in ('artifacts','sources'):
    for name,meta in freeze[category].items():
        data=(OP/meta['operator_raw_copy']).read_bytes();assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
        restored=(CO/name).read_bytes()
        if restored!=data:differences.append(name)
        blob=subprocess.check_output(['git','hash-object','--path='+name,'--stdin'],cwd=CO,input=data).decode().strip()
        assert blob==subprocess.check_output(['git','rev-parse','HEAD:'+name],cwd=CO,text=True).strip(),name
        if name.endswith(('.bin','.elf','.map')):assert restored==data,name
review=read(OP/'reference-review.json');rm={k:v['status'] for k,v in review['items'].items()}
assert rm=={'RM1':'pass','RM2':'partial','RM3':'fail','RM4':'partial','RM5':'partial'} and not review['product_pass']
assert pack['result']==m['outputs']['structured_result'] and pack['evaluation_manifest']==m['outputs']['evaluation_manifest']
result=read(CO/pack['result']);evaluation=read(CO/pack['evaluation_manifest'])
_load_e2e_validator().validate_result(result,manifest=evaluation,evidence_root=CO,manifest_root=CO)
assert result['product_pass'] is False
assert read(OP/'raw-result.json')==read(OP/freeze['sources'][pack['result']]['operator_raw_copy'])
candidate_raw=read(OP/'raw-result.json');candidate_normalized=copy.deepcopy(candidate_raw)
candidate_normalized['manifest']['path']=pack['evaluation_manifest'];assert candidate_normalized==result
video=OP/'operator-observation/user-video-01';confirmation=read(video/'capture-identity-confirmation.json')
assert confirmation['user_supplied_current_firmware_video'] and confirmation['video_sha256']==digest((video/'source.mp4').read_bytes())
assert confirmation['implementation_commit']==freeze['commit']
capture=read(OP/'operator-observation/reference-capture-r1/capture.json')
assert capture['status']=='captured' and [x['bytes_written'] for x in capture['frames']]==[1543,1543]
serial=(OP/'operator-observation/reference-capture-r1/device-serial.bin').read_bytes()
assert b'Frame accepted: seq=' not in serial and serial.count(b"panic'ed (LoadProhibited)")==2
finalization=read(OP/'operator-observation/observation-finalization.json');assert finalization['board_slot_released']
hold=read(OP/'operator-user-hold.json');assert not hold['next_model_start_authorized_now'] and not hold['additional_candidate_round_start_authorized_now']
host=read(OP/'operator-observation/fresh-host-artifact-inventory.json')
for name,meta in host['files'].items():
    data=(OP/'operator-observation/fresh-host-binary-snapshot'/name).read_bytes()
    assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
report={**read(REST/'restore-report.json'),'frozen_operator_validators_used':True,'original_run_or_checkout_path_used':False,
    'inventory_bytes_verified':True,'immutable_input_files_verified':57,'source_snapshot_files_verified':len(freeze['sources']),
    'raw_artifact_and_config_copies_verified':len(freeze['artifacts']),'source_and_artifact_git_blobs_verified':True,
    'raw_source_and_normalized_checkout_differences':differences,'raw_pre_git_bytes_preserved_separately':True,
    'package_result_manifest_path_normalization_verified':True,'raw_candidate_result_json_preserved':True,
    'original_terminal_and_cost_preserved':True,'post_review_evidence_addition_verified':True,
    'candidate_result_submission':'present','candidate_selection_document_submission':'present',
    'user_video_identity_confirmed':True,'user_video_sha256':confirmation['video_sha256'],'rm_review_completed':True,'rm_items':rm,
    'reference_status':'fail','product_pass':False,'hardware_capture_status':'captured','frame_acceptance_observed':False,
    'load_prohibited_panics_observed':2,'fresh_host_artifacts_verified':len(host['files']),
    'remaining_followup_seconds':finalization['remaining_followup_seconds'],'followups_run':1,'remaining_followup_rounds':2,
    'board_slot_released':True,'user_hold_preserved':True,'next_model_start_authorized_now':False,
    'additional_candidate_round_start_authorized_now':False,'optical_precision_and_30s_flicker_certification':'not_measured'}
save(REST/'frozen-validator-audit.json',report)
print(json.dumps(report,ensure_ascii=False))
