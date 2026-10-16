# Gemini 4 Argon 별도 테스트 기록

확인일: 2026-10-16. 상태: **18:04:36.026 KST 별도 최초 실행 시작 확인, 현재 실행 중.** 실제 시작은 [native 관측](launch/native-start-observation.json)과 [시작 manifest](launch/manifest-at-start.json)에 보존한다. 시작 1회·종료 0회이며 제품 결과·비용·정책·RM은 미확정이다.

사용자 요청: “gemini 4 argon가 나왔어 새로운 모델 테스트 드가자!! 새롭게 모델 테스트 브랜치 만들어서 테스트 진행 요청”.

- 운영 branch: `lkj000619/test-gemini-4-argon-20261016`, 기준 `b933eacc91589c3350556399cc250cd3e2651e6e`.
- 모델: `gemini-4-argon-high`, AGY CLI 1.2.14, ESP-IDF 5.3.2. 기존 Pro의 high 조건을 사용한다. CLI 1.3.2 설치본 대신 기존 동결 실행 파일을 유지한다.
- 제품 baseline: `comparison-baseline-20261004`, commit `272875140d1998d458e26fdb2f6deab5e5d8f7b5`.
- Run: `20261016-antigravity-cli-agy-argon-high-r01`, 후보 입력 57개·Git 이력 1개·기존 구현과 빌드 미상속을 검증했다. 검증 후 제품 모델 최초 호출 1회를 시작했다.
- 실행 경로: `C:/meter-runs-20261016/20261016-antigravity-cli-agy-argon-high-r01`; 독립 ledger는 `C:/meter-runs-20261016/ledgers/20261016-antigravity-cli-agy-argon-high-r01.json`.
- Preflight 경로: `C:/meter-preflight-20261016/argon-high/probe-r01`. 이 별도 infrastructure 호출은 제품 최초 실행이 아니다. private backup은 저장소/evidence에 복사하지 않는다.
- 예산: 최초 7,200초, 종료·동결·평가 후 후속 최대 3회/누적 7,200초. 최초 실행 중 운영자 구현 피드백·serial/flash는 없다.

기존 첫 블록 5개 모델의 17회·5/15 series와 원본 판정·비용·동결 ref는 유지한다. 이 추가 모델을 기존 무작위 순서나 반복 완료 수에 합산하지 않는다. 실물/RM·제품 합격은 미평가다.

[실행 계획](../../docs/plans/2026-10-16-gemini-4-argon-test.md) · [운영 계약](../../docs/experiments/comparison-operating-contract.md) · [현재 상태](../../docs/experiments/next-comparison-readiness.md)

실제 infrastructure probe는 17:55:16.628~17:58:58.285 KST·221.656초·exit 0이다. Native init의 모델·cwd·request-review, 파일 도구·Git·host build/CTest 1개·IDF 빈 app build·py_compile·승인된 SDK/vendor 참조·원시 usage를 확인했다. [검토](capabilities.json) · [원시 stream](preflight/stdout.jsonl) · [설정 복원](preflight/scope-restoration.json). 정규화 46,989 token(input 42,186+output 4,803), provider total 46,989·cache read 187,047·thinking 2,489를 각각 보존한다. 제품 최초 비용에 섞지 않는다.

동결 baseline 회귀는 [원본](unittest-frozen-baseline-complete.txt)의 220개 중 219개 통과·1개 symlink 권한 skip·실패 0이다. 현재 운영 branch의 224개 시험에는 과거 evidence의 임시 압축 해제 경로 길이 오류 2건·skip 1개가 있었고 [실패 원본](unittest-current-branch-path-errors.txt)을 남겼다. PowerShell stderr 취급으로 끝나지 않은 동결 검사 시도와 공용 activation shim 경합도 [운영자 메모](operator-verification-notes.json)에 기록했다. 코드·동결 도구·제품 입력 변경으로 검사를 우회하지 않았다.

실행 전 [receipt](receipt.json)의 38개 증거 hash와 준비 manifest·57개 입력·baseline·profile·reference·ledger를 동결 validator로 검증했다. 과거 Pro 최초 입력 57개와도 hash가 일치한다. 제품 모델 호출은 준비 단계에서 0회다. [포트 열거](hardware-enumeration-idf-python.json)는 COM1만 확인했고 USB 보드는 없었다. serial open/reset/flash는 0회이며 실물 평가는 연결 후 필요하다.

Orca 터미널 `term_f890e4c7-90f5-4849-9c66-8c12293dce42`(제목 `Gemini 4 Argon high test`)에 [launcher](launch.ps1)를 한 번 전송했다. Receipt request `c56e9cb4-4bdf-4420-8db0-4b025279e950`의 accepted와 별개로 실제 native init·PID 8696·session `7d7658d2-7be8-4d99-a92d-00ff7a7c2898`·cwd·모델·권한을 검증했다. 초기 [진행 snapshot](progress.json)은 관측 시점 기록이다. 종료 후의 상태는 외부 run manifest와 원본 stdout/stderr를 다시 확인한다.

재개 시 같은 run을 다시 호출하지 않는다. 위 터미널과 외부 run의 `run-manifest.json`, `stdout.jsonl`, `stderr.txt`, 독립 ledger를 읽는다. 동결 runner가 종료 결과·구현을 보존한 뒤 source/artifact·원시 비용·정책을 검토하고, 같은 펌웨어의 host/실물/RM을 평가한다. 사용자 설정은 scoped wrapper 종료 시 원래 bytes로 복원되며, 실행 중 설정을 수동 변경하지 않는다. 후속은 자신의 동결 결과·평가와 잔여 예산으로만 준비한다. 현재 보드 미연결이며 실물 pass를 추정하지 않는다.

공식 출시 확인: [Google 개발자 발표](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-4-argon/). 실행에 사용하는 정확한 high ID의 근거는 로컬 AGY 모델 목록과 실제 native init이다.
