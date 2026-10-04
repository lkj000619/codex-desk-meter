# Benchmark 브랜치와 결과 관리

## 상태

이 문서는 운영자의 run ID·계측·보관·복구 방법을 정의한다. 다음 비교의 채택 조건은
[운영 계약](comparison-operating-contract.md), 실제 준비 상태는
[새 비교 준비 상태](next-comparison-readiness.md)가 소유한다.

2026-09-25의 `PILOT_PREPARED / LAUNCH_RECHECK_REQUIRED`는 당시 준비 상태다.
이후 첫 실행과 r21 보완의 결과는 [원본 evidence](evidence/agy-remediation-r21-final-evaluation-20260929.md)에
보존했다. [기존 pilot gate](benchmark-readiness.md)와 receipt는 해당 날짜·baseline·profile에만 적용한다.
새 baseline은 검토한 입력 commit/hash이며 실행 지시나 제품 합격의 증거가 아니다.

## 브랜치와 run ID

`main`은 실행 가이드, 고정 입력, 평가 도구, 검증된 결과 요약과 비교표를 보관한다.
agent/model 브랜치는 구현 코드와 각 반복의 원본 결과를 보관한다.

정식 기준 branch는 `main`이다. `main-2`는 과거 runner tooling을 추가한 중간
개발 branch이며 새 실험의 기준으로 사용하지 않는다. 현재 동결된 Antigravity
수동 파일럿은 별도 결과로 보존하되, 정량 비교 baseline이나 main의 제품 합격으로
승격하지 않는다.

```text
experiment/openai/codex-cli/sol
experiment/openai/codex-cli/luna
experiment/antigravity/cli/<model>
experiment/opencode/cli/<model>

results/20260911-codex-cli-gpt-5-6-luna-r01/
results/20260911-codex-cli-gpt-5-6-luna-r02/
results/20260911-codex-cli-gpt-5-6-luna-r03/
```

`experiment/google/gemini-cli/<model>` 경로 예시는 폐기한다. Google 기본
표면은 `experiment/antigravity/cli/<model>`이며, `gemini-cli`는
Enterprise/API 키 conditional에서만 별도 경로를 사용한다.

기본 정책은 [isolation-policy.md](isolation-policy.md)의 `prompt-and-log`다.
현재 main의 고정 입력과 전용 checkout, 프롬프트 참조 제한, 명령·자료 로그를 사용한다.
Docker/VM은 선택 사항이며 미사용 자체는 정량 비교 제외 사유가 아니다.

run ID는 `YYYYMMDD-<product>-<model-slug>-rNN`이다. 날짜는 실행 시작의
Asia/Seoul 날짜이며 자정을 지나도 ID는 유지한다. 같은 날짜·product·model의
번호는 pilot을 포함해 순차 배정하고 재사용하지 않는다. pilot 여부는 별도 필드로
기록한다. 정확한 시각은 UTC RFC3339로 기록한다.

모델 slug와 실제 모델 ID는 구분한다. slug 충돌은 실행 전에 고유 별칭으로 해결한다.
OpenCode 등의 모델 제공자·endpoint 별칭·정확한 모델 ID·자동 라우팅 여부를 기록한다.
비밀키는 기록하지 않는다. 브랜치 경로의 이름을 모델 제공자로 추론하지 않는다.

## 독립 반복과 코드 보존

독립적인 최초 run은 동일 baseline의 새 임시 checkout과 새 에이전트 세션에서 시작한다.
agent/model 보관 브랜치의 최신 코드를 다음 반복의 시작점으로 사용하지 않는다.
이전 run의 코드·로그·대화·결과 요약은 실행 checkout에 제공하지 않는다.
Git 이력으로 이전 결과를 읽는 것을 피하려면 baseline 파일만 가진 별도 저장소를
준비하고, 원본 baseline SHA와 입력 해시는 운영자가 별도 기록한다.

종료 후 운영자가 다음 순서로 보존한다.

1. 실행 종료 시점의 코드 스냅샷을 커밋하고 SHA를 고정한다.
2. agent/model 브랜치에 해당 스냅샷과 `results/<run-id>/`를 보존한다.
   앞선 결과 디렉터리를 유지하면서 프로젝트 소스는 해당 run의 스냅샷으로 교체한다.
3. 결과 레코드가 구현 commit SHA와 증거 파일 해시를 참조하도록 별도 커밋한다.
4. 다음 독립 반복은 다시 baseline에서 시작한다. 후속 수정은 자신의 직전 frozen
   결과에서 이어지며 최초 결과와 연결해 보관한다. 회차·누적 예산은 운영 계약을 따른다.

