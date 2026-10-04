"""Record user hold and preserve/extract current submitted-firmware video."""
from datetime import datetime,timezone
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

ROOT=Path.cwd();RUN=Path('C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02')
OUT=RUN/'operator-observation/user-video-01'
sys.path[:0]=['C:/meter-operator-20261004/scripts','C:/meter-observer-tools/video-20261005']
from benchmark_support import digest,read,save
import imageio_ffmpeg
from PIL import Image,ImageDraw

now=datetime.now(timezone.utc).isoformat()
hold={'recorded_at':now,'source':'Explicit user instruction while supplying current firmware video',
      'scope':'Hold candidate progression after current AGY Flash r02 evaluation; no additional AGY round or next model without user resumption.',
      'current_run':RUN.name,'next_model_start_authorized_now':False,'additional_candidate_round_start_authorized_now':False,
      'current_video_preservation_and_evaluation_allowed':True,'board_firmware_replacement_authorized_now':False}
save(RUN/'operator-user-hold.json',hold)
p=ROOT/'results/formal-comparison-20261004/progress.json';progress=read(p)
progress.update(checked_at=now,user_requested_hold=True,hold_scope=hold['scope'],
    next_model_start_authorized_now=False,additional_candidate_round_start_authorized_now=False,
    restart_instruction='User requested waiting after current AGY Flash firmware video. Preserve/evaluate this video and finalize r02 evidence only. Do not start another model or an AGY followup, replace firmware, or resume progression until explicit user resumption.')
save(p,progress)
found=list((ROOT.parents[1]/'Documents').rglob('KakaoTalk_20261005_054708010.mp4'))
assert len(found)==1
source=found[0];stat=source.stat();OUT.mkdir(exist_ok=False)
video=OUT/'source.mp4';shutil.copyfile(source,video)
assert digest(source.read_bytes())==digest(video.read_bytes())
exe=imageio_ffmpeg.get_ffmpeg_exe()
probe=subprocess.run([exe,'-hide_banner','-i',str(video)],capture_output=True)
(OUT/'metadata-raw.txt').write_bytes(probe.stderr)
metadata=probe.stderr.decode('utf-8',errors='replace')
duration=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',metadata)
seconds=sum(float(x)*scale for x,scale in zip(duration.groups(),(3600,60,1)))
frames=OUT/'frames';frames.mkdir()
result=subprocess.run([exe,'-hide_banner','-i',str(video),'-vf','fps=1,scale=1280:-2','-compression_level','3',str(frames/'frame-%03d.png')],capture_output=True)
(OUT/'extraction-stdout.txt').write_bytes(result.stdout);(OUT/'extraction-stderr.txt').write_bytes(result.stderr)
assert result.returncode==0
paths=sorted(frames.glob('*.png'))
sampled=[{'path':p.relative_to(OUT).as_posix(),'sample_index':i,'nominal_sample_second':i+0.5,'sha256':digest(p.read_bytes())} for i,p in enumerate(paths)]
for start in range(0,len(paths),12):
    tiles=[]
    for i,p in enumerate(paths[start:start+12],start=start):
        im=Image.open(p).convert('RGB');im.thumbnail((450,360))
        tile=Image.new('RGB',(460,395),'#151a22');tile.paste(im,((460-im.width)//2,30))
        ImageDraw.Draw(tile).text((10,8),f'frame {i+1:03d} / approx {i+0.5:.1f}s',fill='white')
        tiles.append(tile)
    sheet=Image.new('RGB',(1380,((len(tiles)+2)//3)*395),'#151a22')
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%3)*460,(i//3)*395))
    sheet.save(OUT/f'contact-{start//12+1:02d}.jpg',quality=92)
report={'run_id':RUN.name,'received_at':now,'source_path':str(source),'source_bytes':stat.st_size,
    'source_sha256':digest(video.read_bytes()),'preserved_source':'source.mp4','duration_seconds':seconds,
    'source_filesystem_creation_time_utc':datetime.fromtimestamp(stat.st_ctime,timezone.utc).isoformat(),
    'source_filesystem_modified_time_utc':datetime.fromtimestamp(stat.st_mtime,timezone.utc).isoformat(),
    'ffmpeg_binary':exe,'ffmpeg_sha256':digest(Path(exe).read_bytes()),'sample_frames':sampled,
    'capture_identity':'User supplied video in reply to current r02 upload/observation instructions; saved after 05:38:52 KST upload. Exact capture UTC unknown.',
    'precise_latency':'not_measured','candidate_execution_repeated':False,'user_hold_recorded':True}
save(OUT/'video-metadata.json',report)
shutil.copy2(Path(__file__),OUT/'inspect-video.py')
print(json.dumps({k:v for k,v in report.items() if k!='sample_frames'},ensure_ascii=False))
print(json.dumps({'sample_frames':len(paths),'contact_sheets':(len(paths)+11)//12}))
