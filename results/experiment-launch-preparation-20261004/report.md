# 정식 비교 시작 선행 작업 실행 결과

확인일: 2026-10-04. 상태: 코드·문서·활성 5개 실제 모델 검증 완료, baseline 동결·당일 실행 기록 연결 중.
작업 원본은 [계획](../../docs/plans/2026-10-03-formal-comparison-launch-prerequisites.md)과
[E1~E5 검토](../experiment-execution-review-20261003/report.md)다. 토큰 한도 중단 이후 같은 작업을 이어서 수행했다.
과거 평가 원본·commit/tag·evidence와 2026-10-02 준비 package는 보존한다.

## 시작 전 필요한 작업과 반영 내용

| 선행 작업 | 실제 보완 | 완료 근거 |
|---|---|---|
| E1 정책 준수→비교 적격성 연결 | 신규 benchmark의 필수 sidecar review, run/profile/input/raw 로그·개입 기록 결합, eligible만 품질 비교 | 정책·집계·패키지 회귀, 원본 manifest 불변 |
| E2 fresh 후속 세션의 과제·제한 재전달 | 최초 공통 task를 운영자 영역·ledger에 동결, 전문과 새 ID·잔여 예산 재전달, 자기 증거의 후보용 상대 경로·hash | 후속 제한·예산·원본 task·후보 사본 변조·독립 복원 시험 |
| E3 공통 명령과 native 권한 정합성 | OpenCode relative py_compile 허용, ref 이력 조회 제거, SDK/vendor native edit 거부; AGY git log 허용 제거 | 선언 회귀와 native 실효 config, 실제 정상 도구 사용 |
| E4 실제 CLI 문법 | `benchmark.py run <directory> --receipt ...`, 독립 반복별 ledger 경로 | 실제 run parser help와 문서 대조 |
| E5 AGY 전역 설정 경합·중단 | root 단위 OS lock·owner journal, child tree 종료 확인 후 복원, 복구 전 재진입 차단 | 임시 fixture의 동시 진입·강제 중단·복원·복구 실패 시험 |
| 추가: 고정 입력의 원본 bytes 복원 | Git 줄바꿈 변환과 별개로 후속 clone·package에서 57개 고정 입력·generated metadata·후속 증거 bytes 보존 | CRLF 변환을 강제한 회귀, 기존 prepare→archive→restore 시험 |
| 추가: Codex 전역 hook | runtime home의 8개 hook event 존재 확인, 비교 profile에서 hooks 명시 비활성화 | native feature `hooks=false`, 수정 조건으로 실제 capability 재실행 |

policy review는 운영자 판단을 구조화하며 로그만으로 준수를 자동 입증하지 않는다.
review digest는 변조 검사용이며 전자서명이나 검토자 신원 인증을 대신하지 않는다.
후보 checkout 밖의 운영자 기록을 신뢰 경계로 사용한다.
미검토·위반·미검증 결과도 전체 시도·실패 비용과 제외 사유를 보존한다.
RM 도달 비용은 앞선 모든 회차가 적격이어야 인정하며 과거 flag 없는 실행에 소급하지 않는다.

## 공통 입력과 동결 범위

새 baseline 예정 tag는 `comparison-baseline-20261004`다. 후보 allowlist 57개/필수 MD 3개를 유지한다.
2026-10-03 계획의 “57개 bytes 모두 이전과 동일” 조건은 E3 수정으로 다음 비교에 한해 정정한다:
`experiments/config/agy-pilot-permissions.json`의 git log 허용 규칙을 제거한 1개 파일만 바꾸고
나머지 56개 archive bytes는 이전 `85ba108`과 같음을 확인한다. 활성 후보 5개에는 같은 새 입력을 제공한다.
제품 계약·fixture·공통 과제 내용은 변경하지 않는다. 원래 baseline을 덮어쓰지 않는다.

baseline에는 평가 기준·운영 도구·새 profile을 함께 고정한다. `operator-baseline.zip`은 후보
checkout 밖에 보관하며 입력/평가 hash를 재계산해 독립 복원을 검증한다.
본문에 baseline commit 자체를 자기 참조로 넣지 않으며 실제 commit·tree·ZIP hash는 후속 freeze 기록에 남긴다.

## 실제 준비 검증 범위

별도 ASCII root `C:/meter-preflight-20261004`의 빈 ESP-IDF 앱·산술 CTest를 사용한다.
제품 source·이전 후보 구현·실물 serial은 제공하지 않는다.
[검증 실행기](run_capability.py)는 read/write/list/host_build/host_test/idf_build/vendor_reference/
telemetry/settings 근거와 모든 시도의 원본·비용을 남긴다.
[native inventory 수집기](native_inventory.py)는 읽기 전용 native 설정을 수집한다.