실행 checkout의 로컬 SHA, 원본 baseline SHA, 보관된 구현 SHA를 구분한다.
에이전트 종료 후 운영자가 코드를 고치면 원본 run은 그대로 보존하고 별도 수정으로 기록한다.

## 실행 환경과 계측

동일 비교군은 OS·하드웨어·ESP-IDF·제조사 ZIP 해시·의존성 버전·캐시 초기 상태를
고정한다. 필요한 패키지는 사전 확보한다. offline 모드에서는 다운로드를 요구하지 않는다.
기본 모드는 host에서 compiler·Ninja·Git·임시 폴더 쓰기와 최소 빌드를 검증하고
prompt scope·activity logging 준비를 기록한다. external-sandbox 선택 시에는
같은 검증과 실제 읽기 차단을 sandbox 내부에서 수행한다.

skills, plugins, MCP, 사용자 지침, 자동 메모리, 검색 권한, 승인 정책, reasoning 설정과
설정 해시를 기록한다. 도구마다 동일 권한을 제공할 수 없으면 별도 비교군으로 둔다.
측정 대상은 agent+model+설정의 조합이며 도구 차이를 모델 능력 차이로 단정하지 않는다.

운영 실행기가 실제 prompt 전달 직전에 시작 시각과 단조 시계를 기록하고,
프로세스 종료 시 종료 시각·경과 시간·종료 코드를 기록한다. 준비 시간과 운영자
실물 평가 시간은 별도 기록한다. 에이전트 실행 중 대기·승인은 실행 시간에 포함한다.
120분 제한과 사용자 중단은 자식 프로세스까지 종료·확인하고 부분 산출물을 보존한다.

원본 stdout/stderr와 telemetry는 실행 checkout 밖에서 수집해 자기 로그를 읽는
피드백을 방지한다. 종료 후 마스킹된 사본과 해시를 결과에 보관한다. 도구 호출 수,
명령 실패 수, 거부된 호출 수를 구분하고, 셸 종료 코드가 0이어도 내부 명령 실패가
있으면 증거를 남긴다. 토큰은 제공자 정의와 원본 사용량 이벤트를 보존한다.
cached/reasoning이 input/output의 부분집합인지 명시하고 중복 합산하지 않는다.

공통 prompt 템플릿 해시와 run ID 치환 후 실제 전달한 UTF-8 prompt 해시를 모두
기록한다. Windows PowerShell의 읽기·stdin 전달 인코딩도 검증한다.

## 판정과 중단

운영 기록에 `phase`(pilot/benchmark), 반복 번호, 비교군 ID, 실행 상태
(prepared/running/completed/aborted/timeout/environment_failed), 중단 사유가 필요하다.
실행 상태와 제품 합격 여부는 별개다. 준비 상태에서는 종료·토큰 값이 null일 수 있다.
미측정 값을 0으로 대체하지 않는다.

공통 평가 도구·입력·기대값은 baseline에 고정한다. 실제 펌웨어 파서와 상태 전이
코드를 검사하며 별도로 작성한 모방 파서의 성공으로 대체하지 않는다. 에이전트
자체 시험과 운영자 평가를 구분하고, 판정자·증거·평가 버전을 보존한다.
형식 검증 통과는 C1~C8 합격을 의미하지 않는다. 부분합격·미검증은 제품 합격으로 집계하지 않는다.
중단되어 후보 3개를 작성하지 못한 run도 운영 기록만으로 보존할 수 있어야 한다.

최소 3회는 탐색적 비교다. 실행 순서와 난수 seed를 사전 기록한다.
비교군별로 전체 시도 수와 completed/aborted/timeout/environment_failed를 각각 보고하고,
reference 도달과 제품 합격의 성공 수를 구분한다. 완료 결과에 조건부인 성공률과
전체 시도 기준 성공률을 별도 이름으로 표시한다. 실행된 실패·중단·timeout의 시간과
측정 가능한 token도 소비 비용에 포함하며, 준비·독립 평가 비용은 운영 계약대로 분리한다.

`summarize-benchmark.py`의 첫 표는 유효 completed에 조건부인 비율·중앙값이며
후속 회차는 독립 반복에서 제외한다. 별도 전체 시도 표에 실패 상태·소비 시간·
정규화 token과 측정 coverage를 표시한다. 제품 결과가 누락/무효여도 유효 manifest의
실행 비용은 남긴다. 최초·후속·누적·reference 도달 비용 표도 출력한다.
RM 도달 비용은 hashed 전체 pass review와 이전 모든 회차·측정이 있을 때만 계산한다.

