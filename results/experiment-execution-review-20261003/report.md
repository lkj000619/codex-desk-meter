# 실험 실행 경계·hook·제한 정책 검토

검토일: 2026-10-03. 기준: HEAD `681be5315f2b9c3c0e4083527c3ebc38f75b65d6`과
현재 미커밋 보완 파일. 대상은 다음 GPT-6 포함 6개 조합의 Version 2 fixture E2E 비교다.
이 보고서는 [이전 문서 검토](../documentation-review-20261003/report.md)와
[보완 결과](../documentation-review-20261003/remediation.md)의 후속 검토다. 과거 판정·evidence는 보존한다.

## 실행 판단

**현재 상태로 정식 비교를 바로 시작하는 것은 권고하지 않는다.** 목적·제품 요구·입력 분리·
평가 의미·예산 설계는 목적에 맞지만, 명령 예제와 실효 권한, 후속 지침, 정책 준수 판정의
집계 연결에 Major 4건을 확인했다. AGY를 병렬 준비할 경우의 Minor 1건도 있다.
이미 알려진 새 baseline commit 동결, GPT-6 실제 capability, 당일 run/ledger/receipt 연결도 남아 있다.

로컬 회귀·입력 검사는 수행 가능하다. 이번 검토에서는 실제 모델 호출·serial port·flash를 실행하지 않았다.
합성 자료로 재현한 결함은 실제 후보가 이미 규칙을 위반했다는 의미가 아니다.

## 목적과 문서 연결에서 잘 정의된 부분

- 제품 목표는 PC collector→정규화→USB→실제 firmware→LCD로 이어지고,
  [제품 계약](../../docs/PRODUCT_CONTRACT.md)이 C1~C8·I1~I4·F1~F9를 정의한다.
  fixture 비교, owner-only live, Version 1 이식의 완료 범위를 구분한다.
- [문서 지도](../../docs/DOCUMENTATION_MAP.md)는 후보 필수 MD 3개와 운영자 자료를 나눈다.
  runner는 allowlist 57개만 전달하고 identity·입력 hash를 실행 전후 검사한다.
- [운영 계약](../../docs/experiments/comparison-operating-contract.md)은 최초 120분,
  후속 최대 3회·누적 120분, 독립 반복 3회, 실패 비용 보존을 정의한다.
  manager는 자기 직전 결과에서 이어가기, 같은 profile, 예산 소진과 동시 회차 차단을 검사한다.
- reference 도달, 제품 합격, 프로세스 종료, F9/GUI 점수를 구분한다.
  실물 실패나 불완전 제출은 보존할 실험 결과이며 제품 성공을 새로운 시작 조건으로 요구하지 않는다.
- baseline ZIP/profile 보존과 독립 복원 hash 검사는 구현됐고 회귀시험이 통과했다.
  실제 다음 비교 commit이 이미 동결됐다는 뜻은 아니다.

## E1 · Major · 정책 준수 검토가 비교 적격성과 집계에 연결되지 않음

근거: [접근 정책](../../docs/experiments/isolation-policy.md)의 비교 결과 취급,
[운영 계약](../../docs/experiments/comparison-operating-contract.md) 6절,
[집계](../../scripts/summarize-benchmark.py)의 `collect_records()`(193행),
[운영 schema](../../experiments/schema/operator.schema.json).

문서는 다른 구현 참조·실행 중 외부 피드백·사람의 코드 수정이 있으면 정량 비교에서 제외하고,
준수 여부를 검토할 수 없으면 `unverified`로 순위에서 제외하도록 한다.
현재 schema와 집계에는 정책 준수·비교 적격성의 구조화된 판정과 필수 검토 gate가 없다.
집계는 completed와 제품 결과 유효성을 검사하며 `user_interventions`나 준수 검토를 요구하지 않는다.
RM review의 pass도 이 검토를 대신하지 못한다.

**재현:** 유효 예제에 맞춘 합성 E2E run은 검토 기록 없이 1건 포함됐다.
`user_interventions=1`과 외부 구현 피드백으로 `invalid_for_comparison`이라고 적은
hash 연결 보조 review를 넣어도 1건 포함됐고 excluded.invalid는 0이었다.
이 보조 review는 현행 공식 schema가 지원하는 판정 형식이 아니라, 그 연결이 없음을 확인하는 probe다.
[재현 결과](probes.json)의 `summary`를 참조한다.

**영향:** 운영자가 수동으로 manifest 목록에서 빼지 않으면 문서상 제외 대상이나 미검토 run이
유효 반복·순위 자료로 들어갈 수 있다. prompt-and-log에서 필요한 사후 통제가 약하다.

