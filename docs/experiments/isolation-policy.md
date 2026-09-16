# 실험 참조 범위와 실행 환경 정책

기본 실행 방식은 **현재 main의 검토된 문서·입력을 전용 branch/worktree에 제공하고,
프롬프트로 참조 범위를 제한하며 명령·참고 자료를 기록하는 방식**이다.
Docker, VM 또는 별도 OS sandbox는 선택 사항이다.

## 기본 모드: prompt-and-log

profile의 기존 `sandbox_policy` 필드에 `prompt-and-log`를 기록한다.
필드 이름은 호환성을 위해 유지하며 선택한 접근 정책을 뜻한다.

- 같은 비교군은 현재 main의 동일한 문서·prompt·config·fixture를 고정하고 해시를 기록한다.
  각 run은 새 branch/worktree 또는 runner checkout과 새 agent session에서 시작한다.
- agent는 지정 checkout의 현재 파일과 운영자가 명시적으로 제공한 자료만 사용한다.
  다른 branch/worktree, 과거 구현·결과·로그·대화를 탐색하지 않는다.
- `git log`, `git show`, 다른 Git ref 조회, branch 전환, 외부 저장소 검색으로
  이전 구현을 찾아보지 않는다. 자체 변경 확인용 `git status`, `git diff`는 허용한다.
- 명령·도구 사용·참고 자료·오류를 raw log에 기록한다. 로그가 일부만 제공되면
  관측 한계를 명시하고 완전한 기록이라고 주장하지 않는다.
- skills, plugins, MCP, memory, user instructions, cache, routing, 권한·승인
  조건을 기록하고 같은 비교군에 동등한 조건을 적용한다.

이 모드는 프롬프트 준수와 로그 검토에 의존한다. OS 수준의 읽기 차단을
적용하지 않은 것으로 `read_isolation: not_enforced`를 기록한다.
branch/worktree 자체를 기술적 보안 경계로 주장하지 않는다.

## 선택 모드: external-sandbox

파일·process·network 접근을 기술적으로 차단해야 할 때 Docker, VM 또는 실제
도구 sandbox를 선택할 수 있다. profile에 `sandbox_policy: external-sandbox`를
기록하고 내부 toolchain·TEMP·네트워크·읽기 차단을 검증한다.
증거가 있을 때만 `read_isolation: pass`로 기록한다.
Docker 미설치나 sandbox 미확보 자체는 기본 모드의 실행을 막지 않는다.
다른 접근 정책·권한을 사용한 결과는 별도 cohort 또는 비교표에서 해석한다.

## 비교 결과의 취급

기본 모드에서도 동일 입력, one-shot 전달, 독립 실행, 사전 기록된 조건,
원본 로그·계측과 공통 평가를 갖추면 정량 비교를 수행할 수 있다.
보고서에는 기술적 읽기 차단 없이 프롬프트와 로그에 의존했다는 한계를 명시한다.
Docker/VM 미사용 자체는 정량 비교 제외 사유가 아니다.

다른 branch나 이전 결과를 실제 참조한 run, 실행 중 외부 구현 피드백을 받은 run,
사람이 같은 실행 코드를 수정한 run은 원본을 보존하고 정량 비교에서 제외한다.
참조 준수 여부를 로그로 검토할 수 없으면 `unverified`로 표시하고 순위에서 제외한다.
runner 밖에서 직접 전달한 수동 실행은 입력·시간·계측 증거 부족에 따라 기존
`manual pilot; invalid for cross-agent quantitative comparison` 분류를 유지한다.
수동 실행 분류와 OS sandbox 사용 여부는 별개의 조건이다.

## preflight와 승인

R5는 선택한 접근 정책의 **실행 환경·참조 범위 preflight 기록**이다.
기본 모드에서는 host의 compiler, Ninja, Git, TEMP write, 최소 ESP-IDF build,
네트워크 정책, 설정 목록, prompt scope와 activity logging 준비를 검증한다.
선택 모드에서는 sandbox 내부에서 검증하며 실제 읽기 차단도 확인한다.
receipt는 baseline/profile 해시와 증거 파일 SHA-256에 묶는다.
작성 예시는 [실행 가이드](agent-run-commands.md)의 preflight receipt를 따른다.

제품 collector의 `offline-fixture` 입력과 agent 모델 호출 네트워크는 구분한다.
승인된 모델 endpoint 호출은 실행 조건에 명시한다. 웹 검색·외부 코드 검색·MCP
접근은 별도 조건으로 기록한다. `offline-fixture`는 모델 호출까지 오프라인이라는
뜻이 아니다. credential 자체를 profile·prompt·저장소·공개 로그에 넣지 않는다.

이 정책 변경은 실행 승인이 아니다. R10의 대상 baseline/profile/surface/phase 승인,
serial/COM3/ESP32 동작의 별도 승인, host simulation과 hardware 증거의 구분은 유지한다.
현재 상태는 [readiness gate](benchmark-readiness.md)를 따른다.
R5는 실제 preflight 증거를 검토한 뒤 갱신하며 문서 수정만으로 pass로 바꾸지 않는다.

## 스킬·플러그인·MCP 비교 조건 — 채택 정책

첫 비교군은 `builtin-only-v1` 확장 조건을 사용한다. 이는 접근 정책
`prompt-and-log`와 별개의 실행 조건이며 제품 cohort의 범위는 변경하지 않는다.

- 사용자 설치/custom 스킬, 외부 플러그인, MCP 서버는 비활성화한다.
- 도구 자체 내장 기능은 유지하되 기능 목록과 실제 사용 내역을 기록한다.
  도구마다 내장 기능이 다르므로 결과는 agent + model + 고정 설정의 비교로 해석한다.
- 실행 전 이름·버전·출처·설정·가능한 파일 SHA-256, 활성 여부,
  비활성화 방법과 검증 증거를 profile 및 preflight 설정 목록에 기록한다.
- 실행 후 실제 사용한 스킬·플러그인·MCP 이름, 호출 횟수, 참고 자료와
  raw log 위치를 기록한다. 기능 자체의 활성 여부와 실제 호출 여부를 구분한다.
- telemetry가 제공하지 않는 호출 횟수·버전·해시는 null과 사유로 기록한다.
  로그에 보이지 않는 호출을 0회 또는 미사용으로 단정하지 않는다.

이 문서와 profile의 설정은 채택된 실행 조건이다. 현재 설치 환경에 실제로
비활성화가 적용되었다는 증거는 아니며, 각 surface의 preflight에서 확인한다.
도구가 custom 기능과 내장 기능을 구분하거나 비활성화할 수 없으면 해당 차이를
기록하고 별도 확장 조건/비교군으로 분리한다.

ponytail 등 사용자 확장을 적용한 실험은 후속 별도 비교군으로 둔다.
같은 agent/model과 나머지 조건을 유지한 기본 실행과 비교한다.
확장의 정확한 패키지 ID·출처·버전·지원 surface는 적용 전에 확인하며,
이름이 같다는 이유로 다른 도구에서 동일한 기능이라고 가정하지 않는다.
기본 비교군 결과와 확장 적용 결과를 하나의 반복 통계로 합치지 않는다.
