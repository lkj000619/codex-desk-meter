"""Audit the restored package using only its archived frozen validators."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import zipfile

PACK=Path('C:/meter-run-packages-20261005/agy-flash-r01-final');REST=Path('C:/meter-run-restores-20261005/agy-flash-r01-final')
FROZEN=Path('C:/meter-run-restores-20261005/agy-flash-r01-final-frozen-operator');FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(REST/'operator/operator-baseline.zip') as z:
    for info in z.infolist():
        p=FROZEN/info.filename;assert p.resolve().is_relative_to(FROZEN.resolve()) and not info.is_dir()
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
sys.path.insert(0,str(FROZEN/'scripts'))
from benchmark_support import digest,read,save,validate_schema,validate_operator,verify_evidence
from benchmark import verify_agent_inputs,validate_preflight_receipt
from evidence_package import verify_report_dependencies
from policy_review import review_eligibility
from reference_inputs import validate_reference

expected='c800ac8aabdebc10961d7ae7ac9dd4a5fceb47f13fba984afc45552054b1b426'
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
assert digest(orig_path.read_bytes())==freeze['original_terminal_manifest_sha256']==ledger['runs'][0]['terminal_manifest_sha256']
assert orig['operator']['status']==m['operator']['status']=='environment_failed'
assert orig['outputs']['implementation_commit'] is None and m['measurement']==orig['measurement']
assert {k:v for k,v in orig['execution'].items() if k!='worktree'}=={k:v for k,v in m['execution'].items() if k!='worktree'}
assert ledger['runs'][0]['reviewed'] and ledger['runs'][0]['reference_status']=='fail'
before=read(OP/'run-manifest-after-reference-review.json');post=read(OP/'operator-post-review-evidence.json')
assert digest((OP/'run-manifest-after-reference-review.json').read_bytes())==post['reference_review_manifest_sha256']
assert post['post_review_changes']==['operator.evidence'];normalized=copy.deepcopy(before)
for name in post['added_files']+['operator-post-review-evidence.json']:normalized['operator']['evidence'][name]=digest((OP/name).read_bytes())
assert normalized==raw
eligible,status,reason=review_eligibility(m,OP/'run-manifest.json');assert eligible and status=='eligible'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CO,text=True).strip()==freeze['commit']==m['outputs']['implementation_commit']
assert subprocess.check_output(['git','remote'],cwd=CO,text=True).strip()==''
normalizations=[]
for category in ('artifacts','sources'):
    for name,meta in freeze[category].items():
        data=(OP/meta['operator_raw_copy']).read_bytes();assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
        restored=(CO/name).read_bytes()
        if restored!=data:normalizations.append(name)
        blob=subprocess.check_output(['git','hash-object','--path='+name,'--stdin'],cwd=CO,input=data).decode().strip()
        assert blob==subprocess.check_output(['git','rev-parse','HEAD:'+name],cwd=CO,text=True).strip(),name
        if name.endswith(('.bin','.elf','.map')):assert restored==data,name
review=read(OP/'reference-review.json');rm={k:v['status'] for k,v in review['items'].items()}
assert rm=={'RM1':'pass','RM2':'partial','RM3':'fail','RM4':'partial','RM5':'partial'} and not review['product_pass']
assert not pack['result'] and not pack['evaluation_manifest']
assert not (CO/m['outputs']['structured_result']).exists() and (CO/m['outputs']['selection_document']).is_file()
video=OP/'operator-observation/user-video-01';confirmation=read(video/'capture-identity-confirmation.json')
assert confirmation['user_confirmed_current_firmware'] and confirmation['video_sha256']==digest((video/'source.mp4').read_bytes())
assert confirmation['implementation_commit']==freeze['commit']
capture=read(OP/'operator-observation/reference-capture-r1/capture.json')
assert capture['status']=='failed' and capture['error']=='Write timeout' and capture['frames'][0]['bytes_written'] is None
assert (OP/'operator-observation/reference-capture-r1/device-serial.bin').stat().st_size==0
assert read(OP/'operator-observation/observation-finalization.json')['board_slot_released']
report={**read(REST/'restore-report.json'),'frozen_operator_validators_used':True,'original_run_or_checkout_path_used':False,
    'inventory_bytes_verified':True,'immutable_input_files_verified':57,'source_snapshot_files_verified':len(freeze['sources']),
    'raw_artifact_and_config_copies_verified':len(freeze['artifacts']),'source_and_artifact_git_blobs_verified':True,
    'git_text_normalization_in_restored_checkout':normalizations,'raw_pre_git_bytes_preserved_separately':True,
    'original_terminal_and_cost_preserved':True,'post_review_evidence_addition_verified':True,
    'candidate_result_submission':'missing','candidate_selection_document_submission':'present',
    'user_video_identity_confirmed':True,'user_video_sha256':confirmation['video_sha256'],'rm_review_completed':True,'rm_items':rm,
    'reference_status':'fail','product_pass':False,'hardware_capture_status':'failed','hardware_capture_error':'Write timeout',
    'remaining_followup_seconds':7200,'followups_run':0,'board_slot_released':True,
    'optical_precision_and_30s_flicker_certification':'not_measured'}
save(REST/'frozen-validator-audit.json',report)
print(json.dumps(report,ensure_ascii=False))
