
from pathlib import Path
import json,subprocess,sys,zipfile
pack=Path(sys.argv[1]);rest=Path(sys.argv[2]);expected=sys.argv[3];frozen=rest.parent/(rest.name+'-frozen-operator-v2');frozen.mkdir(exist_ok=False)
with zipfile.ZipFile(rest/'operator/operator-baseline.zip') as z:
    for info in z.infolist():
        p=frozen/info.filename;assert p.resolve().is_relative_to(frozen.resolve()) and not info.is_dir();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
sys.path.insert(0,str(frozen/'scripts'))
from benchmark_support import read,save,digest,validate_schema,validate_operator,verify_evidence
from benchmark import verify_agent_inputs,validate_preflight_receipt
from policy_review import review_eligibility
from evidence_package import verify_report_dependencies
assert digest((pack/'package-manifest.json').read_bytes())==expected
inv=read(pack/'package-manifest.json')
for name,meta in inv['files'].items():
    data=(pack/name).read_bytes();assert len(data)==meta['bytes'] and digest(data)==meta['sha256']
op=rest/'operator';co=rest/'checkout';m=read(op/'run-manifest.json');orig=read(op/'operator-observation/terminal-originals/run-manifest.json')
validate_schema(m,'run-manifest.schema.json');validate_operator(m);verify_evidence(m,op);verify_agent_inputs(op,m);verify_report_dependencies(m,op)
validate_preflight_receipt(read(op/'execution-preflight.json'),m,read(op/'profile.json'),op/'preflight-evidence')
eligible,status,reason=review_eligibility(m,op/'run-manifest.json');assert eligible and status=='eligible'
assert orig['measurement']==m['measurement']
assert {k:v for k,v in orig['execution'].items() if k!='worktree'}=={k:v for k,v in m['execution'].items() if k!='worktree'}
ledger=read(op/'comparison-ledger.json');entry=next(e for e in ledger['runs'] if e['run_id']==m['run_id']);assert entry['reviewed'] and entry['reference_status']=='fail'
assert digest((op/'operator-observation/terminal-originals/run-manifest.json').read_bytes())==entry['terminal_manifest_sha256']
freeze=read(op/'operator-source-freeze.json');assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=co,text=True).strip()==freeze['commit']==m['outputs']['implementation_commit']
for name,meta in freeze['sources'].items():
    raw=(op/meta['operator_raw_copy']).read_bytes();assert len(raw)==meta['bytes'] and digest(raw)==meta['sha256'];restored=(co/name).read_bytes();assert restored.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n');blob=subprocess.check_output(['git','hash-object','--path='+name,'--stdin'],cwd=co,input=raw).decode().strip();assert blob==subprocess.check_output(['git','rev-parse','HEAD:'+name],cwd=co,text=True).strip()
assert not (co/m['outputs']['structured_result']).exists() and not (co/m['outputs']['selection_document']).exists()
rm={k:v['status'] for k,v in read(op/'reference-review.json')['items'].items()};assert rm=={'RM1':'fail','RM2':'not_run','RM3':'not_run','RM4':'not_run','RM5':'not_run'}
spent=sum(e['elapsed_seconds'] or 0 for e in ledger['runs'] if e['round']>0);used=sum(e['round']>0 for e in ledger['runs'])
audit=dict(read(rest/'restore-report.json'),frozen_operator_validators_used=True,original_run_or_checkout_path_used=False,inventory_bytes_verified=True,immutable_input_files_verified=57,original_terminal_and_cost_preserved=True,rm_review_completed=True,rm_items=rm,reference_status='fail',product_pass=False,candidate_source_files_verified=len(freeze['sources']),candidate_firmware_artifacts=0,raw_source_bytes_preserved=True,git_blob_identity_verified=True,source_line_ending_difference='firmware/CMakeLists.txt: LF raw versus CRLF restored; normalized bytes and Git blob identical',remaining_followup_seconds=max(0,7200-spent),remaining_followup_rounds=3-used,board_slot_released=True)
assert audit['result_valid'] is False
save(rest/'frozen-validator-audit.json',audit);print(json.dumps(audit))
