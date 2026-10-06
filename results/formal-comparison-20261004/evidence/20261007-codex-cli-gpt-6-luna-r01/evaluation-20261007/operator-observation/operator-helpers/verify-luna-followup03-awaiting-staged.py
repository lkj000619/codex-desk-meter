from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path.cwd();BASE='results/formal-comparison-20261004/evidence/20261007-codex-cli-gpt-6-luna-r01/'
prefixes=[BASE+'observation-awaiting-20261007/',BASE+'publication-correction-20261007/']
def git(*args):return subprocess.check_output(['git','-c','core.longpaths=true',*args],cwd=ROOT)
allowed={'docs/DOCUMENTATION_MAP.md','docs/experiments/next-comparison-readiness.md','docs/plans/2026-10-06-codex-luna-remaining-followups.md','results/formal-comparison-20261004/progress.json','results/formal-comparison-20261004/report.md','results/formal-comparison-20261004/comparison-checkpoint-15.md'}
files=git('diff','--cached','--name-only','-z').decode('utf-8').rstrip('\0').split('\0')
assert all(any(name.startswith(prefix) for prefix in prefixes) or name in allowed for name in files)
raw_names=[name for name in files if any(name.startswith(prefix) for prefix in prefixes) or name.endswith('/progress.json')]
data=subprocess.check_output(['git','-c','core.longpaths=true','cat-file','--batch'],input=''.join(':'+name+'\n' for name in raw_names).encode('utf-8'),cwd=ROOT)
position=0
for name in raw_names:
    end=data.index(b'\n',position);header=data[position:end].split();assert len(header)==3 and header[1]==b'blob'
    size=int(header[2]);staged=data[end+1:end+1+size];position=end+2+size
    assert staged==Path('\\\\?\\'+str((ROOT/name).resolve())).read_bytes(),name
assert position==len(data)
inventory_count=0
expected_files=set(allowed)
for prefix in prefixes:
    inventory=json.loads((ROOT/prefix/'snapshot-inventory.json').read_text(encoding='utf-8'))
    for name,item in inventory['files'].items():
        raw=Path('\\\\?\\'+str((ROOT/prefix/name).resolve())).read_bytes()
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],name
    inventory_count+=len(inventory['files'])
    expected_files.update(prefix+name for name in inventory['files'])
    expected_files.add(prefix+'snapshot-inventory.json')
supplement_path=BASE+'publication-correction-20261007/inventory-supplement.json'
supplement=json.loads((ROOT/supplement_path).read_text(encoding='utf-8'))
assert supplement['round']==3 and supplement['original_inventory_preserved']
assert supplement['original_inventory_sha256']==hashlib.sha256((ROOT/prefixes[0]/'snapshot-inventory.json').read_bytes()).hexdigest()
freeze=json.loads((ROOT/prefixes[0]/'operator-source-freeze.json').read_text(encoding='utf-8'))
assert len(supplement['additional_inventory_entries'])==1
for name,item in supplement['additional_inventory_entries'].items():
    raw=Path('\\\\?\\'+str((ROOT/prefixes[0]/name).resolve())).read_bytes()
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
    assert all(freeze['sources'][supplement['frozen_source_entry']][key]==item[key] for key in ('bytes','sha256'))
    expected_files.add(prefixes[0]+name)
expected_files.add(supplement_path)
assert set(files)==expected_files,{'missing':sorted(expected_files-set(files)),'unexpected':sorted(set(files)-expected_files)}
for name in [x for x in allowed if x.endswith('.md')]:
    for target in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text(encoding='utf-8')):
        if any(part in target for part in ('observation-awaiting-20261007','evaluation-20261007','comparison-checkpoint-15','publication-correction-20261007')):
            assert (ROOT/name).parent.joinpath(target).resolve().exists(),(name,target)
old=json.loads(git('show','HEAD:results/formal-comparison-20261004/progress.json'))
new=json.loads((ROOT/'results/formal-comparison-20261004/progress.json').read_text(encoding='utf-8'))
for key in ['previous_series','closed_agy_pro_series','deferred_agy_flash_series','closed_codex_sol_series','codex_sol_result_at_transition','current_series_first_result','current_series_previous_result']:assert old[key]==new[key],key
assert new['product_executions_completed']==15 and new['total_normalized_tokens_all_attempts'] is None and new['token_measurement_coverage']=='14/15'
for prefix in [BASE+'launch-20261007','results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r02']:
    assert not git('status','--porcelain',prefix)
assert not subprocess.check_output(['git','status','--porcelain'],cwd='C:/meter-operator-20261004')
assert not subprocess.check_output(['git','status','--porcelain'],cwd='C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01/checkout')
print(json.dumps({'staged_files':len(files),'byte_exact_blobs':len(raw_names),'inventory_files':inventory_count,'new_links_valid':True,'historical_state_preserved':True}))

note=json.loads((ROOT/BASE/'publication-correction-20261007/correction-note.json').read_text(encoding='utf-8'))
inventory=ROOT/BASE/'observation-awaiting-20261007/snapshot-inventory.json'
assert note['original_inventory_sha256']==hashlib.sha256(inventory.read_bytes()).hexdigest()
assert note['original_inventory_round']==2 and note['corrected_ledger_round']==3 and new['round']==3
assert new['candidate_terminal_status_observed']=='completed' and new['tokens']['total']==4090978
assert new['state']=='codex_luna_followup_03_uploaded_awaiting_optical_observation'
assert new['observation_inventory_supplement']==supplement_path
assert new['remaining_current_series_followup_rounds']==0 and not new['additional_candidate_round_start_authorized_now']
assert new['known_normalized_tokens_all_attempts']==61608453 and new['current_series_known_normalized_tokens']==34918496
cost=json.loads((ROOT/BASE/'observation-awaiting-20261007/cost-checkpoint-inputs.json').read_text(encoding='utf-8'))
assert len(cost['input_manifests'])==15 and cost['token_measurement_coverage']=='14/15'
known=[]
for item in cost['input_manifests']:
    raw=(ROOT/BASE/'observation-awaiting-20261007'/item['snapshot_path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    token=json.loads(raw)['measurement']['tokens']['total']
    if token is not None:known.append(token)
assert len(known)==14 and sum(known)==61608453
assert hashlib.sha256((ROOT/cost['checkpoint']).read_bytes()).hexdigest()==cost['checkpoint_sha256']
