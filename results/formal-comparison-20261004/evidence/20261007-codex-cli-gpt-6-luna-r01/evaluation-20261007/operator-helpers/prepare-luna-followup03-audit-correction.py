"""Correct the independent audit's overlong literal boot-hash assertion."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json

ROOT = Path('C:/meter-run-packages-20261007')
REST = Path('C:/meter-run-restores-20261007/codex-luna-followup03-evaluation')
original = ROOT / 'verify-codex-luna-followup03-evaluation.py'
revised = ROOT / 'verify-codex-luna-followup03-evaluation-v2.py'
assert not revised.exists()
source = original.read_text(encoding='utf-8')
source = source.replace('import json, sys, zipfile', 'import json, re, sys, zipfile')
source = source.replace('FROZEN.mkdir(exist_ok=False)', 'FROZEN.mkdir(exist_ok=True)')
source = source.replace("assert b'd404366963' in raw and b'esp_psram: SPI SRAM memory test OK' in raw", "boot_prefix=re.search(rb'ELF file SHA256:\\s*([a-f0-9]+)',raw)\nassert boot_prefix and len(boot_prefix.group(1))>=9 and digest(elf).startswith(boot_prefix.group(1).decode())\nassert b'esp_psram: SPI SRAM memory test OK' in raw")
source = source.replace("save(REST/'frozen-validator-audit.json',audit)", "procedure=read(REST/'operator-audit-procedure-correction.json')\nassert procedure['original_auditor_sha256']==digest((OBS/'operator-helpers/verify-codex-luna-followup03-evaluation.py').read_bytes())\nassert procedure['corrected_auditor_sha256']==digest(Path(__file__).read_bytes())\naudit['operator_audit_procedure_correction']=procedure\nsave(REST/'frozen-validator-audit.json',audit)")
compile(source, str(revised), 'exec')
revised.write_text(source, encoding='utf-8')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
note = {
    'run_id': '20261007-codex-cli-gpt-6-luna-r01',
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'scope': 'Independent operator audit procedure only; original584-file package and all candidate/source/artifact/native-cost/physical records preserved.',
    'original_auditor_sha256': sha(original), 'corrected_auditor_sha256': sha(revised),
    'original_error': 'Line45 literal d404366963 required10 hash characters; the original ESP boot log prints the correct9-character prefix d40436696...',
    'correction': 'Extract the actual printed prefix, require at least9 characters and match it against the preserved full ELF hash. Reuse the already extracted frozen validator directory and the same immutable package.',
    'candidate_execution_repeated': False, 'source_or_firmware_modified': False,
    'host_tests_repeated': False, 'hardware_operation_repeated': False,
}
(REST / 'operator-audit-procedure-correction.json').write_text(json.dumps(note, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'original_package_preserved': True, 'correct_boot_prefix': 'd40436696', 'audit_v2_prepared': True}))
