# 동결 조건의 정식 비교 실행

목표: ESP32-S3-LCD-3.16 제품 구현에서 에이전트의 첫 결과·자기 후속 수정 비용과 RM 도달·제품 품질을 동일 조건으로 비교한다.
시작 승인: 2026-10-04 사용자 요청 “프로젝트 목적과 목표에 엇나가지않도록 실험 시작”.
상태: 2026-10-06 Codex Sol 최초의 구현·제출 종료와 평가·동결 펌웨어 업로드를 마쳤다. 정책 eligible·RM1 pass/RM2~RM5 fail이며 제품 완성이 아니다. 자기 후속 준비가 남아 있고 후속 예산 7,200초·3회를 보존한다. OpenCode는 예산 소진, Pro는 후속 3회 한도로 종료했고 Pro firmware·최종 제출물이 없다. Flash 추가 회차는 보류한다. 현재 독립 series 종료 2개/예정 15개, 후보 호출 시작·종료 각각 9회다. Codex Luna는 미시작이며 이전 판정·비용·업로드 근거는 보존한다.
원본: [운영 계약](../experiments/comparison-operating-contract.md), [현재 상태](../experiments/next-comparison-readiness.md),
[동결 기록](../../results/experiment-launch-preparation-20261004/freeze.json).

## 고정 조건

- baseline `272875140d1998d458e26fdb2f6deab5e5d8f7b5` / `comparison-baseline-20261004`.
- 활성 5개·독립 3블록, Claude 제외. seed별 순서는 freeze의 block_orders를 따른다.
- 최초 최대 7,200초, 후속 최대 3회 AND 후속 누적 최대 7,200초. 임의 재시도·추가 prompt·실행 중 구현 피드백 금지.
- 후보 입력 57개·필수 MD 3개를 수정하지 않는다. 동결된 runner/profile과 run-bound receipt를 사용한다.
- 후보는 serial/flash에 접근하지 않는다. 운영자는 결과를 동결한 뒤 COM3에서 직렬 실물 평가한다.
- 정책 적격성·RM 도달·전체 제품 합격을 구분한다. 불완전한 관측은 not_run/blocked로 남기며 비용은 모두 기록한다.
- 실제 계정 수집·credential·다른 후보 구현을 제공하지 않는다. prompt-and-log와 OS 격리 미적용이라는 한계를 유지한다.

## 실행과 완료 조건

1. 최초 호출: OpenCode Muse `20261004-opencode-cli-opencode-muse-r01`을 독립 process로 실행한다.
   작업 상태: 완료. 22:47:50~23:04:54 KST, 1,024.64초, 원본 계측·terminal ledger 보존.
   완료 조건: 실제 시작 시각·상태·원본 stdout/stderr·실제 경과 시간·provider usage가 manifest와 ledger에 연결됨.
2. 운영자 검토: 제출물·고정 입력·자체 시험·빌드 artifact를 확인하고 원본 구현을 동결한다.
   작업 상태: 완료. 고정 입력/clean 동결, 독립 Python 25개·host 6개 통과. 정책 위반은 별도 부적격 판정.
   후보의 source를 수정하거나 대신 구현하지 않는다. 정책 검토와 실제 제품 동작 관측을 각각 기록한다.
3. 관측·RM·후속: 동결된 제출물로 실물 평가하고 RM review·policy review를 연결한다.
   작업 상태: 첫 series 완료. 최초 COM3 수락·사용자 사진·RM 판정 완료. 후속 round 1 timeout·최종 제출 누락·정책 부적격 보존. 후속 남은 코드 동결·Python 28개/host 6개 통과·COM3 수락과 관측 전 독립 보존 완료. 사용자 요청으로 같은 artifact를 재업로드하고 확인된 66.57초 영상으로 후속 RM review를 적용했다. RM1·RM5 pass/RM2·RM3·RM4 partial로 기준 미도달이다. 최종 430개 파일을 독립 복원했고 누적 수정 예산 소진으로 추가 회차는 없다.
   미도달이면 자신의 직전 결과와 허용된 관측 근거만 전달하며 잔여 회차/예산 안에서 후속을 시작한다.
