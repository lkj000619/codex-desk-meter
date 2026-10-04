"""Package prepared, unexecuted series and audit in a separate Python process."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from benchmark_support import digest, read, save


def zip_tree(source,target,skip_git=False):
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(source.rglob('*')):
            if path.is_file() and not (skip_git and '.git' in path.relative_to(source).parts):
                z.write(path,path.relative_to(source).as_posix())


def main():
    freeze=read(REPORT/'freeze.json')
    stage=Path('C:/meter-preparation-package-20261004-r2')
    reuse = '--reuse-stage' in sys.argv
    if reuse:
        for name, expected in read(stage/'package-inventory.json')['files'].items():
            assert digest((stage/name).read_bytes()) == expected, name
        assert (stage/'evidence/freeze.json').read_bytes() == (REPORT/'freeze.json').read_bytes()
    else:
        stage.mkdir(exist_ok=False)
    evidence=stage/'evidence'
    evidence.mkdir(exist_ok=reuse)
    for name in ('freeze.json','capability-summary.json','preparation-attempts.json','tests-final.txt','tests-final-status.json','final-review.md'):
        shutil.copyfile(REPORT/name,evidence/name)
    shutil.copytree(REPORT/'evidence',evidence/'evidence',dirs_exist_ok=reuse)
    for row in freeze['series']:
        original=Path(row['directory'])
        target=stage/'runs'/Path(row['profile']).stem
        if reuse:
            continue
        target.mkdir(parents=True)
        for source in original.iterdir():
            if source.name=='checkout':
                continue
            if source.is_dir():
                shutil.copytree(source,target/source.name)
            else:
                shutil.copyfile(source,target/source.name)
        shutil.copyfile(row['ledger'],target/'comparison-ledger.json')
        shutil.copyfile(row['receipt'],evidence/Path(row['receipt']).name)
        zip_tree(original/'checkout',target/'candidate-source.zip',skip_git=True)
        subprocess.run(['git','bundle','create',str(target/'candidate-source.bundle'),'HEAD'],cwd=original/'checkout',check=True,capture_output=True)
    shutil.copyfile(Path(freeze['series'][0]['directory'])/'operator-baseline.zip',stage/'operator-source.zip')
    shutil.copyfile(REPORT/'audit_preparation.py',stage/'audit_preparation.py')
    inventory={p.relative_to(stage).as_posix():digest(p.read_bytes()) for p in stage.rglob('*') if p.is_file() and p.name!='package-inventory.json'}
    save(stage/'package-inventory.json',{'schema_version':1,'files':inventory})
    package=Path('C:/meter-preparation-archives/20261004/preparation-package-r2.zip')
    package.parent.mkdir(parents=True,exist_ok=True)
    zip_tree(stage,package)
    destination=Path('C:/meter-preparation-restore-20261004-r2')
    result=subprocess.run([sys.executable,'-X','utf8',str(REPORT/'audit_preparation.py'),str(package),str(destination)],capture_output=True)
    (REPORT/'restore-audit-output.txt').write_bytes(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError('Independent restore failed; see restore-audit-output.txt')
    shutil.copyfile(destination/'audit-result.json',REPORT/'restore-audit.json')
    save(REPORT/'package-metadata.json',{'package_path':str(package),'package_sha256':digest(package.read_bytes()),'package_bytes':package.stat().st_size,
        'inventory_sha256':digest((stage/'package-inventory.json').read_bytes()),'restored_at':str(destination),
        'scope':'Prepared series, frozen operator source, exact candidate bytes, receipts and evidence; no product run.'})
    print((REPORT/'restore-audit.json').read_text(encoding='utf-8'))


if __name__=='__main__':
    main()
