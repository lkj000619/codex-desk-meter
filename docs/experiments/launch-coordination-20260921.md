# 실험 시작 준비: 위임·검증·결정 기록

사용자 요청: 실험 시작 가능 상태를 만들고, 체크리스트와 문항을 작성하여
Luna max로 준비한 결과를 Sol medium으로 검증·종합한다.

## 작업 순서와 재개 지점

- [x] 기존 체크리스트·실행 가이드·조건부 승인·draft profile 확인.
- [x] 준비 담당 `/root/readiness_luna`: `gpt-5.6-luna`, reasoning `max` 지정.
- [x] Luna: 실제 도구/환경 증거 수집, CLI 인자 순서와 UTF-8 실행 환경 보완.
  settings 실제 적용 증명은 미완료로 분리했다.
- [x] Luna: `launch-readiness-20260921.md`에 항목별 근거·실행 명령·미완료 기록.
- [x] 사용자 결정 반영: 첫 비교군(기존 6종 계획 유지), baseline 로컬 commit/tag 생성 승인.
- [x] Sol: `gpt-5.6-sol`, reasoning `medium`으로 Luna 준비 산출물 최초 독립 검증.
- [x] 발견된 CLI 인자·문서 상태·빌드 hash 기록 문제를 Luna가 수정하고 Sol 재검증.
- [x] 2026-09-22 prompt-input 추가 진단 결과를 Sol이 검증하고 기존 제안을 정정.
- [x] 주 에이전트: 최종 상태와 다음 명령 종합, 기존 체크리스트 연결 및 Preflight Receipt 발행.
  2026-09-25 AGY 감사에서 근거 공백과 잘못 복사된 approval 정책을 확인해 receipt를
  `blocked`로 정정했다.

현재 단계: AGY 파일럿은 시작 불가하다. 2026-09-25 감사에서 R4는 `not_ready`,
R5 receipt는 `blocked`, R6/R7은 AGY-shaped offline mock으로 exact one-shot stdin·raw
JSONL·unsupported metric null 처리를 확인했지만 real AGY stream·user intervention·
evaluator read-only 증거가 없어 `not_ready`(실제 raw log/telemetry는 post-run 기록),
R8은 pre-pilot evaluator-harness와 post-run production 평가의 경계가 미확정이라
`not_ready`, R9는 과거 16MiB
백업 hash는 확인됐지만 현재 보드/artifact 연계·COM3 단독 점유·운영자 checklist가
없어 `not_ready`, R10은 `not_authorized`로 확인했다. 새 prepare/run과 COM3/flash는
수행하지 않는다.
과거 Sol 사전 검토 세션 `/root/readiness_sol`은 `gpt-5.6-sol`, reasoning `medium`으로
시작했다. 이번 2026-09-25 수정은 `/root/agy_readiness_luna`가 수행했고
`/root/agy_readiness_sol`이 [독립 재검증](agy-launch-sol-review-20260925.md)을 완료했다.
담당 모델·reasoning은 준비/검증 에이전트 설정이며 실험 비교군 결정과 별개다.
중단 후 이 문서와 Luna 산출물을 먼저 읽고 완료 항목을 반복하지 않는다.

## 사용자 결정 문항

| ID | 문항 | 상태 |
|---|---|---|
| Q1 | 첫 비교군을 Codex Luna max·Sol medium 2종으로 할지, 기존 6종 계획을 유지하고 각 모델/reasoning을 지정할지 | **기존 6종 계획 유지 확정 (이후 변경됨)** |
| Q2 | 검증 완료 후 기존 변경을 포함한 로컬 baseline commit과 새 tag를 생성할지, 먼저 변경 목록을 검토할지 | **미커밋 변경 검토 완료 후 baseline 커밋 및 태그 생성 승인** |
| Q3 | (추가) ChatGPT 주간 세션 크레딧 고갈에 따른 파일럿 프로파일 변경 및 하드웨어 플래싱 옵션 선택 | **agy gemini 3.8 flash 프로파일로 파일럿 대상 변경 승인. 옵션 A(실제 보드 COM3 플래싱 및 실물 평가 진행) 채택.** |

