"""Preserve final RM-pass but quality-ineligible video/evidence without replay."""
from pathlib import Path
import json,shutil,sys
BASE=Path('C:/meter-operator-20261004');RUN=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-sol-r02')
PACK=Path('C:/meter-run-packages-20261006/codex-sol-followup02-final');REST=Path('C:/meter-run-restores-20261006/codex-sol-followup02-final')
sys.path.insert(0,str(BASE/'scripts'))
import benchmark
from benchmark_support import read,save,digest,verify_evidence
from policy_review import validate_review
from evidence_package import create_package,restore_package
m=read(RUN/'run-manifest.json');f=read(RUN/'operator-source-freeze.json');ledger=read(Path(m['operator']['comparison']['ledger']))
assert len(ledger['runs'])==3 and ledger['state']=='reached' and ledger['runs'][-1]['reviewed'] and ledger['runs'][-1]['reference_status']=='pass'
assert benchmark.git('rev-parse','HEAD',cwd=RUN/'checkout')==f['commit'] and not benchmark.git('status','--porcelain',cwd=RUN/'checkout')
assert validate_review(m,RUN/'run-manifest.json')['decision']['status']=='invalid_for_comparison'
target=RUN/'operator-observation/operator-helpers'/Path(__file__).name;shutil.copy2(Path(__file__),target)
m['operator']['evidence'][target.relative_to(RUN).as_posix()]=digest(target.read_bytes())
save(RUN/'run-manifest.json',m);verify_evidence(m,RUN)
created=create_package(RUN,PACK);save(PACK.parent/'codex-sol-followup02-final-create.json',created)
restored=restore_package(PACK,REST,created['package_manifest_sha256'])
print(json.dumps({'package':created,'restore':restored}))
