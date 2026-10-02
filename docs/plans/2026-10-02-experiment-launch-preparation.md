# 본실험 실행 준비 계획

작성일: 2026-10-02. 상태: **준비 완료·본 실험 시작 전 정지**. 제품 공통 시작점: `85ba1089226a2e3198983a42eea375a3fd7e6ed0`.
사용자 지시: profile 갱신 → 실제 CLI 사전 테스트 → 실험 설정 고정. 준비 완료 후 정지하며 본실험은 시작하지 않는다.

## 목표와 범위

[운영 계약](../experiments/comparison-operating-contract.md)과
[준비 상태](../experiments/next-comparison-readiness.md)의 실행 설정·capability·동결 항목을 준비한다.
실제 CLI 호출은 제품 코드를 제공하지 않은 별도 ASCII 경로의 준비 probe에만 사용한다.
준비 비용·model 원본 telemetry는 후보 최초 실행과 분리한다. 기존 중지 작업과 후보는 재개하지 않는다.

## 모델과 입력

현재 설치본의 version/help·모델 목록으로 기존 계획의 대상에 대응하는 profile을 확정한다.
명시한 기존 ID가 목록에 있으면 유지한다. 목록 노출과 실제 호출 성공은 별도 근거로 기록한다.

| 대상 | 정확한 모델·effort | 근거·선택 |
|---|---|---|
| Codex Sol | `gpt-5.6-sol`, medium | 기존 후보 profile 유지, 현재 catalog에 존재 |
| Codex Luna | `gpt-5.6-luna`, max | 기존 후보 profile 유지, 현재 catalog에 존재 |
| OpenCode | `opencode/muse-spark-1.3-contributor-free` | 기존 비교 대상 유지, 현재 모델 목록에 존재 |
| Antigravity Flash | `gemini-3.8-flash-medium` | 기존 실제 후보의 medium 유지 |
| Antigravity Pro | `gemini-3.1-pro-high` | 기록된 Pro 계열 중 high를 고정. low와 혼합하지 않음 |
| Antigravity Claude | `claude-opus-4-6-thinking` | 기록된 Opus Thinking ID 유지 |

## 작업 상태와 완료 조건

1. [x] 실제 version·help·model 목록과 run별 확장 기능/권한 설정을 기록한다. 과거 profile은 보존하며 새 profile을 작성한다.
2. [x] 읽기·쓰기·목록·host build/test·IDF build·제조사 source 읽기·settings·telemetry를 해당 CLI의 실제 준비 session에서 확인한다.
   허용·거부 관측과 실제 source/artifact/log hash를 보존한다. 권한 선언이나 dummy process로 실제 session을 대체하지 않는다.
3. [x] 동일 baseline·입력과 고정 profile에서 `check`·`prepare`·comparison `init`을 수행하고 profile-bound receipt를 만든다.
   호출 전에 receipt의 구조·hash·capability 연결과 prepared 상태를 검증한다. 후보 prompt는 전달하지 않는다.
4. [x] 동일 조건의 실행 목록·순서·예산·포트/관측 절차와 독립 복원 가능한 준비 증거 package를 고정한다.
5. [x] readiness·문서 지도·보고서 갱신, 최종 검토와 fresh 검증 완료. 이전 conditional push의 기준을 충족했다. 게시 commit과 push 여부는 Git 이력·원격 HEAD로 확인하고 본 실험 전 정지한다.

## 유지할 경계

- 실제 provider 계정 값·credential 내용은 문서/로그/profile에 기록하지 않는다. CLI의 정상 인증 경로를 사용한다.
- 전역 사용자 설정을 지속 변경하지 않는다. 실행 전용 설정은 별도 디렉터리/프로세스로 구성한다.
  AGY는 기존 scoped wrapper로 다른 AGY 프로세스가 없는지 확인한 뒤 설정·instructions·hooks를 private backup하고 한 세션 동안만 제한하며 원본 bytes를 복원한다.
  인증 파일은 복사하지 않으며 private backup은 공개 증거에 포함하지 않는다. 다른 작업·과거 tag·원본 evidence는 보존한다.
