# Argon 최초 실행·실물 평가와 영상 보완

2026-10-16 적용 범위: `20261016-antigravity-cli-agy-argon-high-r01`의 종료·동결·독립 검증·COM3 관측과 사용자가 제공한 현재 보드 영상. 시작 당시 [원본 기록](../report.md)·[50파일 inventory](../snapshot-inventory.json)·첫 포트 관측은 변경하지 않았다.

후보는 **18:04:36.026~19:01:43.821 KST, completed·exit 0, 3,427.781초(57분 7.781초)**로 종료했다. 정규화 token은 **968,377**(input 753,291 + output 215,086), provider total 968,377·cache read 19,433,199·thinking 58,188을 각각 보존한다. 별도 infrastructure probe 221.656초·46,989 token은 제품 최초 비용에 합산하지 않는다.

소스 commit은 `92ef8a6c4e389cacc8d025cf71fd4b04e52efdb2`다. 고정 입력 57개와 원본 source 92개를 확인했고, 생성 build/cache 파일만 Git metadata의 exclude로 구분했다. 후보 소스 변경·운영자 펌웨어 재빌드·추가 모델 호출은 없다. [원본 산출물 목록](artifact-inventory.json), [종료 manifest](run-manifest.json), [정책 검토](policy-review.json)를 따른다. 203개 도구 동작의 접근·명령·개입 검토는 eligible이며, native가 제공하지 않은 failed_commands·user_interventions 계측 null은 원본에 유지한다.

독립 복원본에서 원본 실행 파일로 **Python 5개·C 4개 시험을 통과**했다. Python 시험 중 동결 evaluate-product 29개 case는 고정 operator host-device pipeline 29개 시험을 대체하지 않는다. 후보 encoder는 공통 원본 payload의 `codex-reset.com`에 `FORBIDDEN_GLOBAL_RESET_SOURCE`를 내므로 정확한 자기 sender 경로는 미입증이다. 공통 raw frame 두 개는 원본 C receiver가 수락했다. 최초에 기본 registry의 다섯 provider fixture를 과거 공통 세 fixture와 잘못 비교한 운영자 guard 실패는 [host 검토](host-review.json)에 별도로 설명했다.

**19:09 KST COM3·USB `303A:1001`·MAC `28:84:85:B0:85:18`에 원본 bootloader/partition/app을 업로드했다.** App SHA-256은 `54789595efd2035011585b168cabbae792ff4dd682bc35876233f09dbd835ea3`, ELF는 `14a0131bd6fecd6c2b8e32ed2153caeea9ffd8be77d91657b7dc1e84f4d44d71`다. 후보 runbook의 잘못된 app 주소 `0x100000` 대신 원본 `build/flasher_args.json`의 `0x10000`을 사용했다. 전체 flash/NVS erase는 하지 않았다. [슬롯/명령](hardware-slot.json) · [업로드 원본](upload-stdout.txt).

두 번의 공통 frame 0/1 전송에서 각각 1,543 bytes씩 쓰고 실제 수락 로그를 확인했다. 그러나 **각 frame 수락 직후 `main` task stack overflow·`Rebooting...`·software reset이 발생해 총 4회** 확인됐다. Boot/오류 로그 ELF prefix가 원본 ELF와 일치한다. 첫 간이 tail 확인에서 빠졌던 수락과 오류를 전체 raw log로 보완했다. 기본 capture의 `accepted_at_seconds: null`은 후보의 다른 로그 형식을 인식하지 못한 값으로 보존하며, 별도 source 검토와 전체 로그에서 수락을 판정했다. [오류 검토](runtime-crash-review.json) · [수신/source 연결](receiver-source-review.json) · [raw 1](device-serial-r1.bin) · [raw 2](device-serial-r2.bin).

사용자는 “화면은 켜지지만 글자나 배치가 이상함”이라고 보고했다. 이어 제공한 **31.44초 영상**의 원본 SHA-256은 `c9b7007de5be051afe74cc561d9845b36939a59842edd79e60345476d751dee9`다. 1초 간격 31개 표본·contact sheet 3개와 detail frame 5/10/15/22/26을 확인했다. Header/body/footer 글자가 사각형·조각 형태로 손상돼 정상적인 58%·82%와 세 정보 내용을 읽을 수 없다. 여러 panel/행 색상 구성이 반복 전환되지만 버튼 종류·횟수는 아직 사용자 확인 전이다. 영상만으로 자동 재부팅·정확한 조작 시점·IMU 자동 회전·30초 정상 가독 화면을 추정하지 않는다. Serial에서 확정한 stack overflow와 영상의 글자 손상이 같은 원인인지는 진단하지 않았다. [영상 원본](video/source.mp4) · [검토](video/video-review.json) · [대표 상세 화면](video/readable-010.png).

| 항목 | 영상 보완 후 상태 | 근거 범위 |
|---|---|---|
| RM1 | pass | 원본 build/upload·일치 ELF의 부팅. 입력 후 안정 실행 합격과 구분 |
| RM2 | partial | operator replay의 실제 수락. 자기 sender 예외·수락 직후 재부팅 |
| RM3 | fail | 영상에서 손상된 glyph와 정상 58%·82% 미확인 |
| RM4 | fail | 화면 구성은 바뀌지만 세 정보 내용을 읽을 수 없음 |
| RM5 | not_run | BOOT/RESET 조작 확인 전. 영상의 변화만으로 탐색 합격 처리하지 않음 |

**Reference 미도달·product_pass false**다. 영상 이전 RM3 partial/RM4 not_run인 [최초 판정](reference-review.json)을 덮어쓰지 않고 [날짜 있는 영상 보완](video-reference-review.json)을 연결했다. 실행·소스·비용·정책·기존 5개 모델의 17회·5/15 series는 보존한다. 후속은 0회 사용, 최대 3회·누적 7,200초가 남아 있고 아직 예약·호출하지 않았다.

영상 이전 306파일 package는 [독립 복원 감사](restore-audit.json), 영상 보완 package는 [영상 포함 감사](video-restore-audit.json)를 따른다. 전체 원본 source bundle·artifact·fixed inputs·raw model/hardware·영상은 별도 로컬 package에 보존한다. 동결 operator baseline ZIP 자체가 286,505,344 bytes라 전체 ZIP은 Git에 추가하지 않고 [보존 경로와 hash](archive-receipt.json)를 기록했다. 저장소에는 판단과 주요 raw 증거·영상 사본을 남겼다.

후속 재개 시 같은 최초 run을 다시 호출하지 않는다. 현재 보드는 같은 Argon 원본이며 마지막 수신 뒤 재부팅한 상태다. COM3 serial은 닫았다. 추가 모델 지시가 있으면 자기 동결 source와 현재 관측·고정 기대·남은 예산을 연결하는 정상 후속 gate를 사용한다.