첫 Sol 검증과 첫 OpenCode 검증은 수정 전 조건에서 성공했으므로 실패 비용과 함께 준비 시도로 보존하며,
최종 비교 조건의 근거는 hook 비활성화 이후 재검증에서 선택한다.
Codex native skills/list는 동일 skills/feature override를 사용하는 app-server 검증이며,
exec의 `--ignore-user-config`와 구성 layer가 같다고 주장하지 않는다. 실행 argv와 feature override,
실제 exec 원본을 함께 확인한다. 사용자 hook 원문·credentials·AGY private backup은 공개하지 않는다.

현재 원본 모델 목록·version만으로 capability를 pass로 처리하지 않는다.
provider quota나 권한 오류가 있으면 원본과 미해결 항목을 남긴다. 준비 비용은 제품 최초/후속 예산에 넣지 않는다.
제품의 BSP·LCD·BOOT·단절 복구 합격은 이번 준비 검증 범위가 아니며 후보 제출 이후 평가한다.

## 실행 순서와 잔여 조건

독립 반복은 3개 블록(5개 조합×3회=15개 최초 series)이며 후속은 각자 최대 3회·누적 120분이다.
한 series의 최초 120분과 합쳐 최대 4시간, 후보 시간 전체 상한은 60시간이다.
provider 사용량과 보드 관측 시간은 예약으로 보장할 수 없으므로 시작 직전에 확인한다.
당일 첫 블록 5개의 ID·ledger·receipt를 hash에 결합하고 이후 블록은 실제 시작일에 새로 준비한다.
한 보드의 flash/serial/광학 관측은 후보 결과가 동결된 뒤 하나씩 수행한다.
실험 실행 시 series→operator 관측→RM·정책 review→필요한 후속→다음 대상 순서를 따른다.

최종 검증 결과, 모델별 capability, 동결과 준비 예약의 실제 상태는 이 보고서 후속 기록과
[다음 비교 상태](../../docs/experiments/next-comparison-readiness.md)에 기록한다.

## 2026-10-04 검증 결과

- 전체 회귀: **220개 중 219개 통과·1개 skip, 실패 0**. [원본](tests-final.txt). skip은 Windows symlink 생성 권한 제한이며 IDF child 환경 시험은 통과했다. [독립 최종 검토](final-review.md)의 추가 3건도 보완했다.
- 활성 5개 실제 capability: **모두 pass**. [기계 목록](capability-summary.json). raw tool events·CTest 원본·빈 앱 bin/ELF/map/bootloader/partition bytes를 각각 보존했다.
- 사용자 결정: Claude를 이번 비교에서 제외한다. AGY의 기존 Opus 4.6 호출은 모델 미지원 오류(exit 1, 모델 turn 0)로 실패했다. Opus 5.5를 대신 선택하지 않았다.
- 모든 준비 모델 시도와 비용은 [전체 시도](preparation-attempts.json)에 보존한다. 원래 probe profile hash와 검토 후 profile hash를 구분한다. argv·model·effort·CLI version·접근 조건은 동일하며 검토된 inventory/설명만 갱신했음을 필드 대조로 확인했다.
- AGY native MCP·plugins·custom agents는 비어 있고 wrapper 전후 전역 파일 bytes가 같았다. CLI가 노출하는 browser/MCP/subagent 도구 이름 목록은 사용 허가·실제 호출을 뜻하지 않는다.
- AGY 두 probe는 공개 SDK를 view_file로 읽으며 요청한 8줄보다 큰 파일 범위를 보고했다. native 비동기 build task와 Flash schedule 사용도 원본에 남겼다. 준비 read capability는 승인 source 접근을 확인한 것이며 모든 지침의 준수나 표면별 내부 흐름이 같음을 보장하지 않는다. 본 비교는 별도 정책 review로 이를 판정한다.
- Codex IDF build는 SDK Git dubious-ownership 진단을 출력했지만 실제 빌드·artifact 생성은 성공했다. SDK 설정을 변경하지 않았다.
- 현재 읽기 전용 포트 열거에는 COM1만 있고 원래 ESP32 COM3/VID_303A는 확인되지 않았다. 후보 구현 세션은 보드 접근을 금지한다. flash·serial·광학 평가 전에 실제 보드를 연결하고 포트·VID/PID를 재확인한다. 확인하지 않은 실물 항목은 not_run으로 남긴다.
