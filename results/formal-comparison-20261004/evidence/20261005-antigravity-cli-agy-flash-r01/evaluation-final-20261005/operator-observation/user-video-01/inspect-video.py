"""Preserve the user video and extract labeled visual evidence outside the candidate."""
from datetime import datetime,timezone
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

ROOT=Path.cwd()
RUN=Path('C:/meter-runs-20261005/20261005-antigravity-cli-agy-flash-r01')
OUT=RUN/'operator-observation/user-video-01'
sys.path[:0]=['C:/meter-operator-20261004/scripts','C:/meter-observer-tools/video-20261005']
from benchmark_support import digest,save
import imageio_ffmpeg
from PIL import Image,ImageDraw

found=list((ROOT.parents[1]/'Documents').rglob('KakaoTalk_20261005_041710515.mp4'))
assert len(found)==1
source=found[0]
stat=source.stat()
OUT.mkdir(exist_ok=False)
video=OUT/'source.mp4'
shutil.copyfile(source,video)
assert source.read_bytes()==video.read_bytes()
exe=imageio_ffmpeg.get_ffmpeg_exe()
probe=subprocess.run([exe,'-hide_banner','-i',str(video)],capture_output=True)
(OUT/'metadata-raw.txt').write_bytes(probe.stderr)
metadata=probe.stderr.decode('utf-8',errors='replace')
duration=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',metadata)
seconds=sum(float(x)*scale for x,scale in zip(duration.groups(),(3600,60,1)))
frames=OUT/'frames';frames.mkdir()
p=subprocess.run([exe,'-hide_banner','-i',str(video),'-vf','fps=1,scale=1280:-2','-compression_level','3',str(frames/'frame-%03d.png')],capture_output=True)
(OUT/'extraction-stdout.txt').write_bytes(p.stdout)
(OUT/'extraction-stderr.txt').write_bytes(p.stderr)
assert p.returncode==0
paths=sorted(frames.glob('*.png'))
sampled=[]
for index,path in enumerate(paths):
    sampled.append({'path':path.relative_to(OUT).as_posix(),'sample_index':index,
                    'nominal_sample_second':index+0.5,'sha256':digest(path.read_bytes())})
for start in range(0,len(paths),12):
    selected=paths[start:start+12]
    tiles=[]
    for index,path in enumerate(selected,start=start):
        im=Image.open(path).convert('RGB');im.thumbnail((450,360))
        tile=Image.new('RGB',(460,395),'#151a22');tile.paste(im,((460-im.width)//2,30))
        ImageDraw.Draw(tile).text((10,8),f'frame {index+1:03d} / approx {index+0.5:.1f}s',fill='white')
        tiles.append(tile)
    rows=(len(tiles)+2)//3
    sheet=Image.new('RGB',(3*460,rows*395),'#151a22')
    for n,tile in enumerate(tiles):sheet.paste(tile,((n%3)*460,(n//3)*395))
    sheet.save(OUT/f'contact-{start//12+1:02d}.jpg',quality=92)
report={'run_id':RUN.name,'received_at':datetime.now(timezone.utc).isoformat(),'source_path':str(source),
        'source_bytes':stat.st_size,'source_sha256':digest(video.read_bytes()),'preserved_source':'source.mp4',
        'source_filesystem_creation_time_utc':datetime.fromtimestamp(stat.st_ctime,timezone.utc).isoformat(),
        'source_filesystem_modified_time_utc':datetime.fromtimestamp(stat.st_mtime,timezone.utc).isoformat(),
        'duration_seconds':seconds,'ffmpeg_binary':exe,'ffmpeg_sha256':digest(Path(exe).read_bytes()),
        'operator_tools_root':'C:/meter-observer-tools/video-20261005','sample_frames':sampled,
        'capture_identity':'User supplied this as the current AGY Flash firmware video; filesystem save is after upload. Precise capture UTC is unknown.',
        'exact_input_to_display_or_button_latency':'not_measured','candidate_execution_repeated':False}
save(OUT/'video-metadata.json',report)
print(json.dumps({k:v for k,v in report.items() if k!='sample_frames'},ensure_ascii=False,indent=2))
print(metadata)
