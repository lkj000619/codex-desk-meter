"""Prepare only today's unstarted Luna series; preserve prior proofs and reservations."""
import contextlib, io, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
BASE=Path('C:/meter-operator-20261004'); ROOT=Path('C:/Users/\uC774\uAD11\uC9C4/orca/codex-desk-meter')
RUN_ROOT=Path('C:/meter-runs-20261006'); EVIDENCE=Path('C:/meter-preflight-20261006/luna-initial')
OLD_ROOT=Path('C:/meter-preflight-20261005/renewal')
OLD_RUN=Path('C:/meter-runs-20261005/20261005-codex-cli-gpt-6-luna-r01')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import KST, read, save, digest, verify_evidence
from comparison_manager import init_comparison
from operator_baseline import verify
assert datetime.now(KST).strftime('%Y%m%d')=='20261006'
assert benchmark.git('rev-parse','HEAD',cwd=BASE)=='272875140d1998d458e26fdb2f6deab5e5d8f7b5'
assert not benchmark.git('status','--porcelain',cwd=BASE)
previous=read(ROOT/'results/formal-comparison-20261004/progress.json')
assert previous['state']=='codex_sol_series_closed_reference_reached_quality_ineligible'
assert previous['product_executions_started']==previous['product_executions_completed']==11
assert previous['closed_codex_sol_series']['ledger_state']=='reached'
old=read(OLD_RUN/'run-manifest.json'); old_bytes=(OLD_RUN/'run-manifest.json').read_bytes()
assert old['operator']['status']=='prepared' and old['execution']['started_at'] is None
source=read(OLD_ROOT/'codex-luna-receipt.json')
benchmark.validate_preflight_receipt(source,old,read(OLD_RUN/'profile.json'),OLD_ROOT)
profile_path=BASE/'experiments/config/next-profiles-20261003/codex-luna.json'
profile=read(profile_path); assert profile['model']=='gpt-6-luna' and profile['reasoning']=='max'
output=io.StringIO()
with contextlib.redirect_stdout(output):
    benchmark.prepare(SimpleNamespace(baseline='comparison-baseline-20261004',profile=str(profile_path),root=str(RUN_ROOT),phase='benchmark',seed=1,timeout=7200,port=None))
RUN=Path(output.getvalue().strip().splitlines()[-1]); ledger=RUN_ROOT/'ledgers'/(RUN.name+'.json')
init_comparison(ledger,RUN,BASE/'experiments/reference/codex-7923f96/reference-inputs.json')
m=read(RUN/'run-manifest.json'); CO=RUN/'checkout'
benchmark.verify_agent_inputs(RUN,m); verify(m,RUN); verify_evidence(m,RUN)
assert benchmark.git('rev-list','--count','HEAD',cwd=CO)=='1'
assert not benchmark.git('status','--porcelain',cwd=CO)
assert len(read(RUN/'candidate-inputs.json')['files'])==57
assert not (CO/'build').exists() and not (CO/'build-host').exists()
assert not (CO/'pc').exists() and not (CO/'firmware').exists()
assert (RUN/'profile.json').read_bytes()==(OLD_RUN/'profile.json').read_bytes()
assert m['execution']['input_bundle_sha256']==old['execution']['input_bundle_sha256']
EVIDENCE.mkdir(parents=True,exist_ok=False)
for name,sha in source['evidence'].items():
    origin=OLD_ROOT/name; assert digest(origin.read_bytes())==sha
    dest=EVIDENCE/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(origin,dest)
receipt=dict(source,comparison_id=m['operator']['comparison']['comparison_id'],
    input_bundle_sha256=m['execution']['input_bundle_sha256'],reference_inputs_sha256=m['operator']['comparison']['reference_inputs_sha256'],
    checked_at=datetime.now(timezone.utc).isoformat(),launch_run_id=RUN.name,
    note='New2026-10-06 Luna reservation bound to frozen profile/input/reference. Original2026-10-04 capability proofs and2026-10-05 inventory retained as historical evidence. Fresh CLI/SDK/native checks and a new launch receipt are required before any model call.')
save(EVIDENCE/'luna-prepared-receipt.json',receipt)
benchmark.validate_preflight_receipt(receipt,m,profile,EVIDENCE)
assert (OLD_RUN/'run-manifest.json').read_bytes()==old_bytes
record={'run_id':RUN.name,'directory':str(RUN),'ledger':str(ledger),'block':1,'seed':1,
    'baseline_commit':m['execution']['base_commit'],'candidate_commit':m['operator']['local_base_commit'],
    'candidate_tree':benchmark.git('rev-parse','HEAD^{tree}',cwd=CO),'local_branch':benchmark.git('branch','--show-current',cwd=CO),
    'manifest_branch_label':m['execution']['branch'],'profile_sha256':m['execution']['profile_sha256'],
    'input_bundle_sha256':m['execution']['input_bundle_sha256'],'immutable_input_files_verified':57,
    'old_unstarted_reservation':OLD_RUN.name,'old_reservation_bytes_unchanged':True,
    'model_calls_during_preparation':0,'candidate_product_code_present':False,
    'scope':'Independent fresh initial input repository, one baseline commit only; no previous product implementation or generated build artifacts.'}
save(RUN_ROOT/'luna-preparation.json',record)
print(json.dumps(record))
