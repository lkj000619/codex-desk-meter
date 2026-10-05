"""Register preserved operator originals; keep the first archive and its audit error."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

RUN = Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-pro-r01')
sys.path.insert(0, 'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest, verify_evidence
from policy_review import validate_review
from evidence_package import create_package, restore_package

m = read(RUN / 'run-manifest.json')
before = (RUN / 'run-manifest.json').read_bytes()
assert not (RUN / 'run-manifest-before-package-coverage-correction.json').exists()
(RUN / 'run-manifest-before-package-coverage-correction.json').write_bytes(before)
names = ['run-manifest-before-package-coverage-correction.json', 'operator-source-freeze.json',
         'operator-review-finalization.json', 'operator-reference-review-input.json',
         'operator-policy-decision.json', 'operator-next-model-decision.json', 'previous-progress-at-transition.json']
names += [p.relative_to(RUN).as_posix() for p in (RUN / 'operator-observation/terminal-originals').iterdir() if p.is_file()]
names += [p.relative_to(RUN).as_posix() for p in (RUN / 'operator-launch-preflight').iterdir() if p.is_file()]
correction = {
    'run_id': RUN.name, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'original_package_manifest_sha256': '8b1e5e2f2d369d4d765f4bfc0e7574651ef0fa2dae84b1e8199d5aa80762fae6',
    'original_package_files': 315, 'original_package_and_restore_preserved': True,
    'original_audit_failure': 'FileNotFoundError: operator/operator-observation/terminal-originals/run-manifest.json',
    'cause': 'Frozen packager collects registered operator.evidence and review dependencies. Terminal-originals and restoration sidecars had been preserved outside the package but not registered in operator.evidence.',
    'post_review_changes': ['operator.evidence'], 'review_applied_again': False,
    'before_manifest_sha256': digest(before), 'added_files': names,
    'candidate_source_or_permissions_changed': False, 'model_calls': 0, 'costs_changed': False
}
save(RUN / 'operator-package-coverage-correction.json', correction)
for name in names + ['operator-package-coverage-correction.json']:
    m['operator']['evidence'][name] = digest((RUN / name).read_bytes())
save(RUN / 'run-manifest.json', m)
verify_evidence(m, RUN)
validate_review(m, RUN / 'run-manifest.json')
created = create_package(RUN, Path('C:/meter-run-packages-20261005/agy-pro-r01-final-v2'))
save(Path('C:/meter-run-packages-20261005/agy-pro-r01-final-v2-create.json'), created)
restored = restore_package(Path(created['package']), Path('C:/meter-run-restores-20261005/agy-pro-r01-final-v2'), created['package_manifest_sha256'])
print(json.dumps({'corrected_package': created, 'restore': restored}))
