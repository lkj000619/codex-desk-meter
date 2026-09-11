# Benchmark 브랜치와 결과 관리

## 상태

이 문서는 합의된 운영 설계다. schema v2, 격리 checkout 생성, 실행기와 공통 평가
도구가 구현되었다. 도구별 설정·모델 및 sandbox 검증을 완료하기 전까지 pilot을 실행하지 않는다.
기존 baseline 태그는 보존하고, 전환 완료 후 새로운 baseline을 만든다.

## 브랜치와 run ID

`main`은 실행 가이드, 고정 입력, 평가 도구, 검증된 결과 요약과 비교표를 보관한다.
agent/model 브랜치는 구현 코드와 각 반복의 원본 결과를 보관한다.

```text
experiment/openai/codex-cli/gpt-5-6-luna
experiment/google/gemini-cli/<model>
experiment/antigravity/cli/<model>
experiment/opencode/cli/<model>

results/20260911-codex-cli-gpt-5-6-luna-r01/
results/20260911-codex-cli-gpt-5-6-luna-r02/
results/20260911-codex-cli-gpt-5-6-luna-r03/
```

run ID는 `YYYYMMDD-<product>-<model-slug>-rNN`이다. 날짜는 실행 시작의
Asia/Seoul 날짜이며 자정을 지나도 ID는 유지한다. 같은 날짜·product·model의
번호는 pilot을 포함해 순차 배정하고 재사용하지 않는다. pilot 여부는 별도 필드로
기록한다. 정확한 시각은 UTC RFC3339로 기록한다.

모델 slug와 실제 모델 ID는 구분한다. slug 충돌은 실행 전에 고유 별칭으로 해결한다.
OpenCode 등의 모델 제공자·endpoint 별칭·정확한 모델 ID·자동 라우팅 여부를 기록한다.
비밀키는 기록하지 않는다. 브랜치 경로의 이름을 모델 제공자로 추론하지 않는다.

## 독립 반복과 코드 보존

각 run은 동일 baseline의 새 임시 checkout과 새 에이전트 세션에서 시작한다.
agent/model 보관 브랜치의 최신 코드를 다음 반복의 시작점으로 사용하지 않는다.
이전 run의 코드·로그·대화·결과 요약은 실행 checkout에 제공하지 않는다.
Git 이력으로 이전 결과를 읽는 것을 피하려면 baseline 파일만 가진 별도 저장소를
준비하고, 원본 baseline SHA와 입력 해시는 운영자가 별도 기록한다.

종료 후 운영자가 다음 순서로 보존한다.

1. 실행 종료 시점의 코드 스냅샷을 커밋하고 SHA를 고정한다.
2. agent/model 브랜치에 해당 스냅샷과 `results/<run-id>/`를 보존한다.
   앞선 결과 디렉터리를 유지하면서 프로젝트 소스는 해당 run의 스냅샷으로 교체한다.
3. 결과 레코드가 구현 commit SHA와 증거 파일 해시를 참조하도록 별도 커밋한다.
4. 다음 run은 다시 baseline에서 시작한다. 이전 구현을 개선하는 실행은
   독립 반복이 아닌 별도 개선 실험으로 분류한다.

실행 checkout의 로컬 SHA, 원본 baseline SHA, 보관된 구현 SHA를 구분한다.
에이전트 종료 후 운영자가 코드를 고치면 원본 run은 그대로 보존하고 별도 수정으로 기록한다.

## 실행 환경과 계측

동일 비교군은 OS·하드웨어·ESP-IDF·제조사 ZIP 해시·의존성 버전·캐시 초기 상태를
고정한다. 필요한 패키지는 사전 확보한다. offline 모드에서는 다운로드를 요구하지 않는다.
각 도구의 sandbox 안에서 compiler·Ninja·Git·임시 폴더 쓰기와 최소 빌드를
사전 검증한다. 호스트 셸의 성공만으로 대체하지 않는다.

skills, MCP, 사용자 지침, 자동 메모리, 검색 권한, 승인 정책, reasoning 설정과
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

최소 3회는 탐색적 비교다. 실행 순서와 난수 seed를 사전 기록한다. 성공/시도 수,
중단·시간 초과·환경 실패 수, 완료 run의 시간 중앙값·범위를 함께 표시한다.
미완료 run의 경과 시간은 별도로 제시하며 빠른 성공으로 취급하지 않는다.

## main 결과 게시

운영자가 검증한 요약과 비교표만 main에 반영한다. 실험 브랜치 전체를 main에
머지하지 않는다. 요약에는 run ID, 비교군·baseline, 상태, C1~C8, 자율 기능 점수,
시간·토큰과 측정 한계, 실물 검증 여부, 구현·결과의 고정 commit 링크를 포함한다.
원본 대용량 로그·영상은 별도 artifact로 보관하고 위치·SHA-256·보존 정책을 기록한다.

## 구현 및 검증 상태

- 구현: date-only ID, schema v2, JSON Schema 실제 적용, manifest-only 실패 보존
- 구현: 새 저장소 baseline snapshot, 로컬 bundle 및 agent/model 보관 브랜치
- 구현: 실행 시작/종료, 단조 시간, timeout/중단, 외부 로그, Codex usage 이벤트 수집
- 구현: 시각·경과 시간·ID·상태 교차 검사, 증거 경로·SHA-256 검사
- 구현: host preflight 실패 차단, profile/baseline에 묶인 sandbox 증거 receipt gate
- 구현: 실제 제품 host 어댑터 평가, 오류 주입, 0/299/300초 기준, 실물 채점표
- 구현: main 결과 인덱스와 요약 초안 생성기. 최종 판정과 게시는 운영자 검토
- 미완료: 도구별 정확한 모델/설정 확정, 실제 sandbox receipt, Gemini/OpenCode/Antigravity telemetry 어댑터 검증
- 미완료: 새 baseline 확정 및 각 도구의 제품 pilot, COM 포트와 실물 검증

운영 도구 자동 시험과 제품 pilot은 별개다. synthetic subprocess 시험을 제품 pilot으로
기록하지 않는다. schema v1 과거 자료는 보존하며 새 validator로 덮어쓰거나 자동 이관하지 않는다.

이 목록은 향후 구현 작업이며, 문서 보완 자체가 실험 실행 승인을 뜻하지 않는다.
