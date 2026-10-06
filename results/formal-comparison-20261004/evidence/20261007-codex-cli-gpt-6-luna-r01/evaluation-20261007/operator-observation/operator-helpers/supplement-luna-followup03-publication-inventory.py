"""Preserve the original inventory; record its single Windows path omission."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, shutil, sys

ROOT = Path.cwd()
RUN = Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01')
PUBLIC = ROOT / 'results/formal-comparison-20261004/evidence' / RUN.name
SNAPSHOT = PUBLIC / 'observation-awaiting-20261007'
CORRECTION = PUBLIC / 'publication-correction-20261007'
sys.path.insert(0, 'C:/meter-operator-20261004/scripts')
from benchmark_support import read, save, digest

source_name = 'docs/agent-runs/' + RUN.name + '/reproduction-and-hardware-check.md'
snapshot_name = 'operator-observation/source-snapshot/' + source_name
path = SNAPSHOT / snapshot_name
extended = Path('\\\\?\\' + str(path.resolve()))
raw = extended.read_bytes()
original_inventory = SNAPSHOT / 'snapshot-inventory.json'
assert snapshot_name not in read(original_inventory)['files']
assert len(str(path.resolve())) == 264 and not path.is_file() and extended.is_file()
assert {'bytes': len(raw), 'sha256': digest(raw)} == {
    key: read(RUN / 'operator-source-freeze.json')['sources'][source_name][key]
    for key in ('bytes', 'sha256')
}
destination = CORRECTION / 'inventory-supplement.json'
assert not destination.exists()
save(destination, {
    'run_id': RUN.name, 'round': 3, 'recorded_at': datetime.now(timezone.utc).isoformat(),
    'scope': 'Operator publication inventory only; original file bytes, source freeze, candidate execution, cost and verdicts unchanged.',
    'original_inventory_sha256': digest(original_inventory.read_bytes()),
    'cause': '264-character Windows path exists through the extended path prefix but ordinary Path.is_file() excludes it from the publisher inventory.',
    'additional_inventory_entries': {snapshot_name: {'bytes': len(raw), 'sha256': digest(raw)}},
    'frozen_source_entry': source_name,
    'original_inventory_preserved': True,
})
shutil.copy2(destination, RUN / 'operator-observation/operator-publication-inventory-supplement.json')
progress_path = ROOT / 'results/formal-comparison-20261004/progress.json'
progress = read(progress_path)
progress['observation_inventory_supplement'] = destination.relative_to(ROOT).as_posix()
save(progress_path, progress)
for document, link in [
    (ROOT / 'docs/experiments/next-comparison-readiness.md', '../../' + progress['observation_inventory_supplement']),
    (ROOT / 'results/formal-comparison-20261004/report.md', 'evidence/' + RUN.name + '/publication-correction-20261007/inventory-supplement.json'),
]:
    with document.open('a', encoding='utf-8') as stream:
        stream.write('\n2026-10-07 [관측 대기 파일 목록 보완](' + link + '): Windows 긴 경로 검사로 원본 inventory에서 빠진 재현 문서1개의 hash·크기를 동결 source와 대조해 추가 목록에 보존했다. 원본 inventory·문서 bytes·펌웨어·계측·판정은 유지한다.\n')
print(json.dumps({'inventory_supplement_created': True, 'source_hash_verified': True, 'original_inventory_preserved': True}))