4. 다음 대상: 해당 series 처리 후 다음 대상을 진행한다. 날짜가 바뀐 미시작 예약은 새 ID·ledger·receipt로 준비한다.
   작업 상태: 진행 중. AGY Flash `20261005-antigravity-cli-agy-flash-r01`을 03:09:41 KST 시작했다. 동결 runner와 새 예약·receipt·동일 입력을 유지한다. 모델 호출 전 런처 CLI 인자 오류 1건은 후보 미호출 상태로 보존하고 정정했다. 2026-10-05 일반 포장 도구의 `firmware/build/` 경로 지원을 [별도 운영 계획](2026-10-04-evidence-artifact-layout-remediation.md)에 따라 보완하고 첫 실제 package의 독립 복원을 확인했다. 원본 거부 기록은 유지한다.
   당시 다음 4개 예약은 2026-10-05 새 ID·개별 ledger·receipt와 현재 환경 재확인까지 완료했다. 이 중 AGY Flash 최초 호출은 종료됐으며 나머지 AGY Pro·Codex Sol/Luna 3개는 미시작이다. 준비 중 모델 호출은 0회였으며 다음 시작은 현재 series 평가와 허용 후속 처리 뒤다. AGY 종료 후 작업은 [평가 계획](2026-10-05-agy-flash-initial-evaluation.md)을 따른다.
   당시 Flash 최초의 종료 후 평가를 마치고 자기 동결 source·관측·기대·근거만 연결한 후속 `20261005-antigravity-cli-agy-flash-r02`를 같은 모델/profile/권한으로 실행했다. 이후 후속 최종 평가·501개 파일의 독립 복원을 마쳤으며 Flash 잔여 5,710.781초·2회는 사용자 요청으로 보류한다.
   2026-10-05 다음 모델 재개 지시로 Pro 최초를 시작하고 첫 command 거부로 종료한 환경 실패를 보존했다. 코드·펌웨어·제출물은 없으며 정책 eligible·RM1 fail/RM2~RM5 not_run, 338개 파일의 독립 복원을 확인했다. 자기 직전 결과의 고정 근거만 전달한 Pro 후속 `20261005-antigravity-cli-agy-pro-r02`가 실행 중이다. 새 receipt·native model/cwd/request-review를 확인했으며 보드는 Flash 후속 원본을 유지한다. [Pro 최초 계획](2026-10-05-agy-pro-initial-launch.md)과 [Pro 후속 계획](2026-10-05-agy-pro-followup-execution.md)을 따른다.
   위 r02 시작 시점 이후 r02·r03도 native command 거부로 종료했고 정책/RM·원본 비용·각 독립 복원을 마쳤다. [남은 후속 계획](2026-10-05-agy-pro-remaining-followups.md)의 마지막 r04가 실행 중이다. 새 회차마다 자기 직전 source와 고정 관측만 전달하며 원본 권한·baseline·공통 입력은 유지한다.
   22:58:07 KST 마지막 r04도 거부 후 종료했고 최종 평가·361개 파일의 독립 복원과 partial host 보완 검증을 마쳤다. 후속 최대 3회에 도달해 Pro series는 종료다. Pro 누적 677.5초·정규화 660,989 token과 정책 eligible·RM1 fail/RM2~RM5 not_run, 최종 제출·firmware 누락을 보존한다. 다음 Codex Sol/Luna는 아직 시작하지 않았다.
   이후 사용자 지시로 [Codex Sol 최초 계획](2026-10-05-codex-sol-initial-launch.md)의 독립 호출을 23:56:01.520 KST에 시작했다. 실제 thread/process argv와 같은 날짜 미실행 예약·현재 도구/native inventory를 확인했다. 실행 중 제품 source를 운영자가 고치거나 피드백·serial/flash를 제공하지 않는다. 최초 종료 후 동결·평가하며 firmware가 있으면 업로드·실물 관측으로 이어간다. Codex Luna는 함께 실행하지 않는다.
   2026-10-06 00:37:01.691 KST Sol 최초가 completed로 종료됐다. [최초 평가](2026-10-06-codex-sol-initial-evaluation.md)는 정책 eligible·RM1 pass/RM2~RM5 fail다. 공통 frame 0·1을 host/실제 장치가 SCHEMA_INVALID로 거부했고, 영상과 BOOT 무반응 보고를 연결했다. 453개 파일의 최종 독립 감사를 마쳤다. 추적된 build 출력은 새 후속 준비 사본에서만 제거하고 source 동일성을 확인해야 하며 원본 commit·비용·판정은 보존한다.
   원래 예약·중단·실패 비용은 보존한다. 전체 비교 완료는 15개 독립 series와 필요한 후속/관측/적격성 집계가 끝난 시점이다.

## 중단과 재개

실행 process는 대화의 토큰 한도와 분리해 최대 실행 시간을 자체 적용한다. launcher PID·명령·console 경로를 남긴다.
재개 시 manifest·ledger·process부터 확인하고 running 후보를 다시 실행하지 않는다.
강제 종료 후 running 기록이 남으면 자식 종료·원본 로그·실제 경과 시간을 확인하고 기존 reconcile 절차를 따른다.
모델/도구 오류와 관측 불가능 사유를 감추거나 자동으로 완료·적격 처리하지 않는다.
