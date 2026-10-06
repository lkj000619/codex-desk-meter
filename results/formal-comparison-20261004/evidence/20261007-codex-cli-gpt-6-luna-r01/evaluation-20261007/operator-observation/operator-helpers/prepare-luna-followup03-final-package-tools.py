"""Reuse the established package and independent-audit procedures for final round3."""
from pathlib import Path
import shutil

ROOT = Path.cwd()
RUN = Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01')
OUT = RUN / 'operator-observation'
old_run = 'C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03'
def adapt(text):
    return text.replace(old_run, str(RUN).replace('\\', '/')).replace('followup02', 'followup03').replace('followup2', 'followup3').replace('followup-02', 'followup-03')

package = adapt(Path('C:/meter-followups-20261006/package-codex-luna-followup02-evaluation.py').read_text(encoding='utf-8'))
package = package.replace("if p.is_file():m", "if Path('\\\\\\\\?\\\\'+str(p.resolve())).is_file():m")
(RUN.parent / 'package-codex-luna-followup03-evaluation.py').write_text(package, encoding='utf-8')
audit = adapt(Path('C:/meter-run-packages-20261007/verify-codex-luna-followup02-evaluation.py').read_text(encoding='utf-8'))
audit = audit.replace("m['measurement']['tokens']['total'] is None", "m['measurement']['tokens']['total']==4090978")
audit = audit.replace("len(f['sources'])==38", "len(f['sources'])==37")
audit = audit.replace('raw_candidate_source_files_verified=38', 'raw_candidate_source_files_verified=37')
audit = audit.replace('==86', '==150').replace('first_serial_capture_bytes=86', 'first_serial_capture_bytes=150')
audit = audit.replace('5732', '5733').replace('217445082', 'd404366963')
start = audit.index("placement=read(")
end = audit.index("video=read(", start)
audit = audit[:start] + '''terminal=read(OBS/'terminal-verification.json')
assert original['operator']['status']==m['operator']['status']=='completed'
assert terminal['measurement']==m['measurement'] and terminal['raw_native_events']==229
events=[json.loads(line) for line in (OBS/'terminal-originals/stdout.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
completed=[event for event in events if event.get('type')=='turn.completed']
assert len(completed)==1 and completed[0]['usage']['input_tokens']==4032791 and completed[0]['usage']['output_tokens']==58187
correction=read(OBS/'operator-publication-correction.json')
inventory_raw=(OBS/'operator-publication-previous-checkpoint/snapshot-inventory.json').read_bytes()
assert correction['original_inventory_sha256']==digest(inventory_raw)
assert correction['original_publisher_sha256']==digest((OBS/'operator-helpers/publish-luna-followup03-optical-awaiting.py').read_bytes())
assert correction['original_inventory_round']==2 and correction['corrected_ledger_round']==3
supplement=read(OBS/'operator-publication-inventory-supplement.json')
assert supplement['original_inventory_sha256']==digest(inventory_raw) and supplement['round']==3
for name,item in supplement['additional_inventory_entries'].items():
    raw=Path('\\\\\\\\?\\\\'+str((OP/name).resolve())).read_bytes()
    assert len(raw)==item['bytes'] and digest(raw)==item['sha256']
''' + audit[end:]
audit = audit.replace('38.55', '48.17').replace("len(video['sample_frames'])==39", "len(video['sample_frames'])==48")
audit = audit.replace("user['button_answer_original']=='BOOT와 RESET 모두 누름'", "user['button_answer_original']=='BOOT와 RESET 모두'")
audit = audit.replace("len(ledger['runs'])==3", "len(ledger['runs'])==4")
audit = audit.replace('2965.735', '1773.142').replace("final['remaining_followup_rounds']==1", "final['remaining_followup_rounds']==0")
audit = audit.replace('remaining_followup_rounds=1)', 'remaining_followup_rounds=0)')
insertion = "closure=read(OBS/'operator-series-completion.json')\nassert closure['derived_state']=='remediation_round_limit_reached' and closure['followup_rounds']==3 and closure['candidate_invocations']==4\nassert closure['remaining_followup_rounds']==0 and not closure['additional_followup_allowed']\nassert closure['ledger_sha256']==digest((OP/'comparison-ledger.json').read_bytes())\nassert closure['series_normalized_tokens'] is None and closure['known_series_normalized_tokens']==34918496 and closure['token_measurement_coverage']=='3/4'\nassert ledger['runs'][2]['status']=='environment_failed' and ledger['runs'][2]['tokens']['total'] is None\n"
audit = audit.replace("audit=dict(read(", insertion + "audit=dict(read(")
audit = audit.replace("save(REST/'frozen-validator-audit.json',audit)", "audit.update(series_closed=True,derived_series_state=closure['derived_state'],known_series_normalized_tokens=34918496,series_token_measurement_coverage='3/4',publication_metadata_corrections_preserved=True)\nsave(REST/'frozen-validator-audit.json',audit)")
auditor = Path('C:/meter-run-packages-20261007/verify-codex-luna-followup03-evaluation.py')
auditor.write_text(audit, encoding='utf-8')

prior = ROOT / 'results/formal-comparison-20261004/evidence' / RUN.name / 'observation-awaiting-20261007'
previous = OUT / 'operator-publication-previous-checkpoint'
previous.mkdir(exist_ok=False)
shutil.copy2(prior / 'snapshot-inventory.json', previous / 'snapshot-inventory.json')
shutil.copy2(RUN.parent / 'publish-luna-followup03-optical-awaiting.py', OUT / 'operator-helpers/publish-luna-followup03-optical-awaiting.py')
shutil.copy2(Path(__file__), OUT / 'operator-helpers' / Path(__file__).name)
assert 'followup02' not in audit and '5732' not in audit and '38.55' not in audit
compile(package, 'package-followup03', 'exec')
compile(audit, 'audit-followup03', 'exec')
print('Prepared reused final package/audit procedures; original checkpoints retained.')
