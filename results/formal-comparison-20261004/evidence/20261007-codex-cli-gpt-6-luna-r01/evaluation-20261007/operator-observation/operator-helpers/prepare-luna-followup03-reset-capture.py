from pathlib import Path
import subprocess,sys
prior=Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03/operator-observation/hardware-post-upload-reset/capture-reset-and-frames.py')
out=Path('C:/meter-followups-20261007/20261007-codex-cli-gpt-6-luna-r01/operator-observation/hardware-post-upload-reset')
out.mkdir(exist_ok=False)
text=prior.read_text(encoding='utf-8').replace('20261006-codex-cli-gpt-6-luna-r03','20261007-codex-cli-gpt-6-luna-r01').replace('codex-luna-followup02-pre-observation','codex-luna-followup03-pre-observation').replace('frozen followup2 app','frozen followup3 app').replace('first 86-byte','first 150-byte')
target=out/'capture-reset-and-frames.py';target.write_text(text,encoding='utf-8')
subprocess.run([sys.executable,'-B','-X','utf8',str(target)],check=True)
