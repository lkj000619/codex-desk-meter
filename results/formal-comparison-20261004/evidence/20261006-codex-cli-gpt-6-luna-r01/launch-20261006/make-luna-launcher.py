"""Reuse the tested Sol initial launcher, changing dated identities and transition guards."""
from pathlib import Path
import ast
source=Path('C:/meter-runs-20261005/launch-codex-sol-r01.py').read_text(encoding='utf-8')
source=source.replace('C:/meter-runs-20261005/20261005-codex-cli-gpt-6-sol-r01','C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01')
source=source.replace("Path('C:/meter-preflight-20261005/renewal')", "Path('C:/meter-preflight-20261006/luna-initial')")
source=source.replace("'codex-sol-receipt.json'", "'luna-prepared-receipt.json'").replace("'codex-sol-launch-20261005-receipt.json'", "'luna-launch-receipt.json'")
source=source.replace("'20261005'", "'20261006'").replace("'gpt-6-sol'", "'gpt-6-luna'").replace("'medium'", "'max'")
source=source.replace("'agy_pro_series_ended_round_limit'", "'codex_sol_series_closed_reference_reached_quality_ineligible'")
source=source.replace("== 8", "== 11")
source=source.replace("assert previous['remaining_current_series_followup_rounds'] == 0", "assert previous['closed_codex_sol_series']['ledger_state'] == 'reached' and not previous['additional_followup_allowed']")
source=source.replace('C:/meter-run-restores-20261005/agy-pro-r04-final/frozen-validator-audit.json','C:/meter-run-restores-20261006/codex-sol-followup02-final/frozen-validator-audit.json')
source=source.replace("previous['current_series_completion']", "previous['closed_codex_sol_series']")
source=source.replace("'\\uADF8\\uB7FC \\uB2E4\\uC74C \\uBAA8\\uB378\\uB85C \\uB118\\uC5B4\\uAC00\\uC790'", "'luna \\uC2DC\\uC791\\uD558\\uC790'")
source=source.replace('Proceed to independent Codex Sol series under existing comparison contract. Pro round limit and Flash deferred budget retained; no other candidate implementation provided.',
                      'Proceed to independent Luna initial series, block1/seed1 under frozen contract. Sol reached closure, Pro round limit and Flash deferred budget retained; no previous product implementation or observations supplied.')
source=source.replace('current/codex-sol-launch-20261005', 'current/codex-luna-launch-20261006')
source=source.replace('Codex initial call', 'Luna initial call')
source=source.replace("'model_invocations_during_preflight':0,", "'model_invocations_during_preflight':0,'old_unstarted_reservation_preserved':True,")
ast.parse(source)
assert 'gpt-6-sol' not in source and '20261005' not in source and 'agy_pro_series_ended' not in source
target=Path('C:/meter-runs-20261006/launch-codex-luna-r01.py'); assert not target.exists();target.write_text(source,encoding='utf-8')
ps=Path('C:/meter-runs-20261005/launch-codex-sol-r01.ps1').read_text(encoding='utf-8').replace('C:/meter-runs-20261005/launch-codex-sol-r01.py',str(target))
Path('C:/meter-runs-20261006/launch-codex-luna-r01.ps1').write_text(ps,encoding='utf-8')
print('Fresh Luna launcher prepared from prior initial-launch workflow; no model invoked.')
