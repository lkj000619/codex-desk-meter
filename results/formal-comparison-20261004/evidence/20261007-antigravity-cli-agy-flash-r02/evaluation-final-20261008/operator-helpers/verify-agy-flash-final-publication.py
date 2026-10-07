"""Check staged bytes, inventories, cost binding, final closure and old history."""
from pathlib import Path
import hashlib, json, re, subprocess
ROOT=Path.cwd();FORMAL=ROOT/'results/formal-comparison-20261004'
RUN='20261007-antigravity-cli-agy-flash-r02';E=FORMAL/'evidence'/RUN
def extended(p):return Path('\\\\?\\'+str(p.resolve()))
def read(p):return json.loads(extended(p).read_text(encoding='utf-8'))
def digest(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git','-c','core.longpaths=true',*args],cwd=ROOT)
p=read(FORMAL/'progress.json');prior=json.loads(git('show','HEAD:results/formal-comparison-20261004/progress.json'))
for key in ('previous_series','closed_agy_pro_series','closed_codex_sol_series','codex_sol_result_at_transition','closed_codex_luna_series','codex_luna_result_at_transition','agy_flash_deferred_state_at_resumption','current_series_first_result','current_series_previous_result'):
    assert p[key]==prior[key],key
assert p['independent_series_completed']==5 and p['independent_series_planned']==15 and p['first_block_closed'] and not p['formal_comparison_complete']
assert p['product_executions_completed']==p['product_executions_started']==17
assert p['state']=='agy_flash_series_closed_reference_reached' and all(v=='pass' for v in p['rm_items'].values())
assert p['policy_status']=='eligible' and p['series_policy_status']=='invalid_for_comparison' and not p['quality_reference_cost_eligible'] and not p['product_pass']
assert p['remaining_current_series_followup_rounds']==0 and abs(p['remaining_current_series_followup_seconds']-4303.593)<0.00001
assert not p['additional_candidate_round_start_authorized_now'] and not p['next_model_start_authorized_now'] and not p['next_model_execution_started']
scopes=[E/name for name in ('observation-awaiting-20261007','cost-checkpoint-17-20261007','evaluation-final-20261008')]
inventories=0
for folder in scopes:
    inventory=read(folder/'snapshot-inventory.json')['files']
    actual={x.relative_to(extended(folder)).as_posix() for x in extended(folder).rglob('*') if x.is_file() and x.name!='snapshot-inventory.json'}
    assert actual==set(inventory),(folder,actual^set(inventory))
    for name,item in inventory.items():
        raw=extended(folder/name).read_bytes();assert len(raw)==item['bytes'] and digest(raw)==item['sha256'],name
    inventories+=len(inventory)
final=scopes[-1];audit=read(final/'restore-audit.json');closure=read(final/'operator-observation/operator-series-completion.json')
assert audit['files_verified']==588 and audit['package_manifest_sha256']==p['final_package_manifest_sha256']=='70027d7fff7b21712be780989409a8be699e1fb11a5d9901f02b28f05365206c'
assert closure['series_normalized_tokens']==3892990 and abs(closure['series_measured_seconds']-3659.220)<0.00001
assert closure['ledger_state']=='reached' and closure['effective_policy_status']=='invalid_for_comparison'
ledger=read(final/'ledger-at-review.json');assert len(ledger['runs'])==4 and all(x['reviewed'] for x in ledger['runs'])
assert ledger['runs'][:3]==read(scopes[0]/'ledger-before-reference-review.json')['runs'][:3]
assert digest(extended(final/'operator-observation/terminal-originals/run-manifest.json').read_bytes())==ledger['runs'][-1]['terminal_manifest_sha256']
video=read(final/'operator-observation/user-video-01/video-metadata.json')
assert video['duration_seconds']==62.87 and digest(extended(final/'operator-observation/user-video-01/source.mp4').read_bytes())==video['source_sha256']==p['video_sha256']
cost=read(scopes[1]/'cost-checkpoint-inputs.json');assert cost['unique_attempts']==17 and cost['token_measurement_coverage']=='16/17' and cost['known_normalized_tokens']==62535521 and cost['total_normalized_tokens'] is None
known=0;coverage=0;seen=set()
for item in cost['input_manifests']:
    raw=extended(scopes[1]/item['snapshot_path']).read_bytes();assert digest(raw)==item['sha256']
    m=json.loads(raw);assert m['run_id'] not in seen;seen.add(m['run_id'])
    token=m['measurement']['tokens']['total']
    if token is not None:known+=token;coverage+=1
assert len(seen)==17 and known==62535521 and coverage==16
binding=read(final/'cost-checkpoint-origin.json')
assert digest(extended(scopes[1]/'checkpoint-original.md').read_bytes())==binding['checkpoint_original_sha256']
assert digest(extended(ROOT/binding['checkpoint']).read_bytes().replace(b'\r\n',b'\n'))==binding['checkpoint_repository_lf_sha256']
names=[x.decode('utf-8') for x in git('diff','--cached','--name-only','-z').split(b'\0') if x]
allowed={'docs/DOCUMENTATION_MAP.md','docs/experiments/next-comparison-readiness.md','docs/plans/2026-10-04-formal-comparison-execution.md','docs/plans/2026-10-07-agy-flash-remaining-followups.md','results/formal-comparison-20261004/progress.json','results/formal-comparison-20261004/report.md','results/formal-comparison-20261004/comparison-checkpoint-17.md'}
prefixes=[folder.relative_to(ROOT).as_posix()+'/' for folder in scopes]
assert all(name in allowed or any(name.startswith(prefix) for prefix in prefixes) for name in names)
batch=subprocess.run(['git','-c','core.longpaths=true','cat-file','--batch'],cwd=ROOT,input=''.join(':'+name+'\n' for name in names).encode('utf-8'),capture_output=True,check=True).stdout
offset=0
for name in names:
    end=batch.index(b'\n',offset);header=batch[offset:end].split();assert header[1]==b'blob',name
    size=int(header[2]);blob=batch[end+1:end+1+size];offset=end+size+2
    raw=extended(ROOT/name).read_bytes()
    if name in allowed and name.endswith('.md'):raw=raw.replace(b'\r\n',b'\n')
    assert blob==raw,name
assert offset==len(batch)
for name in allowed:
    if not name.endswith('.md'):continue
    path=ROOT/name;text=path.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)\n]+)\)',text):
        if target.startswith(('http:','https:','app:','#')):continue
        resolved=(path.parent/target.split('#')[0]).resolve()
        assert extended(resolved).exists(),(name,target)
assert not git('diff','--name-only')
print(json.dumps({'staged_files_byte_verified':len(names),'inventory_files_verified':inventories,'final_package_files_verified':588,'closed_series':5,'cost_attempts':17,'coverage':'16/17','known_tokens':known,'prior_results_preserved':True,'new_links_resolve':True}))
