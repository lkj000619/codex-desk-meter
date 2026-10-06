from pathlib import Path
import subprocess, sys

prior = Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r02/operator-observation/hardware-post-upload-reset/capture-reset-and-frames.py')
out = Path('C:/meter-followups-20261006/20261006-codex-cli-gpt-6-luna-r03/operator-observation/hardware-post-upload-reset')
out.mkdir(exist_ok=False)
text = prior.read_text(encoding='utf-8').replace('20261006-codex-cli-gpt-6-luna-r02', '20261006-codex-cli-gpt-6-luna-r03').replace('meter-run-restores-20261006/codex-luna-followup01-pre-observation', 'meter-run-restores-20261007/codex-luna-followup02-pre-observation').replace('frozen followup1 app', 'frozen followup2 app').replace('first zero-byte capture preserved', 'first 86-byte USB data log capture preserved; no complete accepted/rejected frame observed')
target = out / 'capture-reset-and-frames.py'
target.write_text(text, encoding='utf-8')
subprocess.run([sys.executable, '-B', '-X', 'utf8', str(target)], check=True)