- COM3 연결은 확인됐지만 port 열거를 펌웨어/LCD pass로 해석하지 않는다. 준비 단계에서 flash·erase·제품 전송을 수행하지 않는다.
- 제품 parser/BSP/LCD 구현을 미리 작성하거나 다른 후보/reference 제품 코드를 준비 session에 제공하지 않는다.
- 기본 입력의 필수 MD 3개와 allowlist를 유지한다. 실제 후보의 제품 실패는 결과로 남긴다.
- 준비 완료는 본실험 실행 승인이 아니다. prepared 후보의 `benchmark.py run`을 호출하지 않는다.

## 검증 기록과 판정

진행 ledger와 원본 준비 log는 `artifacts/experiment-preparation-20261002/` 및 별도 ASCII probe root에 저장한다.
정리한 기계 목록·판정은 `results/experiment-preparation-20261002/`에 기록한다.
현재 운영 source는 사용자 요청에 따라 main에서 기존 작업을 이어서 정리하고 실제 probe는 격리된 디렉터리에서 수행한다.
프로젝트의 계획·증거 경로와 사용자의 정지 조건을 스킬 기본 workspace/finish 단계보다 우선한다.

Ruling: 이전 모델 계획의 Sol/Luna ID가 현재 목록에 있으므로 최신 세대 모델로 바꾸지 않는다. 바꾸면 다른 비교 조건이 되는 비용이 있다.
Ruling: Pro effort는 현재 목록의 high로 고정한다. 사용자 선호가 다르면 별도 profile/조건을 새로 고정해야 한다.
Ruling: 포트 연결 완료와 제품 관측 완료를 구분한다. 제품 관측은 후보 실행 이후이며 준비 완료의 선행 제품 합격 gate로 추가하지 않는다.
Ruling: AGY 1.2.11은 공개 도움말/설정 문서에 별도 settings root override가 없다. 검증된 기존 scoped wrapper를 순차 사용하고 복원 hash를 확인한다. 사용자 전역 설정의 지속 변경은 하지 않는다.
Ruling: IDF activation은 공용 shim을 쓰므로 병렬 activation의 파일 충돌이 관측됐다. 환경 활성화는 순차 수행하며 독립 probe 작업만 병렬화한다.
Ruling: AGY 초기 프로필의 bare `--print`가 다음 옵션을 prompt로 소비했다. 보존된 argv 후보의 UTF-8 stdin → 단일 `--print=VALUE` 어댑터를 재사용한다. 실패한 준비 호출은 비용 기록에 남긴다.
Ruling: Codex의 unelevated sandbox에서 Python asyncio pipe가 WinError 5로 실패했다. 동일 workspace-write 범위를 유지한 공식 elevated sandbox의 pipe 진단은 성공했다. sandbox를 끄지 않고 elevated 설정으로 다시 확인한다.
Ruling: skip_host_skill_discovery만으로는 사용자 스킬 9개가 활성으로 남았다. native skills/list로 발견한 사용자 스킬 경로를 skills.config에서 각각 비활성화하고 system 스킬 5개는 유지했다. 전역 설정은 변경하지 않는다.
Ruling: 최종 Codex 준비 session 두 개가 provider usage limit으로 종료됐다. 실패한 원본을 보존하고 CLI가 안내한 재시도 시각이 지난 뒤 동일 profile로 새 준비 session을 실행했다. 제품 예산과 별도로 집계한다.
Ruling: 동시 준비 build 중 Flash의 ESP-IDF GCC 내부 오류 1회가 관측됐다. CLI process exit 0을 build pass로 보지 않는다. 원본 실패를 보존하고 동일 source/profile의 독립 순차 probe로 재검증한다. 원인이 동시 실행이라고 단정하거나 SDK를 수정하지 않는다.
Ruling: 준비 중 AGY 설치본이 1.2.11에서 1.2.14로 바뀌어 version guard가 거부했다. 원인을 단정하지 않는다. 1.2.14의 실행용 복사본을 별도 ASCII 경로에 고정하고 hash/version 및 실제 capability를 다시 확인한다. 기존 1.2.11 선언의 prepared 예약은 실행하지 않고 대체 기록으로 보존한다.
Ruling: Flash의 GCC 내부 오류는 순차 실행에서도 재발했다. 원인을 확정하거나 해결됐다고 기록하지 않는다. SDK source/flags를 바꾸지 않은 새 빈 앱 probe는 첫 빌드에 성공했다. 앞선 오류 2회와 비용을 보존하고 실제 실행에서도 실패·자체 재시험을 기존 시간 예산에 기록한다.
Ruling: baseline YAML의 randomized_run_order를 따라 seed 1의 무작위 첫 후보 블록 순서를 동결한다. 6개 prepared 예약은 3회 독립 반복 완료를 뜻하지 않으며, 이후 반복은 새 식별자로 준비한다.
Ruling: 준비 package에는 대상과 무관한 과거 영상/evidence zip을 넣지 않는다. operator source 186개와 candidate 원래 working bytes·commit/tree를 보존하며 parent 이력은 shallow 경계로 명시한다. 준비 fixture artifact만 선별 포함하고 실제 제품 terminal package는 후보 종료 후 생성한다.
Ruling: 새 Codex reasoning_output_tokens는 원본에 있으나 기존 정규화기가 매핑하지 않는다. 현재 baseline을 변경하지 않고 raw native usage에 별도 보존하며 normalized null을 미계측·0으로 해석하지 않는다. 같은 비용 정의가 필요한 후속 집계에서 원본을 사용한다.