사용자 응답(Q1 기존 6종 유지)이 확정되었으나, 이후 OpenAI(ChatGPT) 크레딧 고갈 문제로 인해 첫 파일럿 대상이 `Codex CLI`에서 `Antigravity CLI (gemini-3.8-flash-medium)`로 변경되었습니다 (Q3). 문서상 `antigravity-cli`는 공식 지원 어댑터이므로 충돌은 없습니다.
또한, 이번 첫 파일럿 실험에서 하드웨어 플래싱(옵션 A)을 진행하기로 결정되었습니다. (R10 최종 실행 인가 대기 중)

## Sol 검증 문항

1. profile의 모델·reasoning·argv·설치 버전은 서로 일치하고 실제 근거가 있는가?
2. builtin-only 설정은 정책 선언만이 아니라 실제 적용 방법/확인 증거가 있는가?
3. profile·baseline·check hash·receipt가 같은 입력을 가리키는가?
4. preflight 실패나 미확인 항목을 pass로 꾸미지 않았는가?
5. 최신 수정이 선택 baseline snapshot에 포함되는가? commit/tag 전이면 이를 명시했는가?
6. prepare와 실제 모델 실행을 구분하고 기존 조건부 승인 조건을 보존했는가?
7. 운영 명령이 실제 파일·CLI 옵션과 일치하고 재개 가능한가?
8. 테스트와 dry-run을 실물/모델 접근 합격으로 오인하지 않았는가?
9. 비밀정보 없이 증거가 보존되고 다른 사용자 변경을 유지했는가?
10. 시작 가능 판정은 구체적 baseline/profile/receipt와 미해결 항목에 근거하는가?

실제 제품 실험·provider 호출·serial/flash는 이번 준비 작업에서 자동 실행하지 않는다.
시작 준비와 실제 실행을 구분하고, 사용자의 추가 지시가 오면 범위를 반영한다.

## Sol 사전 검토와 종합 판단

- main이 dirty이고 HEAD는 `47b720d7...`이다. prepare는 clean HEAD와 선택한
  baseline의 일치를 요구한다. 현재 HEAD를 check해도 미커밋 수정은 포함되지 않는다.
- candidate profile의 문법 검증 성공은 모델 접근이나 builtin-only 설정의 증거가
  아니다. 모델 ID/effort와 실제 적용 설정 확인이 필요하다.
- 실제 receipt가 아직 없다. receipt는 baseline commit과 semantic profile hash에
  연결된다. 전체 bundle/component hash는 최종 check와 prepare 출력을 별도로
  대조한다. receipt 자체가 bundle hash를 직접 검증한다고 서술하지 않는다.
- R10은 현재 운영자 검토 gate이며 runner가 승인 문서를 자동 검증하지 않는다.
  CLI의 `--ask-for-approval never` 설정은 이 실험 승인과 별개다.
- 과거 조건부 승인의 대상과 준비 성공·동결·COM3 조건을 보존한다. 새 후보가
  그 대상에 포함되는지는 Q1 확정 후 검토한다.

주 에이전트 판단: 독립 승인 시스템 추가는 이번 준비의 필수 범위로 확대하지 않는다.
대신 실제 적용 증거, 최종 hash 대조, 수동 gate의 한계를 명확히 기록한다.

## 준비 산출물

- [Luna 준비 기록](launch-readiness-20260921.md)
- [CLI·환경·빌드 증거](evidence/codex-cli-preflight-20260921.txt)
- 후보 profile: `experiments/config/verified-profiles-candidate/`의 Codex 2종.
- 설치 CLI 0.153.2, IDF v5.3.2 활성화 및 ESP32-S3 hello-world 빌드 확인.
- 81개 테스트, 세 validator, host dry-run, diff 검사 통과.
- 두 후보의 check는 현 HEAD에서 통과하나 미커밋 변경을 포함하지 않는다.
- Sol은 두 후보의 argv 도움말, profile/component/bundle hash 및 빌드 파일 hash를
  독립 확인했다. hello-world hash 기록 오타는 Luna가 수정했다.

