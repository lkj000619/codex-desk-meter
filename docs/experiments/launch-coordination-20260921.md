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
- [x] 주 에이전트: 최종 상태와 다음 명령 종합, 기존 체크리스트 연결 및 Preflight Receipt 발행 완료.

현재 단계: 파일럿 실행을 위한 모든 사전 문서 작업 및 Receipt 발행(R4/R5) 통과 완료.
Sol 사전 검토 세션 `/root/readiness_sol`을 `gpt-5.6-sol`, reasoning `medium`으로
시작했다. 사전 검토는 완료됐으며 Luna 완료 후 같은 세션에서 최종 검증한다.
담당 모델·reasoning은 준비/검증 에이전트 설정이며 실험 비교군 결정과 별개다.
중단 후 이 문서와 Luna 산출물을 먼저 읽고 완료 항목을 반복하지 않는다.

## 사용자 결정 문항

| ID | 문항 | 상태 |
|---|---|---|
| Q1 | 첫 비교군을 Codex Luna max·Sol medium 2종으로 할지, 기존 6종 계획을 유지하고 각 모델/reasoning을 지정할지 | **기존 6종 계획 유지 확정** (사용자 승인) |
| Q2 | 검증 완료 후 기존 변경을 포함한 로컬 baseline commit과 새 tag를 생성할지, 먼저 변경 목록을 검토할지 | **미커밋 변경 검토 완료 후 baseline 커밋 및 태그 생성 승인** (사용자 승인) |

사용자 응답(Q1 기존 6종 유지, Q2 검토 후 커밋 및 baseline 태그 생성)이 확정되어
해당 결정에 따라 기준선 동결 및 태그 생성을 진행한다. 이미 승인된 준비 작업과 오프라인 검증은 계속한다.

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

현재 실험 시작 불가: Q1/Q2 미응답, 최신 baseline 미동결, 설정 적용/모델 접근
증거 및 실제 receipt 미완료. 모델 metadata/help는 실행 성공 증거가 아니다.

## 추가 진단 재개 결과 (2026-09-22)

Luna 사용량 제한 후 동일 세션 재개 성공. `debug prompt-input`은 현재 세션 문맥만
렌더링하며 candidate exec의 ignore 옵션을 받지 않는다(exit 2). 따라서 이 명령만으로
후보의 builtin-only 적용을 검증할 수 없다. 원문 문맥은 저장하지 않고 개수만 기록했다.
현재 skills/plugins 링크 존재는 확인됐지만 미래 exec에서의 활성 여부로 단정하지 않는다.
후속으로 global features/debug metadata에서 실제 제외 지원 여부만 제한적으로 조사한다.

로컬 metadata의 모델 ID/effort 지원과 실제 요청 시 계정 접근 성공을 구분한다.
현재 후보 파일은 변경하지 않았으며, 전체 모델 ID와 지정 effort는 그대로다.
추가 증거와 수정된 Sol 판정이 최종 종합 대상이다.
