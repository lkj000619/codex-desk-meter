"""Import frozen source bundles into a bare publisher without changing candidates."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path.cwd();ARCHIVE=Path('C:/meter-followups-20261007/source-branches-publication-20261008.git')
RECORD=Path('C:/meter-followups-20261007/source-branches-publication-20261008.json')
LEDGERS=[Path('C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-flash-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-antigravity-cli-agy-pro-r01.json'),
    Path('C:/meter-runs-20261005/ledgers/20261005-codex-cli-gpt-6-sol-r01.json'),
    Path('C:/meter-runs-20261006/ledgers/20261006-codex-cli-gpt-6-luna-r01.json')]
def git(*args,cwd=ROOT):
    return subprocess.check_output(['git','-c','core.longpaths=true',*map(str,args)],cwd=cwd,stderr=subprocess.PIPE).decode('utf-8').strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if not ARCHIVE.exists():ARCHIVE.mkdir();git('init','--bare',cwd=ARCHIVE)
assert git('rev-parse','--is-bare-repository',cwd=ARCHIVE)=='true'
url=git('remote','get-url','origin')
if not git('remote',cwd=ARCHIVE):git('remote','add','origin',url,cwd=ARCHIVE)
assert git('remote','get-url','origin',cwd=ARCHIVE)==url
formal=[];ledger_hashes={}
for ledger_path in LEDGERS:
    ledger=json.loads(ledger_path.read_text(encoding='utf-8'));ledger_hashes[str(ledger_path)]=sha(ledger_path)
    for entry in ledger['runs']:
        assert entry['reviewed'] and entry['status'] in {'completed','timeout','environment_failed','aborted'}
        directory=Path(entry['directory']);bundle=directory/'comparison-source.bundle';commit=entry['implementation_commit']
        assert sha(bundle)==entry['source_bundle_sha256']
        heads=dict(line.split() for line in git('bundle','list-heads',bundle).splitlines());assert heads.get(commit)=='HEAD'
        git('bundle','verify',bundle,cwd=ARCHIVE)
        branch='experiment/formal-comparison-20261004/'+entry['run_id'];git('check-ref-format','refs/heads/'+branch)
        git('fetch','--quiet','--no-tags',bundle,'HEAD:refs/heads/'+branch,cwd=ARCHIVE)
        assert git('rev-parse','refs/heads/'+branch,cwd=ARCHIVE)==commit
        formal.append({'run_id':entry['run_id'],'comparison_id':ledger['comparison_id'],'round':entry['round'],'execution_status':entry['status'],
            'reference_status':entry['reference_status'],'branch':branch,'commit':commit,'bundle':str(bundle),'bundle_sha256':entry['source_bundle_sha256']})
        print('Imported '+entry['run_id'],flush=True)
assert len(formal)==17 and len({x['run_id'] for x in formal})==17
existing=[]
for line in git('for-each-ref','--format=%(refname:short) %(objectname)','refs/heads/experiment','refs/heads/lkj000619/codex-reference-20260929').splitlines():
    branch,commit=line.split();git('fetch','--quiet','--no-tags',ROOT,'refs/heads/'+branch+':refs/heads/'+branch,cwd=ARCHIVE)
    assert git('rev-parse','refs/heads/'+branch,cwd=ARCHIVE)==commit
    existing.append({'branch':branch,'commit':commit,'scope':'Existing pilot/preparation/reference branch; not an additional formal attempt.'})
assert len(existing)==4
refs=formal+existing;advertised=git('ls-remote','--heads','origin',cwd=ARCHIVE)
remote={ref:commit for commit,ref in [x.split() for x in advertised.splitlines()]}
for row in refs:assert 'refs/heads/'+row['branch'] not in remote or remote['refs/heads/'+row['branch']]==row['commit'],row['branch']
objects=subprocess.check_output(['git','rev-list','--objects','--branches'],cwd=ARCHIVE)
checked=subprocess.run(['git','cat-file','--batch-check=%(objecttype) %(objectsize) %(rest)'],cwd=ARCHIVE,input=objects,capture_output=True,check=True).stdout
blobs=[]
for line in checked.splitlines():
    parts=line.split(b' ',2)
    if parts[0]==b'blob':blobs.append((int(parts[1]),parts[2].decode('utf-8',errors='replace') if len(parts)>2 else ''))
assert all(size<100*1024*1024 for size,name in blobs),'Blob exceeds GitHub100MiB limit; original commits must not be rewritten.'
for path,value in ledger_hashes.items():assert sha(Path(path))==value
record={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'prepared_not_pushed','repository':url,'bare_publisher':str(ARCHIVE),
    'formal_branch_count':17,'existing_branch_count':4,'formal_branches':formal,'existing_branches':existing,
    'ledger_hashes':ledger_hashes,'original_remote_heads':remote,'source_commits_rewritten':False,'candidate_checkouts_modified':False,
    'new_product_experiments_started':False,'largest_blobs':sorted(blobs,reverse=True)[:5]}
RECORD.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'formal_branches':17,'existing_branches':4,'largest_blob_bytes':max(x[0] for x in blobs),'status':'prepared_not_pushed'}))