현재 실험 시작 불가: Q1/Q2/Q3 결정은 보존되어 있지만, AGY effective settings·approval
정책·network·prompt/activity·host preflight evidence가 부족하고 receipt가 blocked다.
모델 metadata/help는 실행 성공 증거가 아니다. 선택 baseline tag는
`benchmark-v2-baseline-20260923` → `9ef945efd9d6c2c4b4eedca75eccc9f280b3aced`이며,
감사 시작 시점 HEAD `a36747ab2f7ac50676343b3b53517c8491d54b03`와 5 commits 차이가 난다.
새 문서/profile/receipt는 선택 baseline commit/tag에 반영하지 않았다. 감사 작성 시 작업
트리는 dirty였으며, 이후 상태는 `git status`로 확인한다.

## AGY 현재 감사 연결 (2026-09-25)

상세 판정과 다음 작업은 [AGY launch review](agy-launch-review-20260925.md)에 기록하며,
수정 후 독립 재검증은 [AGY Sol review](agy-launch-sol-review-20260925.md)에 기록한다.
Q1의 기존 6종 계획 유지, Q2의 baseline commit/tag 승인, Q3의
`antigravity-cli / gemini-3.8-flash-medium` 파일럿 및 옵션 A(COM3/실물 평가) 결정은
변경하지 않는다. Q3는 R10 발효가 아니다.

- 실제 `agy --version`은 `1.2.9`이고, `agy --help` 및 MCP/plugin 목록은
  [2026-09-25 evidence](evidence/agy-cli-20260925.txt)에 원문과 SHA-256으로 보존했다.
- 2026-09-24 raw preflight는 version과 빈 MCP/plugin 목록만 관측하며
  memory/cache/routing이 CLI에서 직접 관측되지 않는다고 명시한다. 기존 candidate의
  builtin-only·cleared/disabled/direct 주장은 제거하고 `unverified`로 표시했다.
- AGY에 없는 `--ask-for-approval` 정책 문자열을 제거했다. help의
  `--disable-slash-commands`는 모든 skill expansion을 차단해 builtin-only-v1과 다른
  조건이고, `--effort`는 model ID에 effort가 포함된 경우 중복 지정하지 않으므로
  candidate argv에는 넣지 않았다.
- receipt는 base commit/profile semantic hash/evidence SHA를 새 입력으로 갱신했지만,
  관측되지 않은 checks는 `not_observed`, settings inventory는 `blocked`로 남겼다.
  `pilot_pass`는 `false`다.
- 보존된 `20260924-antigravity-cli-agy-flash-medium-r01`은 날짜가 지났고 수정된
  profile/receipt hash와도 맞지 않는다. 예약 ID와 산출물은 보존하며 재사용하지 않는다.

## 추가 진단 재개 결과 (2026-09-22)

Luna 사용량 제한 후 동일 세션 재개 성공. `debug prompt-input`은 현재 세션 문맥만
렌더링하며 candidate exec의 ignore 옵션을 받지 않는다(exit 2). 따라서 이 명령만으로
후보의 builtin-only 적용을 검증할 수 없다. 원문 문맥은 저장하지 않고 개수만 기록했다.
현재 skills/plugins 링크 존재는 확인됐지만 미래 exec에서의 활성 여부로 단정하지 않는다.
후속으로 global features/debug metadata에서 실제 제외 지원 여부만 제한적으로 조사한다.

로컬 metadata의 모델 ID/effort 지원과 실제 요청 시 계정 접근 성공을 구분한다.
현재 후보 파일은 변경하지 않았으며, 전체 모델 ID와 지정 effort는 그대로다.
추가 증거와 수정된 Sol 판정이 최종 종합 대상이다.
