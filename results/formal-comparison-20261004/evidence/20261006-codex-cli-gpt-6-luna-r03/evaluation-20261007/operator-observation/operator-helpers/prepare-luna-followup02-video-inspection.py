from pathlib import Path
import subprocess, sys

prior = Path('C:/meter-followups-20261006/inspect-codex-sol-followup02-user-video.py')
text = prior.read_text(encoding='utf-8')
text = text.replace('20261006-codex-cli-gpt-6-sol-r02', '20261006-codex-cli-gpt-6-luna-r03').replace('Codex Sol followup2', 'Codex Luna followup2').replace('KakaoTalk_20261006_042359926.mp4', 'KakaoTalk_20261007_022215104.mp4')
text = text.replace("found=list((ROOT.parents[1]/'Documents').rglob('KakaoTalk_20261007_022215104.mp4'))", "found=[ROOT.parents[1]/'Documents/카카오톡 받은 파일/KakaoTalk_20261007_022215104.mp4']")
target = Path('C:/meter-followups-20261006/inspect-codex-luna-followup02-user-video.py')
assert not target.exists()
target.write_text(text, encoding='utf-8')
subprocess.run([sys.executable, '-B', '-X', 'utf8', str(target)], check=True)
