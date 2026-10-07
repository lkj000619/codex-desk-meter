"""Push explicit prepared refs atomically and verify exact remote commits."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path.cwd();RECORD=Path('C:/meter-followups-20261007/source-branches-publication-20261008.json')
p=json.loads(RECORD.read_text(encoding='utf-8'));archive=Path(p['bare_publisher']);rows=p['formal_branches']+p['existing_branches']
assert len(rows)==21 and p['status']=='prepared_not_pushed'
for row in rows:
    actual=subprocess.check_output(['git','rev-parse','refs/heads/'+row['branch']],cwd=archive,text=True).strip();assert actual==row['commit']
for path,sha in p['ledger_hashes'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
command=['git','-c','core.longpaths=true','push','--atomic','origin']+['refs/heads/'+r['branch']+':refs/heads/'+r['branch'] for r in rows]
result=subprocess.run(command,cwd=archive,capture_output=True)
out=RECORD.with_name('source-branches-push-stdout-20261008.txt');err=RECORD.with_name('source-branches-push-stderr-20261008.txt')
out.write_bytes(result.stdout);err.write_bytes(result.stderr)
p.update(push_command=command,push_exit_code=result.returncode,push_stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),push_stderr_sha256=hashlib.sha256(result.stderr).hexdigest())
RECORD.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(result.stdout.decode('utf-8',errors='replace'),end='');print(result.stderr.decode('utf-8',errors='replace'),end='',flush=True)
assert result.returncode==0,'Push failed; exact original refs/commits remain preserved.'
advertised=subprocess.check_output(['git','ls-remote','--heads','origin'],cwd=archive,text=True)
remote={ref:sha for sha,ref in [x.split() for x in advertised.splitlines()]}
for row in rows:assert remote.get('refs/heads/'+row['branch'])==row['commit'],row['branch']
for ref,sha in p['original_remote_heads'].items():assert remote.get(ref)==sha,'Existing remote ref changed: '+ref
for path,sha in p['ledger_hashes'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
for row in p['formal_branches']:assert hashlib.sha256(Path(row['bundle']).read_bytes()).hexdigest()==row['bundle_sha256']
p.update(status='pushed_and_remote_verified',verified_at=datetime.now(timezone.utc).isoformat(),verified_remote_heads={r['branch']:remote['refs/heads/'+r['branch']] for r in rows},
    original_remote_refs_preserved=True,original_ledgers_and_bundles_preserved=True)
RECORD.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'formal_branches_pushed':17,'existing_branches_pushed':4,'remote_sha_verified':21,'source_commits_rewritten':False,'previous_remote_refs_preserved':True}))