조건부 표에서는 pilot·incomplete·schema-invalid·semantic-unjoined result와 중복 경로/run
identity를 제외한다. 비교군은 agent 설정·experiment·baseline id/ref/commit·input bundle의
전체 값으로 구분하며 화면의 짧은 label로 병합하지 않는다. `--min-repetitions` 미만은
ineligible로 표시한다. E2E 유효성에는 operator·evaluation manifest·result·baseline·evidence의 연결 검사가 포함된다.
명령과 입력 범위는 [도구 안내](comparison-tooling.md)를 따른다.

## main 결과 게시

운영자가 검증한 요약과 비교표만 main에 반영한다. 실험 브랜치 전체를 main에
머지하지 않는다. 요약에는 run ID, 비교군·baseline, 상태, C1~C8, 자율 기능 점수,
F1~F9 기능 범위, G1~G6 GUI 점수, 시간·토큰과 측정 한계, 실물 검증 여부,
구현·결과의 고정 commit 링크를 포함한다. F1/F3이 `not_run`인 firmware-only
결과를 실시간 개인 계정 연동 완료로 요약하지 않는다.
원본 대용량 로그·영상은 별도 artifact로 보관하고 위치·SHA-256·보존 정책을 기록한다.

`benchmark.py archive`는 E2E schema·상태별 evidence·manifest identity·최종 normalized
경로를 검사한 뒤 로컬 archive index에 게시한다. E2E 검증에 실패한 입력은 raw source
snapshot을 보존하며 normalized result나 성공 상태를 부여하지 않는다.
`automated_test_status`는 integration-test evidence에서 가져오며 `product_pass`로 대체하지 않는다.

## 구현 및 검증 상태

현재 도구에는 독립 checkout·allowlist 복사·입력 hash/변조 검사, 외부 실행 로그·timeout,
E2E 평가 manifest 생성과 archive의 identity/evidence 검사가 구현돼 있다.
기존 회귀시험의 범위와 새 비교에 남은 연결은
[준비 상태](next-comparison-readiness.md)에서 함께 확인한다.
historical schema는 과거 결과 형식으로 유지하며 새 E2E 필드를 소급 확장하지 않는다.

운영 도구 자동 시험과 제품 pilot은 별개다. synthetic subprocess 시험을 제품 pilot으로
기록하지 않는다. schema v1 과거 자료는 보존하며 새 validator로 덮어쓰거나 자동 이관하지 않는다.

문서 보완 자체가 실험 실행 승인을 뜻하지 않는다. runner 밖에서 prompt를 직접 복사한
실행은 manual pilot으로 기록하고 독립 최초 실행의 정량 비교에서 제외한다.
실행 중 maintainer/evaluator가 수정·피드백을 제공하면 개입을 보존하고 비교 적격성을
검토한다. 종료 후 채택 절차대로 전달한 후속 피드백은 별도 수정 회차로 연결한다.

## source와 evidence의 독립 복구

소스 Git bundle과 실행 증거 package를 함께 보관한다. 소스에서 ignore된 frame·빌드
로그·binary도 result가 참조하면 복구 대상이다. 아래 목록은 운영자 package의 보관 조건이며
후보 result schema에 새 필드를 추가하는 지시가 아니다.

| 보관 항목 | 식별·복구 조건 |
|---|---|
| source | run ID, baseline commit, 최초/직전/구현 commit과 검증 가능한 Git bundle |
| operator baseline | 신규 run의 `operator-baseline.zip`과 profile을 operator evidence에 hash로 등록. 후보 입력과 분리하며 package 복원 시 평가·입력 hash를 재계산 |
| artifact | 원본 app·ELF·map·bootloader·partition, 빌드 명령·도구 버전, 파일별 상대 경로·byte 수·SHA-256 |
| stimulus·관측 | 실제 fixture와 기준 시각, expected/raw frame·sequence, collector/capture 명령·로그·사진/영상과 hash |
| 결과·계측 | run/evaluation manifest, result, raw telemetry, 최초/후속 연결과 기록별 집계 범위 |
| package 목록 | package별 SHA-256과 root 기준의 파일 목록. 절대 로컬 경로는 원본 provenance로만 별도 보존 |

완료 검사는 기존 checkout을 참조할 수 없는 새 임시 root에 source와 evidence를 복원해
수행한다. 원본 commit과 파일 hash를 대조하고, 복원 root를 `--evidence-root`로 지정해
`validate-end-to-end-result.py --result <복원-result> --manifest <복원-evaluation-manifest>`를
실행한다. source bundle 확인만으로 evidence 복구를 완료 처리하지 않는다.
복원 검사 로그·종료 코드·root·검사 목록을 운영자가 보존한다.
`package-evidence.py`의 source/evidence 제작·독립 root 복원은 임시 E2E 회귀시험으로 검증했다.
실제 후보 firmware artifact와 실물 원본을 담은 package는 해당 실행 종료 뒤 별도 검증한다.
