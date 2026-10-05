"""Reuse the prior unchanged launch procedure with round/budget guards."""
from pathlib import Path
base=Path('C:/meter-followups-20261006')
source=(base/'launch-codex-sol-followup-01.py').read_text(encoding='utf-8')
rules=[
    ('20261006-codex-cli-gpt-6-sol-r01','20261006-codex-cli-gpt-6-sol-r02'),
    ('codex-sol-followup01-20261006','codex-sol-followup02-20261006'),
    ("previous['state'] == 'codex_sol_initial_evaluated_followup_pending'","previous['state'] == 'codex_sol_followup_01_evaluated_followup_02_pending'"),
    ("previous['product_executions_completed'] == 9","previous['product_executions_completed'] == 10"),
    ("previous['remaining_current_series_followup_rounds'] == 3","previous['remaining_current_series_followup_rounds'] == 2"),
    ('codex-sol-r01-final/frozen-validator-audit.json','codex-sol-followup01-final/frozen-validator-audit.json'),
    ("m['execution']['timeout_seconds'] == 7200","m['execution']['timeout_seconds'] == 6750"),
    ("len(ledger['runs']) == 2 and ledger['runs'][0]['reviewed'] and ledger['runs'][1]['status'] == 'prepared' and ledger['runs'][1]['round'] == 1",
     "len(ledger['runs']) == 3 and all(v['reviewed'] for v in ledger['runs'][:-1]) and ledger['runs'][-1]['status'] == 'prepared' and ledger['runs'][-1]['round'] == 2"),
    ("cleanup['deleted_files']==1413","cleanup['deleted_files']==3"),
    ("'round':1","'round':2"),
    ("'remaining_rounds_including_this':3,'remaining_seconds_including_this':7200",
     "'remaining_rounds_including_this':2,'remaining_seconds_including_this':previous['remaining_current_series_followup_seconds']"),
    ("'timeout_seconds':7200","'timeout_seconds':6750")]
for old,new in rules:
    assert old in source,old
    source=source.replace(old,new)
source=source.replace("assert not (CO/'build').exists() and not (CO/'build-host').exists()",
    "assert not (CO/'build').exists() and not (CO/'build-host').exists()\nassert not list(CO.rglob('*.pyc'))\nassert previous['series_effective_policy_status']=='invalid_for_comparison'\nassert abs(previous['remaining_current_series_followup_seconds']-6750.313)<.001")
target=base/'launch-codex-sol-followup-02.py';assert not target.exists();target.write_text(source,encoding='utf-8')
ps=(base/'launch-codex-sol-followup-01.ps1').read_text(encoding='utf-8').replace('launch-codex-sol-followup-01.py','launch-codex-sol-followup-02.py')
(base/'launch-codex-sol-followup-02.ps1').write_text(ps,encoding='utf-8')
print('Round2 launcher prepared, same native inventory and frozen benchmark runner; no invocation yet.')
