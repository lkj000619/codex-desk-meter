"""Record visual findings without applying the once-only RM review before capture identity is confirmed."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import sys
ROOT=Path.cwd()
RUN=Path('C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02')
OUT=RUN/'operator-observation/user-video-01'
PUB=ROOT/'results/formal-comparison-20261004/evidence'/RUN.name/'operator-observation/user-video-01'
sys.path.insert(0,str(ROOT/'scripts'))
from benchmark_support import digest,read,save
meta=read(OUT/'video-metadata.json')
freeze=read(RUN/'operator-source-freeze.json')
assert digest((OUT/'source.mp4').read_bytes())==meta['source_sha256']
report={'run_id':RUN.name,'reviewer':'Codex operator','reviewed_at':datetime.now(timezone.utc).isoformat(),
        'status':'awaiting_user_capture_identity_confirmation','video_sha256':meta['source_sha256'],
        'duration_seconds':meta['duration_seconds'],'expected_candidate_commit':freeze['commit'],
        'expected_app_sha256':freeze['artifacts']['firmware/build/cdm_meter.bin']['sha256'],
        'capture_time_utc':None,'capture_identity_note':'Filesystem save precedes second upload. No embedded capture timestamp. User confirmation of first r02 upload is pending.',
        'nominal_timestamps_are_precision_measurements':False,
        'visual_findings':[
            {'at_seconds':24.5,'frame':'readable-frame-025.jpg','screen':'STATUS',
             'text':['CDM METER STATUS','LINK:USB-OK STALE:NO','ERR:n/a','LAST-GOOD:2026-09-30T18:40:54Z','RETRY:host-polls-5s']},
            {'at_seconds':28.5,'frame':'readable-frame-029.jpg','screen':'DASHBOARD',
             'text':['CDM METER DASHBOARD','openai/five-hour REM 58% percent','R:n/a O:n/a'],
             'weekly_remaining_82_visible':False},
            {'at_seconds':30.5,'frame':'readable-frame-031.jpg','screen':'GLOBAL RESET',
             'text':['CDM METER GLOBAL RESET','GLOBAL RESET: default (no history)','src:codex-resets.com','obs:n/a'],
             'reference_reset_values_visible':False},
            {'at_seconds':32.5,'frame':'readable-frame-033.jpg','screen':'STATUS',
             'text':['CDM METER STATUS','LINK:USB-LOST STALE:NO','ERR:n/a','LAST-GOOD:2026-09-30T18:40:54Z','RETRY:reopen<=1Hz']},
            {'interval_seconds':[42.5,44.5],'screen':'blank_then_default_dashboard',
             'note':'Button manipulation coincides with text disappearing and awaiting-PC-frame screen. RST identity and spontaneous-reboot classification are not proven.'},
            {'interval_seconds':[50.5,55.5],'screen':'power_removed_then_default_dashboard',
             'note':'USB cable visibly disconnected and reconnected; display goes dark and boots without payload. This is an intentional power removal, not powered-link recovery proof.'}],
        'navigation':{'starting_screen':'STATUS','observed_path':['STATUS','DASHBOARD','GLOBAL RESET','STATUS'],
                      'nominal_view_times_seconds':[24.5,28.5,30.5,32.5],
                      'physical_button_manipulation_visible':True,'same_starting_information_returned':True,
                      'exact_button_press_count':None,'button_response_latency_ms':None,
                      'scope':'Visible cycle between three named views; correctness of displayed data is evaluated separately.'},
        'continuity':{'video_length_seconds':meta['duration_seconds'],
                      'sampled_display_visible_before_reset_seconds':[0.5,41.5],
                      'sample_interval_seconds':1,'continuous_30s_no_flicker_certified':False,
                      'note':'One-second samples do not rule out between-sample flicker. The later intentional cable removal is separate.'},
        'data_gaps':['Weekly remaining 82 is absent in the observed usage view.',
                     'Global reset reports no history despite frozen payload having reset dates.',
                     'STATUS says STALE:NO despite the input observations being stale.',
                     'Usage observation time is n/a and STATUS LAST-GOOD shows transport sent_at rather than source last_good_at.'],
        'draft_rm_status_if_capture_identity_confirmed':{'RM1':'pass','RM2':'partial','RM3':'partial','RM4':'partial','RM5':'pass'},
        'reference_reached':False,'whole_product_pass':False,'policy_status':'invalid_for_comparison',
        'rm_review_applied':False,'candidate_execution_repeated':False}
save(OUT/'video-review.json',report)
shutil.copyfile(Path(__file__),OUT/'record-video-review.py')
shutil.copyfile(Path('C:/meter-followups-20261004/inspect-opencode-r02-user-video.py'),OUT/'inspect-video.py')
PUB.mkdir(parents=True,exist_ok=False)
names=['video-metadata.json','video-review.json','metadata-raw.txt','record-video-review.py','inspect-video.py']
names += [p.name for p in sorted(OUT.glob('contact-*.jpg'))]
names += [p.name for p in sorted(OUT.glob('readable-frame-*.jpg'))]
for name in names:shutil.copyfile(OUT/name,PUB/name)
files={name:{'sha256':digest((PUB/name).read_bytes()),'bytes':(PUB/name).stat().st_size} for name in names}
save(PUB/'inventory.json',{'run_id':RUN.name,'files':files,'original_video':{'operator_path':str(OUT/'source.mp4'),
     'sha256':meta['source_sha256'],'bytes':meta['source_bytes'],'stored_outside_repository':True},
     'scope':'Video findings pending capture identity; no final RM review yet.'})
progress_path=ROOT/'results/formal-comparison-20261004/progress.json'
progress=read(progress_path)
progress.update(checked_at=datetime.now(timezone.utc).isoformat(),state='followup_timeout_awaiting_video_capture_identity',
                rm_review='pending_user_capture_identity_confirmation',
                optical_video_received=True,video_review=str(PUB/'video-review.json'),
                provisional_video_findings=report['draft_rm_status_if_capture_identity_confirmed'])
save(progress_path,progress)
print(json.dumps({'video_sha256':meta['source_sha256'],'review_status':report['status'],
                  'draft_rm_status':report['draft_rm_status_if_capture_identity_confirmed'],
                  'public_files':len(names),'final_review_applied':False},indent=2))
