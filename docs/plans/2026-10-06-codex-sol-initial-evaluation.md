# Codex Sol 최초 결과 평가와 보존

목표: 종료된 `20261005-codex-cli-gpt-6-sol-r01`의 첫 구현·제출·원본 비용을 보존하고, 동일 fixture와 동결 펌웨어의 실물 관측을 연결해 정책·RM·제품 판정을 구분한다.
상태: 2026-10-06 최초 평가·보존 작업 완료. 정책 eligible·RM1 pass/RM2~RM5 fail·reference fail/product_pass false다. 최종 package 453개 파일의 독립 감사를 마쳤고 공개 원본 bytes·staged Git blob·문서 링크를 검증해 이 기록을 커밋한다. 제품 완성이 아니며 후속 예산 7,200초·3회를 보존한다.
원본: [운영 계약](../experiments/comparison-operating-contract.md) · [RM 목록](../experiments/reference-match-matrix.md) · [현재 상태](../experiments/next-comparison-readiness.md) · [최초 실행 계획](2026-10-05-codex-sol-initial-launch.md).

- [x] 실제 종료·원본 manifest/ledger/stdout/stderr·57개 고정 입력·운영자 개입을 확인한다. 별도 저장소 source와 원본 artifact를 동결한다.
- [x] native 행동을 검토하고 정책 적격성을 적용한다. 원본 계측의 `user_interventions: null`과 별도 감사의 0회를 구분한다.
- [x] 표준 package와 별도 복원을 검증한다. 자체 시험 통과, 공통 collector/receiver 실패, 제출 형식 유효성을 각각 기록한다.
- [x] 동결된 app/bootloader/partition을 COM3에 올리고 동일 reference frame 0·1을 전송한다. 장치의 거부 로그를 source의 실제 분기와 대조한다.
- [x] 사용자 영상의 원본 bytes·hash·시점·관측 범위를 보존한다. LCD·BOOT·유지 관측을 검토하고 RM review를 한 번 적용한다.
- [x] 최종 evidence package를 독립 복원하고 현재 상태·진행 기록·비용·공개 snapshot을 검증해 커밋한다.

완료 조건: 최초 원본과 최종 판정의 연결이 검증돼 있으며 미관측 항목을 합격으로 채우지 않는다. 구현·제출 종료, 평가 완료, reference 도달, 전체 제품 합격, series 종료를 구분한다. 최초 2,460.156초와 cache 포함 정규화 token은 보존하며 후속 예산을 최초 시간으로 차감하지 않는다.

후속 선행 조건: 동결 commit `2257fffaa5316773d08fe3353356112c7002159d`에는 생성된 `build/`·`build-host/` 출력이 추적돼 있다. 이전 회차 절대 경로와 executable이 후속 checkout에 승계되지 않도록 **새 후속 준비 사본에서만** 생성 출력을 제외하고 날짜·범위·source 동일성 근거를 기록해야 한다. 최초 commit/tag·package·판정은 수정하지 않는다. 자신의 직전 고정 관측만 전달하고 동일 profile·입력·권한, 후속 최대 3회 AND 누적 7,200초를 유지한다. Codex Luna는 이 평가와 필요한 후속 처리를 마치기 전에 시작하지 않는다.