Task 1: complete — native version/model/settings inventory, 사용자 확장 비활성 관측 및 고정 프로필 6개.
Task 2: complete — CLI 6개 각각 실제 9개 capability 통과. 실패한 준비 시도와 원본도 별도 보존.
Task 3: complete — baseline 85ba108의 파일 57개/MD 3개, prepared 6개, 시작 null/소비 0초, profile-bound receipt validator 통과.
Task 4: complete — 새 독립 root에서 operator source 186개, package 파일 325개, 6개 candidate 원래 commit/tree/input/receipt 및 fixture artifact hash 복원 통과.
Task 5: complete — [준비 보고서](../../results/experiment-preparation-20261002/report.md), readiness·문서 지도, 최종 검토·fresh 확인 완료. 본 실험은 시작하지 않는다.

Final review: fresh reviewer (`gpt-6-astra`), Critical 0 / Important 0 / Minor 0.
package 325/325 hash, 게시 근거와 package의 겹치는 파일 232개, live 6개 입력·profile·receipt 및 실행본 hash 재확인.
Final: Ruling: 제품 BSP/LCD·실물 관측은 후보 미실행 때문에 판정하지 않는다 — 빈 앱 검증을 제품 합격으로 오해하면 비교가 왜곡된다.
Final: Ruling: 이후 quota/120분 연속 사용은 보장하지 않는다 — 실제 한도 실패도 기록·비용에 포함한다.
Final: Ruling: SDK 내부 오류의 원인·영구 해결은 이번 준비에서 확정하지 않는다 — 이후 동일 오류가 재발할 수 있다.
Final: Ruling: 새 Codex reasoning 정규화 수정은 동결 baseline에 적용하지 않는다 — 원본 값을 보존하고 null을 미계측/0으로 읽으면 안 된다.
Final: Ruling: 3회 독립 반복·최종 순위는 첫 준비 블록에서 판단하지 않는다 — 실행하지 않은 반복을 완료로 세면 근거가 과장된다.
Final: Ruling: 이후 설정 변경의 격리는 지금 보장하지 않는다 — 실제 시작 전 native inventory를 다시 확인해야 한다.
Final: Ruling: 다른 PC의 설치·인증 실행 환경은 package 범위가 아니다 — 누락된 도구/인증은 별도 설치가 필요하다.
Final: Ruling: reviewer는 기존 full preflight/restore를 중복 실행하지 않고 live validator·package hash를 새로 확인했다 — 원 실행 근거도 함께 보존한다.
Final: Ruling: 민감정보 확인은 경로·패턴·내용의 제한된 검사다 — 모든 가능한 인코딩의 비밀 부재를 형식적으로 증명했다고 주장하지 않는다.
Final: 게시 검증 — ignore 규칙의 상위 artifacts 제외와 Git JSON 줄바꿈 변환을 실제 staged 파일 목록/bytes 검사로 발견·수정했다. 준비 파일 전체와 원본/profile/receipt/package 242개 Git blob bytes가 일치하고 staged whitespace 검사도 통과했다. 소스 구현은 변경하지 않았다.
