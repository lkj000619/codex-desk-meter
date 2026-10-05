# Codex Sol 남은 후속 실행

목표: 같은 Sol 모델·medium·profile·공통 과제와 자기 직전 동결 구현으로 남은 수정 비용과 제품 도달 여부를 기록한다. 기존 정책 위반으로 series 품질 적격성이 invalid인 사실과 모든 실패 비용을 유지한다.
상태: 후속2 `20261006-codex-cli-gpt-6-sol-r02`는 04:19:16 KST 구현·제출 종료, 원본622.562초·418개 파일 독립 복원과 host 검증 완료다. 04:21:15 KST 같은 artifact를 COM3에 올려 공통 frame0·1 수락을 확인했다. 새 LCD/BOOT/연속 유지 관측과 정식 RM/최종 package는 대기다. 잔여6,127.751초·1회는 이 평가 뒤에만 처리한다. 기존 series 품질 부적격과 후속2 파이프9건 위반, 원본 source/비용/과거 판정을 유지한다. Luna 미시작이다.
원본: [운영 계약](../experiments/comparison-operating-contract.md) · [후속 1회차](2026-10-06-codex-sol-followup-execution.md) · [현재 상태](../experiments/next-comparison-readiness.md).

- [x] 직전 평가·원본 비용·동결 commit `3a09f26f2f375f4f45bebb79eb5902667a3ccb1a`·정책 정정을 보존한다.
- [x] 직전 관측·고정 기대·hash와 잔여 예산만 담은 후속 2회차를 준비한다. 다른 후보 구현이나 수정 방법을 제공하지 않는다.
- [x] 새 사본에서 생성 build 출력·추적된 Python bytecode만 제외하고 실제 source 18개·고정 입력 57개·profile 동일성을 증명한다. local Git exclude에 생성 경로만 추가하며 이전 원본·전역 설정은 유지한다.
- [x] 새 run-bound receipt·native inventory·같은 CLI/SDK를 확인하고 한 번 호출한다. 이번 timeout은 잔여 예산의 내림값 이하이며 실제 thread/argv/시작 근거를 보존한다.
- [x] 후속2 종료 후 source·비용·정책·host·같은 artifact 업로드/수신과 관측 전 독립 복원을 완료하고 실제 후속622.562초를 차감한다.
- [ ] 사용자 새 artifact 관측을 연결해 정식 RM를 한 번 적용하고 최종 package/독립 감사를 완료한다. 사진·BOOT·30초 유지 근거를 얻기 전 평가 완료로 표시하지 않는다.
- [ ] 기준 도달 또는 최대 3회/누적 7,200초에 도달하면 series를 종료한다. 추가 후보 호출을 임의 재시도하지 않는다.

완료 조건: 각 호출의 종료·평가·보존·누적 비용과 실제 보드 artifact가 연결되며, 남은 한도와 정책 적격성·RM·제품 합격을 구분한다. 최초·후속 1회차를 재실행하거나 과거 판정 원본을 덮어쓰지 않는다. 새 bytecode 제외는 준비 사본의 생성 캐시 정비이며 후보 구현·권한 변경은 아니다.

후속2 원본 commit `09ecdaf1645511033b4efda40bb2a9e3b96ae8f7`, app SHA-256 `486cd84ba91af26fd86ea8642c166c4708b7e3537806cf18f93d9579c23c0377`이다.
[관측 전 독립 복원](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/restore-audit.json)·
[실물 기록](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/operator-observation/hardware-slot.json)·
[관측 대기](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/operator-observation/optical-observation-pending.json)를 연결했다. 후보 형식 검증 통과나 장치 frame 수락만으로 LCD/RM/제품 합격을 표시하지 않는다.
