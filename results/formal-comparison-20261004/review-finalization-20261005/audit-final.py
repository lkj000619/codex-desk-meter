"""Verify final RM evidence with validators from the packaged frozen operator ZIP."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import zipfile

PACK=Path('C:/meter-run-packages-20261005/opencode-muse-r02-final')
REST=Path('C:/meter-run-restores-20261005/opencode-muse-r02-final')
FROZEN=Path('C:/meter-run-restores-20261005/opencode-muse-r02-final-frozen-operator')
FROZEN.mkdir(exist_ok=False)
with zipfile.ZipFile(REST/'operator/operator-baseline.zip') as archive:
    for item in archive.infolist():
        target=FROZEN/item.filename
        assert target.resolve().is_relative_to(FROZEN.resolve()) and not item.is_dir()
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(item))
sys.path.insert(0,str(FROZEN/'scripts'))
from benchmark_support import digest,read,save,validate_operator,validate_schema,verify_evidence
from benchmark import verify_agent_inputs,validate_preflight_receipt
from evidence_package import verify_report_dependencies
from policy_review import review_eligibility
from reference_inputs import validate_reference
expected='948261ab0ea75f3742b11664086976816dd353cf5f6cd39394a7270422117fd4'
assert digest((PACK/'package-manifest.json').read_bytes())==expected
package=read(PACK/'package-manifest.json')
assert {p.relative_to(PACK).as_posix() for p in PACK.rglob('*') if p.is_file()}==set(package['files'])|{'package-manifest.json'}
for name,meta in package['files'].items():
    data=(PACK/name).read_bytes()
    assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
    if name.startswith(('operator/','checkout/')):
        target='operator/raw-run-manifest.json' if name=='operator/run-manifest.json' else name
        assert (REST/target).read_bytes()==data
OP=REST/'operator';CO=REST/'checkout'
m=read(OP/'run-manifest.json');raw=read(OP/'raw-run-manifest.json')
validate_schema(m,'run-manifest.schema.json');validate_operator(m)
verify_evidence(m,OP);verify_report_dependencies(m,OP);verify_agent_inputs(OP,m)
validate_preflight_receipt(read(OP/'execution-preflight.json'),m,read(OP/'profile.json'),OP/'preflight-evidence')
validate_reference(OP/'reference/reference-inputs.json')
original=read(OP/'operator-terminal-manifest-original.json')
ledger=read(OP/'comparison-ledger.json');completion=read(OP/'operator-series-completion.json')
assert digest((OP/'operator-terminal-manifest-original.json').read_bytes())==ledger['runs'][-1]['terminal_manifest_sha256']==completion['original_terminal_manifest_sha256']
assert original['outputs']['implementation_commit'] is None and original['operator']['status']=='timeout'
assert m['operator']['status']=='timeout' and m['measurement']==original['measurement']
assert {k:v for k,v in m['execution'].items() if k!='worktree'}=={k:v for k,v in original['execution'].items() if k!='worktree'}
assert ledger['runs'][-1]['reviewed'] and ledger['runs'][-1]['reference_status']=='fail'
assert digest((OP/'comparison-ledger.json').read_bytes())==completion['reviewed_ledger_sha256']
assert digest((OP/'run-manifest-after-reference-review.json').read_bytes())==completion['reviewed_manifest_sha256']
post=read(OP/'operator-review-finalization.json');before=read(OP/'run-manifest-after-reference-review.json')
assert post['post_review_changes']==['operator.evidence']
normalized=copy.deepcopy(before)
for name in post['added_files']+['operator-review-finalization.json']:
    normalized['operator']['evidence'][name]=digest((OP/name).read_bytes())
assert normalized==raw
eligible,status,reason=review_eligibility(m,OP/'run-manifest.json')
assert eligible is False and status=='invalid_for_comparison'
review=read(OP/'reference-review.json')
rm={key:value['status'] for key,value in review['items'].items()}
assert rm=={'RM1':'pass','RM2':'partial','RM3':'partial','RM4':'partial','RM5':'pass'}
assert not review['product_pass'] and not package['result'] and not package['evaluation_manifest']
for field in ('structured_result','selection_document'):assert not (CO/m['outputs'][field]).exists()
freeze=read(OP/'operator-source-freeze.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CO,text=True).strip()==freeze['commit']==m['outputs']['implementation_commit']
assert subprocess.check_output(['git','remote'],cwd=CO,text=True).strip()==''
artifacts={}
for name,meta in freeze['artifacts'].items():
    data=(OP/meta['operator_copy']).read_bytes()
    assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
    assert (CO/name).read_bytes()==data
    artifacts[name]=digest(data)
source=read(OP/'operator-source-snapshot.json')
for name,meta in source['files'].items():
    data=(OP/meta['operator_copy']).read_bytes()
    assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
    assert (CO/name).read_bytes()==data
    blob=subprocess.check_output(['git','hash-object','--path='+name,'--stdin'],cwd=CO,input=data).decode().strip()
    assert blob==subprocess.check_output(['git','rev-parse','HEAD:'+name],cwd=CO,text=True).strip()
confirmation=read(OP/'operator-observation/user-video-01/capture-identity-confirmation.json')
assert confirmation['video_sha256']==digest((OP/'operator-observation/user-video-01/source.mp4').read_bytes())
assert confirmation['implementation_commit']==freeze['commit'] and not confirmation['second_upload_video_claimed']
assert read(OP/'operator-observation/observation-finalization.json')['board_slot_released_for_next_candidate']
assert completion['derived_state']=='budget_exhausted' and not completion['additional_followup_allowed']
report={**read(REST/'restore-report.json'),'frozen_operator_validators_used':True,
        'frozen_operator_scripts_root':str(FROZEN/'scripts'),'original_run_path_used':False,
        'inventory_bytes_verified':True,'immutable_input_files_verified':57,
        'source_snapshot_files_verified':len(source['files']),'source_snapshot_git_blobs_verified':True,
        'raw_artifact_copies_verified':len(artifacts),'raw_artifact_sha256':artifacts,
        'original_terminal_and_cost_preserved':True,'post_review_evidence_addition_verified':True,
        'candidate_result_submission':'missing','candidate_selection_document_submission':'missing',
        'user_video_identity_confirmed':True,'user_video_sha256':confirmation['video_sha256'],
        'rm_review_completed':True,'rm_items':rm,'reference_status':'fail','product_pass':False,
        'derived_series_state':'budget_exhausted','remaining_followup_seconds':0,
        'board_slot_released':True,'optical_precision_and_30s_flicker_certification':'not_measured'}
save(REST/'frozen-validator-audit.json',report)
print(json.dumps(report,ensure_ascii=False,indent=2))
