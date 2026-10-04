# GPT-6 비교 모델 갱신과 문서상 실행 준비 판단

확인일: 2026-10-03. 사용자 요청에 따라 기존 여섯 비교 대상 중 Codex 두 모델만 GPT-6로 변경했다.
본 실험은 시작하지 않았다. 원래 GPT-5.6 준비 결과를 새 모델의 결과로 변경하지 않았다.

## 변경한 설정

- Codex Sol: `gpt-5.6-sol` → `gpt-6-sol`, medium 유지.
- Codex Luna: `gpt-5.6-luna` → `gpt-6-luna`, max 유지.
- OpenCode Muse, AGY Flash/Pro/Opus: 네 프로필의 bytes를 2026-10-02와 동일하게 유지.
- 새 프로필은 [next-profiles-20261003](../../experiments/config/next-profiles-20261003/README.md)에 저장.
  이전 profile·receipt·freeze·package는 보존하고 현재 선택은 readiness와 README에서 새 목록으로 연결.

## 확인한 근거

로컬 Codex CLI는 `codex-cli 0.159.2`였다. native 모델 cache의 조회 시각은
`2026-10-02T16:24:48.323752500Z`이며, 두 요청 ID와 각각 medium/max 지원 표기가 있다.
[선별한 모델 메타데이터](model-catalog.json)는 인증 내용이나 다른 사용자 설정을 포함하지 않는다.
목록에 있다는 사실은 실제 모델 호출·계정 권한·quota·120분 연속 가용성을 보증하지 않는다.

[검증 목록](validation.json): 6개 JSON schema 통과. 기존 네 프로필은 고정 baseline
`85ba1089226a2e3198983a42eea375a3fd7e6ed0`의 `benchmark.py check`에서 inputs_valid.
GPT-6 두 프로필의 check는 **blocked**다. 새 settings_inventory에 실제 재확인 전임을 뜻하는
`pending`을 남겼기 때문에 runner의 미확정 설정 검사에서 거부됐다. 모델 endpoint를 호출해 받은 오류가 아니다.
미검증 표시를 지워 검사만 통과시키지 않았다. 실제 확인 후 설정과 근거를 갱신하고 check·receipt를 다시 검증한다.

## 문서상 지금 실험해도 되는가

**과제와 평가 절차의 문서 준비는 갖춰져 있다. 현재 GPT-6 설정으로 즉시 본 실험 시작은 아직 아니다.**
다음 세 가지가 시작 전 남은 실행 준비 조건이다.

1. GPT-6 두 설정으로 실제 CLI의 read/write/list/host_build/host_test/idf_build/vendor_reference/
   telemetry/settings를 확인하고 model·effort·profile에 묶인 capability 근거를 남긴다.
2. 모든 후보의 실행 당일 환경을 확인하고 새 run ID·ledger와 profile/input/reference/comparison에
   맞는 receipt를 연결한다. 이전 GPT-5.6 및 10월 2일 식별자를 그대로 재사용하지 않는다.
3. 보완한 운영자 관측 도구 snapshot/hash, RM5 공통 절차와 단일 보드 관측 일정을 공통 평가 조건으로 고정한다.

이는 제품이 성공해야 실험을 시작한다는 조건이 아니다. 후보 firmware의 실제 화면·수신·BOOT·오류 복구,
수신 로그 연결과 terminal artifact 검증은 후보 결과가 나온 뒤 평가한다. 실패도 결과로 보존한다.
최초 120분·후속 최대 3회/누적 120분, fixture-only, BSP 후보 구현, reference와 product_pass 분리를 유지한다.

보완 도구는 [이전 보완 검증](../documentation-assessment-20261002/remediation.md)에서 181개 중
180개 통과·1개 skip이었다. 이번 모델 설정 변경은 실행 코드를 수정하지 않아 같은 전체 suite를 반복하지 않았다.
이번에는 profile schema·고정 입력 check·모델/effort 대조·기존 네 profile bytes·문서 링크를 검증했다.
실물·GPT-6 capability·현재 quota는 확인하지 않았다. Flash SDK의 기존 간헐 오류와 계측 한계도 여전히 기록 대상이다.

이후 현재 상태의 원본은 [준비 상태](../../docs/experiments/next-comparison-readiness.md)다.