**권고:** 정책 준수/적격성 review의 run·profile·입력·raw log hash, 판정자·사유·증거를 고정한다.
새 비교의 품질/순위 표는 검토된 eligible만 포함하며 미검토·위반 run은 제외 사유를 표시한다.
전체 시도와 실패 비용 표에는 원본과 소비 비용을 계속 남긴다. 과거 run에 새 gate를 소급하지 않는다.

## E2 · Major · 새 후속 세션에 공통 과제·제한이 다시 전달되지 않음

근거: [후속 생성](../../scripts/comparison_manager.py)의 `prepare_followup()`(310행),
[공통 과제](../../experiments/prompts/version-2-agent-task.md),
[새 profiles](../../experiments/config/next-profiles-20261003/README.md).

후속도 fresh session이다. Codex는 project 지침 자동 로딩을 끄고 AGY는 전역 지침을 제거한다.
그런데 생성 prompt는 "Continue your own frozen implementation"과 feedback JSON뿐이다.
공통 과제 내용을 포함하거나 해당 파일을 먼저 읽으라는 지시가 없으며,
serial/flash 금지, 참조 범위, 명령 결합 금지, 권한 거부 후 종료도 다시 제시하지 않는다.
원래 과제 파일이 checkout에 남아 있는 것만으로 새 session이 이를 읽는다고 보장할 수 없다.

feedback JSON의 `path`에는 직전 operator root의 절대 경로가 그대로 들어간다.
`packaged_path`의 실제 파일도 후속 checkout 밖에 복사된다. 후보가 근거를 읽으려 하면
프롬프트 참조 범위를 벗어나거나 native 접근 거부로 작업이 멈출 수 있다.

**재현:** 합성 직전 결과에서 실제 manager로 후속 prompt를 생성했다.
공통 과제·그 파일을 읽으라는 지시·serial 금지·거부 시 종료 문구가 모두 없고,
checkout 밖 evidence 절대 경로가 포함됐다. [재현 결과](probes.json)의 `followup`을 참조한다.

**권고:** 매 회차에 동결된 공통 과제와 제한을 재전달하고, 회차 목표·남은 시간은 그 위에 연결한다.
운영자용 원본 evidence 경로와 후보용 설명을 구분한다. 후보에게 증거를 읽힐 필요가 있으면
허용된 자기 자료만 checkout의 immutable 입력에 복사해 상대 경로·hash로 전달한다.

## E3 · Major · 공통 제한과 표면별 native 권한의 의미가 불일치

근거: [공통 과제](../../experiments/prompts/version-2-agent-task.md)의 빌드와 시험,
[OpenCode profile](../../experiments/config/next-profiles-20261003/opencode-muse.json),
[AGY 권한](../../experiments/config/agy-pilot-permissions.json).

1. 과제는 `python -m py_compile <상대 파일>`을 안내하지만 OpenCode bash allow 목록에 없다.
   default deny에 걸리는 명령이며 과제는 권한 거부 후 종료를 요구한다.
   같은 지침을 따른 한 후보가 설정 때문에 일찍 종료할 수 있다.
2. OpenCode의 `git diff*`는 과제에서 금지한 ref 조회인 `git diff HEAD~1`까지 match한다.
   AGY policy도 문서가 금지한 `git log -n 1`을 허용한다.
   자기 이전 회차 이력만 있는 저장소라도 공통 금지 규칙과 실효 목록은 다르다.
3. OpenCode는 SDK/vendor를 `external_directory: allow`로 열고 `edit: allow`를 범용으로 둔다.
   승인 외부 경로를 읽는 용도라는 inventory 설명과 달리, native 파일 수정도 허용되는 구성이다.
   공유 SDK/vendor 변경은 다음 후보의 환경을 바꿀 수 있다.

