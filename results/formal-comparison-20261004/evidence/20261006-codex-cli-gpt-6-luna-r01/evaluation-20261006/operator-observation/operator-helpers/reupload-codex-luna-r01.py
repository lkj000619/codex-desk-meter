"""User-authorized repeat upload of the same frozen firmware; preserve attempt1."""
from datetime import datetime, timezone
from pathlib import Path
import json, subprocess, sys
RUN=Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01')
OUT=RUN/'operator-observation';ATTEMPT=OUT/'hardware-attempt-02'
assert not ATTEMPT.exists()
ATTEMPT.mkdir()
note={'run_id':RUN.name,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'user_report':'다시 업로드 요청 esp32 com3에 연결하지않았었음',
    'first_attempt_record':'operator-observation/hardware-slot.json',
    'scope':'Earlier esptool success/VID303A PID1001 MAC28:84:85:B0:85:18 logs retained. User reports intended board was not connected; physical association of attempt1 is unconfirmed. Do not count attempt1 as user optical observation.',
    'same_original_firmware':True,'candidate_model_rerun':False,'operator_rebuild':False,
    'new_attempt_directory':ATTEMPT.relative_to(RUN).as_posix()}
(ATTEMPT/'user-reupload-request.json').write_text(json.dumps(note,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=(RUN.parent/'observe-codex-luna-r01.py').read_text(encoding='utf-8')
source=source.replace("OUT=RUN/'operator-observation'","OUT=RUN/'operator-observation/hardware-attempt-02'")
target=RUN.parent/'observe-codex-luna-r01-upload02.py';target.write_text(source,encoding='utf-8')
subprocess.run([sys.executable,'-B','-X','utf8',str(target)],check=True)
