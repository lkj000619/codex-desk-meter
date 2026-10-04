"""Reserve and validate the first independent block; never execute a model."""
import contextlib
import io
import json
from datetime import datetime
from pathlib import Path
import random
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'scripts'))
import benchmark
from benchmark_support import KST, digest, read, save, verify_evidence
from comparison_manager import init_comparison
from operator_baseline import verify


def main():
    targets = read(ROOT/'experiments/config/next-profiles-20261003/comparison-targets.json')
    profiles = list(targets['active_profiles'])
    random.Random(1).shuffle(profiles)
    baseline = targets['baseline_ref']
    commit = benchmark.git('rev-parse', baseline+'^{commit}')
    checks = {key: 'pass' for key in ('idf_build','compiler','ninja','git','temp_write','network_policy',
                                     'settings_inventory','prompt_scope','activity_logging')}
    checks['read_isolation'] = 'not_enforced'
    evidence = {path.relative_to(REPORT).as_posix(): digest(path.read_bytes()) for path in (REPORT/'evidence').rglob('*') if path.is_file()}
    evidence['capability-summary.json'] = digest((REPORT/'capability-summary.json').read_bytes())
    evidence['tests-final.txt'] = digest((REPORT/'tests-final.txt').read_bytes())
    capabilities = read(REPORT/'capability-summary.json')
    date = datetime.now(KST).strftime('%Y%m%d')
    run_root = Path('C:/meter-runs-'+date)
    receipts = []
    freeze = {'schema_version':1,'prepared_date':datetime.now(KST).date().isoformat(),'baseline_ref':baseline,'base_commit':commit,
              'block':1,'seed':1,'active_profile_count':len(profiles),'independent_repetitions':3,
              'order':profiles,'series':[], 'product_executions':0,
              'hardware_observation':'Board not enumerated at preparation; verify USB VID/PID and port before flash/optical observation.'}
    for filename in profiles:
        profile = ROOT/'experiments/config/next-profiles-20261003'/filename
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            benchmark.prepare(SimpleNamespace(baseline=baseline,profile=str(profile),root=str(run_root),
                                              phase='benchmark',seed=1,timeout=7200,port=None))
        directory = Path(output.getvalue().strip().splitlines()[-1])
        ledger = run_root/'ledgers'/(directory.name+'.json')
        init_comparison(ledger,directory,ROOT/'experiments/reference/codex-7923f96/reference-inputs.json')
        manifest = read(directory/'run-manifest.json')
        assert manifest['operator']['policy_review_required'] is True
        benchmark.verify_agent_inputs(directory,manifest)
        verify(manifest,directory)
        selected = capabilities[Path(filename).stem]
        assert selected['status']=='pass' and selected['current_profile_sha256']==manifest['execution']['profile_sha256']
        cap_path = 'evidence/probes/'+selected['probe']+'/capabilities.json'
        receipt = {'access_policy':'prompt-and-log','base_commit':commit,
                   'profile_sha256':manifest['execution']['profile_sha256'],'infrastructure_ready':True,
                   'comparison_id':manifest['operator']['comparison']['comparison_id'],
                   'input_bundle_sha256':manifest['execution']['input_bundle_sha256'],
                   'reference_inputs_sha256':manifest['operator']['comparison']['reference_inputs_sha256'],
                   'checks':checks,'evidence':evidence,
                   'capabilities':{key:{'status':'pass','evidence':cap_path} for key in selected['capabilities']},
                   'note':'Fresh run-bound receipt from 2026-10-04 actual infrastructure evidence; no old receipt reused.'}
        receipt_path = REPORT/(Path(filename).stem+'-receipt.json')
        benchmark.validate_preflight_receipt(receipt,manifest,read(profile),REPORT)
        verify_evidence(manifest,directory)
        assert benchmark.git('rev-list','--count','HEAD',cwd=directory/'checkout')=='1'
        assert manifest['execution']['started_at'] is None and manifest['measurement']['wall_clock_seconds'] is None
        item = {'profile':filename,'run_id':directory.name,'directory':str(directory),'ledger':str(ledger),
                'receipt':str(receipt_path),'receipt_sha256':digest((json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode('utf-8')),
                'profile_sha256':manifest['execution']['profile_sha256'],
                'input_bundle_sha256':manifest['execution']['input_bundle_sha256'],
                'evaluation_criteria_sha256':manifest['execution']['evaluation_criteria_sha256'],
                'candidate_commit':manifest['operator']['local_base_commit'],
                'candidate_tree':benchmark.git('rev-parse','HEAD^{tree}',cwd=directory/'checkout'),
                'operator_baseline_sha256':manifest['operator']['evidence']['operator-baseline.zip']}
        receipts.append((receipt_path,receipt))
        freeze['series'].append(item)
        print(json.dumps(item),flush=True)
    # Keep the operator repository clean while every prepare checks its HEAD.
    for receipt_path, receipt in receipts:
        save(receipt_path,receipt)
    for item in freeze['series']:
        item['receipt_sha256'] = digest(Path(item['receipt']).read_bytes())
    freeze['block_orders'] = {}
    for seed in targets['block_seeds']:
        order = list(targets['active_profiles'])
        random.Random(seed).shuffle(order)
        freeze['block_orders'][str(seed)] = order
    save(REPORT/'freeze.json',freeze)


if __name__=='__main__':
    main()