**확인 범위:** [재현 결과](probes.json)의 `permissions`는 profile에 내장된 설정을 실행하지 않고
추출해 정적 매칭한 값이다. OpenCode의 wildcard·마지막 match 우선·외부 허용 경로의
tool 권한 상속은 [공식 권한 문서](https://docs.opencode.ai/docs/permissions/)와 대조했다.
AGY는 저장소의 실제 regex로 match했다. 이번에 실제 에이전트 도구 호출을 시키지는 않았다.

**권고:** 정상 개발에 필요한 공통 명령의 표면별 허용/거부 표를 고정하고 양쪽을 검사한다.
SDK/vendor는 읽기만 허용하고 쓰기를 명시적으로 거부한다. ref 조회 정책을 공통 지침과 맞춘다.
제한 때문에 생긴 실패를 모델의 제품 구현 능력 차이로 해석하지 않는다.

## E4 · Major · 현재 실행 안내의 run 명령이 실제 CLI와 다름

근거: [도구 안내](../../docs/experiments/comparison-tooling.md) 43행,
[CLI parser](../../scripts/benchmark.py)의 `main()`(990행).

안내는 `benchmark.py run --directory <prepared-run> --receipt <receipt>`를 제시한다.
실제 run parser는 directory를 positional 인자로 받는다.
해당 명령을 복사하면 argparse exit 2와 `unrecognized arguments: --directory`로 끝난다.
이 오류는 모델 호출 이전에 발생함을 [재현 결과](probes.json)의 `cli`에서 확인했다.

**올바른 현행 문법:** `python -X utf8 scripts/benchmark.py run <prepared-run> --receipt <receipt>`.
실행 문서의 명령 인자와 parser를 함께 검증하고, 각 독립 series의 ledger 경로도
다르게 배정하도록 예제를 명확히 하는 것을 권고한다.

## E5 · Minor · AGY 전역 설정 wrapper는 다른 backup root의 동시 진입을 막지 못함

근거: [wrapper](../../scripts/agy_pilot_environment.py)의 `scoped_environment()`(122행), `main()`.

active.json은 backup 디렉터리마다 검사한다. 같은 전역 설정에 서로 다른 backup root로
두 wrapper가 진입하는 것은 허용된다. 한 wrapper가 먼저 끝나면 다른 wrapper 실행 중에
원래 지침·hook·권한이 복원될 수 있다. 실제 main의 AGY process 사전 검사는 위험을 줄이지만
검사와 child 시작 사이의 동시 준비를 잠그는 원자적 lock은 아니다.

**재현:** 임시 전역 설정 fixture에 두 context가 진입했다. 첫 context를 먼저 종료한 뒤
두 번째 scope 검증과 복원이 거부됐다. 실제 사용자 전역 파일은 사용하지 않았다.
[재현 결과](probes.json)의 `wrapper`를 참조한다.

단일 보드 관측의 직렬 배정과 전역 설정 변경의 직렬 배정은 다르다.
AGY 준비/실행을 모두 직렬 운영하면 우선 회피할 수 있다. 병렬 실행을 채택한다면
전역 설정 root 하나에 대한 lock과 중단 복구 검증이 필요하다.

## hook은 어떻게 적용되어 있는가

현재 프로젝트에 공통 행동 정책용 `PreToolUse`/`PostToolUse`/`Stop` hook 구현은 없다.
AGY wrapper는 개인 전역 hook을 제거·복원한다. 이는 비교 환경을 정리하는 기능이며,
프로젝트 규칙을 실행 중 차단하는 hook을 설치하는 기능과 다르다.

| 경계 | 현재 구현 | 확인되는 효과와 한계 |
|---|---|---|
| 실행 전 | profile/schema·입력 hash·깨끗한 checkout·날짜·receipt·CLI version, AGY scope 검사 | 준비되지 않은 실행을 차단. hook/권한의 실효 행동 검증은 capability 증거가 필요 |
| 도구 호출 전 | 표면의 native sandbox/permission, 공통 prompt | 권한 방식이 서로 다름. 공통 모든 금지 행동을 검사하는 프로젝트 hook은 없음 |
| 실행 중 | raw stdout/stderr 수집, hard timeout·Ctrl+C의 process tree 종료 | `capture()`는 종료를 기다림. 위반/거부 이벤트로 즉시 중지하는 공통 감시기는 없음 |
| 종료 후 | 입력 hash 재검사, AGY stream/model/permission/denial 검사 | 최종 입력 변조와 AGY 거부를 발견. 참조 범위·사람 개입의 적격성 연결은 E1 보완 필요 |
| 결과 판정 | schema·identity·증거 hash·RM review·제품 평가·package | 미완성 결과를 보존. 종료 hook으로 완성을 강제하지 않으며 이는 실패 비교 목적에 맞음 |

OpenAI Docs의 [공식 hook 문서](https://learn.chatgpt.com/docs/hooks)에 따르면
`PreToolUse`는 지원 도구를 차단할 수 있지만 모든 도구 경로를 덮는 격리 경계는 아니다.
`Stop`의 continuation은 새 prompt를 발생시킬 수 있다. 이를 도입하면 one-shot·추가 개입·비용
정의에 반영해야 하며, 후보가 성공할 때까지 숨겨진 추가 prompt를 주는 식으로 사용하면 안 된다.

따라서 hook이 없다는 사실만으로 채택된 prompt-and-log 정책을 전면 바꿀 필요는 없다.
공통 최소 정책·로그·적격성 검토가 먼저다. hook을 추가하면 지원 표면별 버전·source/hash·
활성 상태·거부/실패 동작과 실제 호출 증거를 profile/receipt에 고정해야 한다.
Codex의 user config 무시나 OpenCode의 pure 실행만으로 실제 hook inventory 검증을 대체하지 않는다.

## 제한 정책에 대한 판단

대상·제품 범위·입력·시간·후속 회차·외부 feedback·계정 정보·serial/flash·추가 하드웨어 제한은
공통 과제에 충분히 구체적으로 적혀 있다. 문제는 주로 기술적 적용과 사후 판정의 연결이다.

`read_isolation: not_enforced`는 이미 채택·공개한 기본 모드의 한계다.
branch/worktree나 명령 allowlist만으로 외부 읽기, 빌드/시험 코드 내부의 side effect,
잠깐 수정한 뒤 원상 복구한 입력까지 전부 막았다고 표현해서는 안 된다.
정식 비교는 완전한 차단을 약속하기보다 관측 범위와 위반/미검토 제외를 정확히 보고해야 한다.

질문·권한 거부·일찍 종료·미완성 제출은 발생할 수 있다. 제품 실패와 정책 위반,
환경 설정 때문에 필요한 명령이 거부된 경우를 구분해 원본·비용·사유를 보존해야 한다.

## 검증과 실제 시작 전 조건

- 전체 회귀: 182개 실행, 181개 통과·1개 skip, 실패 0개, 92.120초.
  [원본 로그](tests.txt). 통과는 위 새 연결 공백이 없다는 증거가 아니다.
- skip은 이 환경에서 symlink 생성 권한이 없어 실행하지 못한 탈출 경로 시험이다.
  사유를 별도 실행으로 확인했다. IDF 활성화가 새 child PowerShell에 전달되는 시험은
  별도 재확인에서도 통과했다. 이것이 실제 GPT-6 모델의 build capability 검증을 대신하지는 않는다.
- 6개 profile의 HEAD 입력 검사: AGY 3개·OpenCode는 inputs_valid, GPT-6 2개는 pending 차단.
  [검사 기록](profile-checks.json). HEAD 검사는 아직 동결되지 않은 보완 파일을 포함한
  새 baseline의 실행 준비 확인을 대신하지 않는다.
- read-only CLI version: Codex 0.159.2, OpenCode 1.18.34, 동결 AGY 1.2.14로 profile 값과 일치했다.
  version/help만으로 모델 권한·quota·실제 도구 성공을 검증하지 않았다.
- provider fixture matrix 검사 VALID, `git diff --check` 오류 0개.
- E1~E5는 [오프라인 재현 스크립트](reproduce.py)와 [출력](probes.json)에 보존한다.
  임시 Git/설정 fixture만 사용했다. 실제 사용자 전역 설정을 수정하지 않았다.

| 우선순위 | 조치 | 역할·완료 시점 |
|---|---|---|
| 1 | E2 공통 후속 과제·범위 및 후보용 evidence 전달 정비 | runner 관리자, 후속 포함 조건 동결 전 |
| 1 | E1 정책 준수 review와 집계 제외/전체 비용 보존 연결 | 평가·집계 관리자, 첫 정량 비교 실행 전 |
| 1 | E3 정상 명령/거부·SDK/vendor 쓰기·ref 정책 대조와 실효 검증 | 표면 관리자, capability/receipt 동결 전 |
| 1 | E4 실행 예제의 실제 parser 문법 수정·검사 | 문서 관리자, 다음 실행 준비 전 |
| 2 | E5 AGY 직렬 운영 명시 또는 전역 lock | 운영 관리자, AGY 병렬 준비를 채택하기 전 |
| 알려진 잔여 조건 | 새 baseline commit, GPT-6 capability, 당일 ID·series ledger·receipt·관측 슬롯 | 운영자, 실제 모델 실험 시작 전 |

품질 점수는 검토자 판단이며 제품 성숙도나 시험 통과율이 아니다.

| 관점 | 점수 / 100 | 판단 |
|---|---:|---|
| 완전성 | 85 | 제품 범위는 구체적, 준수 검토의 적격성 연결 누락 |
| 명확성 | 90 | 상태·증거 의미는 명확, 후속 세션의 읽을 지침 부족 |
| 일관성 | 75 | 공통 명령·금지 규칙과 native permission 불일치 |
| 검증 가능성 | 80 | 회귀·hash 풍부, 새 경계 probe가 필요 |
| 추적 가능성 | 85 | 입력→평가→복원 연결 강점, 정책 준수→집계 연결 공백 |
| 실현 가능성 | 80 | 준비 근거 존재, 실제 GPT-6 capability·명령 예제 정비 필요 |
| 평균 | 82.5 | 구조는 유지하며 실행 경계 보완 후 시작 권고 |

현행 판단의 원본은 [다음 비교 준비 상태](../../docs/experiments/next-comparison-readiness.md)에도 연결한다.
